"""Build a summary-only pass interaction graph from retained depth1 evidence."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Sequence

from .pass_registry_snapshot import load_expected_passes
from .passspec_schema import load_normalized_passspec


NODES_CSV_NAME = "pass_interaction_nodes.csv"
EDGES_CSV_NAME = "pass_interaction_edges.csv"
GRAPH_JSON_NAME = "pass_interaction_graph.json"
REPORT_NAME = "pass_interaction_graph_report.md"

NODE_FIELDS = [
    "pass_name",
    "in_pipeline",
    "in_passspec",
    "in_registry",
    "level",
    "tags",
    "status",
]

EDGE_FIELDS = [
    "pair_a",
    "pair_b",
    "edge_kind",
    "full_matrix_certified",
    "full_matrix_not_certified",
    "prefix_certified_events",
    "prefix_not_certified_events",
    "low_priority_events",
    "one_swap_candidates",
    "both_smaller_count",
    "attribution_cases",
    "evidence_level",
    "hard_prune_scope",
    "notes",
]

DEFAULT_FULL_MATRIX_CSVS = [
    "data/outputs/cert_summary.csv",
    "data/outputs/cert_summary_p8b_misc8_pre.csv",
    "data/outputs/cert_summary_p9_diverse8_pre.csv",
]
DEFAULT_PREFIX_ATTEMPT_CSVS = [
    "data/outputs/lazy_validation_p4_e83c409_first.csv",
    "data/outputs/lazy_validation_p8b_misc8/attempts.csv",
    "data/outputs/lazy_validation_p9_diverse8/attempts.csv",
]
DEFAULT_CANDIDATE_CSVS = [
    "data/outputs/bounded_local_p5_p6_final/candidates.csv",
    "data/outputs/bounded_local_p8b_misc8/candidates.csv",
    "data/outputs/bounded_local_p9_diverse8/candidates.csv",
]
DEFAULT_BOTH_SMALLER_CSVS = [
    "data/outputs/depth1_analysis_p8b_misc8/depth1_both_smaller_cases.csv",
    "data/outputs/depth1_analysis_p9_diverse8/depth1_both_smaller_cases.csv",
]
DEFAULT_ATTRIBUTION_CSVS = [
    "data/outputs/core_evidence_report/ecpor_attribution_summary.csv",
    "data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv",
]
DEFAULT_BENCHMARK_SETS = ["Stanford-8", "Misc8", "Diverse8"]


def build_nodes(
    *,
    registry_rows: Sequence[Mapping[str, str]],
    passspec: Mapping[str, Mapping[str, Any]],
    pipeline_passes: Sequence[str],
) -> list[dict[str, str]]:
    rows_by_name = {str(row.get("pass_name", "")): row for row in registry_rows}
    nodes: list[dict[str, str]] = []
    for pass_name in pipeline_passes:
        row = rows_by_name.get(pass_name, {})
        info = passspec.get(pass_name, {})
        tags = info.get("tags", [])
        nodes.append(
            {
                "pass_name": pass_name,
                "in_pipeline": _bool_text(row.get("in_pipeline", "True")),
                "in_passspec": _bool_text(row.get("in_passspec", str(pass_name in passspec))),
                "in_registry": _bool_text(row.get("in_registry", "")),
                "level": str(row.get("level_in_passspec") or info.get("level", "")),
                "tags": ";".join(str(tag) for tag in tags),
                "status": str(row.get("status", "")),
            }
        )
    return nodes


def build_edges(
    *,
    pipeline_passes: Sequence[str],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    both_smaller_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    pair_order = _pair_order(pipeline_passes)
    edges = {
        pair: _empty_edge(pair)
        for pair in combinations(pipeline_passes, 2)
    }

    for row in full_matrix_rows:
        pair = _canonical_pair(row.get("pair_a"), row.get("pair_b"), pair_order)
        if pair not in edges:
            continue
        label = str(row.get("label", ""))
        if label == "certified_independent":
            edges[pair]["full_matrix_certified"] += 1
        elif label == "not_certified_independent":
            edges[pair]["full_matrix_not_certified"] += 1

    for row in prefix_attempt_rows:
        pair = _canonical_pair(row.get("pass_a"), row.get("pass_b"), pair_order)
        if pair not in edges:
            continue
        label = str(row.get("label", ""))
        action = str(row.get("action", ""))
        if label == "certified_independent":
            edges[pair]["prefix_certified_events"] += 1
        elif label == "not_certified_independent":
            edges[pair]["prefix_not_certified_events"] += 1
        elif label == "skipped_low_priority" or action == "skipped_low_priority":
            edges[pair]["low_priority_events"] += 1

    for row in candidate_rows:
        if str(row.get("source", "")) != "single_swap":
            continue
        pair = _canonical_pair(row.get("pass_a"), row.get("pass_b"), pair_order)
        if pair in edges:
            edges[pair]["one_swap_candidates"] += 1

    both_smaller_cases: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in both_smaller_rows:
        _add_pair_case(
            row=row,
            pair_order=pair_order,
            cases=both_smaller_cases,
        )
    for row in attribution_rows:
        if _row_has_both_smaller(row):
            _add_pair_case(
                row=row,
                pair_order=pair_order,
                cases=both_smaller_cases,
            )
    for pair, cases in both_smaller_cases.items():
        if pair in edges:
            edges[pair]["both_smaller_count"] = len(cases)

    attribution_cases: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in attribution_rows:
        _add_pair_case(
            row=row,
            pair_order=pair_order,
            cases=attribution_cases,
        )
    for pair, cases in attribution_cases.items():
        if pair in edges:
            edges[pair]["attribution_cases"] = len(cases)

    result: list[dict[str, Any]] = []
    for pair in combinations(pipeline_passes, 2):
        edge = edges[pair]
        edge.update(_classify_edge(edge))
        result.append(edge)
    return result


def build_interaction_graph(
    *,
    pipeline_passes: Sequence[str],
    registry_rows: Sequence[Mapping[str, str]],
    passspec: Mapping[str, Mapping[str, Any]],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    both_smaller_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    benchmark_sets: Sequence[str],
    programs: int,
    pipeline_name: str = "mvp_function_scalar",
) -> dict[str, Any]:
    nodes = build_nodes(
        registry_rows=registry_rows,
        passspec=passspec,
        pipeline_passes=pipeline_passes,
    )
    edges = build_edges(
        pipeline_passes=pipeline_passes,
        full_matrix_rows=full_matrix_rows,
        prefix_attempt_rows=prefix_attempt_rows,
        candidate_rows=candidate_rows,
        both_smaller_rows=both_smaller_rows,
        attribution_rows=attribution_rows,
    )
    summary = summarize_graph(nodes, edges)
    return {
        "stage": "P12",
        "scope": {
            "pipeline": pipeline_name,
            "passes": list(pipeline_passes),
            "benchmark_sets": list(benchmark_sets),
            "programs": programs,
            "depth": 1,
            "summary_only": True,
            "graph_construction_only": True,
        },
        "nodes": [
            {
                "id": row["pass_name"],
                "level": row["level"],
                "tags": [tag for tag in row["tags"].split(";") if tag],
                "status": row["status"],
            }
            for row in nodes
        ],
        "edges": [
            {
                "source": row["pair_a"],
                "target": row["pair_b"],
                "kind": row["edge_kind"],
                "full_matrix_certified": row["full_matrix_certified"],
                "full_matrix_not_certified": row["full_matrix_not_certified"],
                "prefix_certified_events": row["prefix_certified_events"],
                "prefix_not_certified_events": row["prefix_not_certified_events"],
                "low_priority_events": row["low_priority_events"],
                "one_swap_candidates": row["one_swap_candidates"],
                "both_smaller_count": row["both_smaller_count"],
                "attribution_cases": row["attribution_cases"],
                "evidence_level": row["evidence_level"],
                "hard_prune_scope": row["hard_prune_scope"],
            }
            for row in edges
        ],
        "evidence_boundary": {
            "certified_independent_events_are_state_indexed": True,
            "certified_dominant_is_not_global_independence": True,
            "objective_sensitive_is_not_independence_proof": True,
            "objective_sensitive_is_not_hard_prune_evidence": True,
            "attribution_is_not_causal_proof": True,
            "static_filter_behavior_change": False,
            "passspec_behavior_change": False,
        },
        "summary": summary,
        "_csv_nodes": nodes,
        "_csv_edges": edges,
    }


def summarize_graph(
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    counts = defaultdict(int)
    observed_edges = 0
    for edge in edges:
        kind = str(edge.get("edge_kind", ""))
        counts[kind] += 1
        if kind != "insufficient_observed_evidence":
            observed_edges += 1
    return {
        "Nodes": len(nodes),
        "Edges": len(edges),
        "ObservedPairEdges": observed_edges,
        "CertifiedDominantPairs": counts["certified_dominant"],
        "OrderSensitivePairs": counts["order_sensitive"],
        "ObjectiveSensitivePairs": sum(
            1 for edge in edges if int(edge.get("both_smaller_count", 0)) > 0
        ),
        "AttributionHypothesisPairs": counts["attribution_hypothesis"],
        "InsufficientObservedEvidencePairs": counts["insufficient_observed_evidence"],
        "FullMatrixCertifiedEvents": sum(
            int(edge.get("full_matrix_certified", 0)) for edge in edges
        ),
        "FullMatrixNotCertifiedEvents": sum(
            int(edge.get("full_matrix_not_certified", 0)) for edge in edges
        ),
        "PrefixCertifiedEvents": sum(
            int(edge.get("prefix_certified_events", 0)) for edge in edges
        ),
        "PrefixNotCertifiedEvents": sum(
            int(edge.get("prefix_not_certified_events", 0)) for edge in edges
        ),
        "LowPriorityEvents": sum(
            int(edge.get("low_priority_events", 0)) for edge in edges
        ),
        "OneSwapCandidates": sum(
            int(edge.get("one_swap_candidates", 0)) for edge in edges
        ),
        "BothSmallerCases": sum(
            int(edge.get("both_smaller_count", 0)) for edge in edges
        ),
        "AttributionCases": sum(
            int(edge.get("attribution_cases", 0)) for edge in edges
        ),
    }


def render_report(graph: Mapping[str, Any]) -> str:
    summary = graph["summary"]
    edges = list(graph["_csv_edges"])
    order_sensitive = _edges_with_kind(edges, "order_sensitive")
    objective_sensitive = [
        edge for edge in edges if int(edge.get("both_smaller_count", 0)) > 0
    ]
    attribution = _edges_with_kind(edges, "attribution_hypothesis")

    lines = [
        "# Pass Interaction Graph v1",
        "",
        "P12 builds a summary-only graph from retained certificate, prefix-state,",
        "objective-layer, and attribution evidence. It does not run new LLVM",
        "experiments, does not create certificates, and does not start search.",
        "",
    ]
    for key in [
        "Nodes",
        "Edges",
        "ObservedPairEdges",
        "CertifiedDominantPairs",
        "OrderSensitivePairs",
        "ObjectiveSensitivePairs",
        "AttributionHypothesisPairs",
        "InsufficientObservedEvidencePairs",
        "FullMatrixCertifiedEvents",
        "FullMatrixNotCertifiedEvents",
        "PrefixCertifiedEvents",
        "PrefixNotCertifiedEvents",
        "LowPriorityEvents",
        "OneSwapCandidates",
        "BothSmallerCases",
        "AttributionCases",
    ]:
        lines.append(f"{key}: {summary[key]}")

    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "- `certified_dominant` means certified-dominant over observed state-indexed events, not global independence.",
            "- `order_sensitive` means at least one observed not-certified event exists.",
            "- objective_sensitive is not hard-prune evidence and is not independence proof.",
            "- attribution_hypothesis is observed attribution, not causal proof.",
            "",
            "## Order-Sensitive Pairs",
            "",
            "| pair | prefix_not_certified_events | full_matrix_not_certified | one_swap_candidates |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    _append_edge_rows(
        lines,
        order_sensitive,
        [
            "prefix_not_certified_events",
            "full_matrix_not_certified",
            "one_swap_candidates",
        ],
    )

    lines.extend(
        [
            "",
            "## Objective-Sensitive Pairs",
            "",
            "| pair | both_smaller_count | attribution_cases | notes |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    _append_edge_rows(
        lines,
        objective_sensitive,
        ["both_smaller_count", "attribution_cases", "notes"],
    )

    lines.extend(
        [
            "",
            "## Attribution Pairs",
            "",
            "| pair | both_smaller_count | attribution_cases | notes |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    _append_edge_rows(
        lines,
        attribution,
        ["both_smaller_count", "attribution_cases", "notes"],
    )

    lines.extend(
        [
            "",
            "## Next",
            "",
            "P12 only constructs the graph. P13 will estimate reduced components and search-space reduction from this graph.",
            "P13 will estimate reduced components before any new search is considered.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_interaction_graph_outputs(
    *,
    output_dir: str | Path,
    pipeline_passes: Sequence[str],
    registry_rows: Sequence[Mapping[str, str]],
    passspec: Mapping[str, Mapping[str, Any]],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    both_smaller_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    benchmark_sets: Sequence[str],
    programs: int,
    pipeline_name: str = "mvp_function_scalar",
) -> dict[str, Path]:
    graph = build_interaction_graph(
        pipeline_passes=pipeline_passes,
        registry_rows=registry_rows,
        passspec=passspec,
        full_matrix_rows=full_matrix_rows,
        prefix_attempt_rows=prefix_attempt_rows,
        candidate_rows=candidate_rows,
        both_smaller_rows=both_smaller_rows,
        attribution_rows=attribution_rows,
        benchmark_sets=benchmark_sets,
        programs=programs,
        pipeline_name=pipeline_name,
    )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    nodes_path = out / NODES_CSV_NAME
    edges_path = out / EDGES_CSV_NAME
    graph_path = out / GRAPH_JSON_NAME
    report_path = out / REPORT_NAME

    _write_csv(nodes_path, NODE_FIELDS, graph["_csv_nodes"])
    _write_csv(edges_path, EDGE_FIELDS, graph["_csv_edges"])
    json_graph = {key: value for key, value in graph.items() if not key.startswith("_")}
    graph_path.write_text(
        json.dumps(json_graph, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(graph), encoding="utf-8")
    return {
        "nodes": nodes_path,
        "edges": edges_path,
        "graph_json": graph_path,
        "report": report_path,
    }


def write_interaction_graph_outputs_from_paths(
    *,
    output_dir: str | Path,
    passspec_path: str | Path,
    pipeline_config_path: str | Path,
    passspec_registry_check_csv: str | Path,
    full_matrix_csvs: Sequence[str | Path],
    prefix_attempt_csvs: Sequence[str | Path],
    candidate_csvs: Sequence[str | Path],
    both_smaller_csvs: Sequence[str | Path],
    attribution_csvs: Sequence[str | Path],
    benchmark_sets: Sequence[str],
    programs: int,
) -> dict[str, Path]:
    passspec = load_normalized_passspec(passspec_path)
    pipeline_passes = load_expected_passes(pipeline_config_path)
    return write_interaction_graph_outputs(
        output_dir=output_dir,
        pipeline_passes=pipeline_passes,
        registry_rows=_read_csv(passspec_registry_check_csv),
        passspec=passspec,
        full_matrix_rows=_read_many_csvs(full_matrix_csvs),
        prefix_attempt_rows=_read_many_csvs(prefix_attempt_csvs),
        candidate_rows=_read_many_csvs(candidate_csvs),
        both_smaller_rows=_read_many_csvs(both_smaller_csvs),
        attribution_rows=_read_many_csvs(attribution_csvs),
        benchmark_sets=benchmark_sets,
        programs=programs,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P12 interaction graph v1.")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument(
        "--passspec-registry-check",
        default="data/outputs/passspec_registry_check/passspec_registry_check.csv",
    )
    parser.add_argument("--out-dir", default="data/outputs/interaction_graph_v1")
    parser.add_argument("--full-matrix-csv", action="append")
    parser.add_argument("--prefix-attempts-csv", action="append")
    parser.add_argument("--candidate-csv", action="append")
    parser.add_argument("--both-smaller-csv", action="append")
    parser.add_argument("--attribution-csv", action="append")
    parser.add_argument("--programs", type=int, default=24)
    parser.add_argument("--benchmark-set", action="append")
    args = parser.parse_args(argv)

    outputs = write_interaction_graph_outputs_from_paths(
        output_dir=args.out_dir,
        passspec_path=args.passspec,
        pipeline_config_path=args.pipeline,
        passspec_registry_check_csv=args.passspec_registry_check,
        full_matrix_csvs=args.full_matrix_csv or DEFAULT_FULL_MATRIX_CSVS,
        prefix_attempt_csvs=args.prefix_attempts_csv or DEFAULT_PREFIX_ATTEMPT_CSVS,
        candidate_csvs=args.candidate_csv or DEFAULT_CANDIDATE_CSVS,
        both_smaller_csvs=args.both_smaller_csv or DEFAULT_BOTH_SMALLER_CSVS,
        attribution_csvs=args.attribution_csv or DEFAULT_ATTRIBUTION_CSVS,
        benchmark_sets=args.benchmark_set or DEFAULT_BENCHMARK_SETS,
        programs=args.programs,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _classify_edge(edge: Mapping[str, Any]) -> dict[str, str]:
    if int(edge["attribution_cases"]) > 0:
        return {
            "edge_kind": "attribution_hypothesis",
            "evidence_level": "observed attribution; not causal proof",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
    if int(edge["both_smaller_count"]) > 0:
        return {
            "edge_kind": "objective_sensitive",
            "evidence_level": "objective-layer observation; not independence proof",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
    if int(edge["prefix_not_certified_events"]) > 0 or int(
        edge["full_matrix_not_certified"]
    ) > 0:
        return {
            "edge_kind": "order_sensitive",
            "evidence_level": "not-certified event observed",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
    if int(edge["prefix_certified_events"]) > 0 or int(
        edge["full_matrix_certified"]
    ) > 0:
        return {
            "edge_kind": "certified_dominant",
            "evidence_level": "state-indexed certified-dominant observed events",
            "hard_prune_scope": "observed_state_indexed_events",
            "notes": _edge_notes(edge),
        }
    return {
        "edge_kind": "insufficient_observed_evidence",
        "evidence_level": "insufficient observed evidence",
        "hard_prune_scope": "none",
        "notes": "no retained evidence for this pair",
    }


def _edge_notes(edge: Mapping[str, Any]) -> str:
    notes: list[str] = []
    if int(edge["full_matrix_certified"]) > 0 and int(edge["full_matrix_not_certified"]) > 0:
        notes.append("has both certified and not-certified full-matrix events")
    if int(edge["prefix_certified_events"]) > 0 and int(edge["prefix_not_certified_events"]) > 0:
        notes.append("has both certified and not-certified prefix-state events")
    if int(edge["attribution_cases"]) > 0:
        notes.append("attribution is observed, not causal proof")
    if int(edge["both_smaller_count"]) > 0:
        notes.append("objective-sensitive is not hard-prune evidence")
    return "; ".join(notes) or "observed state-indexed evidence only"


def _empty_edge(pair: tuple[str, str]) -> dict[str, Any]:
    return {
        "pair_a": pair[0],
        "pair_b": pair[1],
        "edge_kind": "",
        "full_matrix_certified": 0,
        "full_matrix_not_certified": 0,
        "prefix_certified_events": 0,
        "prefix_not_certified_events": 0,
        "low_priority_events": 0,
        "one_swap_candidates": 0,
        "both_smaller_count": 0,
        "attribution_cases": 0,
        "evidence_level": "",
        "hard_prune_scope": "",
        "notes": "",
    }


def _canonical_pair(
    pass_a: object,
    pass_b: object,
    pair_order: Mapping[str, int],
) -> tuple[str, str]:
    a = str(pass_a or "").strip()
    b = str(pass_b or "").strip()
    if not a or not b:
        return ("", "")
    return tuple(sorted((a, b), key=lambda name: (pair_order.get(name, 10_000), name)))  # type: ignore[return-value]


def _pair_order(pipeline_passes: Sequence[str]) -> dict[str, int]:
    return {pass_name: index for index, pass_name in enumerate(pipeline_passes)}


def _pair_from_row(row: Mapping[str, str], pair_order: Mapping[str, int]) -> tuple[str, str]:
    pair_text = str(row.get("pair", "")).strip()
    if pair_text and "," in pair_text:
        left, right = pair_text.split(",", 1)
        return _canonical_pair(left, right, pair_order)
    return _canonical_pair(row.get("pass_a") or row.get("pair_a"), row.get("pass_b") or row.get("pair_b"), pair_order)


def _add_pair_case(
    *,
    row: Mapping[str, str],
    pair_order: Mapping[str, int],
    cases: dict[tuple[str, str], set[str]],
) -> None:
    pair = _pair_from_row(row, pair_order)
    if not pair[0] or not pair[1]:
        return
    program = str(row.get("program", ""))
    case_id = f"{program}|{pair[0]},{pair[1]}"
    cases[pair].add(case_id)


def _row_has_both_smaller(row: Mapping[str, str]) -> bool:
    explicit = str(row.get("both_codegen_smaller", "")).lower()
    if explicit == "true":
        return True
    llc = _parse_float(row.get("llc_text_delta_pct"))
    clang = _parse_float(row.get("clang_text_delta_pct"))
    return llc is not None and clang is not None and llc < 0 and clang < 0


def _parse_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_many_csvs(paths: Sequence[str | Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.extend(_read_csv(path))
    return rows


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


def _append_edge_rows(
    lines: list[str],
    edges: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> None:
    if not edges:
        lines.append("| none | 0 | 0 |  |")
        return
    for edge in edges:
        values = [str(edge.get(field, "")) for field in fields]
        lines.append(f"| `{edge['pair_a']},{edge['pair_b']}` | " + " | ".join(values) + " |")


def _edges_with_kind(
    edges: Sequence[Mapping[str, Any]],
    kind: str,
) -> list[Mapping[str, Any]]:
    return [edge for edge in edges if edge.get("edge_kind") == kind]


def _bool_text(value: object) -> str:
    text = str(value)
    if text in {"True", "False"}:
        return text
    if text.lower() in {"true", "1", "yes"}:
        return "True"
    if text.lower() in {"false", "0", "no"}:
        return "False"
    return text


if __name__ == "__main__":
    raise SystemExit(main())
