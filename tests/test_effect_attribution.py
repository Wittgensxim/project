import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class EffectAttributionTests(unittest.TestCase):
    def test_runs_parameterized_ffbench_attribution(self):
        from ecpor.effect_attribution import run_effect_attribution

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_ir = root / "ffbench.ll"
            output_dir = root / "ffbench_attribution"
            input_ir.write_text("define i32 @main() {\n  ret i32 0\n}\n", encoding="utf-8")
            fake_opt = _write_fake_opt(root)
            fake_llc = _write_fake_compiler(root, "fake_llc.py")
            fake_clang = _write_fake_compiler(root, "fake_clang.py")
            fake_size = _write_fake_size(root)

            result = run_effect_attribution(
                program="testsuite_misc_ffbench",
                input_ir=input_ir,
                output_dir=output_dir,
                prefix=["sroa", "early-cse"],
                pass_a="instcombine",
                pass_b="simplifycfg",
                suffix=["reassociate", "gvn", "dce", "adce"],
                opt_path=[sys.executable, str(fake_opt)],
                llc_path=[sys.executable, str(fake_llc)],
                clang_path=[sys.executable, str(fake_clang)],
                llvm_size_path=[sys.executable, str(fake_size)],
                timeout_sec=5.0,
            )
            report = (output_dir / "attribution_report.md").read_text(encoding="utf-8")

        self.assertEqual(result.summary["Program"], "testsuite_misc_ffbench")
        self.assertEqual(result.summary["Pair"], "instcombine,simplifycfg")
        self.assertTrue(result.summary["BothCodegenSmaller"])
        self.assertIn("# Effect Attribution: testsuite_misc_ffbench", report)
        self.assertIn("Pair: instcombine,simplifycfg", report)
        self.assertNotIn("Queens", report)

    def test_runs_queens_attribution_and_writes_required_outputs(self):
        from ecpor.effect_attribution import run_queens_effect_attribution

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_ir = root / "queens.ll"
            output_dir = root / "attribution"
            input_ir.write_text("define i32 @main() {\n  ret i32 0\n}\n", encoding="utf-8")
            fake_opt = _write_fake_opt(root)
            fake_llc = _write_fake_compiler(root, "fake_llc.py")
            fake_clang = _write_fake_compiler(root, "fake_clang.py")
            fake_size = _write_fake_size(root)

            result = run_queens_effect_attribution(
                input_ir=input_ir,
                output_dir=output_dir,
                opt_path=[sys.executable, str(fake_opt)],
                llc_path=[sys.executable, str(fake_llc)],
                clang_path=[sys.executable, str(fake_clang)],
                llvm_size_path=[sys.executable, str(fake_size)],
                timeout_sec=5.0,
            )

            states = _read_csv(output_dir / "states.csv")
            deltas = _read_csv(output_dir / "feature_deltas.csv")
            opcode_deltas = _read_csv(output_dir / "opcode_delta.csv")
            object_rows = _read_csv(output_dir / "object_size.csv")
            report = (output_dir / "attribution_report.md").read_text(encoding="utf-8")

        self.assertEqual(
            [row["state_name"] for row in states],
            ["S", "A", "B", "AB_local", "BA_local", "AB_final", "BA_final"],
        )
        self.assertEqual(result.summary["LocalABBAHardHashEqual"], False)
        self.assertEqual(result.summary["FinalABBAHardHashEqual"], False)
        local = next(row for row in deltas if row["comparison"] == "local_AB_vs_BA")
        final = next(row for row in deltas if row["comparison"] == "final_AB_vs_BA")
        self.assertEqual(local["hard_hash_equal"], "False")
        self.assertEqual(final["hard_hash_equal"], "False")
        self.assertLess(int(final["num_instructions_delta"]), 0)
        local_opcodes = next(
            row for row in opcode_deltas if row["comparison"] == "local_AB_vs_BA"
        )
        final_opcodes = next(
            row for row in opcode_deltas if row["comparison"] == "final_AB_vs_BA"
        )
        self.assertEqual(local_opcodes["num_add_delta"], "-1")
        self.assertEqual(final_opcodes["num_add_delta"], "-1")
        self.assertEqual(result.summary["FinalOpcodeDeltaNonZero"], "num_add_delta=-1")

        ba_final_sizes = {
            row["compile_mode"]: row
            for row in object_rows
            if row["state_name"] == "BA_final"
        }
        self.assertEqual(ba_final_sizes["llc"]["direction"], "smaller")
        self.assertEqual(ba_final_sizes["clang"]["direction"], "smaller")
        self.assertTrue(result.summary["BothCodegenSmaller"])
        self.assertIn("Observed Attribution Hypothesis", report)
        self.assertIn("Opcode Delta", report)
        self.assertIn("FinalOpcodeDeltaNonZero: num_add_delta=-1", report)
        self.assertIn("LocalABBAHardHashEqual: False", report)
        self.assertIn("BothCodegenSmaller: True", report)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_fake_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            passes = next(arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("-passes="))
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            if "sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce" in passes:
                body = ["%x = call i32 @q()", "%y = add i32 %x, 1", "%z = add i32 %y, 1", "ret i32 %z"]
            elif "sroa,early-cse,simplifycfg,instcombine,reassociate,gvn,dce,adce" in passes:
                body = ["%x = call i32 @q()", "%z = add i32 %x, 1", "ret i32 %z"]
            elif "sroa,early-cse,instcombine,simplifycfg" in passes:
                body = ["%x = call i32 @q()", "%y = add i32 %x, 1", "%z = add i32 %y, 1", "ret i32 %z"]
            elif "sroa,early-cse,simplifycfg,instcombine" in passes:
                body = ["%x = call i32 @q()", "%z = add i32 %x, 1", "ret i32 %z"]
            elif "sroa,early-cse,instcombine" in passes:
                body = ["%x = call i32 @q()", "%y = add i32 %x, 1", "ret i32 %y"]
            elif "sroa,early-cse,simplifycfg" in passes:
                body = ["%x = call i32 @q()", "br label %exit", "exit:", "ret i32 %x"]
            else:
                body = ["%x = call i32 @q()", "ret i32 %x"]
            lines = ["declare i32 @q()", "define i32 @main() {", "entry:"]
            lines.extend("  " + line for line in body)
            lines.append("}")
            output.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


def _write_fake_compiler(tmp_path: Path, name: str) -> Path:
    compiler = tmp_path / name
    compiler.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_bytes(b"fake object")
            """
        ).strip(),
        encoding="utf-8",
    )
    return compiler


def _write_fake_size(tmp_path: Path) -> Path:
    fake_size = tmp_path / "fake_size.py"
    fake_size.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            name = pathlib.Path(sys.argv[-1]).name
            if "BA_final" in name and "llc" in name:
                text = 90
            elif "BA_final" in name and "clang" in name:
                text = 95
            elif "AB_final" in name:
                text = 100
            else:
                text = 100
            print("   text    data     bss     dec     hex filename")
            print(f"{text:7d}       4       8     {text + 12:3d}      70 fake.o")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_size


if __name__ == "__main__":
    unittest.main()
