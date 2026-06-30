import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class DiffReportTests(unittest.TestCase):
    def test_build_diff_report_outputs_only_not_certified_rows(self):
        from ecpor.diff_report import (
            build_not_certified_diff_report,
            build_not_certified_diff_summary,
        )

        rows = [
            _row(
                program="p1",
                pair_a="instcombine",
                pair_b="dce",
                label="certified_independent",
                features_ab='{"num_instructions":10,"num_load":1,"has_branch":false}',
                features_ba='{"num_instructions":10,"num_load":1,"has_branch":false}',
                feature_delta='{"num_instructions":0,"num_load":0,"has_branch":""}',
            ),
            _row(
                program="p2",
                pair_a="simplifycfg",
                pair_b="instcombine",
                label="not_certified_independent",
                features_ab='{"num_instructions":120,"num_branch":10,"num_load":4,"has_branch":true}',
                features_ba='{"num_instructions":119,"num_branch":9,"num_load":5,"has_branch":true}',
                feature_delta='{"num_instructions":-1,"num_branch":-1,"num_load":1,"has_branch":""}',
            ),
        ]

        report = build_not_certified_diff_report(rows)
        summary_rows = build_not_certified_diff_summary(rows)

        self.assertIn("Feature delta is soft evidence only.", report)
        self.assertIn("It is not used for hard pruning.", report)
        self.assertIn("Delta convention: feature_delta = features_ba - features_ab", report)
        self.assertIn("## p2 :: simplifycfg -> instcombine", report)
        self.assertNotIn("## p1 :: instcombine -> dce", report)
        self.assertIn("| num_instructions | 120 | 119 | -1 |", report)
        self.assertIn("| num_load | 4 | 5 | +1 |", report)
        self.assertNotIn("| has_branch |", report)

        self.assertEqual(len(summary_rows), 1)
        self.assertEqual(summary_rows[0]["program"], "p2")
        self.assertEqual(summary_rows[0]["pair_a"], "simplifycfg")
        self.assertEqual(summary_rows[0]["pair_b"], "instcombine")
        self.assertEqual(summary_rows[0]["nonzero_feature_delta"], "num_branch=-1;num_instructions=-1;num_load=+1")

    def test_main_writes_markdown_and_csv_outputs(self):
        from ecpor.diff_report import main

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_csv = tmp_path / "cert_summary.csv"
            output_md = tmp_path / "not_certified_diff_report.md"
            output_csv = tmp_path / "not_certified_diff_summary.csv"

            with summary_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(_row().keys()))
                writer.writeheader()
                writer.writerow(
                    _row(
                        label="not_certified_independent",
                        features_ab='{"num_instructions":2}',
                        features_ba='{"num_instructions":1}',
                        feature_delta='{"num_instructions":-1}',
                    )
                )

            exit_code = main(
                [
                    str(summary_csv),
                    "--out-md",
                    str(output_md),
                    "--out-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("## p :: a -> b", output_md.read_text(encoding="utf-8"))
            self.assertIn("num_instructions=-1", output_csv.read_text(encoding="utf-8"))


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "program": "p",
        "pair_a": "a",
        "pair_b": "b",
        "label": "certified_independent",
        "hash_ab": "hash-ab",
        "hash_ba": "hash-ba",
        "input_state_hash": "input-hash",
        "pipeline_ab": "function(a,b)",
        "pipeline_ba": "function(b,a)",
        "elapsed_ab_ms": "1.000",
        "elapsed_ba_ms": "2.000",
        "cert_id": "cert-1",
        "features_ab": "{}",
        "features_ba": "{}",
        "feature_delta": "{}",
    }
    row.update(overrides)
    return row


if __name__ == "__main__":
    unittest.main()
