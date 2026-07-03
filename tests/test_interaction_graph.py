import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class InteractionGraphTests(unittest.TestCase):
    def test_builds_nodes_from_registry_rows_and_passspec_tags(self):
        from ecpor.interaction_graph import build_nodes

        rows = [
            {
                "pass_name": "a",
                "in_pipeline": "True",
                "in_passspec": "True",
                "in_registry": "True",
                "level_in_passspec": "function",
                "status": "ok",
            },
            {
                "pass_name": "b",
                "in_pipeline": "True",
                "in_passspec": "True",
                "in_registry": "True",
                "level_in_passspec": "function",
                "status": "ok",
            },
        ]
        nodes = build_nodes(
            registry_rows=rows,
            passspec={"a": {"tags": ["scalar"]}, "b": {"tags": ["cfg"]}},
            pipeline_passes=["a", "b"],
        )

        self.assertEqual([node["pass_name"] for node in nodes], ["a", "b"])
        self.assertEqual(nodes[0]["tags"], "scalar")
        self.assertEqual(nodes[1]["status"], "ok")

    def test_not_certified_pair_is_order_sensitive(self):
        from ecpor.interaction_graph import build_edges

        edges = build_edges(
            pipeline_passes=["a", "b"],
            full_matrix_rows=[
                {"pair_a": "a", "pair_b": "b", "label": "not_certified_independent"}
            ],
            prefix_attempt_rows=[],
            candidate_rows=[],
            both_smaller_rows=[],
            attribution_rows=[],
        )

        self.assertEqual(edges[0]["edge_kind"], "order_sensitive")
        self.assertEqual(edges[0]["full_matrix_not_certified"], 1)

    def test_both_smaller_pair_is_objective_sensitive(self):
        from ecpor.interaction_graph import build_edges

        edges = build_edges(
            pipeline_passes=["a", "b"],
            full_matrix_rows=[],
            prefix_attempt_rows=[],
            candidate_rows=[],
            both_smaller_rows=[{"pair": "a,b"}],
            attribution_rows=[],
        )

        self.assertEqual(edges[0]["edge_kind"], "objective_sensitive")
        self.assertEqual(edges[0]["both_smaller_count"], 1)
        self.assertEqual(edges[0]["hard_prune_scope"], "none")

    def test_attribution_pair_has_highest_priority(self):
        from ecpor.interaction_graph import build_edges

        edges = build_edges(
            pipeline_passes=["a", "b"],
            full_matrix_rows=[],
            prefix_attempt_rows=[
                {"pass_a": "a", "pass_b": "b", "label": "not_certified_independent"}
            ],
            candidate_rows=[],
            both_smaller_rows=[{"pair": "a,b"}],
            attribution_rows=[{"pair": "b,a"}],
        )

        self.assertEqual(edges[0]["edge_kind"], "attribution_hypothesis")
        self.assertEqual(edges[0]["attribution_cases"], 1)

    def test_certified_and_not_certified_is_not_pure_independent(self):
        from ecpor.interaction_graph import build_edges

        edges = build_edges(
            pipeline_passes=["a", "b"],
            full_matrix_rows=[
                {"pair_a": "a", "pair_b": "b", "label": "certified_independent"},
                {"pair_a": "a", "pair_b": "b", "label": "not_certified_independent"},
            ],
            prefix_attempt_rows=[],
            candidate_rows=[],
            both_smaller_rows=[],
            attribution_rows=[],
        )

        self.assertEqual(edges[0]["full_matrix_certified"], 1)
        self.assertEqual(edges[0]["full_matrix_not_certified"], 1)
        self.assertEqual(edges[0]["edge_kind"], "order_sensitive")

    def test_graph_json_has_evidence_boundary(self):
        from ecpor.interaction_graph import build_interaction_graph

        graph = build_interaction_graph(
            pipeline_passes=["a", "b"],
            registry_rows=[
                {
                    "pass_name": "a",
                    "in_pipeline": "True",
                    "in_passspec": "True",
                    "in_registry": "True",
                    "level_in_passspec": "function",
                    "status": "ok",
                },
                {
                    "pass_name": "b",
                    "in_pipeline": "True",
                    "in_passspec": "True",
                    "in_registry": "True",
                    "level_in_passspec": "function",
                    "status": "ok",
                },
            ],
            passspec={},
            full_matrix_rows=[],
            prefix_attempt_rows=[],
            candidate_rows=[],
            both_smaller_rows=[],
            attribution_rows=[],
            benchmark_sets=["Synthetic"],
            programs=1,
        )

        self.assertEqual(graph["stage"], "P12")
        self.assertTrue(
            graph["evidence_boundary"][
                "certified_independent_events_are_state_indexed"
            ]
        )
        self.assertTrue(
            graph["evidence_boundary"][
                "objective_sensitive_is_not_independence_proof"
            ]
        )
        self.assertTrue(graph["evidence_boundary"]["attribution_is_not_causal_proof"])

    def test_report_says_objective_sensitive_is_not_hard_prune(self):
        from ecpor.interaction_graph import build_interaction_graph, render_report

        graph = build_interaction_graph(
            pipeline_passes=["a", "b"],
            registry_rows=[
                {
                    "pass_name": "a",
                    "in_pipeline": "True",
                    "in_passspec": "True",
                    "in_registry": "True",
                    "level_in_passspec": "function",
                    "status": "ok",
                },
                {
                    "pass_name": "b",
                    "in_pipeline": "True",
                    "in_passspec": "True",
                    "in_registry": "True",
                    "level_in_passspec": "function",
                    "status": "ok",
                },
            ],
            passspec={},
            full_matrix_rows=[],
            prefix_attempt_rows=[],
            candidate_rows=[],
            both_smaller_rows=[{"pair": "a,b"}],
            attribution_rows=[],
            benchmark_sets=["Synthetic"],
            programs=1,
        )
        report = render_report(graph)

        self.assertIn("ObjectiveSensitivePairs: 1", report)
        self.assertIn("objective_sensitive is not hard-prune evidence", report)
        self.assertIn("P13 will estimate reduced components", report)

    def test_writes_interaction_graph_outputs(self):
        from ecpor.interaction_graph import write_interaction_graph_outputs

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            outputs = write_interaction_graph_outputs(
                output_dir=out_dir,
                pipeline_passes=["a", "b"],
                registry_rows=[
                    {
                        "pass_name": "a",
                        "in_pipeline": "True",
                        "in_passspec": "True",
                        "in_registry": "True",
                        "level_in_passspec": "function",
                        "status": "ok",
                    },
                    {
                        "pass_name": "b",
                        "in_pipeline": "True",
                        "in_passspec": "True",
                        "in_registry": "True",
                        "level_in_passspec": "function",
                        "status": "ok",
                    },
                ],
                passspec={},
                full_matrix_rows=[],
                prefix_attempt_rows=[],
                candidate_rows=[],
                both_smaller_rows=[],
                attribution_rows=[{"program": "p", "pair": "a,b"}],
                benchmark_sets=["Synthetic"],
                programs=1,
            )
            with outputs["edges"].open(newline="", encoding="utf-8") as handle:
                edge_rows = list(csv.DictReader(handle))
            graph = json.loads(outputs["graph_json"].read_text(encoding="utf-8"))
            self.assertTrue(outputs["report"].exists())

        self.assertEqual(edge_rows[0]["edge_kind"], "attribution_hypothesis")
        self.assertEqual(graph["summary"]["Nodes"], 2)


if __name__ == "__main__":
    unittest.main()
