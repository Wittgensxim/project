import csv
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassSpecRegistryCheckTests(unittest.TestCase):
    def test_cross_check_marks_matching_mvp_passes_ok(self):
        from ecpor.passspec_registry_check import build_registry_check

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            pipeline = root / "pipeline_scalar.yaml"
            snapshot = root / "pass_registry_snapshot.json"
            _write_passspec(passspec, ["sroa", "early-cse"])
            _write_pipeline(pipeline, ["sroa", "early-cse"])
            _write_snapshot(snapshot, ["sroa", "early-cse"], missing=[])

            result = build_registry_check(
                passspec_path=passspec,
                pipeline_config_path=pipeline,
                registry_snapshot_path=snapshot,
            )

        self.assertEqual(result["summary"]["PassSpecPasses"], 2)
        self.assertEqual(result["summary"]["PipelinePasses"], 2)
        self.assertEqual(result["summary"]["RegistryExpectedPasses"], 2)
        self.assertEqual(result["summary"]["MissingPassSpecPassesInRegistry"], 0)
        self.assertEqual(result["summary"]["PipelinePassesMissingInPassSpec"], 0)
        self.assertEqual(result["summary"]["RegistryMissingExpectedPasses"], 0)
        self.assertEqual(result["summary"]["Status"], "pass")
        self.assertEqual({row["status"] for row in result["rows"]}, {"ok"})

    def test_cross_check_reports_registry_and_passspec_mismatches(self):
        from ecpor.passspec_registry_check import build_registry_check

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            pipeline = root / "pipeline_scalar.yaml"
            snapshot = root / "pass_registry_snapshot.json"
            _write_passspec(passspec, ["sroa", "gvn"])
            _write_pipeline(pipeline, ["sroa", "missing-from-passspec"])
            _write_snapshot(
                snapshot,
                ["sroa", "gvn", "missing-from-passspec"],
                missing=["gvn"],
            )

            result = build_registry_check(
                passspec_path=passspec,
                pipeline_config_path=pipeline,
                registry_snapshot_path=snapshot,
            )
            by_pass = {row["pass_name"]: row for row in result["rows"]}

        self.assertEqual(by_pass["sroa"]["status"], "ok")
        self.assertEqual(by_pass["gvn"]["status"], "missing_in_registry")
        self.assertEqual(
            by_pass["missing-from-passspec"]["status"],
            "pipeline_pass_missing_in_passspec",
        )
        self.assertEqual(result["summary"]["MissingPassSpecPassesInRegistry"], 1)
        self.assertEqual(result["summary"]["PipelinePassesMissingInPassSpec"], 1)
        self.assertEqual(result["summary"]["RegistryMissingExpectedPasses"], 1)
        self.assertEqual(result["summary"]["Status"], "fail")

    def test_writes_csv_and_report_with_behavior_boundary(self):
        from ecpor.passspec_registry_check import write_registry_check_outputs

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            pipeline = root / "pipeline_scalar.yaml"
            snapshot = root / "pass_registry_snapshot.json"
            output_dir = root / "check"
            _write_passspec(passspec, ["sroa"])
            _write_pipeline(pipeline, ["sroa"])
            _write_snapshot(snapshot, ["sroa"], missing=[])

            outputs = write_registry_check_outputs(
                passspec_path=passspec,
                pipeline_config_path=pipeline,
                registry_snapshot_path=snapshot,
                output_dir=output_dir,
            )
            rows = _read_csv(output_dir / "passspec_registry_check.csv")
            report = (output_dir / "passspec_registry_check_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(outputs["csv"], output_dir / "passspec_registry_check.csv")
        self.assertEqual(rows[0]["pass_name"], "sroa")
        self.assertEqual(rows[0]["status"], "ok")
        self.assertIn("Status: pass", report)
        self.assertIn("It does not infer pass semantics.", report)
        self.assertIn("It does not certify independence.", report)

    def test_main_writes_default_outputs(self):
        from ecpor.passspec_registry_check import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passspec = root / "passspec.yaml"
            pipeline = root / "pipeline_scalar.yaml"
            snapshot = root / "pass_registry_snapshot.json"
            output_dir = root / "check"
            _write_passspec(passspec, ["sroa"])
            _write_pipeline(pipeline, ["sroa"])
            _write_snapshot(snapshot, ["sroa"], missing=[])

            exit_code = main(
                [
                    "--passspec",
                    str(passspec),
                    "--pipeline",
                    str(pipeline),
                    "--registry-snapshot",
                    str(snapshot),
                    "--out-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "passspec_registry_check.csv").exists())
            self.assertTrue((output_dir / "passspec_registry_check_report.md").exists())


def _write_passspec(path: Path, passes: list[str]) -> None:
    body = ["passes:"]
    for pass_name in passes:
        body.extend(
            [
                f"  {pass_name}:",
                "    level: function",
                "    requires_any: []",
                "    may_consume: []",
                "    may_produce: []",
            ]
        )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _write_pipeline(path: Path, passes: list[str]) -> None:
    body = ["passes:"]
    body.extend(f"  - {pass_name}" for pass_name in passes)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _write_snapshot(path: Path, expected: list[str], *, missing: list[str]) -> None:
    presence = {pass_name: pass_name not in missing for pass_name in expected}
    path.write_text(
        json.dumps(
            {
                "expected_passes": expected,
                "expected_pass_presence": presence,
                "missing_expected_passes": missing,
                "all_pass_like_names": expected,
                "parse_confidence": "raw_snapshot_with_presence_check",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
