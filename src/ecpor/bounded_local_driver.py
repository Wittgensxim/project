"""P5 bounded local reorder exploration over one adjacent swap."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .batch_certificates import STANFORD_8_PROGRAMS, Program
from .candidate_pipeline import (
    CandidateGeneration,
    CandidatePipeline,
    build_candidate_pipelines,
    load_attempts_csv,
    validate_candidate_invariants,
    write_candidates_csv,
)
from .environment import detect_environment, file_sha256, git_info
from .normalizer import NORMALIZER_VERSION
from .pipeline_runner import (
    PipelineRunRecord,
    run_pipeline_candidate,
    write_pipeline_runs_csv,
)
from .runner import OptPath
from .static_filter import load_pipeline_config


@dataclass(frozen=True)
class BoundedLocalRun:
    candidates: list[CandidatePipeline]
    pipeline_runs: list[PipelineRunRecord]
    summary: dict[str, int]
    candidate_generation: CandidateGeneration
    metadata: dict[str, str]


def run_bounded_local_exploration(
    *,
    programs: Sequence[Program],
    anchor_passes: Sequence[str],
    attempts_csv: str | Path,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str = "unknown",
    llvm_version: str = "unknown",
    normalizer_version: str = NORMALIZER_VERSION,
    pipeline_config_path: str | Path | None = None,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> BoundedLocalRun:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    attempts = load_attempts_csv(attempts_csv)
    program_paths = {program: Path(path) for program, path in programs}
    generation = build_candidate_pipelines(
        programs=list(program_paths),
        anchor_passes=anchor_passes,
        attempts=attempts,
    )
    invariant_errors = validate_candidate_invariants(generation.candidates)
    if invariant_errors:
        raise ValueError("candidate invariant violation: " + "; ".join(invariant_errors))
    write_candidates_csv(output_root / "candidates.csv", generation.candidates)

    records: list[PipelineRunRecord] = []
    anchor_hashes: dict[str, str | None] = {}
    for candidate in generation.candidates:
        input_ir = program_paths[candidate.program]
        if candidate.source == "anchor":
            record = run_pipeline_candidate(
                input_ir,
                candidate,
                opt_path=opt_path,
                output_dir=output_root / "pipeline_outputs",
                nesting=nesting,
                extra_flags=extra_flags,
                timeout_sec=timeout_sec,
            )
            anchor_hashes[candidate.program] = record.hard_hash
        else:
            record = run_pipeline_candidate(
                input_ir,
                candidate,
                opt_path=opt_path,
                output_dir=output_root / "pipeline_outputs",
                anchor_hash=anchor_hashes.get(candidate.program),
                nesting=nesting,
                extra_flags=extra_flags,
                timeout_sec=timeout_sec,
            )
        records.append(record)

    write_pipeline_runs_csv(output_root / "pipeline_runs.csv", records)
    summary = summarize_bounded_local_run(attempts, generation, records)
    metadata = build_run_metadata(
        attempts_csv=attempts_csv,
        env_id=env_id,
        llvm_version=llvm_version,
        normalizer_version=normalizer_version,
        pipeline_config_path=pipeline_config_path,
    )
    report = build_bounded_local_report(summary, generation, records, metadata=metadata)
    (output_root / "report.md").write_text(report, encoding="utf-8")
    return BoundedLocalRun(
        candidates=generation.candidates,
        pipeline_runs=records,
        summary=summary,
        candidate_generation=generation,
        metadata=metadata,
    )


def summarize_bounded_local_run(
    attempts: Sequence[dict[str, str]],
    generation: CandidateGeneration,
    records: Sequence[PipelineRunRecord],
) -> dict[str, int]:
    label_counts = Counter(row.get("label", "") for row in attempts)
    action_counts = Counter(row.get("action", "") for row in attempts)
    pipeline_failed = sum(1 for record in records if record.failure_kind)
    same_as_anchor = sum(1 for record in records if record.same_as_anchor)
    different_from_anchor = sum(
        1
        for record in records
        if not record.same_as_anchor and not record.failure_kind
    )
    candidate_by_id = {candidate.candidate_id: candidate for candidate in generation.candidates}
    anchor_records = [
        record
        for record in records
        if candidate_by_id.get(record.candidate_id)
        and candidate_by_id[record.candidate_id].source == "anchor"
    ]
    single_swap_records = [
        record
        for record in records
        if candidate_by_id.get(record.candidate_id)
        and candidate_by_id[record.candidate_id].source == "single_swap"
    ]
    return {
        "p4_attempted_adjacent_swaps": len(attempts),
        "p4_candidate_swaps": sum(
            1 for row in attempts if row.get("static_decision") == "candidate"
        ),
        "p4_low_priority_skipped": action_counts["skipped_low_priority"],
        "p4_dynamic_tests": sum(
            1 for row in attempts if row.get("dynamic_test", "").lower() == "true"
        ),
        "p4_certified_independent": label_counts["certified_independent"],
        "p4_not_certified_independent": label_counts["not_certified_independent"],
        "p4_run_failed": label_counts["run_failed"],
        "anchor_candidates": generation.summary["anchor"],
        "single_swap_candidates": generation.summary["single_swap"],
        "collapsed_certified_independent": generation.summary[
            "collapsed_certified_independent"
        ],
        "frozen_by_static_filter": generation.summary["frozen_by_static_filter"],
        "invalid_run_failed": generation.summary["invalid_run_failed"],
        "pipeline_runs": len(records),
        "pipeline_run_failed": pipeline_failed,
        "same_as_anchor": same_as_anchor,
        "different_from_anchor": different_from_anchor,
        "anchor_runs": len(anchor_records),
        "single_swap_runs": len(single_swap_records),
        "single_swap_same_as_anchor": sum(
            1 for record in single_swap_records if record.same_as_anchor
        ),
        "single_swap_different_from_anchor": sum(
            1
            for record in single_swap_records
            if not record.same_as_anchor and not record.failure_kind
        ),
    }


def build_bounded_local_report(
    summary: dict[str, int],
    generation: CandidateGeneration,
    records: Sequence[PipelineRunRecord],
    *,
    metadata: dict[str, str] | None = None,
) -> str:
    lines = [
        "# P5 Bounded Local Reorder Report",
        "",
        "P5 explores only the anchor pipeline and one adjacent swap for each P4 not_certified_independent result.",
        "It does not select an optimum and it does not evaluate code size.",
        "",
    ]
    if metadata:
        lines.extend(
            [
                "## Run metadata",
                f"ecpor_git_commit: {metadata['ecpor_git_commit']}",
                f"ecpor_git_dirty: {metadata['ecpor_git_dirty']}",
                f"env_id: {metadata['env_id']}",
                f"llvm_version: {metadata['llvm_version']}",
                f"normalizer_version: {metadata['normalizer_version']}",
                f"attempts_csv: {metadata['attempts_csv']}",
                f"attempts_csv_sha256: {metadata['attempts_csv_sha256']}",
                f"pipeline_config: {metadata['pipeline_config']}",
                f"pipeline_config_sha256: {metadata['pipeline_config_sha256']}",
                "",
            ]
        )
    lines.extend([
        "## P4 adjacent validation summary",
        f"attempted_adjacent_swaps: {summary['p4_attempted_adjacent_swaps']}",
        f"candidate_swaps: {summary['p4_candidate_swaps']}",
        f"low_priority_skipped: {summary['p4_low_priority_skipped']}",
        f"dynamic_tests: {summary['p4_dynamic_tests']}",
        f"certified_independent: {summary['p4_certified_independent']}",
        f"not_certified_independent: {summary['p4_not_certified_independent']}",
        f"run_failed: {summary['p4_run_failed']}",
        "",
        "## Candidate generation summary",
        f"anchor_candidates: {summary['anchor_candidates']}",
        f"single_swap_candidates: {summary['single_swap_candidates']}",
        f"collapsed_certified_independent: {summary['collapsed_certified_independent']}",
        f"frozen_by_static_filter: {summary['frozen_by_static_filter']}",
        f"invalid_run_failed: {summary['invalid_run_failed']}",
        "",
        "## Full pipeline run summary",
        f"pipeline_runs: {summary['pipeline_runs']}",
        f"pipeline_run_failed: {summary['pipeline_run_failed']}",
        f"same_as_anchor: {summary['same_as_anchor']}",
        f"different_from_anchor: {summary['different_from_anchor']}",
        f"anchor_runs: {summary['anchor_runs']}",
        f"single_swap_runs: {summary['single_swap_runs']}",
        f"single_swap_same_as_anchor: {summary['single_swap_same_as_anchor']}",
        f"single_swap_different_from_anchor: {summary['single_swap_different_from_anchor']}",
        "",
        "## Examples",
    ])
    examples = _example_records(records)
    if examples:
        lines.extend(examples)
    else:
        lines.append("No successful single-swap candidate records were available.")
    if generation.evidence_rows:
        lines.extend(["", "## Collapsed or frozen evidence"])
        for row in generation.evidence_rows[:8]:
            lines.append(
                "{program}: {pass_a},{pass_b} -> {evidence_label} ({reason})".format(
                    **row
                )
            )
    return "\n".join(lines) + "\n"


def build_run_metadata(
    *,
    attempts_csv: str | Path,
    env_id: str,
    llvm_version: str,
    normalizer_version: str,
    pipeline_config_path: str | Path | None,
) -> dict[str, str]:
    repo_git = git_info(Path(__file__).resolve().parents[2])
    pipeline_path = Path(pipeline_config_path) if pipeline_config_path else None
    return {
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": str(repo_git.dirty),
        "env_id": env_id,
        "llvm_version": llvm_version,
        "normalizer_version": normalizer_version,
        "attempts_csv": str(attempts_csv),
        "attempts_csv_sha256": file_sha256(attempts_csv),
        "pipeline_config": "" if pipeline_path is None else str(pipeline_path),
        "pipeline_config_sha256": (
            "" if pipeline_path is None else file_sha256(pipeline_path)
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run P5 bounded local one-swap exploration."
    )
    parser.add_argument("--program-preset", choices=["stanford-8"], default="stanford-8")
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument("--attempts-csv", required=True)
    parser.add_argument("--out", default="data/outputs/bounded_local_p5")
    parser.add_argument("--opt", default="opt")
    parser.add_argument("--opt-arg", action="append", default=[])
    parser.add_argument("--env-id")
    parser.add_argument("--llvm-version")
    parser.add_argument("--normalizer-version", default=NORMALIZER_VERSION)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    pipeline = load_pipeline_config(args.pipeline)
    opt_path: OptPath = [args.opt, *args.opt_arg] if args.opt_arg else args.opt
    env_id = args.env_id
    llvm_version = args.llvm_version
    if env_id is None or llvm_version is None:
        detected = _detect_environment_for_opt(args.opt)
        env_id = env_id or detected.env_id
        llvm_version = llvm_version or detected.llvm_version
    run = run_bounded_local_exploration(
        programs=STANFORD_8_PROGRAMS,
        anchor_passes=list(pipeline["passes"]),
        attempts_csv=args.attempts_csv,
        opt_path=opt_path,
        output_dir=args.out,
        env_id=env_id,
        llvm_version=llvm_version,
        normalizer_version=args.normalizer_version,
        pipeline_config_path=args.pipeline,
        timeout_sec=args.timeout_sec,
    )
    print(
        build_bounded_local_report(
            run.summary,
            run.candidate_generation,
            run.pipeline_runs,
            metadata=run.metadata,
        ),
        end="",
    )
    return 0


def _example_records(records: Sequence[PipelineRunRecord]) -> list[str]:
    non_anchor = [record for record in records if "__anchor" not in record.candidate_id]
    lines: list[str] = []
    for record in non_anchor[:6]:
        relation = "same_as_anchor" if record.same_as_anchor else "different_from_anchor"
        if record.failure_kind:
            relation = f"failed:{record.failure_kind}"
        lines.append(
            f"{record.program} {record.candidate_id}: {relation}, "
            f"num_instructions={record.num_instructions}, "
            f"num_basic_blocks={record.num_basic_blocks}"
        )
    return lines


def _detect_environment_for_opt(opt: str) -> object:
    opt_path = Path(opt)
    if opt_path.exists():
        return detect_environment(opt_path.parent)
    return detect_environment()


if __name__ == "__main__":
    raise SystemExit(main())
