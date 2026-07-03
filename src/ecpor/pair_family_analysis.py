"""Build a targeted pair-family analysis from retained depth1 evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


EVENTS_CSV_NAME = "pair_family_events.csv"
PROGRAM_SUMMARY_CSV_NAME = "pair_family_program_summary.csv"
OBJECTIVE_SUMMARY_CSV_NAME = "pair_family_objective_summary.csv"
ATTRIBUTION_COMPARE_CSV_NAME = "pair_family_attribution_compare.csv"
ANALYSIS_JSON_NAME = "pair_family_analysis.json"
REPORT_NAME = "pair_family_analysis_report.md"

DEFAULT_PAIR_A = "instcombine"
DEFAULT_PAIR_B = "simplifycfg"

DEFAULT_FULL_MATRIX_SOURCES = [
    ("Stanford-8", "data/outputs/cert_summary.csv"),
    ("Misc8", "data/outputs/cert_summary_p8b_misc8_pre.csv"),
    ("Diverse8", "data/outputs/cert_summary_p9_diverse8_pre.csv"),
]
DEFAULT_PREFIX_ATTEMPT_SOURCES = [
    ("Stanford-8", "data/outputs/lazy_validation_p4_e83c409_first.csv"),
    ("Misc8", "data/outputs/lazy_validation_p8b_misc8/attempts.csv"),
    ("Diverse8", "data/outputs/lazy_validation_p9_diverse8/attempts.csv"),
]
DEFAULT_CANDIDATE_SOURCES = [
    ("Stanford-8", "data/outputs/bounded_local_p5_p6_final/candidates.csv"),
    ("Misc8", "data/outputs/bounded_local_p8b_misc8/candidates.csv"),
    ("Diverse8", "data/outputs/bounded_local_p9_diverse8/candidates.csv"),
]
DEFAULT_OBJECT_SOURCES = [
    ("Stanford-8", "data/outputs/code_size_p6_final/object_size.csv"),
    ("Misc8", "data/outputs/code_size_p8b_misc8/object_size.csv"),
    ("Diverse8", "data/outputs/code_size_p9_diverse8/object_size.csv"),
]
DEFAULT_CODEGEN_SOURCES = [
    ("Stanford-8", "data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv"),
    ("Misc8", "data/outputs/codegen_sensitivity_p8b_misc8/p8a_codegen_direction_compare.csv"),
    ("Diverse8", "data/outputs/codegen_sensitivity_p9_diverse8/p8a_codegen_direction_compare.csv"),
]
DEFAULT_ATTRIBUTION_SOURCES = [
    ("Stanford-8", "data/outputs/core_evidence_report/ecpor_attribution_summary.csv"),
    ("Misc8", "data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv"),
]
DEFAULT_INTERACTION_EDGE_CSV = "data/outputs/interaction_graph_v1/pass_interaction_edges.csv"
DEFAULT_REDUCED_COMPONENT_EDGE_CSV = "data/outputs/reduced_components_v1/reduced_component_edges.csv"
DEFAULT_SEARCH_SPACE_CSV = "data/outputs/reduced_components_v1/search_space_estimate.csv"

EVENT_FIELDS = [
    "benchmark_set",
    "program",
    "state_scope",
    "source_stage",
    "pair",
    "label",
    "hard_equal",
    "prefix_state_hash",
    "feature_delta",
    "cert_id",
]
PROGRAM_SUMMARY_FIELDS = [
    "program",
    "benchmark_set",
    "full_matrix_label",
    "prefix_label",
    "generated_one_swap",
    "final_ir_different",
    "llc_direction",
    "clang_direction",
    "both_smaller",
    "has_attribution",
]
OBJECTIVE_SUMMARY_FIELDS = [
    "benchmark_set",
    "programs",
    "one_swap_candidates",
    "llc_smaller",
    "llc_equal",
    "llc_larger",
    "clang_smaller",
    "clang_equal",
    "clang_larger",
    "both_smaller",
    "direction_disagreement",
]
ATTRIBUTION_COMPARE_FIELDS = [
    "benchmark_set",
    "program",
    "pair",
    "opcode_delta",
    "removed_opcodes",
    "added_opcodes",
    "net_instruction_delta",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "evidence_level",
]


def build_pair_family_analysis(
    *,
    pair_a: str = DEFAULT_PAIR_A,
    pair_b: str = DEFAULT_PAIR_B,
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    interaction_edge_rows: Sequence[Mapping[str, str]] = (),
    reduced_component_rows: Sequence[Mapping[str, str]] = (),
    search_space_rows: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    pair = _pair_set(pair_a, pair_b)
    pair_text = f"{pair_a},{pair_b}"

    target_full = [_with_set(row) for row in full_matrix_rows if _row_matches(row, pair)]
    target_prefix = [_with_set(row) for row in prefix_attempt_rows if _row_matches(row, pair)]
    target_candidates = [
        _with_set(row)
        for row in candidate_rows
        if str(row.get("source", "")) == "single_swap" and _row_matches(row, pair)
    ]
    target_objects = [
        _with_set(row)
        for row in object_rows
        if str(row.get("source", "")) == "single_swap" and _row_matches(row, pair)
    ]
    target_codegen = [
        _with_set(row)
        for row in codegen_rows
        if _is_depth1_single_swap(row) and _row_matches(row, pair)
    ]
    target_attribution = [
        _with_set(row) for row in attribution_rows if _row_matches(row, pair)
    ]

    events = _build_events(
        pair_text=pair_text,
        full_rows=target_full,
        prefix_rows=target_prefix,
        candidate_rows=target_candidates,
        codegen_rows=target_codegen,
        attribution_rows=target_attribution,
    )
    program_summary = _build_program_summary(
        pair_text=pair_text,
        full_rows=target_full,
        prefix_rows=target_prefix,
        candidate_rows=target_candidates,
        object_rows=target_objects,
        codegen_rows=target_codegen,
        attribution_rows=target_attribution,
    )
    objective_summary = _build_objective_summary(
        program_summary=program_summary,
        candidate_rows=target_candidates,
        codegen_rows=target_codegen,
    )
    attribution_compare = _build_attribution_compare(
        pair_text=pair_text,
        attribution_rows=target_attribution,
    )
    graph_context = _build_graph_context(
        pair=pair,
        interaction_edge_rows=interaction_edge_rows,
        reduced_component_rows=reduced_component_rows,
        search_space_rows=search_space_rows,
    )
    summary = _summarize(
        pair_text=pair_text,
        program_summary=program_summary,
        full_rows=target_full,
        prefix_rows=target_prefix,
        candidate_rows=target_candidates,
        object_rows=target_objects,
        codegen_rows=target_codegen,
        attribution_compare=attribution_compare,
    )

    return {
        "stage": "P14",
        "scope": {
            "summary_only": True,
            "pair_family_analysis_only": True,
            "target_pair": pair_text,
            "new_experiments": False,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "passspec_behavior_change": False,
            "static_filter_behavior_change": False,
        },
        "summary": summary,
        "graph_context": graph_context,
        "events": events,
        "program_summary": program_summary,
        "objective_summary": objective_summary,
        "attribution_compare": attribution_compare,
        "evidence_boundary": {
            "targeted_pair_family_is_not_global_ordering_rule": True,
            "attribution_is_observed_not_causal_proof": True,
            "objective_sensitive_is_not_hard_prune_proof": True,
            "full_matrix_and_prefix_state_are_separate_scopes": True,
        },
    }


def render_report(analysis: Mapping[str, Any]) -> str:
    summary = analysis["summary"]
    attribution_rows = list(analysis["attribution_compare"])
    objective_rows = list(analysis["objective_summary"])

    lines = [
        "# P14 Pair-Family Analysis",
        "",
        "P14 is a summary-only targeted analysis. It reads retained evidence and does not run LLVM, create certificates, or start search.",
        "P14 is a pair-family analysis for the only objective-sensitive hotspot found by the corpus-level graph. It does not replace per-program reduced-component analysis.",
        "The target pair-family is useful as an observed interaction hotspot, not a global ordering rule and not a hard-prune proof.",
        "",
    ]
    for key in [
        "PairFamily",
        "Programs",
        "FullMatrixCertified",
        "FullMatrixNotCertified",
        "PrefixCertified",
        "PrefixNotCertified",
        "OneSwapCandidates",
        "FinalIrDifferent",
        "BothSmallerPrograms",
        "AttributionCases",
        "SelectRelatedAttributionCases",
        "NewExperiments",
        "NewCertificates",
        "NewSearch",
    ]:
        lines.append(f"{key}: {summary[key]}")

    lines.extend(
        [
            "",
            "## Objective Summary",
            "",
            "| benchmark_set | programs | one_swap_candidates | both_smaller | direction_disagreement |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in objective_rows:
        lines.append(
            "| {benchmark_set} | {programs} | {one_swap_candidates} | {both_smaller} | {direction_disagreement} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Attribution Compare",
            "",
            "| program | pair | removed_opcodes | added_opcodes | llc_text_delta_pct | clang_text_delta_pct |",
            "| --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    if attribution_rows:
        for row in attribution_rows:
            lines.append(
                "| {program} | `{pair}` | {removed_opcodes} | {added_opcodes} | {llc_text_delta_pct} | {clang_text_delta_pct} |".format(
                    **row
                )
            )
    else:
        lines.append("| none |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`instcombine/simplifycfg` is the current objective-sensitive hotspot in the retained 24-program depth1 evidence.",
            "Order-sensitive events are common, but objective propagation is narrow. Treat this as a targeted interaction family for explanation, not as a global ordering rule.",
            "Any follow-up should collect targeted witness states for this pair-family or freeze the research report, not expand to full search.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_pair_family_analysis_outputs(
    *,
    output_dir: str | Path,
    pair_a: str = DEFAULT_PAIR_A,
    pair_b: str = DEFAULT_PAIR_B,
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    interaction_edge_rows: Sequence[Mapping[str, str]] = (),
    reduced_component_rows: Sequence[Mapping[str, str]] = (),
    search_space_rows: Sequence[Mapping[str, str]] = (),
) -> dict[str, Path]:
    analysis = build_pair_family_analysis(
        pair_a=pair_a,
        pair_b=pair_b,
        full_matrix_rows=full_matrix_rows,
        prefix_attempt_rows=prefix_attempt_rows,
        candidate_rows=candidate_rows,
        object_rows=object_rows,
        codegen_rows=codegen_rows,
        attribution_rows=attribution_rows,
        interaction_edge_rows=interaction_edge_rows,
        reduced_component_rows=reduced_component_rows,
        search_space_rows=search_space_rows,
    )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events_path = out / EVENTS_CSV_NAME
    program_summary_path = out / PROGRAM_SUMMARY_CSV_NAME
    objective_summary_path = out / OBJECTIVE_SUMMARY_CSV_NAME
    attribution_compare_path = out / ATTRIBUTION_COMPARE_CSV_NAME
    analysis_json_path = out / ANALYSIS_JSON_NAME
    report_path = out / REPORT_NAME

    _write_csv(events_path, EVENT_FIELDS, analysis["events"])
    _write_csv(program_summary_path, PROGRAM_SUMMARY_FIELDS, analysis["program_summary"])
    _write_csv(objective_summary_path, OBJECTIVE_SUMMARY_FIELDS, analysis["objective_summary"])
    _write_csv(attribution_compare_path, ATTRIBUTION_COMPARE_FIELDS, analysis["attribution_compare"])
    analysis_json_path.write_text(
        json.dumps(analysis, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(analysis), encoding="utf-8")
    return {
        "events": events_path,
        "program_summary": program_summary_path,
        "objective_summary": objective_summary_path,
        "attribution_compare": attribution_compare_path,
        "analysis_json": analysis_json_path,
        "report": report_path,
    }


def write_pair_family_analysis_outputs_from_paths(
    *,
    output_dir: str | Path,
    pair_a: str = DEFAULT_PAIR_A,
    pair_b: str = DEFAULT_PAIR_B,
    full_matrix_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_FULL_MATRIX_SOURCES,
    prefix_attempt_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_PREFIX_ATTEMPT_SOURCES,
    candidate_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_CANDIDATE_SOURCES,
    object_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_OBJECT_SOURCES,
    codegen_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_CODEGEN_SOURCES,
    attribution_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_ATTRIBUTION_SOURCES,
    interaction_edges_csv: str | Path = DEFAULT_INTERACTION_EDGE_CSV,
    reduced_component_edges_csv: str | Path = DEFAULT_REDUCED_COMPONENT_EDGE_CSV,
    search_space_csv: str | Path = DEFAULT_SEARCH_SPACE_CSV,
) -> dict[str, Path]:
    return write_pair_family_analysis_outputs(
        output_dir=output_dir,
        pair_a=pair_a,
        pair_b=pair_b,
        full_matrix_rows=_read_many_labeled_csvs(full_matrix_sources),
        prefix_attempt_rows=_read_many_labeled_csvs(prefix_attempt_sources),
        candidate_rows=_read_many_labeled_csvs(candidate_sources),
        object_rows=_read_many_labeled_csvs(object_sources),
        codegen_rows=_read_many_labeled_csvs(codegen_sources),
        attribution_rows=_read_many_labeled_csvs(attribution_sources),
        interaction_edge_rows=_read_csv(interaction_edges_csv),
        reduced_component_rows=_read_csv(reduced_component_edges_csv),
        search_space_rows=_read_csv(search_space_csv),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P14 pair-family analysis.")
    parser.add_argument("--pair-a", default=DEFAULT_PAIR_A)
    parser.add_argument("--pair-b", default=DEFAULT_PAIR_B)
    parser.add_argument(
        "--out-dir",
        default="data/outputs/pair_family_instcombine_simplifycfg",
    )
    parser.add_argument("--full-matrix-csv", action="append")
    parser.add_argument("--prefix-attempt-csv", action="append")
    parser.add_argument("--candidate-csv", action="append")
    parser.add_argument("--object-csv", action="append")
    parser.add_argument("--codegen-csv", action="append")
    parser.add_argument("--attribution-csv", action="append")
    parser.add_argument("--interaction-edges", default=DEFAULT_INTERACTION_EDGE_CSV)
    parser.add_argument(
        "--reduced-component-edges",
        default=DEFAULT_REDUCED_COMPONENT_EDGE_CSV,
    )
    parser.add_argument("--search-space", default=DEFAULT_SEARCH_SPACE_CSV)
    args = parser.parse_args(argv)

    outputs = write_pair_family_analysis_outputs_from_paths(
        output_dir=args.out_dir,
        pair_a=args.pair_a,
        pair_b=args.pair_b,
        full_matrix_sources=_custom_sources(args.full_matrix_csv)
        or DEFAULT_FULL_MATRIX_SOURCES,
        prefix_attempt_sources=_custom_sources(args.prefix_attempt_csv)
        or DEFAULT_PREFIX_ATTEMPT_SOURCES,
        candidate_sources=_custom_sources(args.candidate_csv)
        or DEFAULT_CANDIDATE_SOURCES,
        object_sources=_custom_sources(args.object_csv) or DEFAULT_OBJECT_SOURCES,
        codegen_sources=_custom_sources(args.codegen_csv) or DEFAULT_CODEGEN_SOURCES,
        attribution_sources=_custom_sources(args.attribution_csv)
        or DEFAULT_ATTRIBUTION_SOURCES,
        interaction_edges_csv=args.interaction_edges,
        reduced_component_edges_csv=args.reduced_component_edges,
        search_space_csv=args.search_space,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _build_events(
    *,
    pair_text: str,
    full_rows: Sequence[Mapping[str, str]],
    prefix_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for row in full_rows:
        events.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "state_scope": "input_state",
                "source_stage": "full_matrix",
                "pair": pair_text,
                "label": row.get("label", ""),
                "hard_equal": row.get("hard_equal", ""),
                "prefix_state_hash": "",
                "feature_delta": row.get("feature_delta", ""),
                "cert_id": row.get("cert_id", ""),
            }
        )
    for row in prefix_rows:
        events.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "state_scope": "prefix_state",
                "source_stage": "prefix_validation",
                "pair": pair_text,
                "label": row.get("label", ""),
                "hard_equal": "",
                "prefix_state_hash": row.get("state_hash", ""),
                "feature_delta": "",
                "cert_id": row.get("cert_id", ""),
            }
        )
    for row in candidate_rows:
        events.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "state_scope": "final_pipeline",
                "source_stage": "one_swap_candidate",
                "pair": pair_text,
                "label": row.get("validation_label", ""),
                "hard_equal": "",
                "prefix_state_hash": row.get("prefix_state_hash", ""),
                "feature_delta": "",
                "cert_id": row.get("candidate_id", ""),
            }
        )
    for row in codegen_rows:
        label = f"llc={row.get('llc_direction', '')};clang={row.get('clang_direction', '')}"
        events.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "state_scope": "objective_layer",
                "source_stage": "codegen_direction",
                "pair": pair_text,
                "label": label,
                "hard_equal": "",
                "prefix_state_hash": "",
                "feature_delta": "",
                "cert_id": row.get("candidate_id", ""),
            }
        )
    for row in attribution_rows:
        events.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "state_scope": "attribution",
                "source_stage": "attribution_summary",
                "pair": pair_text,
                "label": row.get("evidence_level", ""),
                "hard_equal": "",
                "prefix_state_hash": "",
                "feature_delta": row.get("final_feature_delta")
                or row.get("local_feature_delta", ""),
                "cert_id": "",
            }
        )
    return _sort_rows(events)


def _build_program_summary(
    *,
    pair_text: str,
    full_rows: Sequence[Mapping[str, str]],
    prefix_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows_by_program = {
        "full": _group_by_program(full_rows),
        "prefix": _group_by_program(prefix_rows),
        "candidate": _group_by_program(candidate_rows),
        "object": _group_by_program(object_rows),
        "codegen": _group_by_program(codegen_rows),
        "attribution": _group_by_program(attribution_rows),
    }
    programs = sorted(
        {
            row.get("program", "")
            for rows in rows_by_program.values()
            for bucket in rows.values()
            for row in bucket
            if row.get("program", "")
        },
        key=_program_sort_key,
    )
    result: list[dict[str, str]] = []
    for program in programs:
        full = rows_by_program["full"].get(program, [])
        prefix = rows_by_program["prefix"].get(program, [])
        candidates = rows_by_program["candidate"].get(program, [])
        objects = rows_by_program["object"].get(program, [])
        codegen = rows_by_program["codegen"].get(program, [])
        attribution = rows_by_program["attribution"].get(program, [])
        set_name = _first_benchmark_set(full, prefix, candidates, objects, codegen, attribution)
        llc_direction = _direction_summary(codegen, "llc_direction")
        clang_direction = _direction_summary(codegen, "clang_direction")
        both_smaller = any(_row_has_both_smaller(row) for row in codegen) or any(
            _row_has_both_smaller(row) for row in attribution
        )
        final_ir_different = any(
            str(row.get("p5_same_as_anchor", "")).lower() == "false"
            for row in objects
        )
        result.append(
            {
                "program": program,
                "benchmark_set": set_name,
                "full_matrix_label": _label_summary(full),
                "prefix_label": _label_summary(prefix),
                "generated_one_swap": _bool_text(bool(candidates)),
                "final_ir_different": _bool_text(final_ir_different),
                "llc_direction": llc_direction,
                "clang_direction": clang_direction,
                "both_smaller": _bool_text(both_smaller),
                "has_attribution": _bool_text(bool(attribution)),
            }
        )
    return result


def _build_objective_summary(
    *,
    program_summary: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    sets = sorted(
        {_benchmark_set(row) for row in program_summary},
        key=_benchmark_set_sort_key,
    )
    result: list[dict[str, Any]] = []
    for set_name in sets:
        programs = [
            row for row in program_summary if _benchmark_set(row) == set_name
        ]
        candidates = [row for row in candidate_rows if _benchmark_set(row) == set_name]
        codegen = [row for row in codegen_rows if _benchmark_set(row) == set_name]
        both_programs = {
            row.get("program", "") for row in codegen if _row_has_both_smaller(row)
        }
        result.append(
            {
                "benchmark_set": set_name,
                "programs": len(programs),
                "one_swap_candidates": len(candidates),
                "llc_smaller": _direction_count(codegen, "llc_direction", "smaller"),
                "llc_equal": _direction_count(codegen, "llc_direction", "equal"),
                "llc_larger": _direction_count(codegen, "llc_direction", "larger"),
                "clang_smaller": _direction_count(codegen, "clang_direction", "smaller"),
                "clang_equal": _direction_count(codegen, "clang_direction", "equal"),
                "clang_larger": _direction_count(codegen, "clang_direction", "larger"),
                "both_smaller": len({program for program in both_programs if program}),
                "direction_disagreement": sum(
                    1 for row in codegen if _direction_disagrees(row)
                ),
            }
        )
    return result


def _build_attribution_compare(
    *,
    pair_text: str,
    attribution_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in attribution_rows:
        opcode_delta = _opcode_delta_text(row)
        deltas = _parse_named_deltas(opcode_delta)
        removed = [
            _opcode_name(name) for name, value in deltas.items() if value < 0
        ]
        added = [_opcode_name(name) for name, value in deltas.items() if value > 0]
        rows.append(
            {
                "benchmark_set": _benchmark_set(row),
                "program": row.get("program", ""),
                "pair": pair_text,
                "opcode_delta": opcode_delta,
                "removed_opcodes": ";".join(removed),
                "added_opcodes": ";".join(added),
                "net_instruction_delta": _instruction_delta(row),
                "llc_text_delta_pct": row.get("llc_text_delta_pct", ""),
                "clang_text_delta_pct": row.get("clang_text_delta_pct", ""),
                "evidence_level": row.get("evidence_level", ""),
            }
        )
    return _sort_rows(rows)


def _build_graph_context(
    *,
    pair: frozenset[str],
    interaction_edge_rows: Sequence[Mapping[str, str]],
    reduced_component_rows: Sequence[Mapping[str, str]],
    search_space_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    target_edges = [dict(row) for row in interaction_edge_rows if _row_matches(row, pair)]
    target_components = [
        dict(row) for row in reduced_component_rows if _row_matches(row, pair)
    ]
    return {
        "interaction_edges": target_edges,
        "reduced_component_edges": target_components,
        "search_space": [dict(row) for row in search_space_rows],
    }


def _summarize(
    *,
    pair_text: str,
    program_summary: Sequence[Mapping[str, str]],
    full_rows: Sequence[Mapping[str, str]],
    prefix_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_compare: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "PairFamily": pair_text,
        "Programs": len(program_summary),
        "FullMatrixCertified": _label_count(full_rows, "certified_independent"),
        "FullMatrixNotCertified": _label_count(full_rows, "not_certified_independent"),
        "PrefixCertified": _label_count(prefix_rows, "certified_independent"),
        "PrefixNotCertified": _label_count(prefix_rows, "not_certified_independent"),
        "OneSwapCandidates": len(candidate_rows),
        "FinalIrDifferent": sum(
            1
            for row in object_rows
            if str(row.get("p5_same_as_anchor", "")).lower() == "false"
        ),
        "BothSmallerPrograms": len(
            {
                row.get("program", "")
                for row in codegen_rows
                if row.get("program", "") and _row_has_both_smaller(row)
            }
        ),
        "AttributionCases": len(attribution_compare),
        "SelectRelatedAttributionCases": sum(
            1
            for row in attribution_compare
            if "select" in row.get("removed_opcodes", "").split(";")
            or "select" in row.get("added_opcodes", "").split(";")
        ),
        "NewExperiments": False,
        "NewCertificates": False,
        "NewSearch": False,
    }


def _row_matches(row: Mapping[str, str], pair: frozenset[str]) -> bool:
    row_pair = _row_pair(row)
    return bool(row_pair) and row_pair == pair


def _row_pair(row: Mapping[str, str]) -> frozenset[str]:
    pair_text = str(row.get("pair", "")).strip()
    if pair_text and "," in pair_text:
        left, right = pair_text.split(",", 1)
        return _pair_set(left, right)
    left = row.get("pass_a") or row.get("pair_a")
    right = row.get("pass_b") or row.get("pair_b")
    if left and right:
        return _pair_set(left, right)
    return _pair_from_candidate_id(row.get("candidate_id", ""))


def _pair_set(left: object, right: object) -> frozenset[str]:
    return frozenset({str(left).strip(), str(right).strip()})


def _pair_from_candidate_id(candidate_id: str) -> frozenset[str]:
    parts = str(candidate_id).split("__")
    for index, part in enumerate(parts):
        if part.startswith("swap_") and index + 2 < len(parts):
            return _pair_set(parts[index + 1], parts[index + 2])
    return frozenset()


def _with_set(row: Mapping[str, str]) -> dict[str, str]:
    result = dict(row)
    result["benchmark_set"] = _benchmark_set(row)
    return result


def _benchmark_set(row: Mapping[str, str]) -> str:
    explicit = str(row.get("benchmark_set", "")).strip()
    if explicit:
        return explicit
    program = str(row.get("program", ""))
    if program.startswith("testsuite_stanford_"):
        return "Stanford-8"
    if program.startswith("testsuite_misc_"):
        return "Misc8"
    if program.startswith("testsuite_diverse_"):
        return "Diverse8"
    return "unknown"


def _first_benchmark_set(*groups: Sequence[Mapping[str, str]]) -> str:
    for group in groups:
        if group:
            return _benchmark_set(group[0])
    return "unknown"


def _benchmark_set_sort_key(name: str) -> tuple[int, str]:
    order = {"Stanford-8": 0, "Misc8": 1, "Diverse8": 2, "unknown": 99}
    return (order.get(name, 50), name)


def _program_sort_key(program: str) -> tuple[int, str]:
    return (_benchmark_set_sort_key(_benchmark_set({"program": program}))[0], program)


def _group_by_program(rows: Sequence[Mapping[str, str]]) -> dict[str, list[Mapping[str, str]]]:
    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("program", "")].append(row)
    return grouped


def _label_summary(rows: Sequence[Mapping[str, str]]) -> str:
    labels = {row.get("label", "") for row in rows if row.get("label", "")}
    if not labels:
        return "none"
    if len(labels) == 1:
        return next(iter(labels))
    if {"certified_independent", "not_certified_independent"}.issubset(labels):
        return "mixed_certified_not_certified"
    return ";".join(sorted(labels))


def _label_count(rows: Sequence[Mapping[str, str]], label: str) -> int:
    return sum(1 for row in rows if row.get("label", "") == label)


def _direction_summary(rows: Sequence[Mapping[str, str]], field: str) -> str:
    values = {row.get(field, "") for row in rows if row.get(field, "")}
    if not values:
        return ""
    if len(values) == 1:
        return next(iter(values))
    return "mixed"


def _direction_count(rows: Sequence[Mapping[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if row.get(field, "") == value)


def _direction_disagrees(row: Mapping[str, str]) -> bool:
    explicit = str(row.get("direction_agree", "")).lower()
    if explicit == "false":
        return True
    if explicit == "true":
        return False
    return row.get("llc_direction", "") != row.get("clang_direction", "")


def _row_has_both_smaller(row: Mapping[str, str]) -> bool:
    explicit = str(row.get("both_codegen_smaller", "")).lower()
    if explicit == "true":
        return True
    if row.get("llc_direction") == "smaller" and row.get("clang_direction") == "smaller":
        return True
    llc = _float(row.get("llc_text_delta_pct"))
    clang = _float(row.get("clang_text_delta_pct"))
    return llc is not None and clang is not None and llc < 0 and clang < 0


def _is_depth1_single_swap(row: Mapping[str, str]) -> bool:
    if str(row.get("source", "")) != "single_swap":
        return False
    depth = str(row.get("depth", "")).strip()
    return depth in {"", "1"}


def _opcode_delta_text(row: Mapping[str, str]) -> str:
    return (
        row.get("opcode_delta")
        or row.get("final_opcode_delta_nonzero")
        or row.get("FinalOpcodeDeltaNonZero")
        or ""
    )


def _parse_named_deltas(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for match in re.finditer(r"([A-Za-z0-9_]+)=(-?\d+(?:\.\d+)?)", text):
        values[match.group(1)] = float(match.group(2))
    return values


def _opcode_name(name: str) -> str:
    opcode = name
    if opcode.startswith("num_"):
        opcode = opcode[4:]
    if opcode.endswith("_delta"):
        opcode = opcode[:-6]
    return opcode


def _instruction_delta(row: Mapping[str, str]) -> str:
    for key in ("final_instruction_delta", "local_instruction_delta"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    for key in ("final_feature_delta", "local_feature_delta"):
        value = str(row.get(key, "")).strip()
        if not value:
            continue
        deltas = _parse_named_deltas(value)
        for name in ("num_instructions_delta", "num_instruction_delta"):
            if name in deltas:
                return _format_number(deltas[name])
    return ""


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _bool_text(value: bool) -> str:
    return "True" if value else "False"


def _sort_rows(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return sorted(
        [dict(row) for row in rows],
        key=lambda row: (
            _benchmark_set_sort_key(_benchmark_set(row)),
            row.get("program", ""),
            row.get("state_scope", ""),
            row.get("source_stage", ""),
        ),
    )


def _custom_sources(paths: Sequence[str] | None) -> list[tuple[str | None, str | Path]]:
    if not paths:
        return []
    return [(None, path) for path in paths]


def _read_many_labeled_csvs(
    sources: Sequence[tuple[str | None, str | Path]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for benchmark_set, path in sources:
        for row in _read_csv(path):
            if benchmark_set and not row.get("benchmark_set"):
                row["benchmark_set"] = benchmark_set
            rows.append(row)
    return rows


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


if __name__ == "__main__":
    raise SystemExit(main())
