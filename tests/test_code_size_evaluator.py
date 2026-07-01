import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CodeSizeEvaluatorTests(unittest.TestCase):
    def test_evaluates_p5_outputs_against_program_anchor(self):
        from ecpor.code_size_evaluator import run_code_size_evaluation

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            p5_dir = tmp_path / "p5"
            output_dir = tmp_path / "p6"
            pipeline_output_dir = p5_dir / "pipeline_outputs"
            pipeline_output_dir.mkdir(parents=True)
            candidates_csv = p5_dir / "candidates.csv"
            pipeline_runs_csv = p5_dir / "pipeline_runs.csv"
            _write_candidates_csv(candidates_csv)
            _write_pipeline_runs_csv(pipeline_runs_csv)
            _write_ir(pipeline_output_dir / "tiny__anchor.ll")
            _write_ir(pipeline_output_dir / "tiny__swap_0__sroa__early-cse.ll")
            fake_llc = _write_fake_llc(tmp_path)
            fake_size = _write_fake_size_by_name(tmp_path)

            result = run_code_size_evaluation(
                candidates_csv=candidates_csv,
                pipeline_runs_csv=pipeline_runs_csv,
                pipeline_output_dir=pipeline_output_dir,
                output_dir=output_dir,
                llc_path=[sys.executable, str(fake_llc)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )

            object_size_csv = output_dir / "object_size.csv"
            report = (output_dir / "code_size_report.md").read_text(encoding="utf-8")
            with object_size_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(result.summary["object_builds_attempted"], 2)
        self.assertEqual(result.summary["object_build_failed"], 0)
        self.assertEqual(result.summary["size_parse_failed"], 0)
        self.assertEqual(result.summary["anchor_sizes_available"], 1)
        self.assertEqual(result.summary["single_swap_sizes_available"], 1)
        self.assertEqual(result.summary["code_size_delta_computed"], 1)
        self.assertEqual(result.summary["smaller_text"], 1)
        self.assertEqual(result.summary["equal_text"], 0)
        self.assertEqual(result.summary["larger_text"], 0)
        self.assertEqual(len(rows), 2)
        swap = rows[1]
        self.assertEqual(swap["source"], "single_swap")
        self.assertEqual(swap["anchor_candidate_id"], "tiny__anchor")
        self.assertEqual(swap["text_size"], "90")
        self.assertEqual(swap["anchor_text_size"], "100")
        self.assertEqual(swap["text_delta"], "-10")
        self.assertIn("# P6 Code Size Report", report)
        self.assertIn("ObjectBuildFailed: 0", report)
        self.assertIn("SizeParseFailed: 0", report)
        self.assertIn("smaller_text: 1", report)


def _write_candidates_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "base_pipeline",
                "candidate_pipeline",
                "swap_index",
                "pass_a",
                "pass_b",
                "prefix_state_hash",
                "validation_label",
                "cert_id",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "source": "anchor",
                    "base_pipeline": "sroa,early-cse",
                    "candidate_pipeline": "sroa,early-cse",
                    "swap_index": "",
                    "pass_a": "",
                    "pass_b": "",
                    "prefix_state_hash": "",
                    "validation_label": "anchor",
                    "cert_id": "",
                    "reason": "anchor pipeline",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap_0__sroa__early-cse",
                    "source": "single_swap",
                    "base_pipeline": "sroa,early-cse",
                    "candidate_pipeline": "early-cse,sroa",
                    "swap_index": "0",
                    "pass_a": "sroa",
                    "pass_b": "early-cse",
                    "prefix_state_hash": "h0",
                    "validation_label": "not_certified_independent",
                    "cert_id": "cert-0",
                    "reason": "hard hash differs",
                },
            ]
        )


def _write_pipeline_runs_csv(path: Path) -> None:
    path.write_text(
        "program,candidate_id,pipeline,exit_code,failure_kind,hard_hash,"
        "same_as_anchor,num_instructions,num_basic_blocks,num_load,num_store,num_branch\n"
        "tiny,tiny__anchor,function(sroa),0,,ha,True,1,1,0,0,0\n"
        "tiny,tiny__swap_0__sroa__early-cse,function(early-cse,sroa),0,,hb,False,1,1,0,0,0\n",
        encoding="utf-8",
    )


def _write_ir(path: Path) -> None:
    path.write_text("define void @f() { ret void }\n", encoding="utf-8")


def _write_fake_llc(tmp_path: Path) -> Path:
    fake_llc = tmp_path / "fake_llc.py"
    fake_llc.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_text("object:" + pathlib.Path(sys.argv[1]).stem, encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_llc


def _write_fake_size_by_name(tmp_path: Path) -> Path:
    fake_size = tmp_path / "fake_size.py"
    fake_size.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            name = pathlib.Path(sys.argv[-1]).stem
            text = 90 if "swap" in name else 100
            total = text
            print("   text    data     bss     dec     hex filename")
            print(f"{text:7d}       0       0 {total:7d}      0 {name}.o")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_size


if __name__ == "__main__":
    unittest.main()
