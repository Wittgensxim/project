import csv
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class MvpSummaryTests(unittest.TestCase):
    def test_builds_two_benchmark_mvp_summary_without_new_experiments(self):
        from ecpor.mvp_summary import BenchmarkSetInputs, run_mvp_summary

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stanford = root / "stanford"
            misc = root / "misc"
            stanford.mkdir()
            misc.mkdir()
            _write_pair_summary(stanford / "cert_summary.csv", "stanford")
            _write_pair_summary(misc / "cert_summary.csv", "misc")
            _write_text(
                stanford / "static_report.md",
                "StaticFalseNegativeObserved: 0\nStaticCandidateRecall: 100.00%\n",
            )
            _write_text(
                misc / "static_report.md",
                "StaticFalseNegativeObserved: 0\nStaticCandidateRecall: 100.00%\n",
            )
            _write_text(
                stanford / "lazy_report.md",
                "attempted_adjacent_swaps: 3\ncertified_independent: 2\nnot_certified_independent: 1\nrun_failed: 0\n",
            )
            _write_text(
                misc / "lazy_report.md",
                "attempted_adjacent_swaps: 3\ncertified_independent: 2\nnot_certified_independent: 1\nrun_failed: 0\n",
            )
            _write_candidates(stanford / "candidates.csv", "stanford")
            _write_candidates(misc / "candidates.csv", "misc")
            _write_object_size(stanford / "object_size.csv", "stanford")
            _write_object_size(misc / "object_size.csv", "misc")
            _write_codegen_compare(stanford / "compare.csv", "stanford")
            _write_codegen_compare(misc / "compare.csv", "misc")
            _write_attribution(stanford / "attribution.csv", "stanford_case")
            _write_attribution(misc / "attribution.csv", "misc_case")

            result = run_mvp_summary(
                output_dir=root / "final_mvp_summary",
                manifest_path=root / "mvp_summary_manifest.json",
                benchmark_sets=[
                    BenchmarkSetInputs(
                        name="Stanford-8",
                        pair_summary_csv=stanford / "cert_summary.csv",
                        static_filter_report=stanford / "static_report.md",
                        lazy_validation_report=stanford / "lazy_report.md",
                        p5_candidates_csv=stanford / "candidates.csv",
                        p6_object_size_csv=stanford / "object_size.csv",
                        codegen_compare_csv=stanford / "compare.csv",
                        attribution_summary_csv=stanford / "attribution.csv",
                    ),
                    BenchmarkSetInputs(
                        name="Misc8",
                        pair_summary_csv=misc / "cert_summary.csv",
                        static_filter_report=misc / "static_report.md",
                        lazy_validation_report=misc / "lazy_report.md",
                        p5_candidates_csv=misc / "candidates.csv",
                        p6_object_size_csv=misc / "object_size.csv",
                        codegen_compare_csv=misc / "compare.csv",
                        attribution_summary_csv=misc / "attribution.csv",
                    ),
                ],
                repo_root=root,
                result_generated_from_commit="summary123",
            )
            benchmark_rows = _read_csv(
                root / "final_mvp_summary" / "benchmark_set_summary.csv"
            )
            reduction_rows = _read_csv(
                root / "final_mvp_summary" / "reduction_summary.csv"
            )
            objective_rows = _read_csv(
                root / "final_mvp_summary" / "objective_summary.csv"
            )
            attribution_rows = _read_csv(
                root / "final_mvp_summary" / "attribution_case_summary.csv"
            )
            report = (root / "final_mvp_summary" / "mvp_summary_report.md").read_text(
                encoding="utf-8"
            )
            manifest = json.loads(
                (root / "mvp_summary_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(result.summary["BenchmarkSets"], 2)
        self.assertEqual(benchmark_rows[0]["benchmark_set"], "Stanford-8")
        self.assertEqual(benchmark_rows[0]["programs"], "2")
        self.assertEqual(benchmark_rows[0]["pair_matrix_certificates"], "4")
        self.assertEqual(benchmark_rows[0]["reproduced_certificates"], "4")
        self.assertEqual(benchmark_rows[0]["hard_false_independent"], "0")
        self.assertEqual(benchmark_rows[0]["static_false_negative_after_repair"], "0")
        self.assertEqual(benchmark_rows[0]["adjacent_attempts"], "3")
        self.assertEqual(benchmark_rows[0]["certified_events"], "2")
        self.assertEqual(benchmark_rows[0]["not_certified_events"], "1")
        self.assertEqual(benchmark_rows[0]["one_swap_candidates"], "1")
        self.assertEqual(benchmark_rows[0]["both_smaller_programs"], "1")
        self.assertEqual(reduction_rows[0]["certified_independent"], "2")
        self.assertEqual(objective_rows[0]["both_smaller_cases"], "1")
        self.assertEqual(attribution_rows[0]["benchmark_set"], "Stanford-8")
        self.assertIn("P9-1 MVP Summary", report)
        self.assertIn("NoNewExperiments: True", report)
        self.assertEqual(manifest["stage"], "P9-1")
        self.assertEqual(manifest["summary"]["BenchmarkSets"], 2)
        self.assertEqual(manifest["scope_limits"]["new_experiments"], False)


def _write_pair_summary(path: Path, prefix: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "pair_a", "pair_b", "label", "hard_equal", "reproduced"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": f"{prefix}_p1",
                    "pair_a": "a",
                    "pair_b": "b",
                    "label": "certified_independent",
                    "hard_equal": "True",
                    "reproduced": "True",
                },
                {
                    "program": f"{prefix}_p1",
                    "pair_a": "b",
                    "pair_b": "c",
                    "label": "certified_independent",
                    "hard_equal": "True",
                    "reproduced": "True",
                },
                {
                    "program": f"{prefix}_p2",
                    "pair_a": "a",
                    "pair_b": "c",
                    "label": "not_certified_independent",
                    "hard_equal": "False",
                    "reproduced": "True",
                },
                {
                    "program": f"{prefix}_p2",
                    "pair_a": "c",
                    "pair_b": "d",
                    "label": "not_certified_independent",
                    "hard_equal": "False",
                    "reproduced": "True",
                },
            ]
        )


def _write_candidates(path: Path, prefix: str) -> None:
    _write_text(
        path,
        "program,candidate_id,source\n"
        f"{prefix}_p1,{prefix}_p1__anchor,anchor\n"
        f"{prefix}_p1,{prefix}_p1__swap,single_swap\n",
    )


def _write_object_size(path: Path, prefix: str) -> None:
    _write_text(
        path,
        "program,candidate_id,source,text_delta,p5_same_as_anchor,compile_failure_kind,size_failure_kind\n"
        f"{prefix}_p1,{prefix}_p1__swap,single_swap,-4,False,,\n"
        f"{prefix}_p2,{prefix}_p2__swap,single_swap,0,False,,\n",
    )


def _write_codegen_compare(path: Path, prefix: str) -> None:
    _write_text(
        path,
        "program,candidate_id,source,llc_direction,clang_direction,direction_agree\n"
        f"{prefix}_p1,{prefix}_p1__swap,single_swap,smaller,smaller,True\n"
        f"{prefix}_p2,{prefix}_p2__swap,single_swap,equal,equal,True\n",
    )


def _write_attribution(path: Path, program: str) -> None:
    _write_text(
        path,
        "program,pair,opcode_delta,llc_text_delta_pct,clang_text_delta_pct,evidence_level\n"
        f"{program},\"a,b\",num_add_delta=-1,-1.000000,-0.500000,observed attribution\n",
    )


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
