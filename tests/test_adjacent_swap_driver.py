import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class AdjacentSwapDriverTests(unittest.TestCase):
    def test_main_uses_benchmark_config_programs(self):
        from ecpor import adjacent_swap_driver as driver
        from ecpor.adjacent_swap_driver import summarize_attempts

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = _write_state(tmp_path)
            benchmark_config = tmp_path / "benchmarks.yaml"
            pipeline_config = tmp_path / "pipeline.yaml"
            passspec = tmp_path / "passspec.yaml"
            benchmark_config.write_text(
                "programs:\n"
                "  - id: cfg_tiny\n"
                f"    ir: {input_ir.as_posix()}\n",
                encoding="utf-8",
            )
            pipeline_config.write_text("passes:\n  - sroa\n  - early-cse\n", encoding="utf-8")
            passspec.write_text("passes: {}\n", encoding="utf-8")
            fake_run = driver.AdjacentSwapValidationRun(
                attempts=[],
                summary=summarize_attempts([]),
            )

            with patch.object(
                driver,
                "run_adjacent_swap_validation",
                return_value=fake_run,
            ) as run_validation:
                exit_code = driver.main(
                    [
                        "--benchmark-config",
                        str(benchmark_config),
                        "--pipeline",
                        str(pipeline_config),
                        "--passspec",
                        str(passspec),
                        "--cert-dir",
                        str(tmp_path / "certs"),
                        "--out",
                        str(tmp_path / "out"),
                        "--attempts-csv",
                        str(tmp_path / "attempts.csv"),
                        "--report",
                        str(tmp_path / "report.md"),
                        "--opt",
                        "opt",
                        "--env-id",
                        "env-test",
                        "--llvm-version",
                        "llvm-test",
                    ]
                )

        self.assertEqual(exit_code, 0)
        programs = run_validation.call_args.kwargs["programs"]
        self.assertEqual(programs, [("cfg_tiny", input_ir)])

    def test_program_preset_supports_p8b_misc8(self):
        from ecpor.adjacent_swap_driver import _programs_for_preset

        programs = _programs_for_preset("p8b-misc8")

        self.assertEqual(len(programs), 8)
        self.assertEqual(programs[0][0], "testsuite_misc_aarch64_init_cpu_features")
        self.assertEqual(programs[2][0], "testsuite_misc_ffbench")

    def test_dynamic_pruning_ratio_is_not_applicable_without_dynamic_tests(self):
        from ecpor.adjacent_swap_driver import (
            AdjacentSwapAttempt,
            build_summary_report,
            summarize_attempts,
        )

        attempts = [
            AdjacentSwapAttempt(
                program="tiny",
                prefix_passes=[],
                state_path="input.ll",
                state_hash="h0",
                pass_a="sroa",
                pass_b="early-cse",
                static_decision="candidate",
                static_reason="shared_tags_in_window",
                action="cache_hit",
                label="certified_independent",
                cache_hit=True,
                dynamic_test=False,
                reproduced=True,
                cert_id="cert-1",
            )
        ]

        summary = summarize_attempts(attempts)
        report = build_summary_report("P4 Lazy Validation Report", summary)

        self.assertIsNone(summary["certified_pruning_ratio_dynamic"])
        self.assertIn("CertifiedPruningRatioDynamic: N/A", report)

    def test_driver_validates_anchor_adjacent_pairs_and_reuses_cache(self):
        from ecpor.adjacent_swap_driver import run_adjacent_swap_validation
        from ecpor.certificate_db import CertificateDB

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path)
            cert_db = CertificateDB(tmp_path / "certs")
            passes = ["sroa", "early-cse", "dce"]
            passspec = _passspec()

            first = run_adjacent_swap_validation(
                programs=[("tiny", state)],
                passes=passes,
                passspec=passspec,
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "p4",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            second = run_adjacent_swap_validation(
                programs=[("tiny", state)],
                passes=passes,
                passspec=passspec,
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "p4",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(first.summary["attempted_adjacent_swaps"], 2)
            self.assertEqual(first.summary["candidate_swaps"], 2)
            self.assertEqual(first.summary["dynamic_tests"], 2)
            self.assertEqual(first.summary["cache_hits"], 0)
            self.assertEqual(first.summary["run_failed"], 0)
            self.assertEqual(first.summary["certificate_reproduced"], 2)
            self.assertEqual(second.summary["attempted_adjacent_swaps"], 2)
            self.assertEqual(second.summary["dynamic_tests"], 0)
            self.assertEqual(second.summary["cache_hits"], 2)
            self.assertEqual(second.summary["second_run_cache_hit_rate"], 1.0)

    def test_second_run_cache_hit_rate_ignores_low_priority_skips(self):
        from ecpor.adjacent_swap_driver import run_adjacent_swap_validation
        from ecpor.certificate_db import CertificateDB

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path)
            cert_db = CertificateDB(tmp_path / "certs")
            passes = ["sroa", "early-cse", "cold"]
            passspec = _passspec()
            passspec["cold"] = {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": [],
                "may_produce": [],
                "tags": ["cfg"],
            }

            run_adjacent_swap_validation(
                programs=[("tiny", state)],
                passes=passes,
                passspec=passspec,
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "p4",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            second = run_adjacent_swap_validation(
                programs=[("tiny", state)],
                passes=passes,
                passspec=passspec,
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "p4",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(second.summary["attempted_adjacent_swaps"], 2)
            self.assertEqual(second.summary["candidate_swaps"], 1)
            self.assertEqual(second.summary["low_priority_skipped"], 1)
            self.assertEqual(second.summary["cache_hits"], 1)
            self.assertEqual(second.summary["dynamic_tests"], 0)
            self.assertEqual(second.summary["second_run_cache_hit_rate"], 1.0)


def _passspec():
    return {
        "sroa": {
            "level": "function",
            "requires_any": ["has_alloca"],
            "may_consume": ["alloca"],
            "may_produce": ["scalar_value"],
            "tags": ["scalar"],
        },
        "early-cse": {
            "level": "function",
            "requires_any": ["instruction"],
            "may_consume": ["scalar_value"],
            "may_produce": ["dead_instruction"],
            "tags": ["scalar"],
        },
        "dce": {
            "level": "function",
            "requires_any": ["instruction"],
            "may_consume": ["dead_instruction"],
            "may_produce": ["smaller_ir"],
            "tags": ["cleanup"],
        },
    }


def _write_state(tmp_path: Path) -> Path:
    state = tmp_path / "state.ll"
    state.write_text(
        "define void @f() {\n"
        "entry:\n"
        "  %x = alloca i32\n"
        "  store i32 0, ptr %x\n"
        "  ret void\n"
        "}\n",
        encoding="utf-8",
    )
    return state


def _write_fake_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            source = pathlib.Path(sys.argv[1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))
            output.write_text(
                source.read_text(encoding="utf-8") + "\\n; " + pass_arg + "\\n",
                encoding="utf-8",
            )
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
