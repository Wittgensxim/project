import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class AdjacentSwapDriverTests(unittest.TestCase):
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
