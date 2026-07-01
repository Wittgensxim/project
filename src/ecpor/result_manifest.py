"""Build small tracked manifests for generated experiment results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .environment import file_sha256, git_info


P7A_SUMMARY_KEYS = {
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
    "best_depth1_text_delta_pct_vs_anchor",
    "best_depth2_text_delta_pct_vs_anchor",
    "best_depth2_delta_pct_vs_parent",
    "depth2_improves_over_depth1_best",
    "best_candidate_depth",
}


def build_result_manifest(
    *,
    stage: str,
    description: str,
    inputs: Mapping[str, str | Path],
    outputs: Mapping[str, str | Path],
    tools: Mapping[str, str | Path],
    summary: Mapping[str, Any],
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo_git = git_info(repo_root)
    generated_from = result_generated_from_commit or repo_git.commit
    manifest: dict[str, Any] = {
        "manifest_schema_version": 1,
        "stage": stage,
        "description": description,
        "result_generated_from_commit": generated_from,
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": repo_git.dirty,
        "inputs": _path_map(inputs),
        "outputs": _path_map(outputs),
        "sha256": _sha256_map(inputs) | _sha256_map(outputs) | _sha256_map(tools),
        "tools": _tool_map(tools),
        "summary": dict(summary),
    }
    if extra:
        manifest.update(extra)
    return manifest


def build_p7a_manifest(
    *,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    stage: str = "P7a",
    description: str = (
        "Bounded two-swap smoke test seeded from P6 one-swap candidates."
    ),
) -> dict[str, Any]:
    out = Path(output_dir)
    candidates_csv = out / "two_swap_candidates.csv"
    seeds_csv = out / "two_swap_seeds.csv"
    attempts_csv = out / "two_swap_attempts.csv"
    pipeline_runs_csv = out / "two_swap_pipeline_runs.csv"
    object_size_csv = out / "two_swap_object_size.csv"
    report_md = out / "two_swap_report.md"
    p6_rows = _load_csv(p6_object_size_csv)
    seed_rows = _load_csv(seeds_csv)
    p7_candidates = _load_csv(candidates_csv)
    p7_object_rows = _load_csv(object_size_csv)
    extra = {
        "seed": _seed_from_seed_rows(seed_rows) or _seed_from_p6_rows(p6_rows),
        "seeds": _seeds_from_seed_rows(seed_rows),
        "depth2_candidates": _depth2_candidates(
            candidate_rows=p7_candidates,
            object_rows=p7_object_rows,
            p6_rows=p6_rows,
        ),
        "scope_limits": {
            "runtime_benchmarks": False,
            "full_searcher": False,
            "codegen_path": "llc -filetype=obj",
        },
    }
    return build_result_manifest(
        stage=stage,
        description=description,
        inputs={
            "p5_candidates_csv": p5_candidates_csv,
            "p5_pipeline_runs_csv": p5_pipeline_runs_csv,
            "p6_object_size_csv": p6_object_size_csv,
            "passspec": passspec_path,
        },
        outputs={
            "output_dir": output_dir,
            "cert_dir": cert_dir,
            "two_swap_seeds_csv": seeds_csv,
            "two_swap_candidates_csv": candidates_csv,
            "two_swap_attempts_csv": attempts_csv,
            "two_swap_pipeline_runs_csv": pipeline_runs_csv,
            "two_swap_object_size_csv": object_size_csv,
            "two_swap_report": report_md,
        },
        tools={
            "opt": opt_path,
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(_parse_key_value_report(report_md), P7A_SUMMARY_KEYS),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra=extra,
    )


def build_p6_5_manifest(
    *,
    p4_attempts_csv: str | Path,
    p5_dir: str | Path,
    p6_dir: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    p5 = Path(p5_dir)
    p6 = Path(p6_dir)
    code_size_report = p6 / "code_size_report.md"
    return build_result_manifest(
        stage="P6.5",
        description=(
            "Clean P6 code-size run after provenance and candidate-source hardening."
        ),
        inputs={
            "p4_attempts_csv": p4_attempts_csv,
            "p5_output_dir": p5,
            "p6_output_dir": p6,
            "p5_report": p5 / "report.md",
            "candidates_csv": p5 / "candidates.csv",
            "pipeline_runs_csv": p5 / "pipeline_runs.csv",
            "object_size_csv": p6 / "object_size.csv",
            "code_size_report": code_size_report,
        },
        outputs={},
        tools={
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_parse_key_value_report(code_size_report),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "manifest_note": (
                "This tracked manifest records a clean generated-data run. "
                "The generated data under data/outputs is intentionally not tracked."
            )
        },
    )


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build tracked result manifests.")
    subparsers = parser.add_subparsers(dest="stage", required=True)

    p7a = subparsers.add_parser("p7a", help="Build a P7a/P7b two-swap manifest.")
    p7a.add_argument("--out-manifest", required=True)
    p7a.add_argument("--p5-candidates", required=True)
    p7a.add_argument("--p5-pipeline-runs", required=True)
    p7a.add_argument("--p6-object-size", required=True)
    p7a.add_argument("--passspec", required=True)
    p7a.add_argument("--output-dir", required=True)
    p7a.add_argument("--cert-dir", required=True)
    p7a.add_argument("--opt", required=True)
    p7a.add_argument("--llc", required=True)
    p7a.add_argument("--llvm-size", required=True)
    p7a.add_argument("--repo-root", default=".")
    p7a.add_argument("--result-generated-from-commit")
    p7a.add_argument("--stage-name", default="P7a")
    p7a.add_argument(
        "--description",
        default="Bounded two-swap smoke test seeded from P6 one-swap candidates.",
    )

    p65 = subparsers.add_parser("p6-5", help="Build a P6.5 code-size manifest.")
    p65.add_argument("--out-manifest", required=True)
    p65.add_argument("--p4-attempts", required=True)
    p65.add_argument("--p5-dir", required=True)
    p65.add_argument("--p6-dir", required=True)
    p65.add_argument("--llc", required=True)
    p65.add_argument("--llvm-size", required=True)
    p65.add_argument("--repo-root", default=".")
    p65.add_argument("--result-generated-from-commit")

    args = parser.parse_args(argv)
    if args.stage == "p7a":
        manifest = build_p7a_manifest(
            p5_candidates_csv=args.p5_candidates,
            p5_pipeline_runs_csv=args.p5_pipeline_runs,
            p6_object_size_csv=args.p6_object_size,
            passspec_path=args.passspec,
            output_dir=args.output_dir,
            cert_dir=args.cert_dir,
            opt_path=args.opt,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
        )
    else:
        manifest = build_p6_5_manifest(
            p4_attempts_csv=args.p4_attempts,
            p5_dir=args.p5_dir,
            p6_dir=args.p6_dir,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    write_manifest(args.out_manifest, manifest)
    return 0


def _path_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {key: _path_text(path) for key, path in paths.items()}


def _tool_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {f"{key}_path": str(path) for key, path in paths.items()}


def _sha256_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, value in paths.items():
        path = Path(value)
        if path.exists() and path.is_file():
            hashes[key] = file_sha256(path)
    return hashes


def _parse_key_value_report(path: str | Path) -> dict[str, Any]:
    report = Path(path)
    if not report.exists():
        return {}
    summary: dict[str, Any] = {}
    for raw_line in report.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key or " " in key:
            continue
        summary[key] = _parse_scalar(value.strip())
    return summary


def _filter_keys(
    values: Mapping[str, Any], allowed_keys: set[str]
) -> dict[str, Any]:
    return {key: values[key] for key in allowed_keys if key in values}


def _parse_scalar(value: str) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    if value == "":
        return ""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _seed_from_p6_rows(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    seeds = [
        row
        for row in rows
        if row.get("source") == "single_swap"
        and _parse_optional_float(row.get("text_delta_pct")) is not None
        and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) < 0.0
    ]
    if not seeds:
        return {}
    seed = min(seeds, key=lambda row: _parse_optional_float(row["text_delta_pct"]) or 0.0)
    return {
        "program": seed.get("program", ""),
        "candidate_id": seed.get("candidate_id", ""),
        "depth1_text_delta_pct_vs_anchor": _parse_optional_float(
            seed.get("text_delta_pct")
        ),
    }


def _seed_from_seed_rows(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    seeds = _seeds_from_seed_rows(rows)
    return seeds[0] if seeds else {}


def _seeds_from_seed_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "program": row.get("program", ""),
                "candidate_id": row.get("seed_candidate_id")
                or row.get("candidate_id", ""),
                "seed_pipeline": row.get("seed_pipeline", ""),
                "depth1_text_delta_pct_vs_anchor": _parse_optional_float(
                    row.get("seed_text_delta_pct") or row.get("text_delta_pct")
                ),
                "seed_rank": _parse_optional_int(row.get("seed_rank")),
                "seed_reason": row.get("seed_reason", ""),
            }
        )
    return result


def _depth2_candidates(
    *,
    candidate_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    p6_rows: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    object_by_id = {row.get("candidate_id", ""): row for row in object_rows}
    parent_pct = {
        row.get("candidate_id", ""): _parse_optional_float(row.get("text_delta_pct"))
        for row in p6_rows
    }
    result: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row.get("source") != "two_swap":
            continue
        object_row = object_by_id.get(row.get("candidate_id", ""), {})
        text_pct = _parse_optional_float(object_row.get("text_delta_pct"))
        parent_id = row.get("parent_candidate_id", "")
        parent_text_pct = parent_pct.get(parent_id)
        delta_vs_parent = (
            None
            if text_pct is None or parent_text_pct is None
            else text_pct - parent_text_pct
        )
        result.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "swap_index": _parse_optional_int(row.get("swap_index")),
                "pass_a": row.get("pass_a", ""),
                "pass_b": row.get("pass_b", ""),
                "parent_candidate_id": parent_id,
                "candidate_pipeline": row.get("candidate_pipeline", ""),
                "text_delta_pct_vs_anchor": text_pct,
                "delta_pct_vs_parent": delta_vs_parent,
            }
        )
    return result


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    candidate = Path(path)
    if not candidate.exists():
        return []
    with candidate.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value))


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _path_text(path: str | Path) -> str:
    return Path(path).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
