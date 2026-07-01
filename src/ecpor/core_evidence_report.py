"""Summarize ECPOR's pruning and objective-layer evidence chain."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


FUNNEL_FIELDS = [
    "stage",
    "input_count",
    "candidate_count",
    "certified_collapsed",
    "not_certified_kept",
    "low_priority_frozen",
    "duplicates_removed",
    "unique_candidates",
    "notes",
]

PRUNING_FIELDS = [
    "stage",
    "evidence_type",
    "count",
    "hard_prune",
    "evidence_source",
    "meaning",
]

CODEGEN_FIELDS = [
    "direction_comparison_candidates",
    "direction_agreement_count",
    "direction_agreement_rate",
    "smaller_under_both",
    "smaller_only_under_llc",
    "smaller_only_under_clang",
    "direction_disagreement_count",
]


@dataclass(frozen=True)
class CoreEvidenceReport:
    funnel_rows: list[dict[str, str]]
    pruning_rows: list[dict[str, str]]
    codegen_rows: list[dict[str, str]]
    summary: dict[str, Any]


def run_core_evidence_report(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    p7b_attempts_csv: str | Path,
    p7b_candidates_csv: str | Path,
    p7b_object_size_csv: str | Path,
    p7b_analysis_report: str | Path,
    p8a_compare_csv: str | Path,
    output_dir: str | Path,
) -> CoreEvidenceReport:
    p4_attempts = _load_csv(p4_attempts_csv)
    p5_candidates = _load_csv(p5_candidates_csv)
    p5_pipeline_runs = _load_csv(p5_pipeline_runs_csv)
    p6_object_rows = _load_csv(p6_object_size_csv)
    p7b_attempts = _load_csv(p7b_attempts_csv)
    p7b_candidates = _load_csv(p7b_candidates_csv)
    p7b_object_rows = _load_csv(p7b_object_size_csv)
    p7b_analysis = _parse_key_value_report(p7b_analysis_report)
    p8a_compare = _load_csv(p8a_compare_csv)

    funnel_rows = _build_funnel_rows(
        p4_attempts=p4_attempts,
        p5_candidates=p5_candidates,
        p5_pipeline_runs=p5_pipeline_runs,
        p6_object_rows=p6_object_rows,
        p7b_attempts=p7b_attempts,
        p7b_candidates=p7b_candidates,
        p7b_analysis=p7b_analysis,
        p8a_compare=p8a_compare,
    )
    pruning_rows = _build_pruning_rows(
        p4_attempts=p4_attempts,
        p7b_attempts=p7b_attempts,
        p7b_analysis=p7b_analysis,
        p8a_compare=p8a_compare,
    )
    codegen_rows = [_build_codegen_summary(p8a_compare)]
    summary = _build_summary(
        funnel_rows=funnel_rows,
        pruning_rows=pruning_rows,
        codegen_row=codegen_rows[0],
        p6_object_rows=p6_object_rows,
        p7b_object_rows=p7b_object_rows,
        p7b_analysis=p7b_analysis,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "ecpor_reduction_funnel.csv", funnel_rows, FUNNEL_FIELDS)
    _write_csv(
        output_root / "ecpor_certified_pruning_summary.csv",
        pruning_rows,
        PRUNING_FIELDS,
    )
    _write_csv(
        output_root / "ecpor_codegen_sensitivity_summary.csv",
        codegen_rows,
        CODEGEN_FIELDS,
    )
    (output_root / "ecpor_core_evidence_report.md").write_text(
        build_core_evidence_report(
            summary=summary,
            funnel_rows=funnel_rows,
            pruning_rows=pruning_rows,
            codegen_rows=codegen_rows,
        ),
        encoding="utf-8",
    )
    return CoreEvidenceReport(
        funnel_rows=funnel_rows,
        pruning_rows=pruning_rows,
        codegen_rows=codegen_rows,
        summary=summary,
    )


def build_core_evidence_report(
    *,
    summary: Mapping[str, Any],
    funnel_rows: Sequence[dict[str, str]],
    pruning_rows: Sequence[dict[str, str]],
    codegen_rows: Sequence[dict[str, str]],
) -> str:
    codegen = codegen_rows[0] if codegen_rows else {}
    lines = [
        "# ECPOR Core Evidence Report",
        "",
        "本报告把 P4-P8a 的结果收束回最初问题：搜索空间坍缩、证据等级、以及目标函数层的 codegen 敏感性。",
        "它不新增搜索、不新增 certificate、不运行 runtime benchmark。",
        "",
        "## 搜索空间坍缩",
        "",
        "| stage | input | candidate | certified collapsed | not-certified kept | low-priority frozen | duplicates removed | unique |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in funnel_rows:
        lines.append(
            "| {stage} | {input_count} | {candidate_count} | {certified_collapsed} | "
            "{not_certified_kept} | {low_priority_frozen} | {duplicates_removed} | "
            "{unique_candidates} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Hard Evidence Vs Soft Evidence",
            "",
            "| stage | evidence | count | hard prune | meaning |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for row in pruning_rows:
        lines.append(
            "| {stage} | {evidence_type} | {count} | {hard_prune} | {meaning} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Codegen Sensitivity",
            "",
            f"DirectionComparisonCandidates: {codegen.get('direction_comparison_candidates', '0')}",
            f"DirectionAgreementCount: {codegen.get('direction_agreement_count', '0')}",
            f"DirectionAgreementRate: {codegen.get('direction_agreement_rate', '0.00%')}",
            f"SmallerUnderBothCount: {codegen.get('smaller_under_both', '0')}",
            f"SmallerOnlyUnderLlcCount: {codegen.get('smaller_only_under_llc', '0')}",
            f"SmallerOnlyUnderClangCount: {codegen.get('smaller_only_under_clang', '0')}",
            f"DirectionDisagreementCount: {codegen.get('direction_disagreement_count', '0')}",
            "",
            "## 当前结论",
            "",
            "hard pruning 只来自 state-indexed hard hash equality certificate；static filter 和 sequence duplicate 不是语义等价证明。",
            "IR 差异需要继续经过目标函数层验证；P8a 显示 llc 与 clang-c 方向并非总是一致。",
            f"当前 both-smaller candidate 数量为 {summary['SmallerUnderBothCount']}，仍需通过 P8b 扩大 benchmark 验证泛化性。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ECPOR core evidence report.")
    parser.add_argument(
        "--p4-attempts",
        default="data/outputs/lazy_validation_p4_e83c409_first.csv",
    )
    parser.add_argument(
        "--p5-candidates",
        default="data/outputs/bounded_local_p5_p6_final/candidates.csv",
    )
    parser.add_argument(
        "--p5-pipeline-runs",
        default="data/outputs/bounded_local_p5_p6_final/pipeline_runs.csv",
    )
    parser.add_argument(
        "--p6-object-size",
        default="data/outputs/code_size_p6_final/object_size.csv",
    )
    parser.add_argument(
        "--p7b-attempts",
        default="data/outputs/bounded_two_swap_p7b/two_swap_attempts.csv",
    )
    parser.add_argument(
        "--p7b-candidates",
        default="data/outputs/bounded_two_swap_p7b/two_swap_candidates.csv",
    )
    parser.add_argument(
        "--p7b-object-size",
        default="data/outputs/bounded_two_swap_p7b/two_swap_object_size.csv",
    )
    parser.add_argument(
        "--p7b-analysis-report",
        default="data/outputs/bounded_two_swap_p7b_analysis/p7b_analysis_report.md",
    )
    parser.add_argument(
        "--p8a-compare",
        default="data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv",
    )
    parser.add_argument("--out", default="data/outputs/core_evidence_report")
    args = parser.parse_args(argv)

    result = run_core_evidence_report(
        p4_attempts_csv=args.p4_attempts,
        p5_candidates_csv=args.p5_candidates,
        p5_pipeline_runs_csv=args.p5_pipeline_runs,
        p6_object_size_csv=args.p6_object_size,
        p7b_attempts_csv=args.p7b_attempts,
        p7b_candidates_csv=args.p7b_candidates,
        p7b_object_size_csv=args.p7b_object_size,
        p7b_analysis_report=args.p7b_analysis_report,
        p8a_compare_csv=args.p8a_compare,
        output_dir=args.out,
    )
    print(
        build_core_evidence_report(
            summary=result.summary,
            funnel_rows=result.funnel_rows,
            pruning_rows=result.pruning_rows,
            codegen_rows=result.codegen_rows,
        ),
        end="",
    )
    return 0


def _build_funnel_rows(
    *,
    p4_attempts: Sequence[dict[str, str]],
    p5_candidates: Sequence[dict[str, str]],
    p5_pipeline_runs: Sequence[dict[str, str]],
    p6_object_rows: Sequence[dict[str, str]],
    p7b_attempts: Sequence[dict[str, str]],
    p7b_candidates: Sequence[dict[str, str]],
    p7b_analysis: Mapping[str, Any],
    p8a_compare: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    p5_single = [row for row in p5_candidates if row.get("source") == "single_swap"]
    p6_candidate_rows = [
        row for row in p6_object_rows if row.get("source") == "single_swap"
    ]
    p7b_depth2 = [row for row in p7b_candidates if row.get("source") == "two_swap"]
    return [
        {
            "stage": "P4",
            "input_count": str(len(p4_attempts)),
            "candidate_count": str(_count_true(p4_attempts, "dynamic_test")),
            "certified_collapsed": str(_count_label(p4_attempts, "certified_independent")),
            "not_certified_kept": str(_count_label(p4_attempts, "not_certified_independent")),
            "low_priority_frozen": str(_count_action(p4_attempts, "skipped_low_priority")),
            "duplicates_removed": "0",
            "unique_candidates": str(_count_label(p4_attempts, "not_certified_independent")),
            "notes": "state-indexed adjacent lazy validation",
        },
        {
            "stage": "P5",
            "input_count": str(len(p5_pipeline_runs)),
            "candidate_count": str(len(p5_single)),
            "certified_collapsed": str(_count_label(p4_attempts, "certified_independent")),
            "not_certified_kept": str(len(p5_single)),
            "low_priority_frozen": str(_count_action(p4_attempts, "skipped_low_priority")),
            "duplicates_removed": "0",
            "unique_candidates": str(len(p5_single)),
            "notes": "one-swap candidates from not-certified adjacent pairs",
        },
        {
            "stage": "P6",
            "input_count": str(len(p6_candidate_rows)),
            "candidate_count": str(len(p6_candidate_rows)),
            "certified_collapsed": "0",
            "not_certified_kept": str(_count_ir_different(p6_candidate_rows)),
            "low_priority_frozen": "0",
            "duplicates_removed": "0",
            "unique_candidates": str(len(p6_candidate_rows)),
            "notes": "llc object .text objective layer",
        },
        {
            "stage": "P7b",
            "input_count": str(len(p7b_attempts)),
            "candidate_count": str(_as_int(p7b_analysis.get("RawDepth2Candidates"), _count_label(p7b_attempts, "not_certified_independent"))),
            "certified_collapsed": str(_count_label(p7b_attempts, "certified_independent")),
            "not_certified_kept": str(_count_label(p7b_attempts, "not_certified_independent")),
            "low_priority_frozen": str(_count_action(p7b_attempts, "skipped_low_priority")),
            "duplicates_removed": str(_as_int(p7b_analysis.get("DuplicateSequences"), 0)),
            "unique_candidates": str(_as_int(p7b_analysis.get("UniqueDepth2Candidates"), len(p7b_depth2))),
            "notes": "bounded depth2 candidates after sequence-level dedup",
        },
        {
            "stage": "P8a",
            "input_count": str(len(p8a_compare)),
            "candidate_count": str(len(p8a_compare)),
            "certified_collapsed": "0",
            "not_certified_kept": str(len(p8a_compare)),
            "low_priority_frozen": "0",
            "duplicates_removed": "0",
            "unique_candidates": str(len(p8a_compare)),
            "notes": "llc vs clang-c objective direction comparison",
        },
    ]


def _build_pruning_rows(
    *,
    p4_attempts: Sequence[dict[str, str]],
    p7b_attempts: Sequence[dict[str, str]],
    p7b_analysis: Mapping[str, Any],
    p8a_compare: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    certified = _count_label(p4_attempts, "certified_independent") + _count_label(
        p7b_attempts, "certified_independent"
    )
    not_certified = _count_label(p4_attempts, "not_certified_independent") + _count_label(
        p7b_attempts, "not_certified_independent"
    )
    low_priority = _count_action(p4_attempts, "skipped_low_priority") + _count_action(
        p7b_attempts, "skipped_low_priority"
    )
    duplicate_sequences = _as_int(p7b_analysis.get("DuplicateSequences"), 0)
    both_smaller = _count_direction(p8a_compare, "smaller", "smaller")
    return [
        {
            "stage": "P4/P7b",
            "evidence_type": "certified_independent",
            "count": str(certified),
            "hard_prune": "True",
            "evidence_source": "hard hash equality certificate",
            "meaning": "A;B and B;A are equal for the same materialized state",
        },
        {
            "stage": "P4/P7b",
            "evidence_type": "not_certified_independent",
            "count": str(not_certified),
            "hard_prune": "False",
            "evidence_source": "hard hash differs",
            "meaning": "order remains observable and must not be pruned as independent",
        },
        {
            "stage": "P4/P7b",
            "evidence_type": "low_priority",
            "count": str(low_priority),
            "hard_prune": "False",
            "evidence_source": "static filter hint",
            "meaning": "static ordering priority only, not a proof",
        },
        {
            "stage": "P7b",
            "evidence_type": "sequence_duplicate",
            "count": str(duplicate_sequences),
            "hard_prune": "False",
            "evidence_source": "pipeline sequence hash",
            "meaning": "same pass sequence can be deduplicated but is not semantic equivalence",
        },
        {
            "stage": "P8a",
            "evidence_type": "llc_clang_both_smaller",
            "count": str(both_smaller),
            "hard_prune": "False",
            "evidence_source": "object .text under llc and clang-c",
            "meaning": "stronger objective-layer observation, not an independence proof",
        },
    ]


def _build_codegen_summary(rows: Sequence[dict[str, str]]) -> dict[str, str]:
    total = len(rows)
    agreement = sum(1 for row in rows if row.get("direction_agree") == "True")
    disagreement = total - agreement
    both_smaller = _count_direction(rows, "smaller", "smaller")
    smaller_only_llc = sum(
        1
        for row in rows
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") != "smaller"
    )
    smaller_only_clang = sum(
        1
        for row in rows
        if row.get("llc_direction") != "smaller"
        and row.get("clang_direction") == "smaller"
    )
    return {
        "direction_comparison_candidates": str(total),
        "direction_agreement_count": str(agreement),
        "direction_agreement_rate": _percent(agreement, total),
        "smaller_under_both": str(both_smaller),
        "smaller_only_under_llc": str(smaller_only_llc),
        "smaller_only_under_clang": str(smaller_only_clang),
        "direction_disagreement_count": str(disagreement),
    }


def _build_summary(
    *,
    funnel_rows: Sequence[dict[str, str]],
    pruning_rows: Sequence[dict[str, str]],
    codegen_row: Mapping[str, str],
    p6_object_rows: Sequence[dict[str, str]],
    p7b_object_rows: Sequence[dict[str, str]],
    p7b_analysis: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "Stages": len(funnel_rows),
        "CertifiedIndependentTotal": _summary_count(
            pruning_rows, "certified_independent"
        ),
        "NotCertifiedIndependentTotal": _summary_count(
            pruning_rows, "not_certified_independent"
        ),
        "SequenceDuplicates": _as_int(p7b_analysis.get("DuplicateSequences"), 0),
        "P6SmallerText": _count_delta(p6_object_rows, "single_swap", "smaller"),
        "P7bDepth2SmallerText": _as_int(p7b_analysis.get("Depth2SmallerText"), 0),
        "P7bDepth2SmallerPrograms": _as_int(
            p7b_analysis.get("Depth2SmallerPrograms"), 0
        ),
        "P7bObjectRows": len(p7b_object_rows),
        "DirectionAgreementRate": codegen_row.get("direction_agreement_rate", "0.00%"),
        "SmallerUnderBothCount": _parse_int(codegen_row.get("smaller_under_both")),
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_key_value_report(path: str | Path) -> dict[str, Any]:
    report = Path(path)
    values: dict[str, Any] = {}
    if not report.exists():
        return values
    for raw_line in report.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key or " " in key:
            continue
        values[key] = _parse_scalar(value.strip())
    return values


def _parse_scalar(value: str) -> Any:
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


def _count_label(rows: Sequence[dict[str, str]], label: str) -> int:
    return sum(1 for row in rows if row.get("label") == label)


def _count_action(rows: Sequence[dict[str, str]], action: str) -> int:
    return sum(1 for row in rows if row.get("action") == action)


def _count_true(rows: Sequence[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if row.get(field) == "True")


def _count_ir_different(rows: Sequence[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("p5_same_as_anchor") == "False")


def _count_delta(
    rows: Sequence[dict[str, str]], source: str, direction: str
) -> int:
    count = 0
    for row in rows:
        if row.get("source") != source:
            continue
        delta = _parse_optional_float(row.get("text_delta"))
        if delta is None:
            continue
        if direction == "smaller" and delta < 0:
            count += 1
        elif direction == "equal" and delta == 0:
            count += 1
        elif direction == "larger" and delta > 0:
            count += 1
    return count


def _count_direction(
    rows: Sequence[dict[str, str]], llc_direction: str, clang_direction: str
) -> int:
    return sum(
        1
        for row in rows
        if row.get("llc_direction") == llc_direction
        and row.get("clang_direction") == clang_direction
    )


def _summary_count(rows: Sequence[dict[str, str]], evidence_type: str) -> int:
    for row in rows:
        if row.get("evidence_type") == evidence_type:
            return _parse_int(row.get("count"))
    return 0


def _percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator) * 100.0:.2f}%"


def _as_int(value: Any, default: int) -> int:
    if value in {None, ""}:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: str | None) -> int:
    if value in {None, ""}:
        return 0
    return int(str(value))


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


if __name__ == "__main__":
    raise SystemExit(main())
