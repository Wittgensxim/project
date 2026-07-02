import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class Depth1AnalysisTests(unittest.TestCase):
    def test_builds_program_pair_and_both_smaller_summaries(self):
        from ecpor.depth1_analysis import run_depth1_analysis

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "analysis"
            p4_attempts = root / "attempts.csv"
            p5_candidates = root / "candidates.csv"
            p5_pipeline_runs = root / "pipeline_runs.csv"
            p6_object_size = root / "object_size.csv"
            p8a_compare = root / "compare.csv"
            reference_p6 = root / "reference_object_size.csv"
            reference_compare = root / "reference_compare.csv"
            _write_attempts(p4_attempts)
            _write_candidates(p5_candidates)
            _write_pipeline_runs(p5_pipeline_runs)
            _write_object_size(p6_object_size)
            _write_compare(p8a_compare)
            _write_reference_object_size(reference_p6)
            _write_reference_compare(reference_compare)

            result = run_depth1_analysis(
                p4_attempts_csv=p4_attempts,
                p5_candidates_csv=p5_candidates,
                p5_pipeline_runs_csv=p5_pipeline_runs,
                p6_object_size_csv=p6_object_size,
                p8a_compare_csv=p8a_compare,
                output_dir=output_dir,
                reference_p6_object_size_csv=reference_p6,
                reference_p8a_compare_csv=reference_compare,
                benchmark_label="Diverse8",
            )
            program_rows = _read_csv(output_dir / "depth1_program_summary.csv")
            pair_rows = _read_csv(output_dir / "depth1_pair_summary.csv")
            both_smaller = _read_csv(output_dir / "depth1_both_smaller_cases.csv")
            report = (output_dir / "depth1_analysis_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.summary["Programs"], 2)
        self.assertEqual(result.summary["SingleSwapCandidates"], 3)
        self.assertEqual(result.summary["SmallerText"], 1)
        self.assertEqual(result.summary["EqualText"], 2)
        self.assertEqual(result.summary["IRDifferentButTextEqualCount"], 2)
        self.assertEqual(result.summary["Depth1BothSmallerPrograms"], 1)
        self.assertEqual(result.summary["ReferenceIRDifferentButTextEqualRate"], "93.75%")
        self.assertEqual(len(program_rows), 2)
        ffbench = next(row for row in program_rows if row["program"] == "ffbench")
        self.assertEqual(ffbench["both_smaller_cases"], "1")
        inst_simplify = next(
            row for row in pair_rows if row["pair"] == "instcombine,simplifycfg"
        )
        self.assertEqual(inst_simplify["smaller_text"], "1")
        self.assertEqual(both_smaller[0]["program"], "ffbench")
        self.assertEqual(both_smaller[0]["pair"], "instcombine,simplifycfg")
        self.assertIn("# Diverse8 Depth1 Analysis Report", report)
        self.assertIn("Depth1BothSmallerPrograms: 1", report)
        self.assertIn("Diverse8 repeats the Stanford depth1 pattern", report)


def _write_attempts(path: Path) -> None:
    rows = [
        ("ffbench", "dynamic_test", "not_certified_independent", "True", "False"),
        ("ffbench", "dynamic_test", "certified_independent", "True", "False"),
        ("other", "skipped_low_priority", "skipped_low_priority", "False", "False"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "action",
                "label",
                "dynamic_test",
                "cache_hit",
                "pass_a",
                "pass_b",
            ],
        )
        writer.writeheader()
        for program, action, label, dynamic_test, cache_hit in rows:
            writer.writerow(
                {
                    "program": program,
                    "action": action,
                    "label": label,
                    "dynamic_test": dynamic_test,
                    "cache_hit": cache_hit,
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                }
            )


def _write_candidates(path: Path) -> None:
    rows = [
        ("ffbench", "ffbench__anchor", "anchor", "", ""),
        ("other", "other__anchor", "anchor", "", ""),
        ("ffbench", "ffbench__swap_0__sroa__early-cse", "single_swap", "sroa", "early-cse"),
        (
            "ffbench",
            "ffbench__swap_2__instcombine__simplifycfg",
            "single_swap",
            "instcombine",
            "simplifycfg",
        ),
        ("other", "other__swap_0__sroa__early-cse", "single_swap", "sroa", "early-cse"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "source", "pass_a", "pass_b"],
        )
        writer.writeheader()
        for program, candidate_id, source, pass_a, pass_b in rows:
            writer.writerow(
                {
                    "program": program,
                    "candidate_id": candidate_id,
                    "source": source,
                    "pass_a": pass_a,
                    "pass_b": pass_b,
                }
            )


def _write_pipeline_runs(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "same_as_anchor", "failure_kind"],
        )
        writer.writeheader()
        for candidate_id in [
            "ffbench__anchor",
            "other__anchor",
            "ffbench__swap_0__sroa__early-cse",
            "ffbench__swap_2__instcombine__simplifycfg",
            "other__swap_0__sroa__early-cse",
        ]:
            writer.writerow(
                {
                    "program": "ffbench" if candidate_id.startswith("ffbench") else "other",
                    "candidate_id": candidate_id,
                    "same_as_anchor": "True" if candidate_id.endswith("__anchor") else "False",
                    "failure_kind": "",
                }
            )


def _write_object_size(path: Path) -> None:
    rows = [
        ("ffbench", "ffbench__anchor", "anchor", "", "", "0", "0.000000"),
        ("other", "other__anchor", "anchor", "", "", "0", "0.000000"),
        (
            "ffbench",
            "ffbench__swap_0__sroa__early-cse",
            "single_swap",
            "sroa",
            "early-cse",
            "0",
            "0.000000",
        ),
        (
            "ffbench",
            "ffbench__swap_2__instcombine__simplifycfg",
            "single_swap",
            "instcombine",
            "simplifycfg",
            "-16",
            "-1.000000",
        ),
        (
            "other",
            "other__swap_0__sroa__early-cse",
            "single_swap",
            "sroa",
            "early-cse",
            "0",
            "0.000000",
        ),
    ]
    _write_object_like(path, rows)


def _write_reference_object_size(path: Path) -> None:
    rows = [("p", f"p__swap_{index}", "single_swap", "a", "b", "0", "0.000000") for index in range(15)]
    rows.append(("p", "p__swap_smaller", "single_swap", "a", "b", "-1", "-1.000000"))
    _write_object_like(path, rows)


def _write_object_like(path: Path, rows: list[tuple[str, str, str, str, str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "pass_a",
                "pass_b",
                "text_delta",
                "text_delta_pct",
                "p5_same_as_anchor",
                "compile_failure_kind",
                "size_failure_kind",
            ],
        )
        writer.writeheader()
        for program, candidate_id, source, pass_a, pass_b, delta, pct in rows:
            writer.writerow(
                {
                    "program": program,
                    "candidate_id": candidate_id,
                    "source": source,
                    "pass_a": pass_a,
                    "pass_b": pass_b,
                    "text_delta": delta,
                    "text_delta_pct": pct,
                    "p5_same_as_anchor": "True" if source == "anchor" else "False",
                    "compile_failure_kind": "",
                    "size_failure_kind": "",
                }
            )


def _write_compare(path: Path) -> None:
    rows = [
        ("ffbench", "ffbench__swap_0__sroa__early-cse", "sroa", "early-cse", "equal", "larger", "False"),
        (
            "ffbench",
            "ffbench__swap_2__instcombine__simplifycfg",
            "instcombine",
            "simplifycfg",
            "smaller",
            "smaller",
            "True",
        ),
        ("other", "other__swap_0__sroa__early-cse", "sroa", "early-cse", "equal", "equal", "True"),
    ]
    _write_compare_like(path, rows)


def _write_reference_compare(path: Path) -> None:
    rows = [("p", f"p__swap_{index}", "a", "b", "equal", "equal", "True") for index in range(15)]
    rows.append(("p", "p__swap_smaller", "a", "b", "smaller", "smaller", "True"))
    _write_compare_like(path, rows)


def _write_compare_like(path: Path, rows: list[tuple[str, str, str, str, str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "pass_a",
                "pass_b",
                "llc_direction",
                "clang_direction",
                "direction_agree",
                "llc_text_delta_pct",
                "clang_text_delta_pct",
            ],
        )
        writer.writeheader()
        for program, candidate_id, pass_a, pass_b, llc, clang, agree in rows:
            writer.writerow(
                {
                    "program": program,
                    "candidate_id": candidate_id,
                    "source": "single_swap",
                    "pass_a": pass_a,
                    "pass_b": pass_b,
                    "llc_direction": llc,
                    "clang_direction": clang,
                    "direction_agree": agree,
                    "llc_text_delta_pct": "-1.000000" if llc == "smaller" else "0.000000",
                    "clang_text_delta_pct": "-0.100000" if clang == "smaller" else "0.000000",
                }
            )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
