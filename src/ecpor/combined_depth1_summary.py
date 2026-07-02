"""Build the P9-5 combined depth1 summary from retained result files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
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
    "static_false_negative_observed",
    "adjacent_attempts",
    "certified_adjacent_events",
    "not_certified_adjacent_events",
    "low_priority_events",
    "one_swap_candidates",
    "single_swap_same_as_anchor",
    "single_swap_different_from_anchor",
    "both_smaller_programs",
]

REDUCTION_FIELDS = [
    "benchmark_set",
    "pair_matrix_certificates",
    "certified_independent",
    "not_certified_independent",
    "run_failed",
    "reproduced_certificates",
    "certificate_reproduction_rate",
    "hard_false_independent",
    "static_candidate_recall",
    "static_false_negative_observed",
    "adjacent_attempts",
    "candidate_swaps",
    "low_priority_events",
    "dynamic_tests",
    "certified_adjacent_events",
    "not_certified_adjacent_events",
    "adjacent_run_failed",
]

OBJECTIVE_FIELDS = [
    "benchmark_set",
    "one_swap_candidates",
    "object_size_evaluated",
    "smaller_text",
    "equal_text",
    "larger_text",
    "ir_different_but_text_equal_count",
    "ir_different_but_text_equal_rate",
    "direction_comparison_candidates",
    "direction_agreement_rate",
    "smaller_under_both_count",
    "smaller_only_under_llc_count",
    "smaller_only_under_clang_count",
    "direction_disagreement_count",
]

CODEGEN_FIELDS = [
    "benchmark_set",
    "direction_comparison_candidates",
    "direction_agreement_count",
    "direction_agreement_rate",
    "smaller_under_both_count",
    "smaller_only_under_llc_count",
    "smaller_only_under_clang_count",
    "direction_disagreement_count",
    "both_smaller_programs",
]


@dataclass(frozen=True)
class BenchmarkSetInputs:
    name: str
    pair_summary_csv: str | Path
    static_filter_report: str | Path
    lazy_validation_report: str | Path
    p5_candidates_csv: str | Path
    p5_pipeline_runs_csv: str | Path
    p6_object_size_csv: str | Path
    codegen_compare_csv: str | Path
    attribution_summary_csv: str | Path | None = None


@dataclass(frozen=True)
class CombinedDepth1SummaryResult:
    benchmark_rows: list[dict[str, str]]
    reduction_rows: list[dict[str, str]]
    objective_rows: list[dict[str, str]]
    codegen_rows: list[dict[str, str]]
    summary: dict[str, Any]
    manifest: dict[str, Any] | None


def run_combined_depth1_summary(
    *,
    output_dir: str | Path,
    benchmark_sets: Sequence[BenchmarkSetInputs] | None = None,
    manifest_path: str | Path | None = None,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> CombinedDepth1SummaryResult:
    inputs = list(benchmark_sets or default_benchmark_sets())
    _require_input_files(inputs)
    benchmark_rows: list[dict[str, str]] = []
    reduction_rows: list[dict[str, str]] = []
    objective_rows: list[dict[str, str]] = []
    codegen_rows: list[dict[str, str]] = []
    attribution_cases = 0

    for item in inputs:
        pair_rows = _load_csv(item.pair_summary_csv)
        static_summary = _parse_key_value_report(item.static_filter_report)
        lazy_summary = _parse_key_value_report(item.lazy_validation_report)
        candidate_rows = _load_csv(item.p5_candidates_csv)
        pipeline_rows = _load_csv(item.p5_pipeline_runs_csv)
        object_rows = _load_csv(item.p6_object_size_csv)
        compare_rows = _load_csv(item.codegen_compare_csv)
        attribution_rows = _load_optional_csv(item.attribution_summary_csv)

        matrix = _pair_matrix_summary(pair_rows)
        p5 = _p5_summary(candidate_rows, pipeline_rows)
        objective = _objective_summary(item.name, object_rows, p5)
        codegen = _codegen_summary(item.name, compare_rows)
        reduction = _reduction_summary(item.name, matrix, static_summary, lazy_summary)
        benchmark = _benchmark_summary(
            item.name,
            matrix=matrix,
            reduction=reduction,
            objective=objective,
            codegen=codegen,
            p5=p5,
        )
        benchmark_rows.append(benchmark)
        reduction_rows.append(reduction)
        objective_rows.append(objective | _objective_codegen_slice(codegen))
        codegen_rows.append(codegen)
        attribution_cases += len(attribution_rows)

    summary = _combined_summary(
        benchmark_rows=benchmark_rows,
        reduction_rows=reduction_rows,
        objective_rows=objective_rows,
        codegen_rows=codegen_rows,
        attribution_cases=attribution_cases,
    )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_root / "benchmark_set_summary.csv",
        benchmark_rows,
        BENCHMARK_SET_FIELDS,
    )
    _write_csv(
        output_root / "depth1_reduction_summary.csv",
        reduction_rows,
        REDUCTION_FIELDS,
    )
    _write_csv(
        output_root / "depth1_objective_summary.csv",
        objective_rows,
        OBJECTIVE_FIELDS,
    )
    _write_csv(
        output_root / "depth1_codegen_summary.csv",
        codegen_rows,
        CODEGEN_FIELDS,
    )
    report = output_root / "combined_depth1_report.md"
    report.write_text(
        build_combined_depth1_report(
            summary=summary,
            benchmark_rows=benchmark_rows,
            reduction_rows=reduction_rows,
            objective_rows=objective_rows,
            codegen_rows=codegen_rows,
        ),
        encoding="utf-8",
    )

    manifest = build_combined_depth1_summary_manifest(
        benchmark_sets=inputs,
        output_dir=output_root,
        summary=summary,
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
    )
    if manifest_path is not None:
        write_manifest(manifest_path, manifest)

    return CombinedDepth1SummaryResult(
        benchmark_rows=benchmark_rows,
        reduction_rows=reduction_rows,
        objective_rows=objective_rows,
        codegen_rows=codegen_rows,
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
            p5_pipeline_runs_csv="data/outputs/bounded_local_p5_p6_final/pipeline_runs.csv",
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
            p5_pipeline_runs_csv="data/outputs/bounded_local_p8b_misc8/pipeline_runs.csv",
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
        BenchmarkSetInputs(
            name="Diverse8",
            pair_summary_csv="data/outputs/cert_summary_p9_diverse8_pre.csv",
            static_filter_report="data/outputs/static_filter_report_p9_diverse8_pre.md",
            lazy_validation_report="data/outputs/lazy_validation_p9_diverse8/report.md",
            p5_candidates_csv="data/outputs/bounded_local_p9_diverse8/candidates.csv",
            p5_pipeline_runs_csv=(
                "data/outputs/bounded_local_p9_diverse8/pipeline_runs.csv"
            ),
            p6_object_size_csv="data/outputs/code_size_p9_diverse8/object_size.csv",
            codegen_compare_csv=(
                "data/outputs/codegen_sensitivity_p9_diverse8/"
                "p8a_codegen_direction_compare.csv"
            ),
        ),
    ]


def build_combined_depth1_report(
    *,
    summary: Mapping[str, Any],
    benchmark_rows: Sequence[Mapping[str, str]],
    reduction_rows: Sequence[Mapping[str, str]],
    objective_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
) -> str:
    lines = [
        "# P9-5 Combined Depth1 Summary",
        "",
        "This report only aggregates retained depth1 evidence across Stanford-8, "
        "Misc8, and Diverse8. It does not run new LLVM pipelines, generate new "
        "certificates, run two-swap search, or run runtime benchmarks.",
        "",
        f"BenchmarkSets: {summary['BenchmarkSets']}",
        f"TotalPrograms: {summary['TotalPrograms']}",
        f"TotalPairMatrixCertificates: {summary['TotalPairMatrixCertificates']}",
        f"TotalReproducedCertificates: {summary['TotalReproducedCertificates']}",
        f"TotalHardFalseIndependent: {summary['TotalHardFalseIndependent']}",
        f"TotalAdjacentAttempts: {summary['TotalAdjacentAttempts']}",
        f"CertifiedAdjacentEvents: {summary['CertifiedAdjacentEvents']}",
        f"NotCertifiedAdjacentEvents: {summary['NotCertifiedAdjacentEvents']}",
        f"TotalOneSwapCandidates: {summary['TotalOneSwapCandidates']}",
        f"TotalBothSmallerPrograms: {summary['TotalBothSmallerPrograms']}",
        f"Diverse8BothSmallerPrograms: {summary['Diverse8BothSmallerPrograms']}",
        f"AttributionCases: {summary['AttributionCases']}",
        "Depth1Only: True",
        "NoNewExperiments: True",
        "",
        "## Benchmark Set Summary",
        "",
        "| benchmark | programs | pair certs | reproduced | hard false | static FN | adjacent attempts | certified adjacent | not certified adjacent | one-swap | both-smaller programs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in benchmark_rows:
        lines.append(
            "| {benchmark_set} | {programs} | {pair_matrix_certificates} | "
            "{reproduced_certificates} | {hard_false_independent} | "
            "{static_false_negative_observed} | {adjacent_attempts} | "
            "{certified_adjacent_events} | {not_certified_adjacent_events} | "
            "{one_swap_candidates} | {both_smaller_programs} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Reduction Summary",
            "",
            "| benchmark | certified matrix | not certified matrix | adjacent certified | adjacent not certified | low priority |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in reduction_rows:
        lines.append(
            "| {benchmark_set} | {certified_independent} | "
            "{not_certified_independent} | {certified_adjacent_events} | "
            "{not_certified_adjacent_events} | {low_priority_events} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Objective Summary",
            "",
            "| benchmark | one-swap | evaluated | smaller | equal | larger | IR-diff text-equal | direction agreement | both-smaller |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in objective_rows:
        lines.append(
            "| {benchmark_set} | {one_swap_candidates} | "
            "{object_size_evaluated} | {smaller_text} | {equal_text} | "
            "{larger_text} | {ir_different_but_text_equal_count} | "
            "{direction_agreement_rate} | {smaller_under_both_count} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Codegen Summary",
            "",
            "| benchmark | comparisons | agreement | both-smaller | llc-only smaller | clang-only smaller | disagreements |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in codegen_rows:
        lines.append(
            "| {benchmark_set} | {direction_comparison_candidates} | "
            "{direction_agreement_rate} | {smaller_under_both_count} | "
            "{smaller_only_under_llc_count} | {smaller_only_under_clang_count} | "
            "{direction_disagreement_count} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The combined depth1 evidence keeps the original project question in focus: "
            "state-indexed certificates remove many adjacent ordering choices, while "
            "only a small number of depth1 candidates survive into objective-layer "
            "both-smaller cases. Diverse8 adds coverage without adding a new "
            "both-smaller program.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_combined_depth1_summary_manifest(
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
        "depth1_reduction_summary_csv": output_root / "depth1_reduction_summary.csv",
        "depth1_objective_summary_csv": output_root / "depth1_objective_summary.csv",
        "depth1_codegen_summary_csv": output_root / "depth1_codegen_summary.csv",
        "combined_depth1_report": output_root / "combined_depth1_report.md",
    }
    return {
        "manifest_schema_version": 1,
        "stage": "P9-5",
        "description": (
            "Post-MVP combined depth1 summary across Stanford-8, Misc8, and Diverse8."
        ),
        "result_generated_from_commit": result_generated_from_commit
        or repo_git.commit,
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": repo_git.dirty,
        "inputs": _path_map(inputs),
        "outputs": _path_map(outputs),
        "sha256": _sha256_map(inputs) | _sha256_map(outputs),
        "summary": dict(summary),
        "scope_limits": {
            "stage": "P9-5",
            "new_experiments": False,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "two_swap_search": False,
            "summary_only": True,
            "depth": 1,
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


def _pair_matrix_summary(rows: Sequence[Mapping[str, str]]) -> dict[str, str]:
    programs = {row.get("program", "") for row in rows if row.get("program", "")}
    certified = sum(
        1 for row in rows if row.get("label") == "certified_independent"
    )
    not_certified = sum(
        1 for row in rows if row.get("label") == "not_certified_independent"
    )
    run_failed = sum(1 for row in rows if row.get("label") == "run_failed")
    reproduced = sum(1 for row in rows if _truthy(row.get("reproduced")))
    hard_false = sum(
        1
        for row in rows
        if row.get("label") == "certified_independent"
        and not _truthy(row.get("hard_equal"))
    )
    return {
        "programs": str(len(programs)),
        "pair_matrix_certificates": str(len(rows)),
        "certified_independent": str(certified),
        "not_certified_independent": str(not_certified),
        "run_failed": str(run_failed),
        "reproduced_certificates": str(reproduced),
        "certificate_reproduction_rate": _percent(reproduced, len(rows)),
        "hard_false_independent": str(hard_false),
    }


def _reduction_summary(
    name: str,
    matrix: Mapping[str, str],
    static_summary: Mapping[str, Any],
    lazy_summary: Mapping[str, Any],
) -> dict[str, str]:
    return {
        "benchmark_set": name,
        "pair_matrix_certificates": matrix["pair_matrix_certificates"],
        "certified_independent": matrix["certified_independent"],
        "not_certified_independent": matrix["not_certified_independent"],
        "run_failed": matrix["run_failed"],
        "reproduced_certificates": matrix["reproduced_certificates"],
        "certificate_reproduction_rate": matrix["certificate_reproduction_rate"],
        "hard_false_independent": matrix["hard_false_independent"],
        "static_candidate_recall": str(
            static_summary.get("StaticCandidateRecall", "")
        ),
        "static_false_negative_observed": _string_int(
            static_summary.get("StaticFalseNegativeObserved")
        ),
        "adjacent_attempts": _string_int(lazy_summary.get("attempted_adjacent_swaps")),
        "candidate_swaps": _string_int(lazy_summary.get("candidate_swaps")),
        "low_priority_events": _string_int(lazy_summary.get("low_priority_skipped")),
        "dynamic_tests": _string_int(lazy_summary.get("dynamic_tests")),
        "certified_adjacent_events": _string_int(
            lazy_summary.get("certified_independent")
        ),
        "not_certified_adjacent_events": _string_int(
            lazy_summary.get("not_certified_independent")
        ),
        "adjacent_run_failed": _string_int(lazy_summary.get("run_failed")),
    }


def _p5_summary(
    candidate_rows: Sequence[Mapping[str, str]],
    pipeline_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    single_ids = {
        row.get("candidate_id", "")
        for row in candidate_rows
        if row.get("source") == "single_swap"
    }
    single_runs = [
        row for row in pipeline_rows if row.get("candidate_id", "") in single_ids
    ]
    clean_single_runs = [
        row for row in single_runs if not row.get("failure_kind", "").strip()
    ]
    return {
        "one_swap_candidates": str(len(single_ids)),
        "pipeline_run_failed": str(len(single_runs) - len(clean_single_runs)),
        "single_swap_same_as_anchor": str(
            sum(1 for row in clean_single_runs if _truthy(row.get("same_as_anchor")))
        ),
        "single_swap_different_from_anchor": str(
            sum(
                1
                for row in clean_single_runs
                if not _truthy(row.get("same_as_anchor"))
            )
        ),
    }


def _objective_summary(
    name: str,
    object_rows: Sequence[Mapping[str, str]],
    p5: Mapping[str, str],
) -> dict[str, str]:
    single = [row for row in object_rows if row.get("source") == "single_swap"]
    computed = _computed_object_rows(single)
    smaller = [row for row in computed if _parse_float(row.get("text_delta")) < 0]
    equal = [row for row in computed if _parse_float(row.get("text_delta")) == 0]
    larger = [row for row in computed if _parse_float(row.get("text_delta")) > 0]
    ir_diff_text_equal = [
        row for row in equal if not _truthy(row.get("p5_same_as_anchor"))
    ]
    return {
        "benchmark_set": name,
        "one_swap_candidates": p5["one_swap_candidates"],
        "object_size_evaluated": str(len(computed)),
        "smaller_text": str(len(smaller)),
        "equal_text": str(len(equal)),
        "larger_text": str(len(larger)),
        "ir_different_but_text_equal_count": str(len(ir_diff_text_equal)),
        "ir_different_but_text_equal_rate": _percent(
            len(ir_diff_text_equal), len(computed)
        ),
    }


def _codegen_summary(
    name: str,
    compare_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    depth1 = [
        row
        for row in compare_rows
        if row.get("source") == "single_swap"
        and row.get("llc_direction")
        and row.get("clang_direction")
    ]
    agreement = [_direction_agrees(row) for row in depth1]
    both_smaller = [
        row
        for row in depth1
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    ]
    smaller_only_llc = [
        row
        for row in depth1
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") != "smaller"
    ]
    smaller_only_clang = [
        row
        for row in depth1
        if row.get("clang_direction") == "smaller"
        and row.get("llc_direction") != "smaller"
    ]
    both_smaller_programs = {
        row.get("program", "") for row in both_smaller if row.get("program", "")
    }
    agreement_count = sum(1 for value in agreement if value)
    return {
        "benchmark_set": name,
        "direction_comparison_candidates": str(len(depth1)),
        "direction_agreement_count": str(agreement_count),
        "direction_agreement_rate": _percent(agreement_count, len(depth1)),
        "smaller_under_both_count": str(len(both_smaller)),
        "smaller_only_under_llc_count": str(len(smaller_only_llc)),
        "smaller_only_under_clang_count": str(len(smaller_only_clang)),
        "direction_disagreement_count": str(len(depth1) - agreement_count),
        "both_smaller_programs": str(len(both_smaller_programs)),
    }


def _objective_codegen_slice(codegen: Mapping[str, str]) -> dict[str, str]:
    return {
        "direction_comparison_candidates": codegen[
            "direction_comparison_candidates"
        ],
        "direction_agreement_rate": codegen["direction_agreement_rate"],
        "smaller_under_both_count": codegen["smaller_under_both_count"],
        "smaller_only_under_llc_count": codegen["smaller_only_under_llc_count"],
        "smaller_only_under_clang_count": codegen["smaller_only_under_clang_count"],
        "direction_disagreement_count": codegen["direction_disagreement_count"],
    }


def _benchmark_summary(
    name: str,
    *,
    matrix: Mapping[str, str],
    reduction: Mapping[str, str],
    objective: Mapping[str, str],
    codegen: Mapping[str, str],
    p5: Mapping[str, str],
) -> dict[str, str]:
    return {
        "benchmark_set": name,
        "programs": matrix["programs"],
        "pair_matrix_certificates": matrix["pair_matrix_certificates"],
        "reproduced_certificates": matrix["reproduced_certificates"],
        "hard_false_independent": matrix["hard_false_independent"],
        "static_false_negative_observed": reduction[
            "static_false_negative_observed"
        ],
        "adjacent_attempts": reduction["adjacent_attempts"],
        "certified_adjacent_events": reduction["certified_adjacent_events"],
        "not_certified_adjacent_events": reduction["not_certified_adjacent_events"],
        "low_priority_events": reduction["low_priority_events"],
        "one_swap_candidates": objective["one_swap_candidates"],
        "single_swap_same_as_anchor": p5["single_swap_same_as_anchor"],
        "single_swap_different_from_anchor": p5[
            "single_swap_different_from_anchor"
        ],
        "both_smaller_programs": codegen["both_smaller_programs"],
    }


def _combined_summary(
    *,
    benchmark_rows: Sequence[Mapping[str, str]],
    reduction_rows: Sequence[Mapping[str, str]],
    objective_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_cases: int,
) -> dict[str, Any]:
    diverse = next(
        (row for row in benchmark_rows if row.get("benchmark_set") == "Diverse8"),
        {},
    )
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
        "TotalStaticFalseNegativeObserved": sum(
            _parse_int(row.get("static_false_negative_observed"))
            for row in benchmark_rows
        ),
        "TotalAdjacentAttempts": sum(
            _parse_int(row.get("adjacent_attempts")) for row in benchmark_rows
        ),
        "CertifiedAdjacentEvents": sum(
            _parse_int(row.get("certified_adjacent_events"))
            for row in reduction_rows
        ),
        "NotCertifiedAdjacentEvents": sum(
            _parse_int(row.get("not_certified_adjacent_events"))
            for row in reduction_rows
        ),
        "LowPriorityEvents": sum(
            _parse_int(row.get("low_priority_events")) for row in benchmark_rows
        ),
        "TotalOneSwapCandidates": sum(
            _parse_int(row.get("one_swap_candidates")) for row in benchmark_rows
        ),
        "TotalObjectSizeEvaluated": sum(
            _parse_int(row.get("object_size_evaluated")) for row in objective_rows
        ),
        "TotalSmallerText": sum(
            _parse_int(row.get("smaller_text")) for row in objective_rows
        ),
        "TotalEqualText": sum(
            _parse_int(row.get("equal_text")) for row in objective_rows
        ),
        "TotalLargerText": sum(
            _parse_int(row.get("larger_text")) for row in objective_rows
        ),
        "TotalDirectionComparisonCandidates": sum(
            _parse_int(row.get("direction_comparison_candidates"))
            for row in codegen_rows
        ),
        "TotalBothSmallerPrograms": sum(
            _parse_int(row.get("both_smaller_programs")) for row in benchmark_rows
        ),
        "Diverse8BothSmallerPrograms": _parse_int(
            diverse.get("both_smaller_programs")
        ),
        "AttributionCases": attribution_cases,
        "Depth1Only": True,
        "NoNewExperiments": True,
    }


def _require_input_files(benchmark_sets: Sequence[BenchmarkSetInputs]) -> None:
    missing = [
        f"{key}={Path(path).as_posix()}"
        for key, path in _input_paths(benchmark_sets).items()
        if not Path(path).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "missing combined depth1 summary input files: " + "; ".join(missing)
        )


def _input_paths(benchmark_sets: Sequence[BenchmarkSetInputs]) -> dict[str, str | Path]:
    paths: dict[str, str | Path] = {}
    for item in benchmark_sets:
        key = _manifest_key(item.name)
        paths[f"{key}_pair_summary_csv"] = item.pair_summary_csv
        paths[f"{key}_static_filter_report"] = item.static_filter_report
        paths[f"{key}_lazy_validation_report"] = item.lazy_validation_report
        paths[f"{key}_p5_candidates_csv"] = item.p5_candidates_csv
        paths[f"{key}_p5_pipeline_runs_csv"] = item.p5_pipeline_runs_csv
        paths[f"{key}_p6_object_size_csv"] = item.p6_object_size_csv
        paths[f"{key}_codegen_compare_csv"] = item.codegen_compare_csv
        if item.attribution_summary_csv is not None:
            paths[f"{key}_attribution_summary_csv"] = item.attribution_summary_csv
    return paths


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_optional_csv(path: str | Path | None) -> list[dict[str, str]]:
    if path in {None, ""}:
        return []
    candidate = Path(path)
    return _load_csv(candidate) if candidate.exists() else []


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fields: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
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


def _computed_object_rows(rows: Sequence[Mapping[str, str]]) -> list[Mapping[str, str]]:
    return [
        row
        for row in rows
        if row.get("text_delta", "") != ""
        and not row.get("compile_failure_kind", "")
        and not row.get("size_failure_kind", "")
    ]


def _direction_agrees(row: Mapping[str, str]) -> bool:
    if row.get("direction_agree", ""):
        return _truthy(row.get("direction_agree"))
    return row.get("llc_direction") == row.get("clang_direction")


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


def _percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator) * 100.0:.2f}%"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the P9-5 combined depth1 summary from existing files."
    )
    parser.add_argument("--out", default="data/outputs/combined_depth1_summary")
    parser.add_argument(
        "--manifest", default="docs/results/combined_depth1_summary_manifest.json"
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--result-generated-from-commit")
    args = parser.parse_args(argv)
    try:
        result = run_combined_depth1_summary(
            output_dir=args.out,
            manifest_path=args.manifest,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    report = Path(args.out) / "combined_depth1_report.md"
    print(report.read_text(encoding="utf-8"), end="")
    return 0 if result.summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
