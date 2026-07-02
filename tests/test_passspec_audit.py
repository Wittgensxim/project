import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassSpecAuditTests(unittest.TestCase):
    def test_audit_writes_hint_summary_report_and_counts_provenance(self):
        from ecpor.passspec_audit import audit_passspec

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            output_dir = root / "audit"
            passspec.write_text(
                textwrap.dedent(
                    """
                    passes:
                      sroa:
                        level: function
                        requires_any:
                          - has_alloca
                        may_consume:
                          - alloca
                        may_produce:
                          scalar_value:
                            source: manual_domain_knowledge
                            confidence: medium
                          dce_opportunity:
                            source: empirical_false_negative_repair
                            confidence: medium
                            created_in_stage: P8b-2
                            support:
                              - program: testsuite_misc_ffbench
                                pair: sroa,adce
                                observed_label: not_certified_independent
                        tags:
                          - scalar
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = audit_passspec(passspec, output_dir)
            rows = _read_csv(output_dir / "passspec_hint_summary.csv")
            report = (output_dir / "passspec_audit_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result["stats"]["TotalPasses"], 1)
        self.assertEqual(result["stats"]["TotalHints"], 4)
        self.assertEqual(result["stats"]["RequiresAnyHints"], 1)
        self.assertEqual(result["stats"]["MayConsumeHints"], 1)
        self.assertEqual(result["stats"]["MayProduceHints"], 2)
        self.assertEqual(result["stats"]["ManualHints"], 1)
        self.assertEqual(result["stats"]["EmpiricalRepairHints"], 1)
        self.assertEqual(result["stats"]["LegacyHintsWithoutExplicitProvenance"], 2)
        self.assertEqual(result["stats"]["UnknownConfidenceHints"], 2)
        self.assertEqual(result["stats"]["HintsWithSupportCases"], 1)
        self.assertEqual(len(rows), 4)
        self.assertIn("EmpiricalRepairHints: 1", report)
        self.assertIn("LegacyHintsWithoutExplicitProvenance: 2", report)
        self.assertIn("metadata/provenance audit only", report)

    def test_main_accepts_default_output_names(self):
        from ecpor.passspec_audit import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            output_dir = root / "audit"
            passspec.write_text(
                "passes:\n  a:\n    may_produce:\n      - x\n",
                encoding="utf-8",
            )

            exit_code = main(["--passspec", str(passspec), "--out-dir", str(output_dir)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "passspec_hint_summary.csv").exists())
            self.assertTrue((output_dir / "passspec_audit_report.md").exists())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
