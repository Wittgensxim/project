import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CodegenSensitivityTests(unittest.TestCase):
    def test_can_compare_p6_depth1_candidates_without_p7_rows(self):
        from ecpor.codegen_sensitivity import run_codegen_sensitivity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p6_ir = root / "p6_ir"
            output_dir = root / "p8b"
            p6_ir.mkdir()
            p6_object_size = root / "p6_object_size.csv"
            _write_ir(p6_ir / "tiny__anchor.ll")
            _write_ir(p6_ir / "tiny__swap.ll")
            _write_object_size_csv(
                p6_object_size,
                [
                    _row("tiny", "tiny__anchor", "anchor", p6_ir / "tiny__anchor.ll", "100", "0"),
                    _row("tiny", "tiny__swap", "single_swap", p6_ir / "tiny__swap.ll", "90", "-10"),
                ],
            )
            fake_clang = _write_fake_clang(tmp_path=root)
            fake_size = _write_fake_size_by_object_name(tmp_path=root)

            result = run_codegen_sensitivity(
                p6_object_size_csv=p6_object_size,
                p7_object_size_csv=None,
                output_dir=output_dir,
                clang_path=[sys.executable, str(fake_clang)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )
            compare_rows = _read_csv(output_dir / "p8a_codegen_direction_compare.csv")
            report = (output_dir / "p8a_codegen_sensitivity_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.summary["IRInputs"], 2)
        self.assertEqual(result.summary["Depth2Inputs"], 0)
        self.assertEqual(result.summary["DirectionComparisonCandidates"], 1)
        self.assertEqual(compare_rows[0]["source"], "single_swap")
        self.assertIn("Depth2Inputs: 0", report)

    def test_compares_llc_and_clang_directions_for_p6_and_p7b_candidates(self):
        from ecpor.codegen_sensitivity import run_codegen_sensitivity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p6_ir = root / "p6_ir"
            p7_ir = root / "p7_ir"
            output_dir = root / "p8a"
            p6_ir.mkdir()
            p7_ir.mkdir()
            p6_object_size = root / "p6_object_size.csv"
            p7_object_size = root / "p7_object_size.csv"
            _write_ir(p6_ir / "tiny__anchor.ll")
            _write_ir(p6_ir / "tiny__swap.ll")
            _write_ir(p7_ir / "tiny__depth2.ll")
            _write_object_size_csv(
                p6_object_size,
                [
                    _row("tiny", "tiny__anchor", "anchor", p6_ir / "tiny__anchor.ll", "100", "0"),
                    _row("tiny", "tiny__swap", "single_swap", p6_ir / "tiny__swap.ll", "90", "-10"),
                ],
            )
            _write_object_size_csv(
                p7_object_size,
                [
                    _row("tiny", "tiny__anchor", "anchor", p7_ir / "tiny__anchor.ll", "100", "0"),
                    _row("tiny", "tiny__depth2", "two_swap", p7_ir / "tiny__depth2.ll", "110", "10"),
                ],
            )
            fake_clang = _write_fake_clang(tmp_path=root)
            fake_size = _write_fake_size_by_object_name(tmp_path=root)

            result = run_codegen_sensitivity(
                p6_object_size_csv=p6_object_size,
                p7_object_size_csv=p7_object_size,
                output_dir=output_dir,
                clang_path=[sys.executable, str(fake_clang)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )
            clang_rows = _read_csv(output_dir / "p8a_clang_object_size.csv")
            compare_rows = _read_csv(output_dir / "p8a_codegen_direction_compare.csv")
            report = (output_dir / "p8a_codegen_sensitivity_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.summary["IRInputs"], 3)
        self.assertEqual(result.summary["ClangObjectBuildFailed"], 0)
        self.assertEqual(result.summary["ClangSizeParseFailed"], 0)
        self.assertEqual(result.summary["DirectionComparisonCandidates"], 2)
        self.assertEqual(result.summary["DirectionAgreementCount"], 1)
        self.assertEqual(result.summary["DirectionDisagreementCount"], 1)
        self.assertEqual(result.summary["SmallerUnderBothCount"], 1)
        self.assertEqual(result.summary["SmallerOnlyUnderClangCount"], 1)
        self.assertEqual(len(clang_rows), 3)
        self.assertEqual(len(compare_rows), 2)
        depth2 = next(row for row in compare_rows if row["candidate_id"] == "tiny__depth2")
        self.assertEqual(depth2["llc_direction"], "larger")
        self.assertEqual(depth2["clang_direction"], "smaller")
        self.assertEqual(depth2["direction_agree"], "False")
        self.assertIn("DirectionAgreementRate: 50.00%", report)
        self.assertIn("SmallerOnlyUnderClangCount: 1", report)


def _write_ir(path: Path) -> None:
    path.write_text("define void @f() { ret void }\n", encoding="utf-8")


def _row(
    program: str,
    candidate_id: str,
    source: str,
    ir_path: Path,
    text_size: str,
    text_delta: str,
) -> dict[str, str]:
    return {
        "program": program,
        "candidate_id": candidate_id,
        "source": source,
        "ir_path": str(ir_path),
        "object_path": "",
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
        "text_delta_pct": f"{float(text_delta):.6f}",
        "data_delta": "0",
        "bss_delta": "0",
        "total_delta": text_delta,
        "total_delta_pct": f"{float(text_delta):.6f}",
        "p5_same_as_anchor": "True" if source == "anchor" else "False",
        "compile_failure_kind": "",
        "size_failure_kind": "",
    }


def _write_object_size_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_fake_clang(tmp_path: Path) -> Path:
    fake_clang = tmp_path / "fake_clang.py"
    fake_clang.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            if "-x" not in sys.argv or sys.argv[sys.argv.index("-x") + 1] != "ir":
                raise SystemExit(20)
            if "-c" not in sys.argv:
                raise SystemExit(21)
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_text("clang object", encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_clang


def _write_fake_size_by_object_name(tmp_path: Path) -> Path:
    fake_size = tmp_path / "fake_size.py"
    fake_size.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            name = pathlib.Path(sys.argv[-1]).stem
            text = {"tiny__anchor": 100, "tiny__swap": 95, "tiny__depth2": 98}[name]
            print("   text    data     bss     dec     hex filename")
            print(f"{text:7d}       0       0 {text:7d}      0 {name}.o")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_size


if __name__ == "__main__":
    unittest.main()
