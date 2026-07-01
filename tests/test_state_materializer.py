import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class StateMaterializerTests(unittest.TestCase):
    def test_empty_prefix_returns_input_state(self):
        from ecpor.normalizer import hard_hash
        from ecpor.state_materializer import materialize_prefix_state

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = _write_state(tmp_path)

            materialized = materialize_prefix_state(
                state,
                [],
                opt_path="unused",
                output_dir=tmp_path / "prefix",
                env_id="env-1",
            )

            self.assertEqual(materialized.path, state)
            self.assertEqual(materialized.state_hash, hard_hash(state))
            self.assertEqual(materialized.prefix_passes, [])
            self.assertEqual(materialized.pipeline, "input")
            self.assertIsNone(materialized.run_result)

    def test_non_empty_prefix_runs_opt_and_caches_output(self):
        from ecpor.state_materializer import materialize_prefix_state

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path)
            state = _write_state(tmp_path)

            first = materialize_prefix_state(
                state,
                ["sroa", "early-cse"],
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "prefix",
                env_id="env-1",
            )
            second = materialize_prefix_state(
                state,
                ["sroa", "early-cse"],
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "prefix",
                env_id="env-1",
            )

            self.assertTrue(first.path.exists())
            self.assertEqual(first.pipeline, "function(sroa,early-cse)")
            self.assertIsNotNone(first.run_result)
            self.assertFalse(first.cache_hit)
            self.assertEqual(second.path, first.path)
            self.assertEqual(second.state_hash, first.state_hash)
            self.assertTrue(second.cache_hit)
            self.assertIsNone(second.run_result)


def _write_state(tmp_path: Path) -> Path:
    state = tmp_path / "state.ll"
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
