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
            expected_pipeline_runs_sha256 = _sha256(pipeline_runs_csv)
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
        self.assertEqual(result.summary["ir_different_but_text_equal_count"], 0)
        self.assertEqual(result.summary["ir_different_but_text_equal_rate"], 0.0)
        self.assertEqual(
            result.metadata["pipeline_runs_sha256"],
            expected_pipeline_runs_sha256,
        )
        self.assertIn("ecpor_git_commit", result.metadata)
        self.assertEqual(len(rows), 2)
        swap = rows[1]
        self.assertEqual(swap["source"], "single_swap")
        self.assertEqual(swap["anchor_candidate_id"], "tiny__anchor")
        self.assertEqual(swap["text_size"], "90")
        self.assertEqual(swap["data_size"], "0")
        self.assertEqual(swap["bss_size"], "0")
        self.assertEqual(swap["anchor_text_size"], "100")
        self.assertEqual(swap["text_delta"], "-10")
        self.assertEqual(swap["p5_same_as_anchor"], "False")
        self.assertIn("# P6 Code Size Report", report)
        self.assertIn("## Run metadata", report)
        self.assertIn("pipeline_runs_sha256:", report)
        self.assertIn("llc_sha256:", report)
        self.assertIn("ObjectBuildFailed: 0", report)
        self.assertIn("SizeParseFailed: 0", report)
        self.assertIn("smaller_text: 1", report)
        self.assertIn("IRDifferentButTextEqualCount: 0", report)

    def test_validates_object_size_invariants(self):
        from ecpor.code_size_evaluator import validate_object_size_invariants

        rows = [
            {
                "program": "tiny",
                "candidate_id": "tiny__anchor",
                "source": "anchor",
                "anchor_candidate_id": "tiny__anchor",
                "text_size": "100",
                "data_size": "4",
                "bss_size": "1",
                "total_size": "106",
                "anchor_text_size": "100",
                "text_delta": "1",
                "text_delta_pct": "0.000000",
            },
            {
                "program": "tiny",
                "candidate_id": "tiny__swap",
                "source": "single_swap",
                "anchor_candidate_id": "",
                "text_size": "90",
                "data_size": "0",
                "bss_size": "0",
                "total_size": "90",
                "anchor_text_size": "100",
                "text_delta": "-9",
                "text_delta_pct": "-10.000000",
            },
        ]

        errors = validate_object_size_invariants(rows, pipeline_run_count=3)

        self.assertTrue(any("row count" in error for error in errors))
        self.assertTrue(any("total_size != text+data+bss" in error for error in errors))
        self.assertTrue(any("anchor delta is not zero" in error for error in errors))
        self.assertTrue(any("missing program anchor" in error for error in errors))
        self.assertTrue(any("text_delta mismatch" in error for error in errors))

    def test_validates_candidate_source_invariants(self):
        from ecpor.code_size_evaluator import validate_object_size_invariants

        rows = [
            _summary_row("tiny", "tiny__anchor", "anchor", "False", "100", "0"),
            {
                **_summary_row(
                    "tiny",
                    "tiny__swap",
                    "single_swap",
                    "",
                    "90",
                    "-10",
                ),
                "anchor_text_size": "",
                "text_delta": "",
                "text_delta_pct": "",
            },
        ]

        errors = validate_object_size_invariants(rows, pipeline_run_count=2)

        self.assertTrue(
            any("anchor p5_same_as_anchor is not True" in error for error in errors)
        )
        self.assertTrue(
            any("single_swap p5_same_as_anchor missing" in error for error in errors)
        )
        self.assertTrue(
            any("single_swap anchor_text_size missing" in error for error in errors)
        )
        self.assertTrue(
            any("single_swap text_delta missing" in error for error in errors)
        )

    def test_counts_ir_different_but_text_equal_candidates(self):
        from ecpor.code_size_evaluator import summarize_object_size_rows

        rows = [
            _summary_row("tiny", "tiny__anchor", "anchor", "True", "100", "0"),
            _summary_row("tiny", "tiny__swap_a", "single_swap", "False", "100", "0"),
            _summary_row("tiny", "tiny__swap_b", "single_swap", "False", "95", "-5"),
            _summary_row("tiny", "tiny__swap_c", "single_swap", "True", "100", "0"),
        ]

        summary = summarize_object_size_rows(rows)

        self.assertEqual(summary["ir_different_but_text_equal_count"], 1)
        self.assertAlmostEqual(summary["ir_different_but_text_equal_rate"], 1 / 2)
        self.assertEqual(summary["single_swap_p5_same_as_anchor"], 1)
        self.assertEqual(summary["single_swap_p5_different_from_anchor"], 2)

    def test_treats_two_swap_rows_as_code_size_candidates(self):
        from ecpor.code_size_evaluator import summarize_object_size_rows

        rows = [
            _summary_row("tiny", "tiny__anchor", "anchor", "True", "100", "0"),
            _summary_row("tiny", "tiny__depth2", "two_swap", "False", "90", "-10"),
        ]

        summary = summarize_object_size_rows(rows)

        self.assertEqual(summary["candidate_object_builds"], 1)
        self.assertEqual(summary["candidate_sizes_available"], 1)
        self.assertEqual(summary["code_size_delta_computed"], 1)
        self.assertEqual(summary["smaller_text"], 1)
        self.assertEqual(summary["single_swap_p5_different_from_anchor"], 1)


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "pipeline",
                "exit_code",
                "failure_kind",
                "hard_hash",
                "same_as_anchor",
                "num_instructions",
                "num_basic_blocks",
                "num_load",
                "num_store",
                "num_branch",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "pipeline": "function(sroa)",
                    "exit_code": "0",
                    "failure_kind": "",
                    "hard_hash": "ha",
                    "same_as_anchor": "True",
                    "num_instructions": "1",
                    "num_basic_blocks": "1",
                    "num_load": "0",
                    "num_store": "0",
                    "num_branch": "0",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap_0__sroa__early-cse",
                    "pipeline": "function(early-cse,sroa)",
                    "exit_code": "0",
                    "failure_kind": "",
                    "hard_hash": "hb",
                    "same_as_anchor": "False",
                    "num_instructions": "1",
                    "num_basic_blocks": "1",
                    "num_load": "0",
                    "num_store": "0",
                    "num_branch": "0",
                },
            ]
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


def _summary_row(program, candidate_id, source, p5_same_as_anchor, text_size, text_delta):
    return {
        "program": program,
        "candidate_id": candidate_id,
        "source": source,
        "swap_index": "",
        "pass_a": "",
        "pass_b": "",
        "anchor_candidate_id": f"{program}__anchor",
        "text_size": text_size,
        "data_size": "0",
        "bss_size": "0",
        "total_size": text_size,
        "anchor_text_size": "100",
        "anchor_data_size": "0",
        "anchor_bss_size": "0",
        "anchor_total_size": "100",
        "text_delta": text_delta,
        "text_delta_pct": f"{int(text_delta):.6f}",
        "total_delta": text_delta,
        "total_delta_pct": f"{int(text_delta):.6f}",
        "p5_same_as_anchor": p5_same_as_anchor,
        "compile_failure_kind": "",
        "size_failure_kind": "",
    }


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
