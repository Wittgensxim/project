import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassSpecTrustReportTests(unittest.TestCase):
    def test_report_explains_empirical_repairs_legacy_limits_and_behavior_boundary(self):
        from ecpor.passspec_trust_report import build_trust_report

        with tempfile.TemporaryDirectory() as tmp:
            passspec = Path(tmp) / "passspec.yaml"
            passspec.write_text(
                textwrap.dedent(
                    """
                    passes:
                      sroa:
                        level: function
                        may_produce:
                          - scalar_value
                          - dce_opportunity:
                              source: empirical_false_negative_repair
                              confidence: medium
                              created_in_stage: P8b-2
                              support:
                                - program: testsuite_misc_ffbench
                                  pair: sroa,adce
                                  observed_label: not_certified_independent
                              note: SROA can expose cleanup opportunities.
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            report = build_trust_report(passspec)

        self.assertIn("PassSpec is an auditable metadata layer", report)
        self.assertIn("never certify independence", report)
        self.assertIn("EmpiricalRepairHints: 1", report)
        self.assertIn("LegacyHintsWithoutExplicitProvenance: 1", report)
        self.assertIn("sroa.may_produce.dce_opportunity", report)
        self.assertIn("testsuite_misc_ffbench", report)
        self.assertIn("support cases explain why a hint was added", report)
        self.assertIn("Legacy hint limitations", report)
        self.assertIn("Behavioral compatibility", report)
        self.assertIn("static_filter_behavior_change = false", report)
        self.assertIn("PassSpec v3: registry snapshot", report)

    def test_main_writes_report(self):
        from ecpor.passspec_trust_report import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            output = root / "passspec_trust_report.md"
            passspec.write_text(
                "passes:\n  a:\n    may_produce:\n      - x\n",
                encoding="utf-8",
            )

            exit_code = main(["--passspec", str(passspec), "--out", str(output)])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertIn("TotalHints: 1", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
