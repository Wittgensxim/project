"""Build a small Misc8 evidence supplement from existing depth-1 outputs."""

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
    "object_size_evaluated_candidates",
    "notes",
]

OBJECTIVE_LAYER_FIELDS = [
    "count_basis",
    "direction_comparison_candidates",
    "direction_agreement_count",
    "direction_agreement_rate",
    "both_smaller",
    "smaller_only_llc",
    "smaller_only_clang",
    "direction_disagreement_count",
    "depth1_both_smaller_programs",
]

ATTRIBUTION_SUMMARY_FIELDS = [
    "program",
    "pair",
    "local_instruction_delta",
    "final_instruction_delta",
    "final_opcode_delta_nonzero",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "both_codegen_smaller",
    "evidence_level",
]


@dataclass(frozen=True)
class CoreEvidenceMisc8Report:
    validation_rows: list[dict[str, str]]
    propagation_rows: list[dict[str, str]]
    objective_rows: list[dict[str, str]]
    attribution_rows: list[dict[str, str]]
    summary: dict[str, Any]


def run_core_evidence_misc8(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p6_object_size_csv: str | Path,
    p8a_compare_csv: str | Path,
    depth1_analysis_report: str | Path,
    output_dir: str | Path,
    attribution_report: str | Path | None = None,
    attribution_feature_deltas_csv: str | Path | None = None,
    attribution_opcode_delta_csv: str | Path | None = None,
    attribution_object_size_csv: str | Path | None = None,
) -> CoreEvidenceMisc8Report:
    attempts = _load_csv(p4_attempts_csv)
    candidates = _load_csv(p5_candidates_csv)
    object_rows = _load_csv(p6_object_size_csv)
    compare_rows = _load_csv(p8a_compare_csv)
    depth1_summary = _parse_key_value_report(depth1_analysis_report)
    attribution_summary = _parse_optional_key_value_report(attribution_report)
    attribution_feature_rows = _load_optional_csv(attribution_feature_deltas_csv)
    attribution_opcode_rows = _load_optional_csv(attribution_opcode_delta_csv)
    attribution_object_rows = _load_optional_csv(attribution_object_size_csv)

    validation_rows = [_build_validation_row(attempts)]
    propagation_rows = [_build_propagation_row(candidates, object_rows)]
    objective_rows = [_build_objective_row(compare_rows, depth1_summary)]
    attribution_rows = _build_attribution_rows(
        attribution_summary,
        attribution_feature_rows,
        attribution_opcode_rows,
        attribution_object_rows,
    )
    summary = _build_summary(
        validation_rows=validation_rows,
        propagation_rows=propagation_rows,
        objective_rows=objective_rows,
        attribution_rows=attribution_rows,
        depth1_summary=depth1_summary,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_root / "misc8_validation_funnel.csv",
        validation_rows,
        VALIDATION_FUNNEL_FIELDS,
    )
    _write_csv(
        output_root / "misc8_candidate_propagation_funnel.csv",
        propagation_rows,
        CANDIDATE_PROPAGATION_FIELDS,
    )
    _write_csv(
        output_root / "misc8_objective_layer_summary.csv",
        objective_rows,
        OBJECTIVE_LAYER_FIELDS,
    )
    _write_csv(
        output_root / "misc8_attribution_summary.csv",
        attribution_rows,
        ATTRIBUTION_SUMMARY_FIELDS,
    )
    (output_root / "ecpor_misc8_depth1_evidence_report.md").write_text(
        build_core_evidence_misc8_report(
            summary=summary,
            validation_rows=validation_rows,
            propagation_rows=propagation_rows,
            objective_rows=objective_rows,
            attribution_rows=attribution_rows,
        ),
        encoding="utf-8",
    )
    return CoreEvidenceMisc8Report(
        validation_rows=validation_rows,
        propagation_rows=propagation_rows,
        objective_rows=objective_rows,
        attribution_rows=attribution_rows,
        summary=summary,
    )


def build_core_evidence_misc8_report(
    *,
    summary: Mapping[str, Any],
    validation_rows: Sequence[dict[str, str]],
    propagation_rows: Sequence[dict[str, str]],
    objective_rows: Sequence[dict[str, str]],
    attribution_rows: Sequence[dict[str, str]],
) -> str:
    validation = validation_rows[0] if validation_rows else {}
    propagation = propagation_rows[0] if propagation_rows else {}
    objective = objective_rows[0] if objective_rows else {}
    lines = [
        "# Misc8 Depth1 Core Evidence Supplement",
        "",
        "Misc8 repeats the Stanford pattern when depth-1 candidates are projected through validation, candidate propagation, object-size, and attribution layers.",
        "This supplement reuses existing Misc8 depth-1 outputs; it does not run a two-swap search or runtime benchmark.",
        "",
        f"AttemptedSwaps: {validation.get('attempted_swaps', '0')}",
        f"CertifiedIndependentEvents: {validation.get('certified_independent_events', '0')}",
        f"SingleSwapCandidates: {propagation.get('single_swap_candidates', '0')}",
        f"ObjectSizeEvaluatedCandidates: {propagation.get('object_size_evaluated_candidates', '0')}",
        f"DirectionComparisonCandidates: {objective.get('direction_comparison_candidates', '0')}",
        f"DirectionAgreementRate: {objective.get('direction_agreement_rate', '0.00%')}",
        f"BothSmaller: {objective.get('both_smaller', '0')}",
        f"BothSmallerPrograms: {summary['BothSmallerPrograms']}",
        f"AttributionCases: {summary['AttributionCases']}",
        f"AttributionObservedButNotCausalProof: {summary['AttributionObservedButNotCausalProof']}",
        "",
        "## Validation Funnel",
        "",
        "| stage | attempts | dynamic | certified | not certified | low priority | run failed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in validation_rows:
        lines.append(
            "| {stage} | {attempted_swaps} | {dynamic_tests} | "
            "{certified_independent_events} | {not_certified_events} | "
            "{low_priority_events} | {run_failed} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Candidate Propagation",
            "",
            "| stage | anchors | single swap | object-size evaluated |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in propagation_rows:
        lines.append(
            "| {stage} | {anchor_candidates} | {single_swap_candidates} | "
            "{object_size_evaluated_candidates} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Objective Layer",
            "",
            "| comparisons | agreement | both smaller | disagreement |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for row in objective_rows:
        lines.append(
            "| {direction_comparison_candidates} | {direction_agreement_rate} | "
            "{both_smaller} | {direction_disagreement_count} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Attribution Supplement",
            "",
            "| program | pair | final instruction delta | opcode delta | both codegen smaller |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for row in attribution_rows:
        lines.append(
            "| {program} | {pair} | {final_instruction_delta} | "
            "{final_opcode_delta_nonzero} | {both_codegen_smaller} |".format(**row)
        )
    return "\n".join(lines) + "\n"


def _build_validation_row(attempts: Sequence[Mapping[str, str]]) -> dict[str, str]:
    return {
        "stage": "P4 Misc8 lazy validation",
        "count_basis": "attempt rows",
        "attempted_swaps": str(len(attempts)),
        "static_candidate_swaps": str(_count_action(attempts, "candidate")),
        "dynamic_tests": str(
            sum(
                1
                for row in attempts
                if _truthy(row.get("dynamic_test")) or row.get("action") == "dynamic_test"
            )
        ),
        "cache_hits": str(sum(1 for row in attempts if _truthy(row.get("cache_hit")))),
        "certified_independent_events": str(
            _count_label(attempts, "certified_independent")
        ),
        "not_certified_events": str(
            _count_label(attempts, "not_certified_independent")
        ),
        "low_priority_events": str(
            sum(
                1
                for row in attempts
                if "low_priority" in row.get("action", "")
                or "low_priority" in row.get("label", "")
            )
        ),
        "run_failed": str(
            sum(
                1
                for row in attempts
                if row.get("label") == "run_failed"
                or bool(row.get("failure_kind") or row.get("failure_kind_ab"))
            )
        ),
        "notes": "Existing depth-1 Misc8 validation rows.",
    }


def _build_propagation_row(
    candidates: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    return {
        "stage": "P5/P6 Misc8 depth1 propagation",
        "count_basis": "candidate rows",
        "anchor_candidates": str(_count_source(candidates, "anchor")),
        "single_swap_candidates": str(_count_source(candidates, "single_swap")),
        "object_size_evaluated_candidates": str(
            sum(
                1
                for row in object_rows
                if row.get("source") == "single_swap" and not _has_size_failure(row)
            )
        ),
        "notes": "Single-swap candidates only; no depth-2 expansion.",
    }


def _build_objective_row(
    compare_rows: Sequence[Mapping[str, str]],
    depth1_summary: Mapping[str, str],
) -> dict[str, str]:
    rows = [
        row
        for row in compare_rows
        if row.get("source", "single_swap") == "single_swap"
        and row.get("llc_direction", "")
        and row.get("clang_direction", "")
    ]
    agreement = sum(1 for row in rows if _truthy(row.get("direction_agree")))
    both_smaller = [
        row
        for row in rows
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    ]
    smaller_only_llc = sum(
        1
        for row in rows
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") != "smaller"
    )
    smaller_only_clang = sum(
        1
        for row in rows
        if row.get("clang_direction") == "smaller"
        and row.get("llc_direction") != "smaller"
    )
    both_smaller_programs = _parse_int(
        depth1_summary.get("Depth1BothSmallerPrograms"),
        default=len({row.get("program", "") for row in both_smaller if row.get("program")}),
    )
    return {
        "count_basis": "single-swap direction comparisons",
        "direction_comparison_candidates": str(len(rows)),
        "direction_agreement_count": str(agreement),
        "direction_agreement_rate": _pct(agreement, len(rows)),
        "both_smaller": str(len(both_smaller)),
        "smaller_only_llc": str(smaller_only_llc),
        "smaller_only_clang": str(smaller_only_clang),
        "direction_disagreement_count": str(len(rows) - agreement),
        "depth1_both_smaller_programs": str(both_smaller_programs),
    }


def _build_attribution_rows(
    attribution_summary: Mapping[str, str],
    feature_rows: Sequence[Mapping[str, str]],
    opcode_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if not attribution_summary:
        return []
    llc_row = _find_object_row(object_rows, "llc", "BA_final")
    clang_row = _find_object_row(object_rows, "clang", "BA_final")
    final_feature = _find_row(feature_rows, "comparison", "final_AB_vs_BA")
    final_opcode = _find_row(opcode_rows, "comparison", "final_AB_vs_BA")
    return [
        {
            "program": attribution_summary.get("Program", ""),
            "pair": attribution_summary.get("Pair", ""),
            "local_instruction_delta": attribution_summary.get(
                "LocalInstructionDelta", ""
            ),
            "final_instruction_delta": attribution_summary.get(
                "FinalInstructionDelta",
                final_feature.get("num_instructions_delta", ""),
            ),
            "final_opcode_delta_nonzero": attribution_summary.get(
                "FinalOpcodeDeltaNonZero",
                _format_nonzero_delta(final_opcode),
            ),
            "llc_text_delta_pct": llc_row.get("text_delta_pct", ""),
            "clang_text_delta_pct": clang_row.get("text_delta_pct", ""),
            "both_codegen_smaller": attribution_summary.get(
                "BothCodegenSmaller", ""
            ),
            "evidence_level": "observed_attribution_not_causal_proof",
        }
    ]


def _build_summary(
    *,
    validation_rows: Sequence[Mapping[str, str]],
    propagation_rows: Sequence[Mapping[str, str]],
    objective_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    depth1_summary: Mapping[str, str],
) -> dict[str, Any]:
    objective = objective_rows[0] if objective_rows else {}
    return {
        "AttemptedSwaps": _parse_int(validation_rows[0].get("attempted_swaps"), 0)
        if validation_rows
        else 0,
        "CertifiedIndependentEvents": _parse_int(
            validation_rows[0].get("certified_independent_events"), 0
        )
        if validation_rows
        else 0,
        "SingleSwapCandidates": _parse_int(
            propagation_rows[0].get("single_swap_candidates"), 0
        )
        if propagation_rows
        else 0,
        "ObjectSizeEvaluatedCandidates": _parse_int(
            propagation_rows[0].get("object_size_evaluated_candidates"), 0
        )
        if propagation_rows
        else 0,
        "DirectionComparisonCandidates": _parse_int(
            objective.get("direction_comparison_candidates"), 0
        ),
        "DirectionAgreementRate": objective.get("direction_agreement_rate", "0.00%"),
        "BothSmaller": _parse_int(objective.get("both_smaller"), 0),
        "BothSmallerPrograms": _parse_int(
            depth1_summary.get("Depth1BothSmallerPrograms"),
            _parse_int(objective.get("depth1_both_smaller_programs"), 0),
        ),
        "AttributionCases": len(attribution_rows),
        "AttributionObservedButNotCausalProof": bool(attribution_rows),
    }


def _has_size_failure(row: Mapping[str, str]) -> bool:
    return bool(row.get("compile_failure_kind") or row.get("size_failure_kind"))


def _count_action(rows: Sequence[Mapping[str, str]], token: str) -> int:
    return sum(1 for row in rows if token in row.get("action", ""))


def _count_label(rows: Sequence[Mapping[str, str]], label: str) -> int:
    return sum(1 for row in rows if row.get("label") == label)


def _count_source(rows: Sequence[Mapping[str, str]], source: str) -> int:
    return sum(1 for row in rows if row.get("source") == source)


def _find_row(
    rows: Sequence[Mapping[str, str]], key: str, value: str
) -> Mapping[str, str]:
    return next((row for row in rows if row.get(key) == value), {})


def _find_object_row(
    rows: Sequence[Mapping[str, str]], mode: str, state_name: str
) -> Mapping[str, str]:
    return next(
        (
            row
            for row in rows
            if row.get("compile_mode") == mode and row.get("state_name") == state_name
        ),
        {},
    )


def _format_nonzero_delta(row: Mapping[str, str]) -> str:
    deltas = [
        f"{key}={value}"
        for key, value in row.items()
        if key.endswith("_delta") and value not in {"", "0"}
    ]
    return ";".join(deltas) if deltas else "none"


def _parse_key_value_report(path: str | Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def _parse_optional_key_value_report(path: str | Path | None) -> dict[str, str]:
    if path is None or not Path(path).exists():
        return {}
    return _parse_key_value_report(path)


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_optional_csv(path: str | Path | None) -> list[dict[str, str]]:
    if path is None or not Path(path).exists():
        return []
    return _load_csv(path)


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _parse_int(value: object, default: int = 0) -> int:
    if value in {None, ""}:
        return default
    text = str(value).strip()
    if text.endswith("%"):
        text = text[:-1]
    try:
        return int(float(text))
    except ValueError:
        return default


def _pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator) * 100.0:.2f}%"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the P8b-3.5 Misc8 depth1 evidence supplement."
    )
    parser.add_argument("--p4-attempts", required=True)
    parser.add_argument("--p5-candidates", required=True)
    parser.add_argument("--p6-object-size", required=True)
    parser.add_argument("--p8a-compare", required=True)
    parser.add_argument("--depth1-analysis-report", required=True)
    parser.add_argument("--attribution-report")
    parser.add_argument("--attribution-feature-deltas")
    parser.add_argument("--attribution-opcode-delta")
    parser.add_argument("--attribution-object-size")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = run_core_evidence_misc8(
        p4_attempts_csv=args.p4_attempts,
        p5_candidates_csv=args.p5_candidates,
        p6_object_size_csv=args.p6_object_size,
        p8a_compare_csv=args.p8a_compare,
        depth1_analysis_report=args.depth1_analysis_report,
        output_dir=args.out,
        attribution_report=args.attribution_report,
        attribution_feature_deltas_csv=args.attribution_feature_deltas,
        attribution_opcode_delta_csv=args.attribution_opcode_delta,
        attribution_object_size_csv=args.attribution_object_size,
    )
    report = Path(args.out) / "ecpor_misc8_depth1_evidence_report.md"
    print(report.read_text(encoding="utf-8"), end="")
    return 0 if result.summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
