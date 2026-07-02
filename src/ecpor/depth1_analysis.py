"""Analyze depth1 P4/P5/P6/P8a evidence for one benchmark set."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROGRAM_FIELDS = [
    "program",
    "attempted_adjacent_swaps",
    "certified_independent",
    "not_certified_independent",
    "low_priority",
    "anchor_candidates",
    "single_swap_candidates",
    "pipeline_run_failed",
    "single_swap_different_from_anchor",
    "object_evaluated",
    "smaller_text",
    "equal_text",
    "larger_text",
    "ir_different_but_text_equal",
    "both_smaller_cases",
    "direction_disagreements",
]

PAIR_FIELDS = [
    "pair",
    "single_swap_candidates",
    "smaller_text",
    "equal_text",
    "larger_text",
    "both_smaller_cases",
    "direction_disagreements",
]

BOTH_SMALLER_FIELDS = [
    "program",
    "pair",
    "candidate_id",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
]


@dataclass(frozen=True)
class Depth1AnalysisResult:
    program_rows: list[dict[str, str]]
    pair_rows: list[dict[str, str]]
    both_smaller_rows: list[dict[str, str]]
    summary: dict[str, Any]


def run_depth1_analysis(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    p8a_compare_csv: str | Path,
    output_dir: str | Path,
    reference_p6_object_size_csv: str | Path | None = None,
    reference_p8a_compare_csv: str | Path | None = None,
    benchmark_label: str = "Misc8",
) -> Depth1AnalysisResult:
    attempts = _load_csv(p4_attempts_csv)
    candidates = _load_csv(p5_candidates_csv)
    pipeline_runs = _load_csv(p5_pipeline_runs_csv)
    object_rows = _load_csv(p6_object_size_csv)
    compare_rows = _load_csv(p8a_compare_csv)
    reference_objects = _load_optional_csv(reference_p6_object_size_csv)
    reference_compare = _load_optional_csv(reference_p8a_compare_csv)

    program_rows = _program_rows(attempts, candidates, pipeline_runs, object_rows, compare_rows)
    pair_rows = _pair_rows(object_rows, compare_rows)
    both_smaller_rows = _both_smaller_rows(object_rows, compare_rows)
    summary = _summary(
        object_rows=object_rows,
        compare_rows=compare_rows,
        program_rows=program_rows,
        reference_objects=reference_objects,
        reference_compare=reference_compare,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "depth1_program_summary.csv", program_rows, PROGRAM_FIELDS)
    _write_csv(output_root / "depth1_pair_summary.csv", pair_rows, PAIR_FIELDS)
    _write_csv(
        output_root / "depth1_both_smaller_cases.csv",
        both_smaller_rows,
        BOTH_SMALLER_FIELDS,
    )
    (output_root / "depth1_analysis_report.md").write_text(
        build_depth1_analysis_report(
            summary,
            program_rows,
            pair_rows,
            both_smaller_rows,
            benchmark_label=benchmark_label,
        ),
        encoding="utf-8",
    )
    return Depth1AnalysisResult(
        program_rows=program_rows,
        pair_rows=pair_rows,
        both_smaller_rows=both_smaller_rows,
        summary=summary,
    )


def build_depth1_analysis_report(
    summary: Mapping[str, Any],
    program_rows: Sequence[dict[str, str]],
    pair_rows: Sequence[dict[str, str]],
    both_smaller_rows: Sequence[dict[str, str]],
    *,
    benchmark_label: str = "Misc8",
) -> str:
    lines = [
        f"# {benchmark_label} Depth1 Analysis Report",
        "",
        f"本报告解释 {benchmark_label} 的 depth1 结果；它不新增搜索、不跑 two-swap、不运行 runtime。",
        "",
        f"Programs: {summary['Programs']}",
        f"SingleSwapCandidates: {summary['SingleSwapCandidates']}",
        f"ObjectEvaluated: {summary['ObjectEvaluated']}",
        f"SmallerText: {summary['SmallerText']}",
        f"EqualText: {summary['EqualText']}",
        f"LargerText: {summary['LargerText']}",
        f"IRDifferentButTextEqualCount: {summary['IRDifferentButTextEqualCount']}",
        f"IRDifferentButTextEqualRate: {summary['IRDifferentButTextEqualRate']}",
        f"DirectionComparisonCandidates: {summary['DirectionComparisonCandidates']}",
        f"DirectionAgreementRate: {summary['DirectionAgreementRate']}",
        f"BothSmallerCases: {summary['BothSmallerCases']}",
        f"Depth1BothSmallerPrograms: {summary['Depth1BothSmallerPrograms']}",
        f"DirectionDisagreementCount: {summary['DirectionDisagreementCount']}",
        f"ReferenceIRDifferentButTextEqualRate: {summary['ReferenceIRDifferentButTextEqualRate']}",
        f"ReferenceDepth1BothSmallerPrograms: {summary['ReferenceDepth1BothSmallerPrograms']}",
        "",
        "## Both-smaller Cases",
    ]
    if not both_smaller_rows:
        lines.append("none")
    for row in both_smaller_rows:
        lines.append(
            "{program}: {candidate_id} pair={pair} llc={llc_text_delta_pct} "
            "clang={clang_text_delta_pct}".format(**row)
        )
    lines.extend(["", "## Pair Summary", ""])
    for row in pair_rows:
        lines.append(
            "{pair}: candidates={single_swap_candidates} smaller={smaller_text} "
            "equal={equal_text} larger={larger_text} both_smaller={both_smaller_cases}".format(
                **row
            )
        )
    lines.extend(["", "## Program Summary", ""])
    for row in program_rows:
        lines.append(
            "{program}: single_swap={single_swap_candidates} smaller={smaller_text} "
            "equal={equal_text} both_smaller={both_smaller_cases}".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"{benchmark_label} repeats the Stanford depth1 pattern: many IR-different candidates are objective-layer equal, and only a small number become smaller under both codegen paths.",
            "当前稳定收益只来自 both-smaller case；这不足以直接触发更深搜索。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze depth1 P8b Misc8 evidence.")
    parser.add_argument("--p4-attempts", required=True)
    parser.add_argument("--p5-candidates", required=True)
    parser.add_argument("--p5-pipeline-runs", required=True)
    parser.add_argument("--p6-object-size", required=True)
    parser.add_argument("--p8a-compare", required=True)
    parser.add_argument("--reference-p6-object-size")
    parser.add_argument("--reference-p8a-compare")
    parser.add_argument("--benchmark-label", default="Misc8")
    parser.add_argument("--out", default="data/outputs/depth1_analysis_p8b_misc8")
    args = parser.parse_args(argv)
    result = run_depth1_analysis(
        p4_attempts_csv=args.p4_attempts,
        p5_candidates_csv=args.p5_candidates,
        p5_pipeline_runs_csv=args.p5_pipeline_runs,
        p6_object_size_csv=args.p6_object_size,
        p8a_compare_csv=args.p8a_compare,
        output_dir=args.out,
        reference_p6_object_size_csv=args.reference_p6_object_size,
        reference_p8a_compare_csv=args.reference_p8a_compare,
        benchmark_label=args.benchmark_label,
    )
    print(
        build_depth1_analysis_report(
            result.summary,
            result.program_rows,
            result.pair_rows,
            result.both_smaller_rows,
            benchmark_label=args.benchmark_label,
        ),
        end="",
    )
    return 0


def _program_rows(
    attempts: Sequence[dict[str, str]],
    candidates: Sequence[dict[str, str]],
    pipeline_runs: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    compare_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    programs = sorted(
        {
            row.get("program", "")
            for rows in [attempts, candidates, object_rows, compare_rows]
            for row in rows
            if row.get("program", "")
        }
    )
    result: list[dict[str, str]] = []
    for program in programs:
        program_attempts = [row for row in attempts if row.get("program") == program]
        program_candidates = [row for row in candidates if row.get("program") == program]
        program_runs = [row for row in pipeline_runs if row.get("program") == program]
        program_objects = [
            row
            for row in object_rows
            if row.get("program") == program and row.get("source") == "single_swap"
        ]
        program_compare = [
            row
            for row in compare_rows
            if row.get("program") == program and row.get("source") == "single_swap"
        ]
        result.append(
            {
                "program": program,
                "attempted_adjacent_swaps": str(len(program_attempts)),
                "certified_independent": str(_count_label(program_attempts, "certified_independent")),
                "not_certified_independent": str(_count_label(program_attempts, "not_certified_independent")),
                "low_priority": str(_count_action(program_attempts, "skipped_low_priority")),
                "anchor_candidates": str(_count_source(program_candidates, "anchor")),
                "single_swap_candidates": str(_count_source(program_candidates, "single_swap")),
                "pipeline_run_failed": str(sum(1 for row in program_runs if row.get("failure_kind", ""))),
                "single_swap_different_from_anchor": str(
                    sum(
                        1
                        for row in program_runs
                        if not _is_true(row.get("same_as_anchor", ""))
                        and not row.get("failure_kind", "")
                        and "__anchor" not in row.get("candidate_id", "")
                    )
                ),
                "object_evaluated": str(len(_computed_object_rows(program_objects))),
                "smaller_text": str(_count_direction_from_delta(program_objects, "smaller")),
                "equal_text": str(_count_direction_from_delta(program_objects, "equal")),
                "larger_text": str(_count_direction_from_delta(program_objects, "larger")),
                "ir_different_but_text_equal": str(_ir_different_but_text_equal(program_objects)),
                "both_smaller_cases": str(_count_both_smaller(program_compare)),
                "direction_disagreements": str(_count_direction_disagreement(program_compare)),
            }
        )
    return result


def _pair_rows(
    object_rows: Sequence[dict[str, str]],
    compare_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    objects = [row for row in object_rows if row.get("source") == "single_swap"]
    compare_by_id = {row.get("candidate_id", ""): row for row in compare_rows}
    pairs = sorted({_pair(row) for row in objects if _pair(row)})
    result: list[dict[str, str]] = []
    for pair in pairs:
        rows = [row for row in objects if _pair(row) == pair]
        compare = [
            compare_by_id.get(row.get("candidate_id", ""), {})
            for row in rows
        ]
        result.append(
            {
                "pair": pair,
                "single_swap_candidates": str(len(rows)),
                "smaller_text": str(_count_direction_from_delta(rows, "smaller")),
                "equal_text": str(_count_direction_from_delta(rows, "equal")),
                "larger_text": str(_count_direction_from_delta(rows, "larger")),
                "both_smaller_cases": str(_count_both_smaller(compare)),
                "direction_disagreements": str(_count_direction_disagreement(compare)),
            }
        )
    return result


def _both_smaller_rows(
    object_rows: Sequence[dict[str, str]],
    compare_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    object_by_id = {row.get("candidate_id", ""): row for row in object_rows}
    rows: list[dict[str, str]] = []
    for row in compare_rows:
        if row.get("source") != "single_swap":
            continue
        if row.get("llc_direction") != "smaller" or row.get("clang_direction") != "smaller":
            continue
        object_row = object_by_id.get(row.get("candidate_id", ""), {})
        rows.append(
            {
                "program": row.get("program", ""),
                "pair": _pair(object_row) or _pair(row),
                "candidate_id": row.get("candidate_id", ""),
                "llc_text_delta_pct": row.get("llc_text_delta_pct", ""),
                "clang_text_delta_pct": row.get("clang_text_delta_pct", ""),
            }
        )
    return rows


def _summary(
    *,
    object_rows: Sequence[dict[str, str]],
    compare_rows: Sequence[dict[str, str]],
    program_rows: Sequence[dict[str, str]],
    reference_objects: Sequence[dict[str, str]],
    reference_compare: Sequence[dict[str, str]],
) -> dict[str, Any]:
    single_swap_objects = [
        row for row in object_rows if row.get("source") == "single_swap"
    ]
    computed = _computed_object_rows(single_swap_objects)
    single_swap_compare = [
        row for row in compare_rows if row.get("source") == "single_swap"
    ]
    both_smaller_programs = {
        row.get("program", "")
        for row in single_swap_compare
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    }
    reference_single = [
        row for row in reference_objects if row.get("source") == "single_swap"
    ]
    reference_compare_single = [
        row for row in reference_compare if row.get("source") == "single_swap"
    ]
    reference_both_smaller_programs = {
        row.get("program", "")
        for row in reference_compare_single
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    }
    agreement = sum(1 for row in single_swap_compare if row.get("direction_agree") == "True")
    return {
        "Programs": len(program_rows),
        "SingleSwapCandidates": len(single_swap_objects),
        "ObjectEvaluated": len(computed),
        "SmallerText": _count_direction_from_delta(computed, "smaller"),
        "EqualText": _count_direction_from_delta(computed, "equal"),
        "LargerText": _count_direction_from_delta(computed, "larger"),
        "IRDifferentButTextEqualCount": _ir_different_but_text_equal(computed),
        "IRDifferentButTextEqualRate": _percent(_ir_different_but_text_equal(computed), len(computed)),
        "DirectionComparisonCandidates": len(single_swap_compare),
        "DirectionAgreementRate": _percent(agreement, len(single_swap_compare)),
        "BothSmallerCases": _count_both_smaller(single_swap_compare),
        "Depth1BothSmallerPrograms": len({p for p in both_smaller_programs if p}),
        "DirectionDisagreementCount": _count_direction_disagreement(single_swap_compare),
        "ReferenceIRDifferentButTextEqualRate": _percent(
            _ir_different_but_text_equal(reference_single),
            len(_computed_object_rows(reference_single)),
        ),
        "ReferenceDepth1BothSmallerPrograms": len(
            {p for p in reference_both_smaller_programs if p}
        ),
    }


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_optional_csv(path: str | Path | None) -> list[dict[str, str]]:
    if path in {None, ""}:
        return []
    candidate = Path(path)
    return _load_csv(candidate) if candidate.exists() else []


def _write_csv(path: str | Path, rows: Sequence[dict[str, str]], fields: Sequence[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _pair(row: Mapping[str, str]) -> str:
    left = row.get("pass_a", "")
    right = row.get("pass_b", "")
    if not left or not right:
        return _pair_from_candidate_id(row.get("candidate_id", ""))
    return f"{left},{right}"


def _pair_from_candidate_id(candidate_id: str) -> str:
    parts = candidate_id.split("__")
    if len(parts) >= 4:
        return f"{parts[-2]},{parts[-1]}"
    return ""


def _computed_object_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("text_delta", "") != ""
        and not row.get("compile_failure_kind", "")
        and not row.get("size_failure_kind", "")
    ]


def _count_label(rows: Sequence[dict[str, str]], label: str) -> int:
    return sum(1 for row in rows if row.get("label") == label)


def _count_action(rows: Sequence[dict[str, str]], action: str) -> int:
    return sum(1 for row in rows if row.get("action") == action)


def _count_source(rows: Sequence[dict[str, str]], source: str) -> int:
    return sum(1 for row in rows if row.get("source") == source)


def _count_direction_from_delta(rows: Sequence[dict[str, str]], direction: str) -> int:
    return sum(1 for row in rows if _direction_from_delta(row.get("text_delta")) == direction)


def _count_both_smaller(rows: Sequence[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("llc_direction") == "smaller" and row.get("clang_direction") == "smaller"
    )


def _count_direction_disagreement(rows: Sequence[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("direction_agree") == "False")


def _ir_different_but_text_equal(rows: Sequence[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        if not _is_true(row.get("p5_same_as_anchor", ""))
        and _parse_optional_float(row.get("text_delta")) == 0.0
    )


def _direction_from_delta(value: str | None) -> str:
    parsed = _parse_optional_float(value)
    if parsed is None:
        return "unknown"
    if parsed < 0:
        return "smaller"
    if parsed > 0:
        return "larger"
    return "equal"


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _is_true(value: str | None) -> bool:
    return str(value).lower() == "true"


def _percent(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator * 100.0):.2f}%" if denominator else "0.00%"


if __name__ == "__main__":
    raise SystemExit(main())
