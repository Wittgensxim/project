import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ReducedComponentsTests(unittest.TestCase):
    def test_builds_connected_components_for_both_graph_modes(self):
        from ecpor.reduced_components import build_reduced_components

        graph = build_reduced_components(
            nodes=_nodes(["a", "b", "c", "d"]),
            edges=[
                _edge("a", "b", "order_sensitive"),
                _edge("b", "c", "attribution_hypothesis", attribution_cases="1"),
                _edge("c", "d", "certified_dominant"),
            ],
            pipeline_passes=["a", "b", "c", "d"],
        )

        conservative = _components_by_mode(graph, "conservative")
        objective = _components_by_mode(graph, "objective_sensitive")

        self.assertEqual([component["passes"] for component in conservative], [["a", "b", "c"], ["d"]])
        self.assertEqual([component["passes"] for component in objective], [["a"], ["b", "c"], ["d"]])

    def test_certified_dominant_edge_is_not_conservative_component_edge(self):
        from ecpor.reduced_components import build_reduced_components

        graph = build_reduced_components(
            nodes=_nodes(["a", "b"]),
            edges=[_edge("a", "b", "certified_dominant")],
            pipeline_passes=["a", "b"],
        )

        conservative_edges = [
            row for row in graph["component_edges"] if row["graph_mode"] == "conservative"
        ]
        conservative_components = _components_by_mode(graph, "conservative")

        self.assertEqual(conservative_edges, [])
        self.assertEqual([component["passes"] for component in conservative_components], [["a"], ["b"]])

    def test_order_sensitive_edge_enters_conservative_component(self):
        from ecpor.reduced_components import build_reduced_components

        graph = build_reduced_components(
            nodes=_nodes(["a", "b"]),
            edges=[_edge("a", "b", "order_sensitive")],
            pipeline_passes=["a", "b"],
        )

        conservative = _components_by_mode(graph, "conservative")

        self.assertEqual(conservative[0]["passes"], ["a", "b"])
        self.assertEqual(conservative[0]["component_kind"], "order_sensitive_component")

    def test_objective_and_attribution_edges_enter_objective_graph(self):
        from ecpor.reduced_components import build_reduced_components

        graph = build_reduced_components(
            nodes=_nodes(["a", "b", "c"]),
            edges=[
                _edge("a", "b", "objective_sensitive", both_smaller_count="1"),
                _edge("b", "c", "attribution_hypothesis", attribution_cases="1"),
            ],
            pipeline_passes=["a", "b", "c"],
        )

        objective = _components_by_mode(graph, "objective_sensitive")

        self.assertEqual([component["passes"] for component in objective], [["a", "b", "c"]])
        self.assertEqual(objective[0]["component_kind"], "objective_sensitive_component")

    def test_factorial_search_space_estimate_uses_component_sizes(self):
        from ecpor.reduced_components import build_reduced_components

        graph = build_reduced_components(
            nodes=_nodes(["a", "b", "c", "d"]),
            edges=[
                _edge("a", "b", "order_sensitive"),
                _edge("b", "c", "order_sensitive"),
            ],
            pipeline_passes=["a", "b", "c", "d"],
        )
        conservative = _estimate_by_mode(graph, "conservative")

        self.assertEqual(conservative["original_factorial"], 24)
        self.assertEqual(conservative["component_sizes"], "3;1")
        self.assertEqual(conservative["within_component_factorial_product"], 6)
        self.assertEqual(conservative["reduction_ratio"], "75.0000%")

    def test_report_names_both_modes_and_boundaries(self):
        from ecpor.reduced_components import build_reduced_components, render_report

        graph = build_reduced_components(
            nodes=_nodes(["a", "b"]),
            edges=[_edge("a", "b", "attribution_hypothesis", attribution_cases="1")],
            pipeline_passes=["a", "b"],
        )
        report = render_report(graph)

        self.assertIn("ConservativeGraphComponents", report)
        self.assertIn("ObjectiveSensitiveGraphComponents", report)
        self.assertIn("objective-sensitive graph is not a hard-prune proof", report)
        self.assertIn("8! is a coarse upper-bound", report)

    def test_writes_reduced_component_outputs(self):
        from ecpor.reduced_components import write_reduced_components_outputs

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            outputs = write_reduced_components_outputs(
                output_dir=out_dir,
                nodes=_nodes(["a", "b"]),
                edges=[_edge("a", "b", "objective_sensitive", both_smaller_count="1")],
                pipeline_passes=["a", "b"],
            )
            with outputs["component_nodes"].open(newline="", encoding="utf-8") as handle:
                node_rows = list(csv.DictReader(handle))
            graph = json.loads(outputs["components_json"].read_text(encoding="utf-8"))

        self.assertEqual(node_rows[0]["graph_mode"], "conservative")
        self.assertEqual(graph["stage"], "P13")
        self.assertIn("search_space", graph)


def _nodes(names: list[str]) -> list[dict[str, str]]:
    return [
        {
            "pass_name": name,
            "in_pipeline": "True",
            "in_passspec": "True",
            "in_registry": "True",
            "level": "function",
            "tags": "",
            "status": "ok",
        }
        for name in names
    ]


def _edge(
    pair_a: str,
    pair_b: str,
    edge_kind: str,
    *,
    both_smaller_count: str = "0",
    attribution_cases: str = "0",
) -> dict[str, str]:
    return {
        "pair_a": pair_a,
        "pair_b": pair_b,
        "edge_kind": edge_kind,
        "full_matrix_certified": "0",
        "full_matrix_not_certified": "0",
        "prefix_certified_events": "0",
        "prefix_not_certified_events": "0",
        "low_priority_events": "0",
        "one_swap_candidates": "0",
        "both_smaller_count": both_smaller_count,
        "attribution_cases": attribution_cases,
        "evidence_level": "test evidence",
        "hard_prune_scope": "none",
        "notes": "",
    }


def _components_by_mode(graph: dict, mode: str) -> list[dict]:
    return [
        component
        for component in graph["components"]
        if component["graph_mode"] == mode
    ]


def _estimate_by_mode(graph: dict, mode: str) -> dict:
    for row in graph["search_space"]:
        if row["graph_mode"] == mode:
            return row
    raise AssertionError(f"missing search-space row for {mode}")


if __name__ == "__main__":
    unittest.main()
