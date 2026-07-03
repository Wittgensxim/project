import csv
from types import SimpleNamespace
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassExpansionSmokeTests(unittest.TestCase):
    def test_builds_smoke_summary_and_selects_stable_changed_candidates(self):
        from ecpor.pass_expansion_smoke import (
            PassExpansionCandidate,
            build_pass_expansion_smoke,
        )

        calls: list[tuple[str, str]] = []

        def fake_runner(input_ll, passes, output_ll, **_kwargs):
            pass_name = passes.removeprefix("function(").removesuffix(")")
            program = Path(input_ll).stem
            calls.append((program, pass_name))
            if pass_name == "bad":
                return SimpleNamespace(
                    exit_code=1,
                    failure_kind="opt_failed",
                    timed_out=False,
                    stderr="Broken module found",
                    hard_hash=None,
                    elapsed_ms=3.0,
                )
            changed = pass_name == "good" and program == "p1"
            return SimpleNamespace(
                exit_code=0,
                failure_kind=None,
                timed_out=False,
                stderr="",
                hard_hash=f"{program}-{pass_name}-changed" if changed else None,
                elapsed_ms=2.0,
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p1 = _write_ir(root / "p1.ll", "define void @p1() {\n  ret void\n}\n")
            p2 = _write_ir(root / "p2.ll", "define void @p2() {\n  ret void\n}\n")

            analysis = build_pass_expansion_smoke(
                candidates=[
                    PassExpansionCandidate("good", "function", "scalar", "registry", ""),
                    PassExpansionCandidate("bad", "function", "scalar", "registry", ""),
                    PassExpansionCandidate("sroa", "function", "baseline", "registry", ""),
                    PassExpansionCandidate("missing", "function", "absent", "registry", ""),
                ],
                programs=[("p1", p1), ("p2", p2)],
                registry_passes={"good", "bad", "sroa"},
                baseline_passes=["sroa"],
                max_selected=1,
                runner=fake_runner,
                output_dir=root / "smoke_outputs",
            )

        rows = {row["pass_name"]: row for row in analysis["smoke_rows"]}
        self.assertEqual(calls, [("p1", "good"), ("p2", "good"), ("p1", "bad"), ("p2", "bad")])
        self.assertEqual(rows["good"]["programs_attempted"], 2)
        self.assertEqual(rows["good"]["changed_ir_count"], 1)
        self.assertEqual(rows["good"]["noop_count"], 1)
        self.assertEqual(rows["good"]["run_failed"], 0)
        self.assertEqual(rows["good"]["selected_for_scalar12"], "True")
        self.assertEqual(rows["bad"]["run_failed"], 2)
        self.assertEqual(rows["bad"]["verifier_failed"], 2)
        self.assertEqual(rows["bad"]["selected_for_scalar12"], "False")
        self.assertEqual(rows["sroa"]["rejection_reason"], "already_in_baseline")
        self.assertEqual(rows["missing"]["rejection_reason"], "not_in_registry_snapshot")
        self.assertEqual(analysis["summary"]["SelectedNewPasses"], 1)
        self.assertEqual(analysis["summary"]["NewExperiments"], True)
        self.assertEqual(analysis["summary"]["NewCertificates"], False)
        self.assertEqual(analysis["summary"]["NewSearch"], False)

    def test_writes_smoke_outputs_and_scalar12_configs(self):
        from ecpor.pass_expansion_smoke import (
            PassExpansionCandidate,
            load_expansion_candidates,
            write_pass_expansion_smoke_outputs,
            write_scalar12_configs,
        )

        def fake_runner(input_ll, passes, output_ll, **_kwargs):
            pass_name = passes.removeprefix("function(").removesuffix(")")
            Path(output_ll).parent.mkdir(parents=True, exist_ok=True)
            Path(output_ll).write_text("define void @changed() {\n  ret void\n}\n", encoding="utf-8")
            return SimpleNamespace(
                exit_code=0,
                failure_kind=None,
                timed_out=False,
                stderr="",
                hard_hash=f"{Path(input_ll).stem}-{pass_name}",
                elapsed_ms=1.0,
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_config = root / "pass_expansion_candidates.yaml"
            candidate_config.write_text(
                """
candidates:
  - name: instsimplify
    expected_level: function
    reason: scalar_cleanup_candidate
    source: pass_registry_snapshot
    manual_note: cheap scalar simplification
""".strip()
                + "\n",
                encoding="utf-8",
            )
            baseline_pipeline = root / "pipeline_scalar.yaml"
            baseline_pipeline.write_text(
                "name: mvp_function_scalar\npipeline: function(sroa,dce)\npasses:\n  - sroa\n  - dce\n",
                encoding="utf-8",
            )
            baseline_passspec = root / "passspec.yaml"
            baseline_passspec.write_text(
                "passes:\n  sroa:\n    level: function\n    requires_any: []\n    may_consume: []\n    may_produce: []\n    tags: [scalar]\n  dce:\n    level: function\n    requires_any: []\n    may_consume: []\n    may_produce: []\n    tags: [cleanup]\n",
                encoding="utf-8",
            )
            program = _write_ir(root / "program.ll", "define void @f() {\n  ret void\n}\n")
            out_dir = root / "smoke"

            candidates = load_expansion_candidates(candidate_config)
            outputs = write_pass_expansion_smoke_outputs(
                output_dir=out_dir,
                candidates=candidates,
                programs=[("program", program)],
                registry_passes={"instsimplify"},
                baseline_passes=["sroa", "dce"],
                runner=fake_runner,
            )
            config_outputs = write_scalar12_configs(
                baseline_pipeline_path=baseline_pipeline,
                baseline_passspec_path=baseline_passspec,
                smoke_csv_path=outputs["smoke_csv"],
                pipeline_out_path=root / "pipeline_scalar12.yaml",
                passspec_out_path=root / "passspec_scalar12.yaml",
            )

            rows = _read_csv(outputs["smoke_csv"])
            report = outputs["report"].read_text(encoding="utf-8")
            pipeline_text = config_outputs["pipeline"].read_text(encoding="utf-8")
            passspec_text = config_outputs["passspec"].read_text(encoding="utf-8")
            pass_outputs_exists = (Path(outputs["smoke_csv"]).parent / "pass_outputs").exists()

        self.assertEqual(rows[0]["pass_name"], "instsimplify")
        self.assertEqual(rows[0]["selected_for_scalar12"], "True")
        self.assertFalse(pass_outputs_exists)
        self.assertIn("SelectedNewPasses: 1", report)
        self.assertIn("name: scalar12_function_scalar", pipeline_text)
        self.assertIn("function(sroa,dce,instsimplify)", pipeline_text)
        self.assertIn("instsimplify:", passspec_text)
        self.assertIn("source: generated_registry", passspec_text)
        self.assertIn("created_in_stage: P15", passspec_text)


def _write_ir(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
