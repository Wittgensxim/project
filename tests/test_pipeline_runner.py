import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PipelineRunnerTests(unittest.TestCase):
    def test_runs_candidate_pipeline_and_scans_output_features(self):
        from ecpor.candidate_pipeline import CandidatePipeline
        from ecpor.pipeline_runner import run_pipeline_candidate

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_pipeline_opt(tmp_path)
            input_ir = _write_input_ir(tmp_path)
            anchor = CandidatePipeline(
                program="tiny",
                candidate_id="tiny__anchor",
                source="anchor",
                base_pipeline="sroa,early-cse",
                candidate_pipeline="sroa,early-cse",
                swap_index=None,
                pass_a="",
                pass_b="",
                prefix_state_hash="",
                validation_label="anchor",
                cert_id="",
                reason="anchor pipeline",
            )

            record = run_pipeline_candidate(
                input_ir,
                anchor,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "runs",
            )

        self.assertEqual(record.program, "tiny")
        self.assertEqual(record.candidate_id, "tiny__anchor")
        self.assertEqual(record.pipeline, "function(sroa,early-cse)")
        self.assertEqual(record.exit_code, 0)
        self.assertIsNone(record.failure_kind)
        self.assertTrue(record.same_as_anchor)
        self.assertEqual(len(record.hard_hash), 64)
        self.assertGreaterEqual(record.num_instructions, 1)
        self.assertGreaterEqual(record.num_basic_blocks, 1)
        self.assertEqual(record.num_load, 1)
        self.assertEqual(record.num_store, 1)
        self.assertEqual(record.num_branch, 0)

    def test_marks_non_anchor_same_as_anchor_by_hard_hash(self):
        from ecpor.candidate_pipeline import CandidatePipeline
        from ecpor.pipeline_runner import run_pipeline_candidate

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_pipeline_opt(tmp_path)
            input_ir = _write_input_ir(tmp_path)
            anchor = CandidatePipeline(
                program="tiny",
                candidate_id="tiny__anchor",
                source="anchor",
                base_pipeline="sroa,early-cse",
                candidate_pipeline="sroa,early-cse",
                swap_index=None,
                pass_a="",
                pass_b="",
                prefix_state_hash="",
                validation_label="anchor",
                cert_id="",
                reason="anchor pipeline",
            )
            candidate = CandidatePipeline(
                program="tiny",
                candidate_id="tiny__swap_0__sroa__early-cse",
                source="single_swap",
                base_pipeline="sroa,early-cse",
                candidate_pipeline="early-cse,sroa",
                swap_index=0,
                pass_a="sroa",
                pass_b="early-cse",
                prefix_state_hash="h0",
                validation_label="not_certified_independent",
                cert_id="cert-0",
                reason="hard hash differs",
            )
            anchor_record = run_pipeline_candidate(
                input_ir,
                anchor,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "runs",
            )

            candidate_record = run_pipeline_candidate(
                input_ir,
                candidate,
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "runs",
                anchor_hash=anchor_record.hard_hash,
            )

        self.assertFalse(candidate_record.same_as_anchor)
        self.assertNotEqual(candidate_record.hard_hash, anchor_record.hard_hash)

    def test_writes_requested_pipeline_run_fields(self):
        from ecpor.pipeline_runner import PIPELINE_RUN_FIELDS, PipelineRunRecord
        from ecpor.pipeline_runner import write_pipeline_runs_csv

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pipeline_runs.csv"
            write_pipeline_runs_csv(
                out,
                [
                    PipelineRunRecord(
                        program="tiny",
                        candidate_id="tiny__anchor",
                        pipeline="function(sroa)",
                        exit_code=0,
                        failure_kind=None,
                        hard_hash="h",
                        same_as_anchor=True,
                        num_instructions=1,
                        num_basic_blocks=1,
                        num_load=0,
                        num_store=0,
                        num_branch=0,
                    )
                ],
            )

            with out.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, PIPELINE_RUN_FIELDS)
                rows = list(reader)

        self.assertEqual(rows[0]["same_as_anchor"], "True")
        self.assertEqual(rows[0]["failure_kind"], "")


def _write_input_ir(tmp_path: Path) -> Path:
    input_ir = tmp_path / "input.ll"
    input_ir.write_text(
        "define void @f(ptr %p) {\n"
        "entry:\n"
        "  %v = load i32, ptr %p\n"
        "  store i32 %v, ptr %p\n"
        "  ret void\n"
        "}\n",
        encoding="utf-8",
    )
    return input_ir


def _write_fake_pipeline_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            source = pathlib.Path(sys.argv[1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))
            suffix = ""
            if "function(early-cse,sroa)" in pass_arg:
                suffix = "\\n@marker = global i32 0\\n"
            output.write_text(
                source.read_text(encoding="utf-8") + suffix,
                encoding="utf-8",
            )
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
