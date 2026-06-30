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
                },
            ]
        )

        self.assertIn("Total certificates: 3", report)
        self.assertIn("Reproduced: 2 / 3 = 66.67%", report)
        self.assertIn("HardFalseIndependent: 0", report)
        self.assertIn("certified_independent: 1", report)
        self.assertIn("not_certified_independent: 1", report)
        self.assertIn("run_failed: 1", report)
        self.assertIn("opt_failed: 1", report)
        self.assertIn("Average elapsed_ab_ms: 20.000", report)
        self.assertIn("Average elapsed_ba_ms: 25.333", report)
        self.assertIn("instcombine,dce: 1/2 certified", report)
        self.assertIn("p1: 1/1 certified", report)


if __name__ == "__main__":
    unittest.main()
