"""Build reduced component summaries from the P12 interaction graph."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .pass_registry_snapshot import load_expected_passes


COMPONENT_NODES_CSV_NAME = "reduced_component_nodes.csv"
COMPONENT_EDGES_CSV_NAME = "reduced_component_edges.csv"
COMPONENTS_JSON_NAME = "reduced_components.json"
SEARCH_SPACE_CSV_NAME = "search_space_estimate.csv"
REPORT_NAME = "reduced_components_report.md"

GRAPH_MODES = ("conservative", "objective_sensitive")

COMPONENT_NODE_FIELDS = [
    "graph_mode",
    "component_id",
    "pass_name",
    "component_size",
    "component_kind",
]
COMPONENT_EDGE_FIELDS = [
    "graph_mode",
    "component_id",
    "pair_a",
    "pair_b",
    "edge_kind",
    "prefix_not_certified_events",
    "full_matrix_not_certified",
    "both_smaller_count",
    "attribution_cases",
    "evidence_level",
]
SEARCH_SPACE_FIELDS = [
    "graph_mode",
    "pass_count",
    "original_factorial",
    "component_sizes",
    "within_component_factorial_product",
    "reduction_ratio",
    "interpretation",
]


def build_reduced_components(
    *,
    nodes: Sequence[Mapping[str, str]],
    edges: Sequence[Mapping[str, str]],
    pipeline_passes: Sequence[str],
) -> dict[str, Any]:
    pass_names = list(pipeline_passes) or [str(row["pass_name"]) for row in nodes]
    components: list[dict[str, Any]] = []
    component_nodes: list[dict[str, Any]] = []
    component_edges: list[dict[str, Any]] = []

    for mode in GRAPH_MODES:
        selected_edges = [
            edge for edge in edges if _edge_selected_for_mode(edge, mode)
        ]
        mode_components = _connected_components(
            pass_names=pass_names,
            edges=selected_edges,
            mode=mode,
        )
        components.extend(mode_components)
        by_pass = {
            pass_name: component["component_id"]
            for component in mode_components
            for pass_name in component["passes"]
        }
        by_component = {
            component["component_id"]: component for component in mode_components
        }
        for component in mode_components:
            for pass_name in component["passes"]:
                component_nodes.append(
                    {
                        "graph_mode": mode,
                        "component_id": component["component_id"],
                        "pass_name": pass_name,
                        "component_size": component["component_size"],
                        "component_kind": component["component_kind"],
                    }
                )
        for edge in selected_edges:
            left = str(edge.get("pair_a", ""))
            right = str(edge.get("pair_b", ""))
            component_id = by_pass.get(left)
            if not component_id or by_pass.get(right) != component_id:
                continue
            component = by_component[component_id]
            component_edges.append(
                {
                    "graph_mode": mode,
                    "component_id": component_id,
                    "pair_a": left,
                    "pair_b": right,
                    "edge_kind": edge.get("edge_kind", ""),
                    "prefix_not_certified_events": edge.get(
                        "prefix_not_certified_events", "0"
                    ),
                    "full_matrix_not_certified": edge.get(
                        "full_matrix_not_certified", "0"
                    ),
                    "both_smaller_count": edge.get("both_smaller_count", "0"),
                    "attribution_cases": edge.get("attribution_cases", "0"),
                    "evidence_level": edge.get("evidence_level", ""),
                    "component_kind": component["component_kind"],
                }
            )

    search_space = _build_search_space(components, pass_count=len(pass_names))
    return {
        "stage": "P13",
        "scope": {
            "input_stage": "P12",
            "graph_analysis_only": True,
            "summary_only": True,
            "new_experiments": False,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "passspec_behavior_change": False,
            "static_filter_behavior_change": False,
        },
        "nodes": [dict(row) for row in nodes],
        "components": components,
        "component_nodes": component_nodes,
        "component_edges": component_edges,
        "search_space": search_space,
        "summary": _summarize(components, search_space),
        "evidence_boundary": {
            "certified_dominant_is_not_global_independence": True,
            "conservative_graph_keeps_non_certified_dominant_edges": True,
            "objective_sensitive_graph_is_not_hard_prune_proof": True,
            "search_space_estimate_is_coarse_upper_bound": True,
        },
    }


def render_report(graph: Mapping[str, Any]) -> str:
    summary = graph["summary"]
    search_space = {row["graph_mode"]: row for row in graph["search_space"]}
    conservative_components = [
        component
        for component in graph["components"]
        if component["graph_mode"] == "conservative"
    ]
    objective_components = [
        component
        for component in graph["components"]
        if component["graph_mode"] == "objective_sensitive"
    ]

    lines = [
        "# P13 Reduced Components v1",
        "",
        "P13 只分析 P12 interaction graph，不新增实验、不新增 certificate、不启动 search。",
        "8! is a coarse upper-bound for pass-type permutations in the MVP scalar pipeline.",
        "The objective-sensitive graph is not a hard-prune proof; it only marks observed objective/attribution hotspots.",
        "",
        f"OriginalPermutations: {summary['OriginalPermutations']}",
        f"ConservativeGraphComponents: {summary['ConservativeGraphComponents']}",
        f"ObjectiveSensitiveGraphComponents: {summary['ObjectiveSensitiveGraphComponents']}",
        f"ConservativeWithinComponentPermutations: {summary['ConservativeWithinComponentPermutations']}",
        f"ObjectiveWithinComponentPermutations: {summary['ObjectiveWithinComponentPermutations']}",
        f"ConservativeReductionRatio: {summary['ConservativeReductionRatio']}",
        f"ObjectiveReductionRatio: {summary['ObjectiveReductionRatio']}",
        "",
        "## 图模式",
        "",
        "- conservative graph 保留 `order_sensitive`、`objective_sensitive`、`attribution_hypothesis` 和 `insufficient_observed_evidence` 边。",
        "- objective-sensitive graph 只保留 observed objective / attribution evidence，用于定位目标层热点。",
        "- `certified_dominant` 不是 global independence，只能作为 observed-state scope 下的可折叠倾向。",
        "",
        "## Conservative Components",
        "",
        "| component | size | passes | kind |",
        "| --- | ---: | --- | --- |",
    ]
    for component in conservative_components:
        lines.append(_component_line(component))
    lines.extend(
        [
            "",
            "## Objective-Sensitive Components",
            "",
            "| component | size | passes | kind |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for component in objective_components:
        lines.append(_component_line(component))

    lines.extend(
        [
            "",
            "## Search-Space Estimate",
            "",
            "| graph_mode | component_sizes | within_component_factorial_product | reduction_ratio |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for mode in GRAPH_MODES:
        row = search_space[mode]
        lines.append(
            "| {graph_mode} | {component_sizes} | {within_component_factorial_product} | {reduction_ratio} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "P13 不给出新的 pipeline，也不运行 search。P14 是否做 targeted pair-family analysis 或 minimal reduced search，取决于 conservative graph 是否真的分裂成多个小 component，以及 objective-sensitive graph 是否继续集中在 `instcombine,simplifycfg`。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_reduced_components_outputs(
    *,
    output_dir: str | Path,
    nodes: Sequence[Mapping[str, str]],
    edges: Sequence[Mapping[str, str]],
    pipeline_passes: Sequence[str],
) -> dict[str, Path]:
    graph = build_reduced_components(
        nodes=nodes,
        edges=edges,
        pipeline_passes=pipeline_passes,
    )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    component_nodes_path = out / COMPONENT_NODES_CSV_NAME
    component_edges_path = out / COMPONENT_EDGES_CSV_NAME
    search_space_path = out / SEARCH_SPACE_CSV_NAME
    components_json_path = out / COMPONENTS_JSON_NAME
    report_path = out / REPORT_NAME

    _write_csv(component_nodes_path, COMPONENT_NODE_FIELDS, graph["component_nodes"])
    _write_csv(component_edges_path, COMPONENT_EDGE_FIELDS, graph["component_edges"])
    _write_csv(search_space_path, SEARCH_SPACE_FIELDS, graph["search_space"])
    components_json_path.write_text(
        json.dumps(
            {
                key: value
                for key, value in graph.items()
                if key not in {"component_nodes"}
            },
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(graph), encoding="utf-8")
    return {
        "component_nodes": component_nodes_path,
        "component_edges": component_edges_path,
        "search_space": search_space_path,
        "components_json": components_json_path,
        "report": report_path,
    }


def write_reduced_components_outputs_from_paths(
    *,
    output_dir: str | Path,
    nodes_csv: str | Path,
    edges_csv: str | Path,
    pipeline_config_path: str | Path,
) -> dict[str, Path]:
    return write_reduced_components_outputs(
        output_dir=output_dir,
        nodes=_read_csv(nodes_csv),
        edges=_read_csv(edges_csv),
        pipeline_passes=load_expected_passes(pipeline_config_path),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P13 reduced components v1.")
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument(
        "--nodes",
        default="data/outputs/interaction_graph_v1/pass_interaction_nodes.csv",
    )
    parser.add_argument(
        "--edges",
        default="data/outputs/interaction_graph_v1/pass_interaction_edges.csv",
    )
    parser.add_argument("--out-dir", default="data/outputs/reduced_components_v1")
    args = parser.parse_args(argv)
    outputs = write_reduced_components_outputs_from_paths(
        output_dir=args.out_dir,
        nodes_csv=args.nodes,
        edges_csv=args.edges,
        pipeline_config_path=args.pipeline,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _connected_components(
    *,
    pass_names: Sequence[str],
    edges: Sequence[Mapping[str, str]],
    mode: str,
) -> list[dict[str, Any]]:
    adjacency: dict[str, set[str]] = {name: set() for name in pass_names}
    for edge in edges:
        left = str(edge.get("pair_a", ""))
        right = str(edge.get("pair_b", ""))
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)

    visited: set[str] = set()
    components: list[dict[str, Any]] = []
    order = {pass_name: index for index, pass_name in enumerate(pass_names)}
    for pass_name in pass_names:
        if pass_name in visited:
            continue
        queue = deque([pass_name])
        visited.add(pass_name)
        members: list[str] = []
        while queue:
            current = queue.popleft()
            members.append(current)
            for next_pass in sorted(adjacency[current], key=lambda name: order[name]):
                if next_pass not in visited:
                    visited.add(next_pass)
                    queue.append(next_pass)
        members.sort(key=lambda name: order[name])
        component_size = len(members)
        component_id = f"{mode}_c{len(components) + 1}"
        components.append(
            {
                "graph_mode": mode,
                "component_id": component_id,
                "passes": members,
                "component_size": component_size,
                "component_kind": _component_kind(mode, component_size),
            }
        )
    return components


def _edge_selected_for_mode(edge: Mapping[str, str], mode: str) -> bool:
    edge_kind = str(edge.get("edge_kind", ""))
    if mode == "conservative":
        return edge_kind in {
            "order_sensitive",
            "objective_sensitive",
            "attribution_hypothesis",
            "insufficient_observed_evidence",
        }
    if mode == "objective_sensitive":
        return (
            edge_kind in {"objective_sensitive", "attribution_hypothesis"}
            or _int(edge.get("both_smaller_count")) > 0
            or _int(edge.get("attribution_cases")) > 0
        )
    raise ValueError(f"unsupported graph mode: {mode}")


def _component_kind(mode: str, component_size: int) -> str:
    if component_size == 1:
        return "singleton"
    if mode == "objective_sensitive":
        return "objective_sensitive_component"
    return "order_sensitive_component"


def _build_search_space(
    components: Sequence[Mapping[str, Any]],
    *,
    pass_count: int,
) -> list[dict[str, Any]]:
    original = math.factorial(pass_count)
    rows: list[dict[str, Any]] = []
    for mode in GRAPH_MODES:
        mode_components = [
            component
            for component in components
            if component["graph_mode"] == mode
        ]
        sizes = [int(component["component_size"]) for component in mode_components]
        product = 1
        for size in sizes:
            product *= math.factorial(size)
        reduction = 0.0 if original == 0 else (1.0 - (product / original)) * 100.0
        rows.append(
            {
                "graph_mode": mode,
                "pass_count": pass_count,
                "original_factorial": original,
                "component_sizes": ";".join(str(size) for size in sizes),
                "within_component_factorial_product": product,
                "reduction_ratio": f"{reduction:.4f}%",
                "interpretation": "coarse upper-bound estimate; component order anchored to current pipeline",
            }
        )
    return rows


def _summarize(
    components: Sequence[Mapping[str, Any]],
    search_space: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    by_mode = {row["graph_mode"]: row for row in search_space}
    component_counts = defaultdict(int)
    for component in components:
        component_counts[component["graph_mode"]] += 1
    return {
        "OriginalPermutations": by_mode["conservative"]["original_factorial"],
        "ConservativeGraphComponents": component_counts["conservative"],
        "ObjectiveSensitiveGraphComponents": component_counts["objective_sensitive"],
        "ConservativeWithinComponentPermutations": by_mode["conservative"][
            "within_component_factorial_product"
        ],
        "ObjectiveWithinComponentPermutations": by_mode["objective_sensitive"][
            "within_component_factorial_product"
        ],
        "ConservativeReductionRatio": by_mode["conservative"]["reduction_ratio"],
        "ObjectiveReductionRatio": by_mode["objective_sensitive"]["reduction_ratio"],
    }


def _component_line(component: Mapping[str, Any]) -> str:
    return "| `{component_id}` | {component_size} | `{passes}` | {component_kind} |".format(
        component_id=component["component_id"],
        component_size=component["component_size"],
        passes=",".join(component["passes"]),
        component_kind=component["component_kind"],
    )


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
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


def _int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
