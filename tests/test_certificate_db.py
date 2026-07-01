import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CertificateDBTests(unittest.TestCase):
    def test_lookup_hits_same_pair_and_state(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.normalizer import NORMALIZER_VERSION
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cert_db = CertificateDB(tmp_path / "certs")
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            cert_db.save(cert)

            hit = cert_db.lookup(
                "instcombine",
                "dce",
                cert.input_state_hash,
                env_id="env-1",
                execution_model=cert.execution_model,
                normalizer_version=NORMALIZER_VERSION,
                nesting="function",
                region_id="function_scalar_mvp",
            )

            self.assertIsNotNone(hit)
            self.assertEqual(hit.cert_id, cert.cert_id)

    def test_lookup_misses_different_state_or_environment(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.normalizer import NORMALIZER_VERSION, hard_hash
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cert_db = CertificateDB(tmp_path / "certs")
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            other_state = _write_state(tmp_path, "other")
            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            cert_db.save(cert)

            state_miss = cert_db.lookup(
                "instcombine",
                "dce",
                hard_hash(other_state),
                env_id="env-1",
                execution_model=cert.execution_model,
                normalizer_version=NORMALIZER_VERSION,
                nesting="function",
                region_id="function_scalar_mvp",
            )
            env_miss = cert_db.lookup(
                "instcombine",
                "dce",
                cert.input_state_hash,
                env_id="env-2",
                execution_model=cert.execution_model,
                normalizer_version=NORMALIZER_VERSION,
                nesting="function",
                region_id="function_scalar_mvp",
            )

            self.assertIsNone(state_miss)
            self.assertIsNone(env_miss)

    def test_lookup_supports_reversed_pair_on_same_state(self):
        from ecpor.certificate_db import CertificateDB
        from ecpor.normalizer import NORMALIZER_VERSION
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cert_db = CertificateDB(tmp_path / "certs")
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path, "state")
            cert = test_adjacent_swap(
                state,
                "early-cse",
                "simplifycfg",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )
            cert_db.save(cert)

            hit = cert_db.lookup(
                "simplifycfg",
                "early-cse",
                cert.input_state_hash,
                env_id="env-1",
                execution_model=cert.execution_model,
                normalizer_version=NORMALIZER_VERSION,
                nesting="function",
                region_id="function_scalar_mvp",
            )

            self.assertIsNotNone(hit)
            self.assertEqual(hit.cert_id, cert.cert_id)


def _write_state(tmp_path: Path, name: str) -> Path:
    state = tmp_path / f"{name}.ll"
    state.write_text(
        f"; {name}\n"
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
            output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
