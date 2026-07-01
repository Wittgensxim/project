"""P7a bounded two-swap smoke exploration."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .batch_certificates import STANFORD_8_PROGRAMS, Program
from .candidate_pipeline import CandidatePipeline
from .certificate_db import CertificateDB
from .code_size_evaluator import run_code_size_evaluation, write_object_size_csv
from .environment import DEFAULT_EXECUTION_MODEL, detect_environment, git_info
from .feature_scan import scan_ir_file
from .lazy_validator import validate_adjacent_swap
from .normalizer import NORMALIZER_VERSION
from .pipeline_dedup import pipeline_sequence_hash
from .pipeline_runner import (
    PipelineRunRecord,
    run_pipeline_candidate,
    write_pipeline_runs_csv,
)
from .runner import OptPath
from .state_materializer import materialize_prefix_state
from .static_filter import classify_pair, load_passspec, load_pipeline_config
from .two_swap_seed import select_seed_rows, write_seed_csv


P7_ATTEMPT_FIELDS = [
    "program",
    "seed_candidate_id",
    "seed_pipeline",
    "swap_index",
    "prefix_passes",
    "state_path",
    "state_hash",
    "pass_a",
    "pass_b",
    "static_decision",
    "static_reason",
    "action",
    "label",
    "cache_hit",
    "dynamic_test",
    "reproduced",
    "cert_id",
]

P7_CANDIDATE_FIELDS = [
    "program",
    "candidate_id",
    "depth",
    "parent_candidate_id",
    "source",
    "base_pipeline",
    "candidate_pipeline",
    "pipeline_sequence_hash",
    "swap_index",
    "pass_a",
    "pass_b",
    "prefix_state_hash",
    "validation_label",
    "cert_id",
    "reason",
    "swap_path",
]


@dataclass(frozen=True)
class BoundedTwoSwapRun:
    seed_rows: list[dict[str, str]]
    attempt_rows: list[dict[str, str]]
    candidate_rows: list[dict[str, str]]
    pipeline_runs: list[PipelineRunRecord]
    object_size_rows: list[dict[str, str]]
    summary: dict[str, Any]
    metadata: dict[str, str]


def run_bounded_two_swap_smoke(
    *,
    programs: Sequence[Program],
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    passspec: dict[str, dict[str, Any]],
    cert_db: CertificateDB,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    llvm_version: str,
    llc_path: str | Path | Sequence[str | Path] = "llc",
    llvm_size_path: str | Path | Sequence[str | Path] = "llvm-size",
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    region_id: str = "function_scalar_mvp",
    window_size: int = 7,
    timeout_sec: float = 30.0,
    seed_mode: str = "smaller-only",
    max_seeds_per_program: int = 3,
    max_unique_depth2_per_program: int | None = None,
    max_total_depth2: int | None = None,
    stage_name: str = "P7a",
) -> BoundedTwoSwapRun:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    program_paths = {program: Path(path) for program, path in programs}
    p5_candidates = _load_csv(p5_candidates_csv)
    p6_rows = _load_csv(p6_object_size_csv)
    p5_candidate_by_id = {row["candidate_id"]: row for row in p5_candidates}
    seed_rows = select_seed_rows(
        p6_rows,
        p5_candidate_by_id,
        seed_mode=seed_mode,
        max_seeds_per_program=max_seeds_per_program,
    )
    write_seed_csv(output_root / "two_swap_seeds.csv", seed_rows)
    reserved_hashes = _reserved_hashes_by_program(p5_candidates)

    attempt_rows: list[dict[str, str]] = []
    generated_rows: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []
    for seed_size_row in seed_rows:
        seed = p5_candidate_by_id[seed_size_row["candidate_id"]]
        program = seed["program"]
        input_ir = program_paths[program]
        seed_passes = _split_pipeline(seed["candidate_pipeline"])
        for swap_index in range(len(seed_passes) - 1):
            attempt, candidate = _attempt_second_swap(
                input_ir=input_ir,
                seed=seed,
                seed_passes=seed_passes,
                swap_index=swap_index,
                passspec=passspec,
                cert_db=cert_db,
                opt_path=opt_path,
                output_root=output_root,
                env_id=env_id,
                llvm_version=llvm_version,
                execution_model=execution_model,
                normalizer_version=normalizer_version,
                nesting=nesting,
                extra_flags=extra_flags,
                region_id=region_id,
                window_size=window_size,
                timeout_sec=timeout_sec,
            )
            attempt_rows.append(attempt)
            if candidate is None:
                continue
            if candidate["pipeline_sequence_hash"] in reserved_hashes.get(program, set()):
                duplicate_rows.append(candidate)
                continue
            generated_rows.append(candidate)

    deduped_unique_rows, deduped_duplicate_rows = _deduplicate_depth2_rows(generated_rows)
    depth2_rows, budget_skipped_rows = _apply_depth2_budgets(
        deduped_unique_rows,
        max_unique_depth2_per_program=max_unique_depth2_per_program,
        max_total_depth2=max_total_depth2,
    )
    duplicate_rows.extend(deduped_duplicate_rows)
    _validate_depth2_invariants(
        depth2_rows,
        max_unique_depth2_per_program=max_unique_depth2_per_program,
        max_total_depth2=max_total_depth2,
    )
    candidate_rows = _anchor_rows(p5_candidates) + depth2_rows
    write_p7_candidates_csv(output_root / "two_swap_candidates.csv", candidate_rows)
    write_p7_attempts_csv(output_root / "two_swap_attempts.csv", attempt_rows)

    pipeline_runs = _run_full_pipelines(
        programs=program_paths,
        candidate_rows=candidate_rows,
        opt_path=opt_path,
        output_dir=output_root / "pipeline_outputs",
        nesting=nesting,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    write_pipeline_runs_csv(output_root / "two_swap_pipeline_runs.csv", pipeline_runs)

    code_size = run_code_size_evaluation(
        candidates_csv=output_root / "two_swap_candidates.csv",
        pipeline_runs_csv=output_root / "two_swap_pipeline_runs.csv",
        pipeline_output_dir=output_root / "pipeline_outputs",
        output_dir=output_root,
        llc_path=llc_path,
        llvm_size_path=llvm_size_path,
        timeout_sec=timeout_sec,
        p5_report_path=output_root / "two_swap_report.md",
    )
    write_object_size_csv(output_root / "two_swap_object_size.csv", code_size.rows)
    metadata = _build_metadata(
        p5_candidates_csv=p5_candidates_csv,
        p5_pipeline_runs_csv=p5_pipeline_runs_csv,
        p6_object_size_csv=p6_object_size_csv,
        env_id=env_id,
        llvm_version=llvm_version,
        normalizer_version=normalizer_version,
    )
    summary = summarize_two_swap_run(
        seed_rows=seed_rows,
        attempt_rows=attempt_rows,
        candidate_rows=candidate_rows,
        duplicate_rows=duplicate_rows,
        budget_skipped_rows=budget_skipped_rows,
        pipeline_runs=pipeline_runs,
        object_size_rows=code_size.rows,
        object_summary=code_size.summary,
        seed_mode=seed_mode,
        max_seeds_per_program=max_seeds_per_program,
        max_unique_depth2_per_program=max_unique_depth2_per_program,
        max_total_depth2=max_total_depth2,
    )
    report = build_two_swap_report(summary, metadata=metadata, stage_name=stage_name)
    (output_root / "two_swap_report.md").write_text(report, encoding="utf-8")
    return BoundedTwoSwapRun(
        seed_rows=seed_rows,
        attempt_rows=attempt_rows,
        candidate_rows=candidate_rows,
        pipeline_runs=pipeline_runs,
        object_size_rows=code_size.rows,
        summary=summary,
        metadata=metadata,
    )


def write_p7_attempts_csv(
    path: str | Path, rows: Sequence[dict[str, str]]
) -> None:
    _write_csv(path, rows, P7_ATTEMPT_FIELDS)


def write_p7_candidates_csv(
    path: str | Path, rows: Sequence[dict[str, str]]
) -> None:
    _write_csv(path, rows, P7_CANDIDATE_FIELDS)


def summarize_two_swap_run(
    *,
    seed_rows: Sequence[dict[str, str]],
    attempt_rows: Sequence[dict[str, str]],
    candidate_rows: Sequence[dict[str, str]],
    duplicate_rows: Sequence[dict[str, str]],
    budget_skipped_rows: Sequence[dict[str, str]],
    pipeline_runs: Sequence[PipelineRunRecord],
    object_size_rows: Sequence[dict[str, str]],
    object_summary: dict[str, Any],
    seed_mode: str,
    max_seeds_per_program: int,
    max_unique_depth2_per_program: int | None,
    max_total_depth2: int | None,
) -> dict[str, Any]:
    depth2_rows = [row for row in candidate_rows if row.get("depth") == "2"]
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    run_sources = [
        candidate_by_id.get(record.candidate_id, {}).get("source", "")
        for record in pipeline_runs
    ]
    raw_depth2_candidates = (
        len(depth2_rows) + len(duplicate_rows) + len(budget_skipped_rows)
    )
    best_depth1 = _best_depth1_text_delta_pct(seed_rows)
    best_depth2 = _best_depth2_text_delta_pct(object_size_rows)
    best_depth2_vs_parent = _best_depth2_delta_pct_vs_parent(
        depth2_rows=depth2_rows,
        object_size_rows=object_size_rows,
        seed_rows=seed_rows,
    )
    return {
        "seed_candidates": len(seed_rows),
        "selected_seed_candidates": len(seed_rows),
        "selected_smaller_seeds": _count_delta_kind(seed_rows, "smaller"),
        "selected_equal_seeds": _count_delta_kind(seed_rows, "equal"),
        "selected_seed_programs": len({row.get("program", "") for row in seed_rows}),
        "seed_mode": seed_mode,
        "max_seeds_per_program": max_seeds_per_program,
        "attempted_second_swaps": len(attempt_rows),
        "static_candidate_second_swaps": sum(
            1 for row in attempt_rows if row.get("static_decision") == "candidate"
        ),
        "low_priority_skipped": sum(
            1 for row in attempt_rows if row.get("action") == "skipped_low_priority"
        ),
        "validated_second_swaps": sum(
            1
            for row in attempt_rows
            if row.get("cache_hit") == "True" or row.get("dynamic_test") == "True"
        ),
        "cache_hits": sum(1 for row in attempt_rows if row.get("cache_hit") == "True"),
        "dynamic_tests": sum(
            1 for row in attempt_rows if row.get("dynamic_test") == "True"
        ),
        "certified_independent": sum(
            1 for row in attempt_rows if row.get("label") == "certified_independent"
        ),
        "not_certified_independent": sum(
            1
            for row in attempt_rows
            if row.get("label") == "not_certified_independent"
        ),
        "run_failed": sum(1 for row in attempt_rows if row.get("label") == "run_failed"),
        "raw_depth2_candidates": raw_depth2_candidates,
        "duplicate_sequences": len(duplicate_rows),
        "unique_depth2_candidates_before_budget": len(depth2_rows)
        + len(budget_skipped_rows),
        "budget_skipped_depth2_candidates": len(budget_skipped_rows),
        "unique_depth2_candidates": len(depth2_rows),
        "max_unique_depth2_per_program": max_unique_depth2_per_program or 0,
        "max_total_unique_depth2": max_total_depth2 or 0,
        "max_observed_depth2_per_program": _max_depth2_per_program(depth2_rows),
        "anchor_runs": sum(1 for source in run_sources if source == "anchor"),
        "depth1_seed_runs": sum(1 for source in run_sources if source == "single_swap"),
        "depth2_candidate_runs": sum(1 for source in run_sources if source == "two_swap"),
        "total_pipeline_runs": len(pipeline_runs),
        "pipeline_run_failed": sum(1 for record in pipeline_runs if record.failure_kind),
        "object_build_failed": object_summary["object_build_failed"],
        "size_parse_failed": object_summary["size_parse_failed"],
        "depth1_smaller_text": _count_delta_kind(seed_rows, "smaller"),
        "depth1_equal_text": _count_delta_kind(seed_rows, "equal"),
        "depth1_larger_text": _count_delta_kind(seed_rows, "larger"),
        "depth2_smaller_text": _count_delta_kind(
            [row for row in object_size_rows if row.get("source") == "two_swap"],
            "smaller",
        ),
        "depth2_equal_text": _count_delta_kind(
            [row for row in object_size_rows if row.get("source") == "two_swap"],
            "equal",
        ),
        "depth2_larger_text": _count_delta_kind(
            [row for row in object_size_rows if row.get("source") == "two_swap"],
            "larger",
        ),
        "best_depth1_text_delta_pct_vs_anchor": best_depth1,
        "best_depth2_text_delta_pct_vs_anchor": best_depth2,
        "best_depth2_delta_pct_vs_parent": best_depth2_vs_parent,
        "depth2_improves_over_depth1_best": best_depth2 < best_depth1,
        "best_candidate_depth": _best_candidate_depth(best_depth1, best_depth2),
    }


def build_two_swap_report(
    summary: dict[str, Any],
    *,
    metadata: dict[str, str] | None = None,
    stage_name: str = "P7a",
) -> str:
    title = (
        "P7a Bounded Two-Swap Smoke Report"
        if stage_name == "P7a"
        else f"{stage_name} Bounded Two-Swap Report"
    )
    lines = [
        f"# {title}",
        "",
        f"{stage_name} validates bounded two-swap infrastructure.",
        "It is not a full searcher and it does not run runtime benchmarks.",
        "depth1_seed_runs reuses P5/P6 seed metadata and is not re-run here.",
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
                f"p5_candidates_csv: {metadata['p5_candidates_csv']}",
                f"p5_pipeline_runs_csv: {metadata['p5_pipeline_runs_csv']}",
                f"p6_object_size_csv: {metadata['p6_object_size_csv']}",
                "",
            ]
        )
    for key in [
        "seed_candidates",
        "selected_seed_candidates",
        "selected_smaller_seeds",
        "selected_equal_seeds",
        "selected_seed_programs",
        "seed_mode",
        "max_seeds_per_program",
        "attempted_second_swaps",
        "static_candidate_second_swaps",
        "low_priority_skipped",
        "validated_second_swaps",
        "cache_hits",
        "dynamic_tests",
        "certified_independent",
        "not_certified_independent",
        "run_failed",
        "raw_depth2_candidates",
        "duplicate_sequences",
        "unique_depth2_candidates_before_budget",
        "budget_skipped_depth2_candidates",
        "unique_depth2_candidates",
        "max_unique_depth2_per_program",
        "max_total_unique_depth2",
        "max_observed_depth2_per_program",
        "anchor_runs",
        "depth1_seed_runs",
        "depth2_candidate_runs",
        "total_pipeline_runs",
        "pipeline_run_failed",
        "object_build_failed",
        "size_parse_failed",
        "depth1_smaller_text",
        "depth1_equal_text",
        "depth1_larger_text",
        "depth2_smaller_text",
        "depth2_equal_text",
        "depth2_larger_text",
    ]:
        lines.append(f"{key}: {summary[key]}")
    lines.append(
        "best_depth1_text_delta_pct_vs_anchor: "
        f"{summary['best_depth1_text_delta_pct_vs_anchor']:.4f}"
    )
    lines.append(
        "best_depth2_text_delta_pct_vs_anchor: "
        f"{summary['best_depth2_text_delta_pct_vs_anchor']:.4f}"
    )
    lines.append(
        "best_depth2_delta_pct_vs_parent: "
        f"{summary['best_depth2_delta_pct_vs_parent']:.4f}"
    )
    lines.append(
        "depth2_improves_over_depth1_best: "
        f"{summary['depth2_improves_over_depth1_best']}"
    )
    lines.append(f"best_candidate_depth: {summary['best_candidate_depth']}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run P7a bounded two-swap smoke exploration."
    )
    parser.add_argument("--program-preset", choices=["stanford-8"], default="stanford-8")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--p5-dir", default="data/outputs/bounded_local_p5_p6_final")
    parser.add_argument(
        "--p6-object-size",
        default="data/outputs/code_size_p6_final/object_size.csv",
    )
    parser.add_argument("--out", default="data/outputs/bounded_two_swap_p7a")
    parser.add_argument("--cert-dir", default="data/certs/bounded_two_swap_p7a")
    parser.add_argument("--opt", default="E:/llvm/build/bin/opt.exe")
    parser.add_argument("--llc", default="E:/llvm/build/bin/llc.exe")
    parser.add_argument("--llvm-size", default="E:/llvm/build/bin/llvm-size.exe")
    parser.add_argument("--env-id")
    parser.add_argument("--llvm-version")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument(
        "--seed-mode",
        choices=["smaller-only", "top-k-per-program"],
        default="smaller-only",
    )
    parser.add_argument("--max-seeds-per-program", type=int, default=3)
    parser.add_argument("--max-unique-depth2-per-program", type=int)
    parser.add_argument("--max-total-depth2", type=int)
    parser.add_argument("--stage-name", default="P7a")
    args = parser.parse_args(argv)

    env_id = args.env_id
    llvm_version = args.llvm_version
    if env_id is None or llvm_version is None:
        detected = _detect_environment_for_opt(args.opt)
        env_id = env_id or detected.env_id
        llvm_version = llvm_version or detected.llvm_version
    run = run_bounded_two_swap_smoke(
        programs=STANFORD_8_PROGRAMS,
        p5_candidates_csv=Path(args.p5_dir) / "candidates.csv",
        p5_pipeline_runs_csv=Path(args.p5_dir) / "pipeline_runs.csv",
        p6_object_size_csv=args.p6_object_size,
        passspec=load_passspec(args.passspec),
        cert_db=CertificateDB(args.cert_dir),
        opt_path=args.opt,
        output_dir=args.out,
        env_id=env_id,
        llvm_version=llvm_version,
        llc_path=args.llc,
        llvm_size_path=args.llvm_size,
        timeout_sec=args.timeout_sec,
        seed_mode=args.seed_mode,
        max_seeds_per_program=args.max_seeds_per_program,
        max_unique_depth2_per_program=args.max_unique_depth2_per_program,
        max_total_depth2=args.max_total_depth2,
        stage_name=args.stage_name,
    )
    print(
        build_two_swap_report(
            run.summary,
            metadata=run.metadata,
            stage_name=args.stage_name,
        ),
        end="",
    )
    return 0


def _attempt_second_swap(
    *,
    input_ir: Path,
    seed: dict[str, str],
    seed_passes: Sequence[str],
    swap_index: int,
    passspec: dict[str, dict[str, Any]],
    cert_db: CertificateDB,
    opt_path: OptPath,
    output_root: Path,
    env_id: str,
    llvm_version: str,
    execution_model: str,
    normalizer_version: str,
    nesting: str,
    extra_flags: Sequence[str],
    region_id: str,
    window_size: int,
    timeout_sec: float,
) -> tuple[dict[str, str], dict[str, str] | None]:
    program = seed["program"]
    prefix = list(seed_passes[:swap_index])
    pass_a = seed_passes[swap_index]
    pass_b = seed_passes[swap_index + 1]
    program_root = output_root / _safe_name(program) / _safe_name(seed["candidate_id"])
    state = materialize_prefix_state(
        input_ir,
        prefix,
        opt_path=opt_path,
        output_dir=program_root / "prefix_states",
        env_id=env_id,
        nesting=nesting,
        normalizer_version=normalizer_version,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    if not state.state_hash:
        return (
            _attempt_row(
                seed=seed,
                seed_passes=seed_passes,
                swap_index=swap_index,
                prefix=prefix,
                state_path=str(state.path),
                state_hash="",
                pass_a=pass_a,
                pass_b=pass_b,
                static_decision="prefix_failed",
                static_reason="prefix materialization failed",
                action="prefix_failed",
                label="run_failed",
                cache_hit=False,
                dynamic_test=False,
                reproduced=None,
                cert_id="",
            ),
            None,
        )
    decision = classify_pair(
        pass_a,
        pass_b,
        passspec,
        program_features=scan_ir_file(state.path),
        distance=1,
        window_size=window_size,
    )
    validation = validate_adjacent_swap(
        state.path,
        pass_a,
        pass_b,
        static_decision=decision["decision"],
        cert_db=cert_db,
        opt_path=opt_path,
        output_dir=program_root / "lazy_validation",
        env_id=env_id,
        llvm_version=llvm_version,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
        nesting=nesting,
        extra_flags=extra_flags,
        region_id=region_id,
        timeout_sec=timeout_sec,
    )
    attempt = _attempt_row(
        seed=seed,
        seed_passes=seed_passes,
        swap_index=swap_index,
        prefix=prefix,
        state_path=str(state.path),
        state_hash=state.state_hash,
        pass_a=pass_a,
        pass_b=pass_b,
        static_decision=decision["decision"],
        static_reason=decision["reason"],
        action=validation.action,
        label=validation.label,
        cache_hit=validation.cache_hit,
        dynamic_test=validation.dynamic_test,
        reproduced=validation.reproduced,
        cert_id=validation.certificate.cert_id if validation.certificate else "",
    )
    if validation.label != "not_certified_independent":
        return attempt, None
    candidate_passes = list(seed_passes)
    candidate_passes[swap_index], candidate_passes[swap_index + 1] = (
        candidate_passes[swap_index + 1],
        candidate_passes[swap_index],
    )
    return attempt, _two_swap_candidate_row(
        seed=seed,
        candidate_passes=candidate_passes,
        swap_index=swap_index,
        pass_a=pass_a,
        pass_b=pass_b,
        prefix_state_hash=validation.state_hash,
        validation_label=validation.label,
        cert_id=attempt["cert_id"],
        reason=validation.reason,
    )


def _run_full_pipelines(
    *,
    programs: dict[str, Path],
    candidate_rows: Sequence[dict[str, str]],
    opt_path: OptPath,
    output_dir: str | Path,
    nesting: str,
    extra_flags: Sequence[str],
    timeout_sec: float,
) -> list[PipelineRunRecord]:
    records: list[PipelineRunRecord] = []
    anchor_hashes: dict[str, str | None] = {}
    for row in candidate_rows:
        candidate = _candidate_pipeline_from_row(row)
        record = run_pipeline_candidate(
            programs[candidate.program],
            candidate,
            opt_path=opt_path,
            output_dir=output_dir,
            anchor_hash=anchor_hashes.get(candidate.program),
            nesting=nesting,
            extra_flags=extra_flags,
            timeout_sec=timeout_sec,
        )
        if row["source"] == "anchor":
            anchor_hashes[candidate.program] = record.hard_hash
        records.append(record)
    return records


def _candidate_pipeline_from_row(row: dict[str, str]) -> CandidatePipeline:
    return CandidatePipeline(
        program=row["program"],
        candidate_id=row["candidate_id"],
        source=row["source"],
        base_pipeline=row["base_pipeline"],
        candidate_pipeline=row["candidate_pipeline"],
        swap_index=_parse_optional_int(row.get("swap_index", "")),
        pass_a=row.get("pass_a", ""),
        pass_b=row.get("pass_b", ""),
        prefix_state_hash=row.get("prefix_state_hash", ""),
        validation_label=row.get("validation_label", ""),
        cert_id=row.get("cert_id", ""),
        reason=row.get("reason", ""),
    )


def _select_smaller_seed_rows(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    seeds = [
        row
        for row in p6_rows
        if row.get("source") == "single_swap"
        and _parse_optional_float(row.get("text_delta_pct")) is not None
        and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) < 0.0
        and row.get("candidate_id", "") in p5_candidate_by_id
    ]
    return sorted(seeds, key=lambda row: _parse_optional_float(row["text_delta_pct"]) or 0.0)


def _deduplicate_depth2_rows(
    rows: Sequence[dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    seen: set[tuple[str, str]] = set()
    unique_rows: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []
    for row in rows:
        passes = _split_pipeline(row.get("candidate_pipeline", ""))
        sequence_hash = row.get("pipeline_sequence_hash") or pipeline_sequence_hash(
            passes
        )
        enriched = {**row, "pipeline_sequence_hash": sequence_hash}
        key = (row.get("program", ""), sequence_hash)
        if key in seen:
            duplicate_rows.append(enriched)
            continue
        seen.add(key)
        unique_rows.append(enriched)
    return unique_rows, duplicate_rows


def _apply_depth2_budgets(
    rows: Sequence[dict[str, str]],
    *,
    max_unique_depth2_per_program: int | None,
    max_total_depth2: int | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if max_unique_depth2_per_program is not None and max_unique_depth2_per_program < 0:
        raise ValueError("max_unique_depth2_per_program must be >= 0")
    if max_total_depth2 is not None and max_total_depth2 < 0:
        raise ValueError("max_total_depth2 must be >= 0")
    kept: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    per_program: Counter[str] = Counter()
    for row in rows:
        program = row.get("program", "")
        if (
            max_total_depth2 is not None
            and len(kept) >= max_total_depth2
        ):
            skipped.append({**row, "budget_skip_reason": "max_total_depth2"})
            continue
        if (
            max_unique_depth2_per_program is not None
            and per_program[program] >= max_unique_depth2_per_program
        ):
            skipped.append(
                {**row, "budget_skip_reason": "max_unique_depth2_per_program"}
            )
            continue
        kept.append(row)
        per_program[program] += 1
    return kept, skipped


def _validate_depth2_invariants(
    rows: Sequence[dict[str, str]],
    *,
    max_unique_depth2_per_program: int | None,
    max_total_depth2: int | None,
) -> None:
    errors: list[str] = []
    if max_total_depth2 is not None and len(rows) > max_total_depth2:
        errors.append(
            f"unique depth2 candidates exceed total budget: {len(rows)} > {max_total_depth2}"
        )
    per_program: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    for row in rows:
        candidate_id = row.get("candidate_id", "")
        program = row.get("program", "")
        sequence_hash = row.get("pipeline_sequence_hash", "")
        per_program[program] += 1
        key = (program, sequence_hash)
        if key in seen:
            errors.append(f"{candidate_id}: duplicate pipeline_sequence_hash for program")
        seen.add(key)
        if not row.get("parent_candidate_id"):
            errors.append(f"{candidate_id}: missing parent_candidate_id")
        if not row.get("prefix_state_hash"):
            errors.append(f"{candidate_id}: missing prefix_state_hash")
        if row.get("validation_label") != "not_certified_independent":
            errors.append(f"{candidate_id}: validation_label is not not_certified_independent")
    if max_unique_depth2_per_program is not None:
        for program, count in per_program.items():
            if count > max_unique_depth2_per_program:
                errors.append(
                    f"{program}: unique depth2 candidates exceed per-program budget "
                    f"({count} > {max_unique_depth2_per_program})"
                )
    if errors:
        raise ValueError("depth2 invariant violation: " + "; ".join(errors))


def _anchor_rows(p5_candidates: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in p5_candidates:
        if row.get("source") != "anchor":
            continue
        passes = _split_pipeline(row["candidate_pipeline"])
        rows.append(
            {
                "program": row["program"],
                "candidate_id": row["candidate_id"],
                "depth": "0",
                "parent_candidate_id": "",
                "source": "anchor",
                "base_pipeline": row["base_pipeline"],
                "candidate_pipeline": row["candidate_pipeline"],
                "pipeline_sequence_hash": pipeline_sequence_hash(passes),
                "swap_index": "",
                "pass_a": "",
                "pass_b": "",
                "prefix_state_hash": "",
                "validation_label": "anchor",
                "cert_id": "",
                "reason": "anchor pipeline",
                "swap_path": "",
            }
        )
    return rows


def _reserved_hashes_by_program(
    p5_candidates: Sequence[dict[str, str]]
) -> dict[str, set[str]]:
    reserved: dict[str, set[str]] = {}
    for row in p5_candidates:
        reserved.setdefault(row["program"], set()).add(
            pipeline_sequence_hash(_split_pipeline(row["candidate_pipeline"]))
        )
    return reserved


def _attempt_row(
    *,
    seed: dict[str, str],
    seed_passes: Sequence[str],
    swap_index: int,
    prefix: Sequence[str],
    state_path: str,
    state_hash: str,
    pass_a: str,
    pass_b: str,
    static_decision: str,
    static_reason: str,
    action: str,
    label: str,
    cache_hit: bool,
    dynamic_test: bool,
    reproduced: bool | None,
    cert_id: str,
) -> dict[str, str]:
    return {
        "program": seed["program"],
        "seed_candidate_id": seed["candidate_id"],
        "seed_pipeline": ",".join(seed_passes),
        "swap_index": str(swap_index),
        "prefix_passes": ",".join(prefix),
        "state_path": state_path,
        "state_hash": state_hash,
        "pass_a": pass_a,
        "pass_b": pass_b,
        "static_decision": static_decision,
        "static_reason": static_reason,
        "action": action,
        "label": label,
        "cache_hit": str(cache_hit),
        "dynamic_test": str(dynamic_test),
        "reproduced": "" if reproduced is None else str(reproduced),
        "cert_id": cert_id,
    }


def _two_swap_candidate_row(
    *,
    seed: dict[str, str],
    candidate_passes: Sequence[str],
    swap_index: int,
    pass_a: str,
    pass_b: str,
    prefix_state_hash: str,
    validation_label: str,
    cert_id: str,
    reason: str,
) -> dict[str, str]:
    pipeline = ",".join(candidate_passes)
    sequence_hash = pipeline_sequence_hash(candidate_passes)
    candidate_id = (
        f"{_safe_name(seed['program'])}__depth2__"
        f"{_safe_name(seed['candidate_id'])}__swap_{swap_index}__"
        f"{_safe_name(pass_a)}__{_safe_name(pass_b)}"
    )
    seed_swap = seed.get("swap_index", "")
    swap_path = ";".join(part for part in [seed_swap, str(swap_index)] if part != "")
    return {
        "program": seed["program"],
        "candidate_id": candidate_id,
        "depth": "2",
        "parent_candidate_id": seed["candidate_id"],
        "source": "two_swap",
        "base_pipeline": seed.get("base_pipeline", ""),
        "candidate_pipeline": pipeline,
        "pipeline_sequence_hash": sequence_hash,
        "swap_index": str(swap_index),
        "pass_a": pass_a,
        "pass_b": pass_b,
        "prefix_state_hash": prefix_state_hash,
        "validation_label": validation_label,
        "cert_id": cert_id,
        "reason": reason,
        "swap_path": swap_path,
    }


def _best_depth1_text_delta_pct(seed_rows: Sequence[dict[str, str]]) -> float:
    values = [
        value
        for value in (
            _parse_optional_float(row.get("text_delta_pct")) for row in seed_rows
        )
        if value is not None
    ]
    return min(values) if values else 0.0


def _count_delta_kind(rows: Sequence[dict[str, str]], kind: str) -> int:
    count = 0
    for row in rows:
        value = _parse_optional_float(row.get("text_delta_pct"))
        if value is None:
            continue
        if kind == "smaller" and value < 0.0:
            count += 1
        elif kind == "equal" and value == 0.0:
            count += 1
        elif kind == "larger" and value > 0.0:
            count += 1
    return count


def _max_depth2_per_program(rows: Sequence[dict[str, str]]) -> int:
    counts = Counter(row.get("program", "") for row in rows)
    return max(counts.values()) if counts else 0


def _best_candidate_depth(best_depth1: float, best_depth2: float) -> int:
    if best_depth2 < best_depth1:
        return 2
    return 1


def _best_depth2_text_delta_pct(object_size_rows: Sequence[dict[str, str]]) -> float:
    values = [
        value
        for value in (
            _parse_optional_float(row.get("text_delta_pct"))
            for row in object_size_rows
            if row.get("source") == "two_swap"
        )
        if value is not None
    ]
    return min(values) if values else 0.0


def _best_depth2_delta_pct_vs_parent(
    *,
    depth2_rows: Sequence[dict[str, str]],
    object_size_rows: Sequence[dict[str, str]],
    seed_rows: Sequence[dict[str, str]],
) -> float:
    parent_pct_by_id = {
        row["candidate_id"]: _parse_optional_float(row.get("text_delta_pct"))
        for row in seed_rows
    }
    parent_by_depth2_id = {
        row["candidate_id"]: row.get("parent_candidate_id", "") for row in depth2_rows
    }
    deltas: list[float] = []
    for row in object_size_rows:
        if row.get("source") != "two_swap":
            continue
        depth2_pct = _parse_optional_float(row.get("text_delta_pct"))
        parent_id = parent_by_depth2_id.get(row.get("candidate_id", ""))
        parent_pct = parent_pct_by_id.get(parent_id or "")
        if depth2_pct is None or parent_pct is None:
            continue
        deltas.append(depth2_pct - parent_pct)
    return min(deltas) if deltas else 0.0


def _build_metadata(
    *,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    env_id: str,
    llvm_version: str,
    normalizer_version: str,
) -> dict[str, str]:
    repo_git = git_info(Path(__file__).resolve().parents[2])
    return {
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": str(repo_git.dirty),
        "env_id": env_id,
        "llvm_version": llvm_version,
        "normalizer_version": normalizer_version,
        "p5_candidates_csv": str(p5_candidates_csv),
        "p5_pipeline_runs_csv": str(p5_pipeline_runs_csv),
        "p6_object_size_csv": str(p6_object_size_csv),
    }


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _split_pipeline(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value))


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _detect_environment_for_opt(opt: str) -> object:
    opt_path = Path(opt)
    if opt_path.exists():
        return detect_environment(opt_path.parent)
    return detect_environment()


if __name__ == "__main__":
    raise SystemExit(main())
