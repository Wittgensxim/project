import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class BatchCertificateTests(unittest.TestCase):
    def test_run_certificate_matrix_writes_summary_and_reproduces(self):
        from ecpor.batch_certificates import SUMMARY_FIELDS, run_certificate_matrix

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            first = _write_state(tmp_path, "first")
            second = _write_state(tmp_path, "second")
            summary_csv = tmp_path / "cert_summary.csv"

            rows = run_certificate_matrix(
                programs=[("first", first), ("second", second)],
                pass_pairs=[
                    ("instcombine", "dce"),
                    ("simplifycfg", "instcombine"),
                ],
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                cert_dir=tmp_path / "certs",
                summary_csv=summary_csv,
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(len(rows), 4)
            self.assertTrue(summary_csv.exists())
            self.assertTrue(all(row["reproduced"] == "True" for row in rows))
            self.assertTrue(all(row["failure_kind_ab"] == "" for row in rows))
            self.assertTrue(all(row["failure_kind_ba"] == "" for row in rows))
            self.assertEqual(sorted((tmp_path / "certs").glob("*.json")).__len__(), 4)

            with summary_csv.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, SUMMARY_FIELDS)
                loaded = list(reader)

            self.assertEqual(len(loaded), 4)
            self.assertEqual(loaded[0]["label"], "certified_independent")


def _write_state(tmp_path: Path, name: str) -> Path:
    state = tmp_path / f"{name}.ll"
    state.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
    return state


def _write_fake_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_text("define void @f() {\\n  ret void\\n}\\n", encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
