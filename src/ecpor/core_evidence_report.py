"""Summarize ECPOR's pruning and objective-layer evidence chain."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


VALIDATION_FUNNEL_FIELDS = [
    "stage",
    "count_basis",
    "attempted_swaps",
    "static_candidate_swaps",
    "dynamic_tests",
    "cache_hits",
    "certified_independent_events",
    "not_certified_events",
    "low_priority_events",
    "run_failed",
    "notes",
]

CANDIDATE_PROPAGATION_FIELDS = [
    "stage",
    "count_basis",
    "anchor_candidates",
    "single_swap_candidates",
    "raw_depth2_candidates",
    "duplicates_removed",
    "unique_depth2_candidates",
    "object_size_evaluated_candidates",
    "clang_c_compared_candidates",
    "notes",
]

PRUNING_FIELDS = [
    "stage",
    "evidence_event",
    "count",
    "scope",
    "hard_prune",
    "proof_level",
    "evidence_source",
    "meaning",
]

OBJECTIVE_LAYER_FIELDS = [
    "count_basis",
    "direction_comparison_candidates",
    "direction_agreement_count",
    "direction_agreement_rate",
    "smaller_under_both",
    "smaller_only_under_llc",
    "smaller_only_under_clang",
    "direction_disagreement_count",
]

ATTRIBUTION_SUMMARY_FIELDS = [
    "program",
    "pair",
    "scope",
    "local_feature_delta",
    "final_feature_delta",
    "opcode_delta",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "evidence_level",
]


@dataclass(frozen=True)
class CoreEvidenceReport:
    validation_rows: list[dict[str, str]]
    propagation_rows: list[dict[str, str]]
    pruning_rows: list[dict[str, str]]
    objective_rows: list[dict[str, str]]
    attribution_rows: list[dict[str, str]]
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
    p8c_attribution_report: str | Path | None = None,
    p8c_feature_deltas_csv: str | Path | None = None,
    p8c_opcode_delta_csv: str | Path | None = None,
    p8c_object_size_csv: str | Path | None = None,
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
    p8c_attribution = _parse_optional_key_value_report(p8c_attribution_report)
    p8c_feature_deltas = _load_optional_csv(p8c_feature_deltas_csv)
    p8c_opcode_delta = _load_optional_csv(p8c_opcode_delta_csv)
    p8c_object_rows = _load_optional_csv(p8c_object_size_csv)

    validation_rows = _build_validation_rows(
        p4_attempts=p4_attempts,
        p7b_attempts=p7b_attempts,
    )
    propagation_rows = _build_propagation_rows(
        p5_candidates=p5_candidates,
        p6_object_rows=p6_object_rows,
        p7b_candidates=p7b_candidates,
        p7b_object_rows=p7b_object_rows,
        p7b_analysis=p7b_analysis,
        p8a_compare=p8a_compare,
    )
    pruning_rows = _build_pruning_rows(
        p4_attempts=p4_attempts,
        p7b_attempts=p7b_attempts,
        p7b_analysis=p7b_analysis,
        p8a_compare=p8a_compare,
    )
    objective_rows = [_build_objective_summary(p8a_compare)]
    attribution_rows = _build_attribution_rows(
        attribution_report=p8c_attribution,
        feature_deltas=p8c_feature_deltas,
        opcode_deltas=p8c_opcode_delta,
        object_rows=p8c_object_rows,
    )
    summary = _build_summary(
        validation_rows=validation_rows,
        propagation_rows=propagation_rows,
        pruning_rows=pruning_rows,
        objective_row=objective_rows[0],
        attribution_rows=attribution_rows,
        p6_object_rows=p6_object_rows,
        p7b_object_rows=p7b_object_rows,
        p7b_analysis=p7b_analysis,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_root / "ecpor_validation_funnel.csv",
        validation_rows,
        VALIDATION_FUNNEL_FIELDS,
    )
    _write_csv(
        output_root / "ecpor_candidate_propagation_funnel.csv",
        propagation_rows,
        CANDIDATE_PROPAGATION_FIELDS,
    )
    _write_csv(
        output_root / "ecpor_certified_pruning_summary.csv",
        pruning_rows,
        PRUNING_FIELDS,
    )
    _write_csv(
        output_root / "ecpor_objective_layer_summary.csv",
        objective_rows,
        OBJECTIVE_LAYER_FIELDS,
    )
    _write_csv(
        output_root / "ecpor_attribution_summary.csv",
        attribution_rows,
        ATTRIBUTION_SUMMARY_FIELDS,
    )
    (output_root / "ecpor_core_evidence_report.md").write_text(
        build_core_evidence_report(
            summary=summary,
            validation_rows=validation_rows,
            propagation_rows=propagation_rows,
            pruning_rows=pruning_rows,
            objective_rows=objective_rows,
            attribution_rows=attribution_rows,
        ),
        encoding="utf-8",
    )
    return CoreEvidenceReport(
        validation_rows=validation_rows,
        propagation_rows=propagation_rows,
        pruning_rows=pruning_rows,
        objective_rows=objective_rows,
        attribution_rows=attribution_rows,
        summary=summary,
    )


def build_core_evidence_report(
    *,
    summary: Mapping[str, Any],
    validation_rows: Sequence[dict[str, str]],
    propagation_rows: Sequence[dict[str, str]],
    pruning_rows: Sequence[dict[str, str]],
    objective_rows: Sequence[dict[str, str]],
    attribution_rows: Sequence[dict[str, str]],
) -> str:
    objective = objective_rows[0] if objective_rows else {}
    lines = [
        "# ECPOR Core Evidence Report",
        "",
        "本报告把 P4-P8a 的结果收束回最初问题：搜索空间坍缩、证据等级、以及目标函数层的 codegen 敏感性。",
        "它不新增搜索、不新增 certificate、不运行 runtime benchmark。",
        "",
        "## Validation Funnel",
        "",
        "| stage | basis | attempts | static candidate | dynamic tests | cache hits | certified events | not-certified events | low-priority events | run failed |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in validation_rows:
        lines.append(
            "| {stage} | {count_basis} | {attempted_swaps} | {static_candidate_swaps} | "
            "{dynamic_tests} | {cache_hits} | {certified_independent_events} | "
            "{not_certified_events} | {low_priority_events} | {run_failed} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Candidate Propagation Funnel",
            "",
            "| stage | basis | anchors | single-swap | raw depth2 | duplicates removed | unique depth2 | object-size evaluated | clang-c compared |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in propagation_rows:
        lines.append(
            "| {stage} | {count_basis} | {anchor_candidates} | {single_swap_candidates} | "
            "{raw_depth2_candidates} | {duplicates_removed} | {unique_depth2_candidates} | "
            "{object_size_evaluated_candidates} | {clang_c_compared_candidates} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Hard Evidence Vs Soft Evidence",
            "",
            "| stage | evidence event | count | scope | hard prune | proof level | meaning |",
            "| --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in pruning_rows:
        lines.append(
            "| {stage} | {evidence_event} | {count} | {scope} | {hard_prune} | "
            "{proof_level} | {meaning} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Objective-layer Evidence",
            "",
            "This is objective-layer evidence, not pruning evidence.",
            "",
            f"DirectionComparisonCandidates: {objective.get('direction_comparison_candidates', '0')}",
            f"DirectionAgreementCount: {objective.get('direction_agreement_count', '0')}",
            f"DirectionAgreementRate: {objective.get('direction_agreement_rate', '0.00%')}",
            f"SmallerUnderBothCount: {objective.get('smaller_under_both', '0')}",
            f"SmallerOnlyUnderLlcCount: {objective.get('smaller_only_under_llc', '0')}",
            f"SmallerOnlyUnderClangCount: {objective.get('smaller_only_under_clang', '0')}",
            f"DirectionDisagreementCount: {objective.get('direction_disagreement_count', '0')}",
            "",
            "## Observed Attribution Summary",
            "",
            "This is observed attribution evidence, not pruning evidence or causal proof.",
            "",
            f"AttributionCases: {len(attribution_rows)}",
            f"AttributionObservedButNotCausalProof: {bool(attribution_rows)}",
            "",
            "| program | pair | scope | local feature delta | final feature delta | opcode delta | llc text delta % | clang text delta % | evidence level |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in attribution_rows:
        lines.append(
            "| {program} | {pair} | {scope} | {local_feature_delta} | "
            "{final_feature_delta} | {opcode_delta} | {llc_text_delta_pct} | "
            "{clang_text_delta_pct} | {evidence_level} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Relation to Original Research Question",
            "",
            "ECPOR 当前已经证明：",
            "1. 一部分 state-indexed adjacent ordering 可以被 hard certificate 折叠。",
            "2. 一部分 not-certified ordering 必须保留为 candidate。",
            "3. static filter 只减少动态测试优先级，不产生 proof。",
            "4. sequence-level duplicate 能减少重复 candidate path，但不是语义等价证明。",
            "5. code-size observation 必须按 codegen path 区分。",
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
    parser.add_argument("--p8c-attribution-report", default="")
    parser.add_argument("--p8c-feature-deltas", default="")
    parser.add_argument("--p8c-opcode-delta", default="")
    parser.add_argument("--p8c-object-size", default="")
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
        p8c_attribution_report=args.p8c_attribution_report,
        p8c_feature_deltas_csv=args.p8c_feature_deltas,
        p8c_opcode_delta_csv=args.p8c_opcode_delta,
        p8c_object_size_csv=args.p8c_object_size,
    )
    print(
        build_core_evidence_report(
            summary=result.summary,
            validation_rows=result.validation_rows,
            propagation_rows=result.propagation_rows,
            pruning_rows=result.pruning_rows,
            objective_rows=result.objective_rows,
            attribution_rows=result.attribution_rows,
        ),
        end="",
    )
    return 0


def _build_validation_rows(
    *,
    p4_attempts: Sequence[dict[str, str]],
    p7b_attempts: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        _validation_row("P4", p4_attempts, "anchor-adjacent validation"),
        _validation_row("P7b", p7b_attempts, "second-swap prefix validation"),
    ]


def _validation_row(
    stage: str, attempts: Sequence[dict[str, str]], notes: str
) -> dict[str, str]:
    return {
        "stage": stage,
        "count_basis": "state_indexed_adjacent_swap_events",
        "attempted_swaps": str(len(attempts)),
        "static_candidate_swaps": str(_count_static_candidate(attempts)),
        "dynamic_tests": str(_count_true(attempts, "dynamic_test")),
        "cache_hits": str(_count_true(attempts, "cache_hit")),
        "certified_independent_events": str(
            _count_label(attempts, "certified_independent")
        ),
        "not_certified_events": str(
            _count_label(attempts, "not_certified_independent")
        ),
        "low_priority_events": str(_count_action(attempts, "skipped_low_priority")),
        "run_failed": str(_count_label(attempts, "run_failed")),
        "notes": notes,
    }


def _build_propagation_rows(
    *,
    p5_candidates: Sequence[dict[str, str]],
    p6_object_rows: Sequence[dict[str, str]],
    p7b_candidates: Sequence[dict[str, str]],
    p7b_object_rows: Sequence[dict[str, str]],
    p7b_analysis: Mapping[str, Any],
    p8a_compare: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    p5_anchor = [row for row in p5_candidates if row.get("source") == "anchor"]
    p5_single = [row for row in p5_candidates if row.get("source") == "single_swap"]
    p6_candidate_rows = [
        row for row in p6_object_rows if row.get("source") == "single_swap"
    ]
    p7b_anchor = [row for row in p7b_candidates if row.get("source") == "anchor"]
    p7b_depth2 = [row for row in p7b_candidates if row.get("source") == "two_swap"]
    p7b_depth2_object_rows = [
        row for row in p7b_object_rows if row.get("source") == "two_swap"
    ]
    return [
        {
            "stage": "P5",
            "count_basis": "candidate_pipelines_from_P4_evidence",
            "anchor_candidates": str(len(p5_anchor)),
            "single_swap_candidates": str(len(p5_single)),
            "raw_depth2_candidates": "0",
            "duplicates_removed": "0",
            "unique_depth2_candidates": "0",
            "object_size_evaluated_candidates": "0",
            "clang_c_compared_candidates": "0",
            "notes": "one-swap candidates from not-certified adjacent pairs",
        },
        {
            "stage": "P6",
            "count_basis": "single_swap_candidate_object_eval",
            "anchor_candidates": str(
                sum(1 for row in p6_object_rows if row.get("source") == "anchor")
            ),
            "single_swap_candidates": str(len(p6_candidate_rows)),
            "raw_depth2_candidates": "0",
            "duplicates_removed": "0",
            "unique_depth2_candidates": "0",
            "object_size_evaluated_candidates": str(len(p6_candidate_rows)),
            "clang_c_compared_candidates": "0",
            "notes": "llc object .text objective layer",
        },
        {
            "stage": "P7b",
            "count_basis": "depth2_candidate_pipelines",
            "anchor_candidates": str(len(p7b_anchor)),
            "single_swap_candidates": "0",
            "raw_depth2_candidates": str(
                _as_int(p7b_analysis.get("RawDepth2Candidates"), len(p7b_depth2))
            ),
            "duplicates_removed": str(_as_int(p7b_analysis.get("DuplicateSequences"), 0)),
            "unique_depth2_candidates": str(
                _as_int(p7b_analysis.get("UniqueDepth2Candidates"), len(p7b_depth2))
            ),
            "object_size_evaluated_candidates": str(len(p7b_depth2_object_rows)),
            "clang_c_compared_candidates": "0",
            "notes": "bounded depth2 candidates after sequence-level dedup",
        },
        {
            "stage": "P8a",
            "count_basis": "objective_layer_codegen_comparison",
            "anchor_candidates": "0",
            "single_swap_candidates": "0",
            "raw_depth2_candidates": "0",
            "duplicates_removed": "0",
            "unique_depth2_candidates": "0",
            "object_size_evaluated_candidates": "0",
            "clang_c_compared_candidates": str(len(p8a_compare)),
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
            "evidence_event": "certified_independent_events",
            "count": str(certified),
            "scope": "state-indexed adjacent swap events",
            "hard_prune": "True",
            "proof_level": "hard",
            "evidence_source": "hard hash equality certificate",
            "meaning": "A;B and B;A are equal for the same materialized state",
        },
        {
            "stage": "P4/P7b",
            "evidence_event": "not_certified_events",
            "count": str(not_certified),
            "scope": "state-indexed adjacent swap events",
            "hard_prune": "False",
            "proof_level": "hard_negative_for_equality",
            "evidence_source": "hard hash differs",
            "meaning": "order remains observable and must not be pruned as independent",
        },
        {
            "stage": "P4/P7b",
            "evidence_event": "low_priority_events",
            "count": str(low_priority),
            "scope": "static filter classification events",
            "hard_prune": "False",
            "proof_level": "soft",
            "evidence_source": "static filter hint",
            "meaning": "static ordering priority only, not a proof",
        },
        {
            "stage": "P7b",
            "evidence_event": "sequence_duplicates",
            "count": str(duplicate_sequences),
            "scope": "identical pass sequence paths",
            "hard_prune": "False",
            "proof_level": "syntactic_dedup",
            "evidence_source": "pipeline sequence hash",
            "meaning": "same pass sequence can be deduplicated but is not semantic equivalence",
        },
        {
            "stage": "P8a",
            "evidence_event": "llc_clang_both_smaller_object",
            "count": str(both_smaller),
            "scope": "objective-layer object-size observations",
            "hard_prune": "False",
            "proof_level": "target_layer",
            "evidence_source": "object .text under llc and clang-c",
            "meaning": "stronger objective-layer observation, not an independence proof",
        },
    ]


def _build_objective_summary(rows: Sequence[dict[str, str]]) -> dict[str, str]:
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
        "count_basis": "objective_layer_codegen_comparison",
        "direction_comparison_candidates": str(total),
        "direction_agreement_count": str(agreement),
        "direction_agreement_rate": _percent(agreement, total),
        "smaller_under_both": str(both_smaller),
        "smaller_only_under_llc": str(smaller_only_llc),
        "smaller_only_under_clang": str(smaller_only_clang),
        "direction_disagreement_count": str(disagreement),
    }


def _build_attribution_rows(
    *,
    attribution_report: Mapping[str, Any],
    feature_deltas: Sequence[dict[str, str]],
    opcode_deltas: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    if not attribution_report and not feature_deltas and not opcode_deltas:
        return []

    program = str(attribution_report.get("Program") or _first_value(object_rows, "program"))
    if not program:
        program = "testsuite_stanford_queens"
    local_features = _comparison_row(feature_deltas, "local_AB_vs_BA")
    final_features = _comparison_row(feature_deltas, "final_AB_vs_BA")
    final_opcodes = _comparison_row(opcode_deltas, "final_AB_vs_BA")
    return [
        {
            "program": program,
            "pair": "simplifycfg,instcombine",
            "scope": "single-state observed attribution",
            "local_feature_delta": _format_nonzero_deltas(local_features),
            "final_feature_delta": _format_nonzero_deltas(final_features),
            "opcode_delta": (
                str(attribution_report.get("FinalOpcodeDeltaNonZero") or "")
                or _format_nonzero_deltas(final_opcodes)
            ),
            "llc_text_delta_pct": _object_text_delta_pct(object_rows, "llc"),
            "clang_text_delta_pct": _object_text_delta_pct(object_rows, "clang"),
            "evidence_level": "observed attribution, not causal proof",
        }
    ]


def _build_summary(
    *,
    validation_rows: Sequence[dict[str, str]],
    propagation_rows: Sequence[dict[str, str]],
    pruning_rows: Sequence[dict[str, str]],
    objective_row: Mapping[str, str],
    attribution_rows: Sequence[dict[str, str]],
    p6_object_rows: Sequence[dict[str, str]],
    p7b_object_rows: Sequence[dict[str, str]],
    p7b_analysis: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "ValidationStages": len(validation_rows),
        "PropagationStages": len(propagation_rows),
        "CertifiedIndependentTotal": _summary_count(
            pruning_rows, "certified_independent_events"
        ),
        "NotCertifiedIndependentTotal": _summary_count(
            pruning_rows, "not_certified_events"
        ),
        "SequenceDuplicates": _as_int(p7b_analysis.get("DuplicateSequences"), 0),
        "P6SmallerText": _count_delta(p6_object_rows, "single_swap", "smaller"),
        "P7bDepth2SmallerText": _as_int(p7b_analysis.get("Depth2SmallerText"), 0),
        "P7bDepth2SmallerPrograms": _as_int(
            p7b_analysis.get("Depth2SmallerPrograms"), 0
        ),
        "P7bObjectRows": len(p7b_object_rows),
        "DirectionAgreementRate": objective_row.get("direction_agreement_rate", "0.00%"),
        "SmallerUnderBothCount": _parse_int(objective_row.get("smaller_under_both")),
        "AttributionCases": len(attribution_rows),
    }


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_optional_csv(path: str | Path | None) -> list[dict[str, str]]:
    if path in {None, ""}:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    return _load_csv(candidate)


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


def _parse_optional_key_value_report(path: str | Path | None) -> dict[str, Any]:
    if path in {None, ""}:
        return {}
    return _parse_key_value_report(path)


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


def _count_static_candidate(rows: Sequence[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("static_decision") == "candidate")


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
        if row.get("evidence_event") == evidence_type:
            return _parse_int(row.get("count"))
    return 0


def _first_value(rows: Sequence[dict[str, str]], field: str) -> str:
    for row in rows:
        value = row.get(field, "")
        if value:
            return value
    return ""


def _comparison_row(
    rows: Sequence[dict[str, str]], comparison: str
) -> dict[str, str]:
    for row in rows:
        if row.get("comparison") == comparison:
            return row
    return {}


def _format_nonzero_deltas(row: Mapping[str, str]) -> str:
    parts: list[str] = []
    for key, value in row.items():
        if not key.endswith("_delta"):
            continue
        numeric = _parse_optional_float(value)
        if numeric in {None, 0.0}:
            continue
        parts.append(f"{key}={value}")
    return ";".join(parts)


def _object_text_delta_pct(
    rows: Sequence[dict[str, str]], compile_mode: str
) -> str:
    for row in rows:
        if row.get("compile_mode") != compile_mode:
            continue
        if row.get("state_name") not in {"", "BA_final"}:
            continue
        return row.get("text_delta_pct", "")
    return ""


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
