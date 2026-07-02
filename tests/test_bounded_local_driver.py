import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class BoundedLocalDriverTests(unittest.TestCase):
    def test_main_uses_benchmark_config_programs(self):
        from ecpor import bounded_local_driver as driver

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = _write_input_ir(tmp_path)
            attempts_csv = tmp_path / "attempts.csv"
            benchmark_config = tmp_path / "benchmarks.yaml"
            pipeline_config = tmp_path / "pipeline.yaml"
            _write_attempts_csv(attempts_csv)
            benchmark_config.write_text(
                "programs:\n"
                "  - id: cfg_tiny\n"
                f"    ir: {input_ir.as_posix()}\n",
                encoding="utf-8",
            )
            pipeline_config.write_text(
                "passes:\n  - sroa\n  - early-cse\n  - instcombine\n",
                encoding="utf-8",
            )
            fake_run = SimpleNamespace(
                summary={},
                candidate_generation=SimpleNamespace(evidence_rows=[]),
                pipeline_runs=[],
                metadata={},
            )

            with patch.object(
                driver,
                "run_bounded_local_exploration",
                return_value=fake_run,
            ) as run_exploration, patch.object(
                driver,
                "build_bounded_local_report",
                return_value="report\n",
            ):
                exit_code = driver.main(
                    [
                        "--benchmark-config",
                        str(benchmark_config),
                        "--pipeline",
                        str(pipeline_config),
                        "--attempts-csv",
                        str(attempts_csv),
                        "--out",
                        str(tmp_path / "out"),
                        "--opt",
                        "opt",
                        "--env-id",
                        "env-test",
                        "--llvm-version",
                        "llvm-test",
                    ]
                )

        self.assertEqual(exit_code, 0)
        programs = run_exploration.call_args.kwargs["programs"]
        self.assertEqual(programs, [("cfg_tiny", input_ir)])

    def test_program_preset_supports_p8b_misc8(self):
        from ecpor.bounded_local_driver import _programs_for_preset

        programs = _programs_for_preset("p8b-misc8")

        self.assertEqual(len(programs), 8)
        self.assertEqual(programs[0][0], "testsuite_misc_aarch64_init_cpu_features")
        self.assertEqual(programs[2][0], "testsuite_misc_ffbench")

    def test_driver_generates_candidates_runs_pipelines_and_writes_report(self):
        from ecpor.bounded_local_driver import run_bounded_local_exploration

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = _write_input_ir(tmp_path)
            fake_opt = _write_fake_pipeline_opt(tmp_path)
            attempts_csv = tmp_path / "attempts.csv"
            pipeline_config = tmp_path / "pipeline.yaml"
            _write_attempts_csv(attempts_csv)
            pipeline_config.write_text(
                "passes:\n  - sroa\n  - early-cse\n  - instcombine\n",
                encoding="utf-8",
            )

            result = run_bounded_local_exploration(
                programs=[("tiny", input_ir)],
                anchor_passes=["sroa", "early-cse", "instcombine"],
                attempts_csv=attempts_csv,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "p5",
                env_id="env-test",
                llvm_version="llvm-test",
                pipeline_config_path=pipeline_config,
            )

            candidates_path = tmp_path / "p5" / "candidates.csv"
            runs_path = tmp_path / "p5" / "pipeline_runs.csv"
            report_path = tmp_path / "p5" / "report.md"

            self.assertTrue(candidates_path.exists())
            self.assertTrue(runs_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(result.summary["anchor_candidates"], 1)
            self.assertEqual(result.summary["single_swap_candidates"], 1)
            self.assertEqual(result.summary["pipeline_runs"], 2)
            self.assertEqual(result.summary["pipeline_run_failed"], 0)
            self.assertEqual(result.summary["same_as_anchor"], 1)
            self.assertEqual(result.summary["different_from_anchor"], 1)
            self.assertEqual(result.summary["anchor_runs"], 1)
            self.assertEqual(result.summary["single_swap_runs"], 1)
            self.assertEqual(result.summary["single_swap_same_as_anchor"], 0)
            self.assertEqual(result.summary["single_swap_different_from_anchor"], 1)
            self.assertEqual(result.metadata["env_id"], "env-test")
            self.assertEqual(result.metadata["llvm_version"], "llvm-test")
            self.assertEqual(len(result.metadata["attempts_csv_sha256"]), 64)
            self.assertEqual(len(result.metadata["pipeline_config_sha256"]), 64)

            with candidates_path.open(newline="", encoding="utf-8") as handle:
                candidate_rows = list(csv.DictReader(handle))
            with runs_path.open(newline="", encoding="utf-8") as handle:
                run_rows = list(csv.DictReader(handle))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual([row["source"] for row in candidate_rows], ["anchor", "single_swap"])
        self.assertEqual(len(run_rows), 2)
        self.assertIn("# P5 Bounded Local Reorder Report", report)
        self.assertIn("ecpor_git_commit:", report)
        self.assertIn("attempts_csv_sha256:", report)
        self.assertIn("pipeline_config_sha256:", report)
        self.assertIn("P4 adjacent validation summary", report)
        self.assertIn("single_swap_candidates: 1", report)
        self.assertIn("anchor_runs: 1", report)
        self.assertIn("single_swap_runs: 1", report)
        self.assertIn("single_swap_same_as_anchor: 0", report)
        self.assertIn("single_swap_different_from_anchor: 1", report)


def _write_attempts_csv(path: Path) -> None:
    path.write_text(
        "program,prefix_passes,state_path,state_hash,pass_a,pass_b,static_decision,"
        "static_reason,action,label,cache_hit,dynamic_test,reproduced,cert_id\n"
        "tiny,,input.ll,h0,sroa,early-cse,candidate,shared_tags_in_window,"
        "validated,not_certified_independent,False,True,True,cert-0\n"
        "tiny,sroa,state.ll,h1,early-cse,instcombine,candidate,producer_consumer,"
        "validated,certified_independent,False,True,True,cert-1\n",
        encoding="utf-8",
    )


def _write_input_ir(tmp_path: Path) -> Path:
    input_ir = tmp_path / "input.ll"
    input_ir.write_text(
        "define void @f() {\n"
        "entry:\n"
        "  ret void\n"
        "}\n",
        encoding="utf-8",
    )
    return input_ir


def _write_fake_pipeline_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            source = pathlib.Path(sys.argv[1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))
            suffix = ""
            if "function(early-cse,sroa,instcombine)" in pass_arg:
                suffix = "\\n@marker = global i32 0\\n"
            output.write_text(source.read_text(encoding="utf-8") + suffix, encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
