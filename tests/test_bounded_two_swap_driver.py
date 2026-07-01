import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class BoundedTwoSwapDriverTests(unittest.TestCase):
    def test_smoke_generates_depth2_candidates_from_smaller_seed(self):
        from ecpor.bounded_two_swap_driver import run_bounded_two_swap_smoke
        from ecpor.certificate_db import CertificateDB

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = _write_input_ir(tmp_path)
            fake_opt = _write_fake_opt(tmp_path)
            fake_llc = _write_fake_llc(tmp_path)
            fake_size = _write_fake_size(tmp_path)
            p5_dir = tmp_path / "p5"
            p6_dir = tmp_path / "p6"
            out_dir = tmp_path / "p7a"
            p5_dir.mkdir()
            p6_dir.mkdir()
            _write_p5_candidates(p5_dir / "candidates.csv")
            _write_p5_pipeline_runs(p5_dir / "pipeline_runs.csv")
            _write_p6_object_size(p6_dir / "object_size.csv")

            result = run_bounded_two_swap_smoke(
                programs=[("tiny", input_ir)],
                p5_candidates_csv=p5_dir / "candidates.csv",
                p5_pipeline_runs_csv=p5_dir / "pipeline_runs.csv",
                p6_object_size_csv=p6_dir / "object_size.csv",
                passspec=_passspec(),
                cert_db=CertificateDB(tmp_path / "certs"),
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=out_dir,
                env_id="env-test",
                llvm_version="llvm-test",
                llc_path=[sys.executable, str(fake_llc)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )

            candidates_path = out_dir / "two_swap_candidates.csv"
            runs_path = out_dir / "two_swap_pipeline_runs.csv"
            object_size_path = out_dir / "two_swap_object_size.csv"
            report_path = out_dir / "two_swap_report.md"
            with candidates_path.open(newline="", encoding="utf-8") as handle:
                candidate_rows = list(csv.DictReader(handle))
            with runs_path.open(newline="", encoding="utf-8") as handle:
                run_rows = list(csv.DictReader(handle))
            with object_size_path.open(newline="", encoding="utf-8") as handle:
                object_rows = list(csv.DictReader(handle))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.summary["seed_candidates"], 1)
        self.assertEqual(result.summary["attempted_second_swaps"], 2)
        self.assertGreaterEqual(result.summary["two_swap_candidates_generated"], 1)
        self.assertEqual(result.summary["pipeline_run_failed"], 0)
        self.assertEqual(result.summary["object_build_failed"], 0)
        self.assertEqual(result.summary["size_parse_failed"], 0)

        depth2_rows = [row for row in candidate_rows if row["depth"] == "2"]
        self.assertEqual(len(depth2_rows), result.summary["two_swap_candidates_generated"])
        self.assertTrue(all(row["source"] == "two_swap" for row in depth2_rows))
        self.assertTrue(all(row["parent_candidate_id"] == "tiny__swap_0__a__b" for row in depth2_rows))
        self.assertTrue(all(row["pipeline_sequence_hash"] for row in depth2_rows))
        self.assertNotIn("a,b,c", [row["candidate_pipeline"] for row in depth2_rows])

        prefix_attempt = next(row for row in result.attempt_rows if row["swap_index"] == "1")
        self.assertEqual(prefix_attempt["prefix_passes"], "b")
        self.assertEqual(prefix_attempt["pass_a"], "a")
        self.assertEqual(prefix_attempt["pass_b"], "c")

        self.assertEqual(len(run_rows), 1 + len(depth2_rows))
        self.assertTrue(any(row["source"] == "two_swap" for row in object_rows))
        self.assertIn("P7a Bounded Two-Swap Smoke Report", report)
        self.assertIn("seed_candidates: 1", report)


def _write_input_ir(tmp_path: Path) -> Path:
    input_ir = tmp_path / "input.ll"
    input_ir.write_text(
        "define void @f() {\n"
        "entry:\n"
        "  ret void\n"
        "}\n",
        encoding="utf-8",
    )
    return input_ir


def _write_p5_candidates(path: Path) -> None:
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
                    "base_pipeline": "a,b,c",
                    "candidate_pipeline": "a,b,c",
                    "swap_index": "",
                    "pass_a": "",
                    "pass_b": "",
                    "prefix_state_hash": "",
                    "validation_label": "anchor",
                    "cert_id": "",
                    "reason": "anchor",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap_0__a__b",
                    "source": "single_swap",
                    "base_pipeline": "a,b,c",
                    "candidate_pipeline": "b,a,c",
                    "swap_index": "0",
                    "pass_a": "a",
                    "pass_b": "b",
                    "prefix_state_hash": "seed-prefix",
                    "validation_label": "not_certified_independent",
                    "cert_id": "seed-cert",
                    "reason": "hard hash differs",
                },
            ]
        )


def _write_p5_pipeline_runs(path: Path) -> None:
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
                    "pipeline": "function(a,b,c)",
                    "exit_code": "0",
                    "failure_kind": "",
                    "hard_hash": "anchor-hash",
                    "same_as_anchor": "True",
                    "num_instructions": "1",
                    "num_basic_blocks": "1",
                    "num_load": "0",
                    "num_store": "0",
                    "num_branch": "0",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap_0__a__b",
                    "pipeline": "function(b,a,c)",
                    "exit_code": "0",
                    "failure_kind": "",
                    "hard_hash": "seed-hash",
                    "same_as_anchor": "False",
                    "num_instructions": "1",
                    "num_basic_blocks": "1",
                    "num_load": "0",
                    "num_store": "0",
                    "num_branch": "0",
                },
            ]
        )


def _write_p6_object_size(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "text_delta",
                "text_delta_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "source": "anchor",
                    "text_delta": "0",
                    "text_delta_pct": "0.000000",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap_0__a__b",
                    "source": "single_swap",
                    "text_delta": "-10",
                    "text_delta_pct": "-10.000000",
                },
            ]
        )


def _passspec():
    return {
        "a": {"level": "scalar", "requires_any": [], "may_consume": [], "may_produce": [], "tags": ["scalar"]},
        "b": {"level": "scalar", "requires_any": [], "may_consume": [], "may_produce": [], "tags": ["scalar"]},
        "c": {"level": "scalar", "requires_any": [], "may_consume": [], "may_produce": [], "tags": ["scalar"]},
    }


def _write_fake_opt(tmp_path: Path) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            """
            import pathlib
            import re
            import sys

            source = pathlib.Path(sys.argv[1])
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))
            marker = re.sub(r"[^A-Za-z0-9_]+", "_", pass_arg)
            output.write_text(
                source.read_text(encoding="utf-8") + f"@g_{marker} = global i32 0\\n",
                encoding="utf-8",
            )
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


def _write_fake_llc(tmp_path: Path) -> Path:
    fake_llc = tmp_path / "fake_llc.py"
    fake_llc.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_text(pathlib.Path(sys.argv[1]).stem, encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_llc


def _write_fake_size(tmp_path: Path) -> Path:
    fake_size = tmp_path / "fake_size.py"
    fake_size.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            name = pathlib.Path(sys.argv[-1]).stem
            text = 90 if "depth2" in name else 100
            print("   text    data     bss     dec     hex filename")
            print(f"{text:7d}       0       0 {text:7d}      0 {name}.o")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_size


if __name__ == "__main__":
    unittest.main()
