import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PairTesterTests(unittest.TestCase):
    def test_adjacent_swap_equal_outputs_is_certified_independent(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="same")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "certified_independent")
            self.assertTrue(cert.hard_equal)
            self.assertEqual(cert.reason, "hard hash equal")
            self.assertTrue(Path(cert.output_ab).exists())
            self.assertTrue(Path(cert.output_ba).exists())
            self.assertEqual(Path(cert.output_ab).parent.name, cert.cert_id)
            self.assertEqual(Path(cert.output_ba).parent.name, cert.cert_id)
            self.assertEqual(cert.pipeline_ab, "function(instcombine,dce)")
            self.assertEqual(cert.pipeline_ba, "function(dce,instcombine)")

    def test_adjacent_swap_different_outputs_is_not_certified(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="different")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "not_certified_independent")
            self.assertFalse(cert.hard_equal)
            self.assertEqual(cert.reason, "hard hash differs")

    def test_adjacent_swap_failed_run_is_run_failed(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="fail_ba")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "run_failed")
            self.assertFalse(cert.hard_equal)
            self.assertIsNone(cert.failure_kind_ab)
            self.assertEqual(cert.failure_kind_ba, "opt_failed")
            self.assertIn("BA failed", cert.reason)

    def test_adjacent_swap_cert_id_changes_with_extra_flags(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="same")
            state = _write_state(tmp_path)

            base = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            flagged = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
                extra_flags=["-debug-only=none"],
            )

            self.assertNotEqual(base.cert_id, flagged.cert_id)

    def test_pair_test_cli_writes_certificate_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="same")
            state = _write_state(tmp_path)
            cert_path = tmp_path / "cert.json"

            import subprocess
            env = dict(os.environ)
            src_path = Path(__file__).resolve().parents[1] / "src"
            env["PYTHONPATH"] = str(src_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ecpor.pair_test",
                    "--state",
                    str(state),
                    "--A",
                    "instcombine",
                    "--B",
                    "dce",
                    "--opt",
                    sys.executable,
                    "--opt-arg",
                    str(fake_opt),
                    "--out",
                    str(tmp_path / "outputs"),
                    "--cert",
                    str(cert_path),
                    "--env-id",
                    "env-1",
                    "--llvm-version",
                    "test-llvm",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(cert_path.exists())
            self.assertIn("certified_independent", result.stdout)


class CertificateReproductionTests(unittest.TestCase):
    def test_reproduce_certificate_matches_saved_label_and_hashes(self):
        from ecpor.pair_test import reproduce_certificate, test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="same")
            state = _write_state(tmp_path)
            cert_path = tmp_path / "cert.json"

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            cert.save(cert_path)

            result = reproduce_certificate(
                cert_path,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "repro",
            )

            self.assertTrue(result.reproduced)
            self.assertEqual(result.original_label, "certified_independent")
            self.assertEqual(result.reproduced_label, "certified_independent")
            self.assertEqual(result.original_hash_ab, result.reproduced_hash_ab)
            self.assertEqual(result.original_hash_ba, result.reproduced_hash_ba)


def _write_state(tmp_path: Path) -> Path:
    state = tmp_path / "state.ll"
    state.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
    return state


def _write_fake_opt(tmp_path: Path, mode: str) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            f"""
            import pathlib
            import sys

            mode = {mode!r}
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))

            if mode == "fail_ba" and "dce,instcombine" in pass_arg:
                print("BA failed", file=sys.stderr)
                sys.exit(5)

            if mode == "different" and "dce,instcombine" in pass_arg:
                output.write_text("define void @f() {{\\n  ret void\\n}}\\n; BA\\n", encoding="utf-8")
            else:
                output.write_text("define void @f() {{\\n  ret void\\n}}\\n", encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
