import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class RunnerTests(unittest.TestCase):
    def test_run_opt_success_returns_structured_result(self):
        from ecpor.runner import run_opt

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = tmp_path / "fake_opt.py"
            input_ll = tmp_path / "input.ll"
            output_ll = tmp_path / "output.ll"
            input_ll.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
            fake_opt.write_text(
                textwrap.dedent(
                    """
                    import pathlib
                    import sys

                    output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
                    source = pathlib.Path(sys.argv[1])
                    output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                    print("fake opt ok")
                    """
                ).strip(),
                encoding="utf-8",
            )

            result = run_opt(
                input_ll,
                "function(instcombine,dce)",
                output_ll,
                opt_path=[sys.executable, str(fake_opt)],
            )

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(result.verifier_ok)
            self.assertEqual(result.stdout.strip(), "fake opt ok")
            self.assertTrue(result.output_path.exists())
            self.assertEqual(len(result.hard_hash), 64)
            self.assertIn("-verify-each", result.command)

    def test_run_opt_failure_returns_structured_error(self):
        from ecpor.runner import run_opt

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = tmp_path / "fake_opt.py"
            input_ll = tmp_path / "input.ll"
            output_ll = tmp_path / "output.ll"
            input_ll.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
            fake_opt.write_text(
                "import sys\nprint('bad pass', file=sys.stderr)\nsys.exit(7)\n",
                encoding="utf-8",
            )

            result = run_opt(
                input_ll,
                "function(bad-pass)",
                output_ll,
                opt_path=[sys.executable, str(fake_opt)],
            )

            self.assertEqual(result.exit_code, 7)
            self.assertFalse(result.verifier_ok)
            self.assertIn("bad pass", result.stderr)
            self.assertFalse(result.output_path.exists())
            self.assertIsNone(result.hard_hash)


if __name__ == "__main__":
    unittest.main()

