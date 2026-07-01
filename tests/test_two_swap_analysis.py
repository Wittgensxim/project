import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class TwoSwapAnalysisTests(unittest.TestCase):
    def test_builds_program_pair_detail_cache_and_duplicate_tables(self):
        from ecpor.two_swap_analysis import run_two_swap_analysis

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_csv(
                root / "two_swap_seeds.csv",
                [
                    "program",
                    "candidate_id",
                    "source",
                    "seed_candidate_id",
                    "seed_pipeline",
                    "seed_text_delta_pct",
                    "seed_rank",
                    "seed_reason",
                    "text_delta_pct",
                ],
                [
                    ["p1", "p1_seed_smaller", "single_swap", "p1_seed_smaller", "b,a,c", "-5.000000", "1", "best_text_delta", "-5.000000"],
                    ["p1", "p1_seed_equal", "single_swap", "p1_seed_equal", "a,c,b", "0.000000", "2", "equal_text_representative", "0.000000"],
                    ["p2", "p2_seed_equal", "single_swap", "p2_seed_equal", "a,b,c", "0.000000", "1", "best_equal_text_delta", "0.000000"],
                ],
            )
            _write_csv(
                root / "p6_object_size.csv",
                [
                    "program",
                    "candidate_id",
                    "source",
                    "swap_index",
                    "pass_a",
                    "pass_b",
                    "text_delta_pct",
                ],
                [
                    ["p1", "p1_anchor", "anchor", "", "", "", "0.000000"],
                    ["p2", "p2_anchor", "anchor", "", "", "", "0.000000"],
                    ["p1", "p1_seed_smaller", "single_swap", "0", "a", "b", "-5.000000"],
                    ["p1", "p1_seed_equal", "single_swap", "1", "b", "c", "0.000000"],
                    ["p2", "p2_seed_equal", "single_swap", "0", "a", "b", "0.000000"],
                ],
            )
            _write_csv(
                root / "two_swap_attempts.csv",
                [
                    "program",
                    "seed_candidate_id",
                    "seed_pipeline",
                    "swap_index",
                    "prefix_passes",
                    "state_hash",
                    "pass_a",
                    "pass_b",
                    "static_decision",
                    "action",
                    "label",
                    "cache_hit",
                    "dynamic_test",
                    "cert_id",
                ],
                [
                    ["p1", "p1_seed_smaller", "b,a,c", "0", "", "state-anchor", "b", "a", "candidate", "dynamic_test", "not_certified_independent", "False", "True", "cert-anchor"],
                    ["p1", "p1_seed_smaller", "b,a,c", "1", "b", "state-ac", "a", "c", "candidate", "dynamic_test", "not_certified_independent", "False", "True", "cert-ac"],
                    ["p1", "p1_seed_equal", "a,c,b", "0", "", "state-ac", "c", "a", "candidate", "cache_hit", "certified_independent", "True", "False", "cert-ac"],
                    ["p2", "p2_seed_equal", "a,b,c", "0", "", "state-ab", "a", "b", "candidate", "dynamic_test", "not_certified_independent", "False", "True", "cert-ab"],
                    ["p2", "p2_seed_equal", "a,b,c", "1", "a", "state-bc", "b", "c", "low_priority", "skipped_low_priority", "skipped_low_priority", "False", "False", ""],
                ],
            )
            _write_csv(
                root / "two_swap_candidates.csv",
                [
                    "program",
                    "candidate_id",
                    "depth",
                    "parent_candidate_id",
                    "source",
                    "base_pipeline",
                    "candidate_pipeline",
                    "pipeline_sequence_hash",
                    "swap_index",
                    "pass_a",
                    "pass_b",
                    "prefix_state_hash",
                    "validation_label",
                    "cert_id",
                    "reason",
                    "swap_path",
                ],
                [
                    ["p1", "p1_anchor", "0", "", "anchor", "a,b,c", "a,b,c", "", "", "", "", "", "anchor", "", "anchor", ""],
                    ["p2", "p2_anchor", "0", "", "anchor", "a,b,c", "a,b,c", "", "", "", "", "", "anchor", "", "anchor", ""],
                    ["p1", "p1__depth2__p1_seed_smaller__swap_1__a__c", "2", "p1_seed_smaller", "two_swap", "a,b,c", "b,c,a", "", "1", "a", "c", "state-ac", "not_certified_independent", "cert-ac", "hard hash differs", "0;1"],
                    ["p2", "p2__depth2__p2_seed_equal__swap_0__a__b", "2", "p2_seed_equal", "two_swap", "a,b,c", "b,a,c", "", "0", "a", "b", "state-ab", "not_certified_independent", "cert-ab", "hard hash differs", "0;0"],
                ],
            )
            _write_csv(
                root / "two_swap_pipeline_runs.csv",
                ["program", "candidate_id", "pipeline", "exit_code", "failure_kind", "same_as_anchor"],
                [
                    ["p1", "p1_anchor", "function(a,b,c)", "0", "", "True"],
                    ["p2", "p2_anchor", "function(a,b,c)", "0", "", "True"],
                    ["p1", "p1__depth2__p1_seed_smaller__swap_1__a__c", "function(b,c,a)", "0", "", "False"],
                    ["p2", "p2__depth2__p2_seed_equal__swap_0__a__b", "function(b,a,c)", "0", "", "False"],
                ],
            )
            _write_csv(
                root / "two_swap_object_size.csv",
                ["program", "candidate_id", "source", "text_delta_pct"],
                [
                    ["p1", "p1_anchor", "anchor", "0.000000"],
                    ["p2", "p2_anchor", "anchor", "0.000000"],
                    ["p1", "p1__depth2__p1_seed_smaller__swap_1__a__c", "two_swap", "-6.000000"],
                    ["p2", "p2__depth2__p2_seed_equal__swap_0__a__b", "two_swap", "-2.000000"],
                ],
            )

            result = run_two_swap_analysis(
                seeds_csv=root / "two_swap_seeds.csv",
                attempts_csv=root / "two_swap_attempts.csv",
                candidates_csv=root / "two_swap_candidates.csv",
                pipeline_runs_csv=root / "two_swap_pipeline_runs.csv",
                object_size_csv=root / "two_swap_object_size.csv",
                p6_object_size_csv=root / "p6_object_size.csv",
                output_dir=root / "analysis",
            )
            program_rows = _read_csv(root / "analysis" / "p7b_program_summary.csv")
            pair_rows = _read_csv(root / "analysis" / "p7b_pair_summary.csv")
            detail_rows = _read_csv(root / "analysis" / "p7b_depth2_details.csv")
            cache_rows = _read_csv(root / "analysis" / "p7b_cache_audit.csv")
            duplicate_rows = _read_csv(root / "analysis" / "p7b_duplicate_audit.csv")
            report = (root / "analysis" / "p7b_analysis_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.summary["programs"], 2)
        self.assertEqual(result.summary["selected_seeds"], 3)
        self.assertEqual(result.summary["raw_depth2_candidates"], 3)
        self.assertEqual(result.summary["unique_depth2_candidates"], 2)
        self.assertEqual(result.summary["duplicate_sequences"], 1)
        self.assertEqual(result.summary["depth2_smaller_text"], 2)
        self.assertEqual(result.summary["depth2_improves_program_depth1_best_count"], 2)
        self.assertEqual(result.summary["first_run_cache_hits"], 1)

        p1 = next(row for row in program_rows if row["program"] == "p1")
        self.assertEqual(p1["selected_seeds"], "2")
        self.assertEqual(p1["duplicate_sequences"], "1")
        self.assertEqual(p1["depth2_improves_program_depth1_best"], "True")

        ac_pair = next(row for row in pair_rows if row["pass_a"] == "a" and row["pass_b"] == "c")
        self.assertEqual(ac_pair["attempts"], "2")
        self.assertEqual(ac_pair["certified_independent"], "1")
        self.assertEqual(ac_pair["not_certified_independent"], "1")
        self.assertEqual(ac_pair["depth2_smaller_text"], "1")

        p2_detail = next(row for row in detail_rows if row["program"] == "p2")
        self.assertEqual(p2_detail["parent_text_delta_pct"], "0.000000")
        self.assertEqual(p2_detail["depth2_text_delta_pct"], "-2.000000")
        self.assertEqual(p2_detail["delta_pct_vs_parent"], "-2.000000")
        self.assertEqual(p2_detail["depth2_improves_program_depth1_best"], "True")

        cache_hit = next(row for row in cache_rows if row["cache_hit"] == "True")
        self.assertEqual(cache_hit["matched_previous_seed_candidate_id"], "p1_seed_smaller")
        self.assertEqual(cache_hit["matched_previous_swap_index"], "1")

        self.assertEqual(len(duplicate_rows), 1)
        self.assertTrue(
            duplicate_rows[0]["duplicate_candidate_id"].endswith("__swap_0__b__a")
        )
        self.assertIn("DuplicateSequenceRate: 33.33%", report)
        self.assertIn("Depth2SmallerPrograms: 2", report)


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
