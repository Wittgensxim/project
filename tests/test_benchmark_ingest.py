import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class BenchmarkIngestTests(unittest.TestCase):
    def test_ingests_accepts_and_rejects_sources_with_failure_reasons(self):
        from ecpor.benchmark_ingest import run_benchmark_ingest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "suite"
            source_root.mkdir()
            good = source_root / "Good.c"
            optnone = source_root / "Optnone.c"
            good.write_text("int main(void) { return 0; }\n", encoding="utf-8")
            optnone.write_text("/* OPTNONE */\nint main(void) { return 0; }\n", encoding="utf-8")
            tools = _write_fake_tools(root)
            input_dir = root / "inputs"
            output_dir = root / "outputs"
            config_path = root / "configs" / "benchmarks_p8b.yaml"

            result = run_benchmark_ingest(
                source_roots=[source_root],
                input_dir=input_dir,
                output_dir=output_dir,
                config_path=config_path,
                clang_path=[sys.executable, str(tools / "fake_clang.py")],
                opt_path=[sys.executable, str(tools / "fake_opt.py")],
                llc_path=[sys.executable, str(tools / "fake_llc.py")],
                llvm_size_path=[sys.executable, str(tools / "fake_size.py")],
                accepted_limit=1,
                min_scanned=2,
                instruction_limit=5000,
                timeout_sec=5.0,
            )

            rows = _read_csv(output_dir / "ingest_summary.csv")
            report = (output_dir / "report.md").read_text(encoding="utf-8")
            config = config_path.read_text(encoding="utf-8")
            accepted = next(row for row in rows if row["status"] == "accepted")
            rejected = next(row for row in rows if row["status"] == "rejected")
            accepted_input_exists = Path(accepted["input_ir"]).exists()

        self.assertEqual(result.summary["CandidateSourceFilesScanned"], 2)
        self.assertEqual(result.summary["AcceptedPrograms"], 1)
        self.assertEqual(result.summary["RejectedPrograms"], 1)
        self.assertEqual(accepted["program"], "testsuite_misc_good")
        self.assertTrue(accepted_input_exists)
        self.assertEqual(accepted["failure_stage"], "")
        self.assertEqual(accepted["scalar_pipeline_ok"], "True")
        self.assertEqual(accepted["llc_object_ok"], "True")
        self.assertEqual(accepted["clang_object_ok"], "True")
        self.assertEqual(accepted["size_parse_ok"], "True")
        self.assertEqual(accepted["num_functions"], "1")
        self.assertEqual(accepted["num_instructions"], "1")
        self.assertEqual(rejected["program"], "testsuite_misc_optnone")
        self.assertEqual(rejected["failure_stage"], "ir_validation")
        self.assertEqual(rejected["failure_kind"], "optnone_present")
        self.assertIn("AcceptedPrograms: 1", report)
        self.assertIn("RejectedPrograms: 1", report)
        self.assertIn("testsuite_misc_good", config)
        self.assertIn("data/inputs/testsuite_misc_good.ll", config)


def _write_fake_tools(root: Path) -> Path:
    tools = root / "tools"
    tools.mkdir()
    _write_text(
        tools / "fake_clang.py",
        r'''
from pathlib import Path
import sys

args = sys.argv[1:]
out = Path(args[args.index("-o") + 1])
if "-emit-llvm" in args:
    source = Path(args[-3] if args[-2] == "-o" else args[0])
    text = source.read_text(encoding="utf-8")
    attrs = " #0" if "OPTNONE" in text else ""
    suffix = '\nattributes #0 = { noinline nounwind optnone }\n' if "OPTNONE" in text else ""
    out.write_text(f"define i32 @main(){attrs} {{\nentry:\n  ret i32 0\n}}\n{suffix}", encoding="utf-8")
else:
    out.write_text("object", encoding="utf-8")
'''.lstrip(),
    )
    _write_text(
        tools / "fake_opt.py",
        r'''
from pathlib import Path
import sys

args = sys.argv[1:]
out = Path(args[args.index("-o") + 1])
inp = Path(args[0])
out.write_text(inp.read_text(encoding="utf-8"), encoding="utf-8")
'''.lstrip(),
    )
    _write_text(
        tools / "fake_llc.py",
        r'''
from pathlib import Path
import sys

args = sys.argv[1:]
out = Path(args[args.index("-o") + 1])
out.write_text("object", encoding="utf-8")
'''.lstrip(),
    )
    _write_text(
        tools / "fake_size.py",
        "print('text data bss dec hex filename')\nprint('10 0 0 10 a fake.o')\n",
    )
    return tools


def _write_text(path: Path, text: str) -> None:
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
