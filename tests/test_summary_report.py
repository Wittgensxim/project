import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class SummaryReportTests(unittest.TestCase):
    def test_build_summary_report_outputs_counts_rates_and_averages(self):
        from ecpor.summary_report import build_summary_report

        report = build_summary_report(
            [
                {
                    "program": "p1",
                    "pair_a": "instcombine",
                    "pair_b": "dce",
                    "label": "certified_independent",
                    "hard_equal": "True",
                    "failure_kind_ab": "",
                    "failure_kind_ba": "",
                    "elapsed_ab_ms": "10.0",
                    "elapsed_ba_ms": "14.0",
                    "reproduced": "True",
                    "feature_delta": '{"num_instructions":0,"has_branch":""}',
                },
                {
                    "program": "p2",
                    "pair_a": "instcombine",
                    "pair_b": "dce",
                    "label": "not_certified_independent",
                    "hard_equal": "False",
                    "failure_kind_ab": "",
                    "failure_kind_ba": "",
                    "elapsed_ab_ms": "20.0",
                    "elapsed_ba_ms": "26.0",
                    "reproduced": "True",
                    "feature_delta": '{"num_instructions":1,"has_branch":""}',
                },
                {
                    "program": "p2",
                    "pair_a": "sroa",
                    "pair_b": "early-cse",
                    "label": "run_failed",
                    "hard_equal": "False",
                    "failure_kind_ab": "opt_failed",
                    "failure_kind_ba": "",
                    "elapsed_ab_ms": "30.0",
                    "elapsed_ba_ms": "36.0",
                    "reproduced": "False",
                    "feature_delta": "",
                },
            ]
        )

        self.assertIn("Total certificates: 3", report)
        self.assertIn("Reproduced: 2 / 3 = 66.67%", report)
        self.assertIn("HardFalseIndependent: 0", report)
        self.assertIn("CertifiedFeatureMismatchCount: 0", report)
        self.assertIn("Feature delta is soft evidence only.", report)
        self.assertIn("Delta convention: feature_delta = features_ba - features_ab", report)
        self.assertIn("certified_independent: 1", report)
        self.assertIn("not_certified_independent: 1", report)
        self.assertIn("run_failed: 1", report)
        self.assertIn("Certificates with any failure: 1 / 3", report)
        self.assertIn("Failure directions:", report)
        self.assertIn("total_directions: 6", report)
        self.assertIn("no_failure: 5 / 6", report)
        self.assertIn("opt_failed: 1", report)
        self.assertNotIn("none: 0", report)
        self.assertIn("Average elapsed_ab_ms: 20.000", report)
        self.assertIn("Average elapsed_ba_ms: 25.333", report)
        self.assertIn("instcombine,dce: 1/2 certified", report)
        self.assertIn("p1: 1/1 certified", report)

    def test_build_summary_report_counts_certified_feature_mismatches(self):
        from ecpor.summary_report import build_summary_report

        report = build_summary_report(
            [
                {
                    "program": "p1",
                    "pair_a": "instcombine",
                    "pair_b": "dce",
                    "label": "certified_independent",
                    "hard_equal": "True",
                    "failure_kind_ab": "",
                    "failure_kind_ba": "",
                    "elapsed_ab_ms": "1.0",
                    "elapsed_ba_ms": "1.0",
                    "reproduced": "True",
                    "feature_delta": '{"num_instructions":1,"has_branch":""}',
                }
            ]
        )

        self.assertIn("CertifiedFeatureMismatchCount: 1", report)


if __name__ == "__main__":
    unittest.main()
