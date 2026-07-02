import json
import hashlib
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassRegistrySnapshotTests(unittest.TestCase):
    def test_parses_fake_print_passes_and_marks_expected_present(self):
        from ecpor.pass_registry_snapshot import build_registry_snapshot

        raw_output = textwrap.dedent(
            """
            Module passes:
              function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)
              sroa
              early-cse
              instcombine<max-iterations;no-use-loop-info>
              simplifycfg
              reassociate
              gvn
              dce
              adce
            """
        )

        snapshot = build_registry_snapshot(
            raw_output=raw_output,
            expected_passes=[
                "sroa",
                "early-cse",
                "instcombine",
                "simplifycfg",
                "reassociate",
                "gvn",
                "dce",
                "adce",
            ],
            opt_path="opt.exe",
            opt_sha256="opt-sha",
            llvm_version="test-llvm",
        )

        self.assertEqual(snapshot["llvm_version"], "test-llvm")
        self.assertEqual(snapshot["parse_confidence"], "raw_snapshot_with_presence_check")
        self.assertEqual(snapshot["missing_expected_passes"], [])
        self.assertEqual(snapshot["expected_pass_presence"]["sroa"], True)
        self.assertEqual(snapshot["expected_pass_presence"]["early-cse"], True)
        self.assertIn("instcombine", snapshot["all_pass_like_names"])

    def test_reports_missing_expected_pass(self):
        from ecpor.pass_registry_snapshot import build_registry_snapshot, render_report

        snapshot = build_registry_snapshot(
            raw_output="Passes:\n  sroa\n  dce\n",
            expected_passes=["sroa", "gvn", "dce"],
            opt_path="opt.exe",
            opt_sha256="opt-sha",
            llvm_version="test-llvm",
        )
        report = render_report(snapshot)

        self.assertEqual(snapshot["missing_expected_passes"], ["gvn"])
        self.assertIn("MissingExpectedPasses: 1", report)
        self.assertIn("`gvn`: missing", report)
        self.assertIn("snapshot only records pass availability", report)

    def test_writes_raw_snapshot_json_and_report(self):
        from ecpor.pass_registry_snapshot import write_registry_snapshot_outputs

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = write_registry_snapshot_outputs(
                raw_output="Passes:\n  sroa\n  dce\n",
                expected_passes=["sroa", "dce"],
                output_dir=root,
                opt_path="opt.exe",
                opt_sha256="opt-sha",
                llvm_version="test-llvm",
            )
            raw = root / "opt_print_passes_raw.txt"
            snapshot_path = root / "pass_registry_snapshot.json"
            report_path = root / "pass_registry_report.md"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            raw_sha256 = hashlib.sha256(raw.read_bytes()).hexdigest()
            report_text = report_path.read_text(encoding="utf-8")

            self.assertEqual(outputs["raw_output"], raw)
            self.assertTrue(raw.exists())
            self.assertTrue(snapshot_path.exists())
            self.assertTrue(report_path.exists())
            self.assertRegex(snapshot["raw_output_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(snapshot["raw_output_sha256"], raw_sha256)
            self.assertIn("LLVMVersion: test-llvm", report_text)

    def test_main_accepts_raw_input_for_deterministic_snapshot(self):
        from ecpor.pass_registry_snapshot import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline = root / "pipeline_scalar.yaml"
            raw_input = root / "raw.txt"
            out_dir = root / "out"
            pipeline.write_text(
                "passes:\n  - sroa\n  - early-cse\n",
                encoding="utf-8",
            )
            raw_input.write_text("Passes:\n  sroa\n  early-cse\n", encoding="utf-8")

            exit_code = main(
                [
                    "--opt",
                    str(root / "missing-opt.exe"),
                    "--pipeline",
                    str(pipeline),
                    "--out",
                    str(out_dir),
                    "--raw-input",
                    str(raw_input),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((out_dir / "opt_print_passes_raw.txt").exists())
            self.assertTrue((out_dir / "pass_registry_snapshot.json").exists())
            self.assertTrue((out_dir / "pass_registry_report.md").exists())


if __name__ == "__main__":
    unittest.main()
