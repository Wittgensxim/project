import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class LazyValidatorTests(unittest.TestCase):
    def test_candidate_runs_dynamic_test_saves_and_reproduces_certificate(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.lazy_validator import validate_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            cert_db = CertificateDB(tmp_path / "certs")

            result = validate_adjacent_swap(
                state,
                "instcombine",
                "dce",
                static_decision="candidate",
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(result.action, "dynamic_test")
            self.assertTrue(result.dynamic_test)
            self.assertFalse(result.cache_hit)
            self.assertTrue(result.reproduced)
            self.assertIn(
                result.label,
                {"certified_independent", "not_certified_independent"},
            )
            self.assertIsNotNone(result.certificate)
            self.assertTrue((tmp_path / "certs" / f"{result.certificate.cert_id}.json").exists())

    def test_second_candidate_validation_reuses_cached_certificate(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.lazy_validator import validate_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            cert_db = CertificateDB(tmp_path / "certs")

            first = validate_adjacent_swap(
                state,
                "instcombine",
                "dce",
                static_decision="candidate",
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            second = validate_adjacent_swap(
                state,
                "dce",
                "instcombine",
                static_decision="candidate",
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(first.action, "dynamic_test")
            self.assertEqual(second.action, "cache_hit")
            self.assertTrue(second.cache_hit)
            self.assertFalse(second.dynamic_test)
            self.assertEqual(second.certificate.cert_id, first.certificate.cert_id)

    def test_low_priority_skips_dynamic_test_without_claiming_independence(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.lazy_validator import validate_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = _write_state(tmp_path, "state")
            cert_db = CertificateDB(tmp_path / "certs")

            result = validate_adjacent_swap(
                state,
                "simplifycfg",
                "dce",
                static_decision="low_priority",
                cert_db=cert_db,
                opt_path=[sys.executable, "missing_fake_opt.py"],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(result.action, "skipped_low_priority")
            self.assertEqual(result.label, "skipped_low_priority")
            self.assertFalse(result.dynamic_test)
            self.assertIsNone(result.certificate)
            self.assertEqual(list((tmp_path / "certs").glob("*.json")), [])

    def test_input_state_certificate_does_not_match_different_prefix_state(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.normalizer import NORMALIZER_VERSION
        from ecpor.lazy_validator import validate_adjacent_swap
        from ecpor.state_materializer import materialize_prefix_state

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            cert_db = CertificateDB(tmp_path / "certs")

            input_result = validate_adjacent_swap(
                state,
                "instcombine",
                "dce",
                static_decision="candidate",
                cert_db=cert_db,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            prefix_state = materialize_prefix_state(
                state,
                ["sroa"],
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "prefix",
                env_id="env-1",
            )
            prefix_hit = cert_db.lookup(
                "instcombine",
                "dce",
                prefix_state.state_hash,
                env_id="env-1",
                execution_model=input_result.certificate.execution_model,
                normalizer_version=NORMALIZER_VERSION,
                nesting="function",
                region_id="function_scalar_mvp",
            )

            self.assertNotEqual(prefix_state.state_hash, input_result.state_hash)
            self.assertIsNone(prefix_hit)


def _write_state(tmp_path: Path, name: str) -> Path:
    state = tmp_path / f"{name}.ll"
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
