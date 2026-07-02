"""Summarize the current ECPOR scalar-pass MVP from existing result files."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .environment import file_sha256, git_info


BENCHMARK_SET_FIELDS = [
    "benchmark_set",
    "programs",
    "pair_matrix_certificates",
    "reproduced_certificates",
    "hard_false_independent",
    "static_false_negative_after_repair",
    "adjacent_attempts",
    "certified_events",
    "not_certified_events",
    "one_swap_candidates",
    "both_smaller_programs",
]

REDUCTION_FIELDS = [
    "benchmark_set",
    "pair_matrix_certificates",
    "certified_independent",
    "not_certified_independent",
    "reproduced_certificates",
    "certificate_reproduction_rate",
    "hard_false_independent",
    "static_candidate_recall",
    "static_false_negative_after_repair",
    "adjacent_attempts",
    "adjacent_certified_events",
    "adjacent_not_certified_events",
    "adjacent_run_failed",
    "certified_pruning_ratio_attempted",
]

OBJECTIVE_FIELDS = [
    "benchmark_set",
    "one_swap_candidates",
    "object_size_evaluated",
    "smaller_text",
    "equal_text",
    "larger_text",
    "ir_different_but_text_equal",
    "ir_different_but_text_equal_rate",
    "direction_comparisons",
    "direction_agreement_count",
    "direction_agreement_rate",
    "both_smaller_cases",
    "both_smaller_programs",
    "smaller_only_llc",
    "smaller_only_clang",
    "direction_disagreement_count",
]

ATTRIBUTION_FIELDS = [
    "benchmark_set",
    "program",
    "pair",
    "opcode_delta",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "evidence_level",
]


@dataclass(frozen=True)
class BenchmarkSetInputs:
    name: str
    pair_summary_csv: str | Path
    static_filter_report: str | Path
    lazy_validation_report: str | Path
    p5_candidates_csv: str | Path
    p6_object_size_csv: str | Path
    codegen_compare_csv: str | Path
    attribution_summary_csv: str | Path


@dataclass(frozen=True)
class MvpSummaryResult:
    benchmark_rows: list[dict[str, str]]
    reduction_rows: list[dict[str, str]]
    objective_rows: list[dict[str, str]]
    attribution_rows: list[dict[str, str]]
    summary: dict[str, Any]
    manifest: dict[str, Any] | None


def run_mvp_summary(
    *,
    output_dir: str | Path,
    benchmark_sets: Sequence[BenchmarkSetInputs] | None = None,
    manifest_path: str | Path | None = None,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> MvpSummaryResult:
    inputs = list(benchmark_sets or default_benchmark_sets())
    benchmark_rows: list[dict[str, str]] = []
    reduction_rows: list[dict[str, str]] = []
    objective_rows: list[dict[str, str]] = []
    attribution_rows: list[dict[str, str]] = []

    for item in inputs:
        pair_rows = _load_csv(item.pair_summary_csv)
        static_summary = _parse_key_value_report(item.static_filter_report)
        lazy_summary = _parse_key_value_report(item.lazy_validation_report)
        candidate_rows = _load_csv(item.p5_candidates_csv)
        object_rows = _load_csv(item.p6_object_size_csv)
        compare_rows = _load_csv(item.codegen_compare_csv)
        attribution_source_rows = _load_csv(item.attribution_summary_csv)

        reduction = _build_reduction_row(
            item.name, pair_rows, static_summary, lazy_summary
        )
        objective = _build_objective_row(
            item.name, candidate_rows, object_rows, compare_rows
        )
        benchmark_rows.append(_build_benchmark_row(item.name, pair_rows, reduction, objective))
        reduction_rows.append(reduction)
        objective_rows.append(objective)
        attribution_rows.extend(
            _build_attribution_rows(item.name, attribution_source_rows)
        )

    summary = _build_summary(benchmark_rows, reduction_rows, objective_rows, attribution_rows)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_root / "benchmark_set_summary.csv",
        benchmark_rows,
        BENCHMARK_SET_FIELDS,
    )
    _write_csv(output_root / "reduction_summary.csv", reduction_rows, REDUCTION_FIELDS)
    _write_csv(output_root / "objective_summary.csv", objective_rows, OBJECTIVE_FIELDS)
    _write_csv(
        output_root / "attribution_case_summary.csv",
        attribution_rows,
        ATTRIBUTION_FIELDS,
    )
    (output_root / "mvp_summary_report.md").write_text(
        build_mvp_summary_report(
            summary=summary,
            benchmark_rows=benchmark_rows,
            reduction_rows=reduction_rows,
            objective_rows=objective_rows,
            attribution_rows=attribution_rows,
        ),
        encoding="utf-8",
    )

    manifest = build_mvp_summary_manifest(
        benchmark_sets=inputs,
        output_dir=output_root,
        summary=summary,
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
    )
    if manifest_path is not None:
        write_manifest(manifest_path, manifest)

    return MvpSummaryResult(
        benchmark_rows=benchmark_rows,
        reduction_rows=reduction_rows,
        objective_rows=objective_rows,
        attribution_rows=attribution_rows,
        summary=summary,
        manifest=manifest,
    )


def default_benchmark_sets() -> list[BenchmarkSetInputs]:
    return [
        BenchmarkSetInputs(
            name="Stanford-8",
            pair_summary_csv="data/outputs/cert_summary.csv",
            static_filter_report="data/outputs/static_filter_report_per_program.md",
            lazy_validation_report="data/outputs/lazy_validation_p4_e83c409_first.md",
            p5_candidates_csv="data/outputs/bounded_local_p5_p6_final/candidates.csv",
            p6_object_size_csv="data/outputs/code_size_p6_final/object_size.csv",
            codegen_compare_csv=(
                "data/outputs/codegen_sensitivity_p8a/"
                "p8a_codegen_direction_compare.csv"
            ),
            attribution_summary_csv=(
                "data/outputs/core_evidence_report/ecpor_attribution_summary.csv"
            ),
        ),
        BenchmarkSetInputs(
            name="Misc8",
            pair_summary_csv="data/outputs/cert_summary_p8b_misc8_pre.csv",
            static_filter_report="data/outputs/static_filter_report_p8b_misc8_post.md",
            lazy_validation_report="data/outputs/lazy_validation_p8b_misc8/report.md",
            p5_candidates_csv="data/outputs/bounded_local_p8b_misc8/candidates.csv",
            p6_object_size_csv="data/outputs/code_size_p8b_misc8/object_size.csv",
            codegen_compare_csv=(
                "data/outputs/codegen_sensitivity_p8b_misc8/"
                "p8a_codegen_direction_compare.csv"
            ),
            attribution_summary_csv=(
                "data/outputs/core_evidence_report_misc8/"
                "misc8_attribution_summary.csv"
            ),
        ),
    ]


def build_mvp_summary_report(
    *,
    summary: Mapping[str, Any],
    benchmark_rows: Sequence[Mapping[str, str]],
    reduction_rows: Sequence[Mapping[str, str]],
    objective_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> str:
    lines = [
        "# P9-1 MVP Summary",
        "",
        "本报告只汇总已有 Stanford-8 与 Misc8 结果；不新增搜索、不新增 certificate、不运行 LLVM pipeline 或 runtime benchmark。",
        "",
        f"BenchmarkSets: {summary['BenchmarkSets']}",
        f"TotalPrograms: {summary['TotalPrograms']}",
        f"TotalPairMatrixCertificates: {summary['TotalPairMatrixCertificates']}",
        f"TotalReproducedCertificates: {summary['TotalReproducedCertificates']}",
        f"TotalHardFalseIndependent: {summary['TotalHardFalseIndependent']}",
        f"TotalAdjacentAttempts: {summary['TotalAdjacentAttempts']}",
        f"TotalCertifiedEvents: {summary['TotalCertifiedEvents']}",
        f"TotalNotCertifiedEvents: {summary['TotalNotCertifiedEvents']}",
        f"TotalOneSwapCandidates: {summary['TotalOneSwapCandidates']}",
        f"TotalBothSmallerPrograms: {summary['TotalBothSmallerPrograms']}",
        f"AttributionCases: {summary['AttributionCases']}",
        "NoNewExperiments: True",
        "",
        "## Benchmark Set Summary",
        "",
        "| benchmark | programs | pair certs | reproduced | hard false | static FN | adjacent attempts | certified | not certified | one-swap | both-smaller programs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in benchmark_rows:
        lines.append(
            "| {benchmark_set} | {programs} | {pair_matrix_certificates} | "
            "{reproduced_certificates} | {hard_false_independent} | "
            "{static_false_negative_after_repair} | {adjacent_attempts} | "
            "{certified_events} | {not_certified_events} | {one_swap_candidates} | "
            "{both_smaller_programs} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Reduction Summary",
            "",
            "| benchmark | certified | not certified | reproduction | static recall | pruning ratio attempted |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in reduction_rows:
        lines.append(
            "| {benchmark_set} | {certified_independent} | "
            "{not_certified_independent} | {certificate_reproduction_rate} | "
            "{static_candidate_recall} | {certified_pruning_ratio_attempted} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Objective Summary",
            "",
            "| benchmark | object evaluated | smaller | equal | larger | IR-different text-equal | direction agreement | both-smaller cases |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in objective_rows:
        lines.append(
            "| {benchmark_set} | {object_size_evaluated} | {smaller_text} | "
            "{equal_text} | {larger_text} | {ir_different_but_text_equal} | "
            "{direction_agreement_rate} | {both_smaller_cases} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Attribution Cases",
            "",
            "| benchmark | program | pair | opcode delta | llc pct | clang pct | evidence |",
            "| --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in attribution_rows:
        lines.append(
            "| {benchmark_set} | {program} | {pair} | {opcode_delta} | "
            "{llc_text_delta_pct} | {clang_text_delta_pct} | {evidence_level} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "当前 MVP 的主结果是：state-indexed certificate 可以剪掉大量相邻 pass 顺序；static filter 可以校准到高召回；大量 IR 差异不会传导到 `.text`；少数 both-smaller case 可以被压缩成可复查的单状态归因。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_mvp_summary_manifest(
    *,
    benchmark_sets: Sequence[BenchmarkSetInputs],
    output_dir: str | Path,
    summary: Mapping[str, Any],
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    output_root = Path(output_dir)
    repo_git = git_info(repo_root)
    inputs = _input_paths(benchmark_sets)
    outputs = {
        "output_dir": output_root,
        "benchmark_set_summary_csv": output_root / "benchmark_set_summary.csv",
        "reduction_summary_csv": output_root / "reduction_summary.csv",
        "objective_summary_csv": output_root / "objective_summary.csv",
        "attribution_case_summary_csv": output_root / "attribution_case_summary.csv",
        "mvp_summary_report": output_root / "mvp_summary_report.md",
    }
    return {
        "manifest_schema_version": 1,
        "stage": "P9-1",
        "description": "Final MVP summary across Stanford-8 and Misc8 existing evidence.",
        "result_generated_from_commit": result_generated_from_commit
        or repo_git.commit,
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": repo_git.dirty,
        "inputs": _path_map(inputs),
        "outputs": _path_map(outputs),
        "sha256": _sha256_map(inputs) | _sha256_map(outputs),
        "summary": dict(summary),
        "scope_limits": {
            "new_experiments": False,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "llvm_pipeline_rerun": False,
            "benchmark_sets": [item.name for item in benchmark_sets],
        },
    }


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _build_benchmark_row(
    name: str,
    pair_rows: Sequence[Mapping[str, str]],
    reduction: Mapping[str, str],
    objective: Mapping[str, str],
) -> dict[str, str]:
    programs = {row.get("program", "") for row in pair_rows if row.get("program")}
    return {
        "benchmark_set": name,
        "programs": str(len(programs)),
        "pair_matrix_certificates": str(len(pair_rows)),
        "reproduced_certificates": reduction["reproduced_certificates"],
        "hard_false_independent": reduction["hard_false_independent"],
        "static_false_negative_after_repair": reduction[
            "static_false_negative_after_repair"
        ],
        "adjacent_attempts": reduction["adjacent_attempts"],
        "certified_events": reduction["adjacent_certified_events"],
        "not_certified_events": reduction["adjacent_not_certified_events"],
        "one_swap_candidates": objective["one_swap_candidates"],
        "both_smaller_programs": objective["both_smaller_programs"],
    }


def _build_reduction_row(
    name: str,
    pair_rows: Sequence[Mapping[str, str]],
    static_summary: Mapping[str, Any],
    lazy_summary: Mapping[str, Any],
) -> dict[str, str]:
    certified = sum(
        1 for row in pair_rows if row.get("label") == "certified_independent"
    )
    not_certified = sum(
        1 for row in pair_rows if row.get("label") == "not_certified_independent"
    )
    reproduced = sum(1 for row in pair_rows if _truthy(row.get("reproduced")))
    hard_false = sum(
        1
        for row in pair_rows
        if row.get("label") == "certified_independent"
        and not _truthy(row.get("hard_equal"))
    )
    adjacent_attempts = _string_int(lazy_summary.get("attempted_adjacent_swaps"))
    adjacent_certified = _string_int(lazy_summary.get("certified_independent"))
    return {
        "benchmark_set": name,
        "pair_matrix_certificates": str(len(pair_rows)),
        "certified_independent": str(certified),
        "not_certified_independent": str(not_certified),
        "reproduced_certificates": str(reproduced),
        "certificate_reproduction_rate": _pct(reproduced, len(pair_rows)),
        "hard_false_independent": str(hard_false),
        "static_candidate_recall": str(
            static_summary.get("StaticCandidateRecall", "")
        ),
        "static_false_negative_after_repair": _string_int(
            static_summary.get("StaticFalseNegativeObserved")
        ),
        "adjacent_attempts": adjacent_attempts,
        "adjacent_certified_events": adjacent_certified,
        "adjacent_not_certified_events": _string_int(
            lazy_summary.get("not_certified_independent")
        ),
        "adjacent_run_failed": _string_int(lazy_summary.get("run_failed")),
        "certified_pruning_ratio_attempted": _pct(
            _parse_int(adjacent_certified), _parse_int(adjacent_attempts)
        ),
    }


def _build_objective_row(
    name: str,
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    compare_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    one_swap = [row for row in candidate_rows if row.get("source") == "single_swap"]
    object_evaluated = [
        row
        for row in object_rows
        if row.get("source") == "single_swap"
        and row.get("text_delta", "") != ""
        and not row.get("compile_failure_kind")
        and not row.get("size_failure_kind")
    ]
    smaller = [row for row in object_evaluated if _parse_float(row.get("text_delta")) < 0]
    equal = [row for row in object_evaluated if _parse_float(row.get("text_delta")) == 0]
    larger = [row for row in object_evaluated if _parse_float(row.get("text_delta")) > 0]
    ir_diff_text_equal = [
        row
        for row in equal
        if not _truthy(row.get("p5_same_as_anchor", "False"))
    ]
    comparisons = [
        row
        for row in compare_rows
        if row.get("source", "single_swap") in {"single_swap", "depth2"}
        and row.get("llc_direction")
        and row.get("clang_direction")
    ]
    agreement = [row for row in comparisons if _truthy(row.get("direction_agree"))]
    both_smaller = [
        row
        for row in comparisons
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    ]
    smaller_only_llc = [
        row
        for row in comparisons
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") != "smaller"
    ]
    smaller_only_clang = [
        row
        for row in comparisons
        if row.get("clang_direction") == "smaller"
        and row.get("llc_direction") != "smaller"
    ]
    both_smaller_programs = {
        row.get("program", "") for row in both_smaller if row.get("program")
    }
    return {
        "benchmark_set": name,
        "one_swap_candidates": str(len(one_swap)),
        "object_size_evaluated": str(len(object_evaluated)),
        "smaller_text": str(len(smaller)),
        "equal_text": str(len(equal)),
        "larger_text": str(len(larger)),
        "ir_different_but_text_equal": str(len(ir_diff_text_equal)),
        "ir_different_but_text_equal_rate": _pct(
            len(ir_diff_text_equal), len(object_evaluated)
        ),
        "direction_comparisons": str(len(comparisons)),
        "direction_agreement_count": str(len(agreement)),
        "direction_agreement_rate": _pct(len(agreement), len(comparisons)),
        "both_smaller_cases": str(len(both_smaller)),
        "both_smaller_programs": str(len(both_smaller_programs)),
        "smaller_only_llc": str(len(smaller_only_llc)),
        "smaller_only_clang": str(len(smaller_only_clang)),
        "direction_disagreement_count": str(len(comparisons) - len(agreement)),
    }


def _build_attribution_rows(
    benchmark_set: str, rows: Sequence[Mapping[str, str]]
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "benchmark_set": benchmark_set,
                "program": row.get("program", ""),
                "pair": row.get("pair", ""),
                "opcode_delta": row.get("opcode_delta")
                or row.get("final_opcode_delta_nonzero", ""),
                "llc_text_delta_pct": row.get("llc_text_delta_pct", ""),
                "clang_text_delta_pct": row.get("clang_text_delta_pct", ""),
                "evidence_level": row.get("evidence_level", ""),
            }
        )
    return output


def _build_summary(
    benchmark_rows: Sequence[Mapping[str, str]],
    reduction_rows: Sequence[Mapping[str, str]],
    objective_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "BenchmarkSets": len(benchmark_rows),
        "TotalPrograms": sum(_parse_int(row.get("programs")) for row in benchmark_rows),
        "TotalPairMatrixCertificates": sum(
            _parse_int(row.get("pair_matrix_certificates")) for row in benchmark_rows
        ),
        "TotalReproducedCertificates": sum(
            _parse_int(row.get("reproduced_certificates")) for row in benchmark_rows
        ),
        "TotalHardFalseIndependent": sum(
            _parse_int(row.get("hard_false_independent")) for row in benchmark_rows
        ),
        "TotalAdjacentAttempts": sum(
            _parse_int(row.get("adjacent_attempts")) for row in benchmark_rows
        ),
        "TotalCertifiedEvents": sum(
            _parse_int(row.get("adjacent_certified_events")) for row in reduction_rows
        ),
        "TotalNotCertifiedEvents": sum(
            _parse_int(row.get("adjacent_not_certified_events"))
            for row in reduction_rows
        ),
        "TotalOneSwapCandidates": sum(
            _parse_int(row.get("one_swap_candidates")) for row in benchmark_rows
        ),
        "TotalBothSmallerPrograms": sum(
            _parse_int(row.get("both_smaller_programs")) for row in benchmark_rows
        ),
        "AttributionCases": len(attribution_rows),
        "NoNewExperiments": True,
    }


def _input_paths(benchmark_sets: Sequence[BenchmarkSetInputs]) -> dict[str, str | Path]:
    paths: dict[str, str | Path] = {}
    for item in benchmark_sets:
        key = _manifest_key(item.name)
        paths[f"{key}_pair_summary_csv"] = item.pair_summary_csv
        paths[f"{key}_static_filter_report"] = item.static_filter_report
        paths[f"{key}_lazy_validation_report"] = item.lazy_validation_report
        paths[f"{key}_p5_candidates_csv"] = item.p5_candidates_csv
        paths[f"{key}_p6_object_size_csv"] = item.p6_object_size_csv
        paths[f"{key}_codegen_compare_csv"] = item.codegen_compare_csv
        paths[f"{key}_attribution_summary_csv"] = item.attribution_summary_csv
    return paths


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    candidate = Path(path)
    if not candidate.exists():
        return []
    with candidate.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_key_value_report(path: str | Path) -> dict[str, Any]:
    report = Path(path)
    if not report.exists():
        return {}
    summary: dict[str, Any] = {}
    for raw_line in report.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or " " in key:
            continue
        summary[key] = _parse_scalar(value.strip())
    return summary


def _parse_scalar(value: str) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _path_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {key: Path(path).as_posix() for key, path in paths.items()}


def _sha256_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, value in paths.items():
        path = Path(value)
        if path.exists() and path.is_file():
            hashes[key] = file_sha256(path)
    return hashes


def _manifest_key(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_")


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _parse_int(value: object) -> int:
    if value in {None, ""}:
        return 0
    try:
        return int(float(str(value).strip().rstrip("%")))
    except ValueError:
        return 0


def _parse_float(value: object) -> float:
    if value in {None, ""}:
        return 0.0
    try:
        return float(str(value).strip())
    except ValueError:
        return 0.0


def _string_int(value: object) -> str:
    return str(_parse_int(value))


def _pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator) * 100.0:.2f}%"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the P9-1 MVP summary from existing result files."
    )
    parser.add_argument("--out", default="data/outputs/final_mvp_summary")
    parser.add_argument("--manifest", default="docs/results/mvp_summary_manifest.json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--result-generated-from-commit")
    args = parser.parse_args(argv)
    result = run_mvp_summary(
        output_dir=args.out,
        manifest_path=args.manifest,
        repo_root=args.repo_root,
        result_generated_from_commit=args.result_generated_from_commit,
    )
    report = Path(args.out) / "mvp_summary_report.md"
    print(report.read_text(encoding="utf-8"), end="")
    return 0 if result.summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
