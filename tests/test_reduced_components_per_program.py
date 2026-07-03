import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ReducedComponentsPerProgramTests(unittest.TestCase):
    def test_builds_three_graph_modes_with_separate_scope_warnings(self):
        from ecpor.reduced_components_per_program import (
            build_reduced_components_per_program,
        )

        analysis = build_reduced_components_per_program(
            pipeline_passes=["a", "b", "c", "d"],
            full_matrix_rows=[
                _full("SetA", "p1", "a", "b", "not_certified_independent"),
                _full("SetA", "p1", "c", "d", "not_certified_independent"),
                _full("SetA", "p1", "a", "c", "certified_independent"),
            ],
            prefix_attempt_rows=[
                _prefix("SetA", "p1", "b", "c", "not_certified_independent"),
            ],
            codegen_rows=[
                _codegen("SetA", "p1", "a", "b", "smaller", "smaller"),
            ],
            attribution_rows=[
                _attribution("SetA", "p1", "c,d", "-1.0", "-2.0"),
            ],
        )

        search_rows = {
            (row["program"], row["graph_mode"]): row
            for row in analysis["per_program_search_space"]
        }
        self.assertEqual(
            search_rows[("p1", "input_full_matrix")]["component_sizes"], "2;2"
        )
        self.assertEqual(search_rows[("p1", "input_full_matrix")]["edge_count"], 2)
        self.assertEqual(
            search_rows[("p1", "input_full_matrix")]["reduction_ratio"], "83.3333%"
        )
        self.assertEqual(
            search_rows[("p1", "input_full_matrix")]["scope_warning"],
            "input_full_matrix_only_not_prefix_safe",
        )
        self.assertEqual(
            search_rows[("p1", "prefix_adjacent")]["component_sizes"], "1;2;1"
        )
        self.assertEqual(
            search_rows[("p1", "prefix_adjacent")]["scope_warning"],
            "prefix_adjacent_only_not_full_pair_coverage",
        )
        self.assertEqual(
            search_rows[("p1", "objective_sensitive")]["component_sizes"], "2;2"
        )
        self.assertEqual(
            search_rows[("p1", "objective_sensitive")]["scope_warning"],
            "objective_layer_only_not_hard_prune",
        )

        component_rows = [
            row
            for row in analysis["per_program_components"]
            if row["program"] == "p1"
            and row["graph_mode"] == "objective_sensitive"
            and row["component_size"] == 2
        ]
        self.assertEqual(
            sorted(row["pass_name"] for row in component_rows),
            ["a", "b", "c", "d"],
        )

    def test_benchmark_summary_computes_program_local_reduction_statistics(self):
        from ecpor.reduced_components_per_program import (
            build_reduced_components_per_program,
        )

        analysis = build_reduced_components_per_program(
            pipeline_passes=["a", "b", "c", "d"],
            full_matrix_rows=[
                _full("SetA", "p1", "a", "b", "not_certified_independent"),
                _full("SetA", "p1", "c", "d", "not_certified_independent"),
                _full("SetA", "p2", "a", "b", "not_certified_independent"),
                _full("SetA", "p2", "b", "c", "not_certified_independent"),
                _full("SetA", "p2", "c", "d", "not_certified_independent"),
            ],
            prefix_attempt_rows=[],
            codegen_rows=[],
            attribution_rows=[],
        )

        summary = {
            (row["benchmark_set"], row["graph_mode"]): row
            for row in analysis["per_benchmark_summary"]
        }
        row = summary[("SetA", "input_full_matrix")]
        self.assertEqual(row["programs"], 2)
        self.assertEqual(row["median_reduction_ratio"], "41.6667%")
        self.assertEqual(row["mean_reduction_ratio"], "41.6667%")
        self.assertEqual(row["programs_with_single_component_8"], 1)
        self.assertEqual(row["programs_with_multiple_components"], 1)
        self.assertEqual(row["median_component_count"], "1.5000")
        self.assertEqual(row["max_component_size_median"], "3.0000")

    def test_writes_outputs_and_report_scope(self):
        from ecpor.reduced_components_per_program import (
            COMPONENTS_CSV_NAME,
            REPORT_NAME,
            SEARCH_SPACE_CSV_NAME,
            SUMMARY_CSV_NAME,
            write_reduced_components_per_program_outputs,
        )

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            paths = write_reduced_components_per_program_outputs(
                output_dir=out,
                pipeline_passes=["a", "b"],
                full_matrix_rows=[
                    _full("SetA", "p", "a", "b", "not_certified_independent")
                ],
                prefix_attempt_rows=[],
                codegen_rows=[],
                attribution_rows=[],
            )
            self.assertEqual(paths["components"], out / COMPONENTS_CSV_NAME)
            self.assertEqual(paths["search_space"], out / SEARCH_SPACE_CSV_NAME)
            self.assertEqual(paths["summary"], out / SUMMARY_CSV_NAME)
            self.assertEqual(paths["report"], out / REPORT_NAME)

            search_rows = _read_csv(out / SEARCH_SPACE_CSV_NAME)
            self.assertEqual(len(search_rows), 3)
            report = (out / REPORT_NAME).read_text(encoding="utf-8")

        self.assertIn("Programs: 1", report)
        self.assertIn("corpus-union graph", report)
        self.assertIn("program-local graph", report)
        self.assertIn("NewExperiments: False", report)
        self.assertIn("NewCertificates: False", report)
        self.assertIn("NewSearch: False", report)


def _full(
    benchmark_set: str,
    program: str,
    pair_a: str,
    pair_b: str,
    label: str,
) -> dict[str, str]:
    return {
        "benchmark_set": benchmark_set,
        "program": program,
        "pair_a": pair_a,
        "pair_b": pair_b,
        "label": label,
    }


def _prefix(
    benchmark_set: str,
    program: str,
    pass_a: str,
    pass_b: str,
    label: str,
) -> dict[str, str]:
    return {
        "benchmark_set": benchmark_set,
        "program": program,
        "pass_a": pass_a,
        "pass_b": pass_b,
        "label": label,
    }


def _codegen(
    benchmark_set: str,
    program: str,
    pass_a: str,
    pass_b: str,
    llc_direction: str,
    clang_direction: str,
) -> dict[str, str]:
    return {
        "benchmark_set": benchmark_set,
        "program": program,
        "source": "single_swap",
        "depth": "1",
        "pass_a": pass_a,
        "pass_b": pass_b,
        "llc_direction": llc_direction,
        "clang_direction": clang_direction,
    }


def _attribution(
    benchmark_set: str,
    program: str,
    pair: str,
    llc_delta: str,
    clang_delta: str,
) -> dict[str, str]:
    return {
        "benchmark_set": benchmark_set,
        "program": program,
        "pair": pair,
        "llc_text_delta_pct": llc_delta,
        "clang_text_delta_pct": clang_delta,
        "evidence_level": "observed attribution",
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
