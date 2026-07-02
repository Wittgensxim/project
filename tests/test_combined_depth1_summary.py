import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CombinedDepth1SummaryTests(unittest.TestCase):
    def test_combines_three_benchmark_sets_with_depth1_only_codegen(self):
        from ecpor.combined_depth1_summary import (
            BenchmarkSetInputs,
            run_combined_depth1_summary,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stanford = _make_set(
                root,
                "Stanford-8",
                "stanford",
                both_smaller=True,
                include_depth2_both_smaller=True,
                attribution_cases=1,
            )
            misc = _make_set(
                root,
                "Misc8",
                "misc",
                both_smaller=True,
                include_depth2_both_smaller=False,
                attribution_cases=1,
            )
            diverse = _make_set(
                root,
                "Diverse8",
                "diverse",
                both_smaller=False,
                include_depth2_both_smaller=False,
                attribution_cases=0,
            )

            result = run_combined_depth1_summary(
                output_dir=root / "combined_depth1_summary",
                manifest_path=root / "combined_depth1_summary_manifest.json",
                benchmark_sets=[stanford, misc, diverse],
                repo_root=root,
                result_generated_from_commit="depth1abc",
            )

            output_dir = root / "combined_depth1_summary"
            benchmark_rows = _read_csv(output_dir / "benchmark_set_summary.csv")
            objective_rows = _read_csv(output_dir / "depth1_objective_summary.csv")
            codegen_rows = _read_csv(output_dir / "depth1_codegen_summary.csv")
            report = (output_dir / "combined_depth1_report.md").read_text(
                encoding="utf-8"
            )
            manifest = json.loads(
                (root / "combined_depth1_summary_manifest.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(result.summary["BenchmarkSets"], 3)
        self.assertEqual(result.summary["TotalPrograms"], 6)
        self.assertEqual(result.summary["TotalPairMatrixCertificates"], 12)
        self.assertEqual(result.summary["TotalReproducedCertificates"], 12)
        self.assertEqual(result.summary["TotalHardFalseIndependent"], 0)
        self.assertEqual(result.summary["TotalAdjacentAttempts"], 12)
        self.assertEqual(result.summary["TotalOneSwapCandidates"], 6)
        self.assertEqual(result.summary["TotalBothSmallerPrograms"], 2)
        self.assertEqual(result.summary["Diverse8BothSmallerPrograms"], 0)
        self.assertEqual(result.summary["AttributionCases"], 2)
        self.assertEqual(len(benchmark_rows), 3)
        self.assertEqual(benchmark_rows[0]["benchmark_set"], "Stanford-8")
        self.assertEqual(benchmark_rows[0]["both_smaller_programs"], "1")
        self.assertEqual(objective_rows[0]["ir_different_but_text_equal_count"], "1")
        self.assertEqual(codegen_rows[0]["direction_comparison_candidates"], "2")
        self.assertEqual(codegen_rows[0]["smaller_under_both_count"], "1")
        self.assertIn("TotalPrograms: 6", report)
        self.assertIn("Depth1Only: True", report)
        self.assertIn("NoNewExperiments: True", report)
        self.assertEqual(manifest["stage"], "P9-5")
        self.assertEqual(manifest["summary"]["TotalPrograms"], 6)
        self.assertEqual(manifest["scope_limits"]["summary_only"], True)
        self.assertEqual(manifest["scope_limits"]["two_swap_search"], False)
        self.assertEqual(
            manifest["scope_limits"]["benchmark_sets"],
            ["Stanford-8", "Misc8", "Diverse8"],
        )


def _make_set(
    root: Path,
    name: str,
    prefix: str,
    *,
    both_smaller: bool,
    include_depth2_both_smaller: bool,
    attribution_cases: int,
):
    from ecpor.combined_depth1_summary import BenchmarkSetInputs

    folder = root / prefix
    folder.mkdir()
    _write_pair_summary(folder / "cert_summary.csv", prefix)
    _write_text(
        folder / "static_report.md",
        "StaticCandidateRecall: 100.00%\nStaticFalseNegativeObserved: 0\n",
    )
    _write_text(
        folder / "lazy_report.md",
        (
            "attempted_adjacent_swaps: 4\n"
            "candidate_swaps: 3\n"
            "low_priority_skipped: 1\n"
            "dynamic_tests: 3\n"
            "certified_independent: 2\n"
            "not_certified_independent: 1\n"
            "run_failed: 0\n"
            "HardFalseIndependent: 0\n"
            "CertificateReproductionRate: 100.00%\n"
        ),
    )
    _write_candidates(folder / "candidates.csv", prefix)
    _write_pipeline_runs(folder / "pipeline_runs.csv", prefix)
    _write_object_size(folder / "object_size.csv", prefix, both_smaller=both_smaller)
    _write_codegen_compare(
        folder / "compare.csv",
        prefix,
        both_smaller=both_smaller,
        include_depth2_both_smaller=include_depth2_both_smaller,
    )
    _write_attribution(folder / "attribution.csv", prefix, attribution_cases)
    return BenchmarkSetInputs(
        name=name,
        pair_summary_csv=folder / "cert_summary.csv",
        static_filter_report=folder / "static_report.md",
        lazy_validation_report=folder / "lazy_report.md",
        p5_candidates_csv=folder / "candidates.csv",
        p5_pipeline_runs_csv=folder / "pipeline_runs.csv",
        p6_object_size_csv=folder / "object_size.csv",
        codegen_compare_csv=folder / "compare.csv",
        attribution_summary_csv=folder / "attribution.csv",
    )


def _write_pair_summary(path: Path, prefix: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "pair_a",
                "pair_b",
                "label",
                "hard_equal",
                "reproduced",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                _pair_row(prefix, "p1", "a", "b", "certified_independent", "True"),
                _pair_row(prefix, "p1", "b", "c", "certified_independent", "True"),
                _pair_row(prefix, "p2", "c", "d", "not_certified_independent", "False"),
                _pair_row(prefix, "p2", "d", "e", "not_certified_independent", "False"),
            ]
        )


def _pair_row(
    prefix: str, program: str, left: str, right: str, label: str, hard_equal: str
) -> dict[str, str]:
    return {
        "program": f"{prefix}_{program}",
        "pair_a": left,
        "pair_b": right,
        "label": label,
        "hard_equal": hard_equal,
        "reproduced": "True",
    }


def _write_candidates(path: Path, prefix: str) -> None:
    _write_text(
        path,
        (
            "program,candidate_id,source,pass_a,pass_b\n"
            f"{prefix}_p1,{prefix}_p1__anchor,anchor,,\n"
            f"{prefix}_p1,{prefix}_p1__swap_0__a__b,single_swap,a,b\n"
            f"{prefix}_p2,{prefix}_p2__swap_1__c__d,single_swap,c,d\n"
        ),
    )


def _write_pipeline_runs(path: Path, prefix: str) -> None:
    _write_text(
        path,
        (
            "program,candidate_id,failure_kind,same_as_anchor\n"
            f"{prefix}_p1,{prefix}_p1__anchor,,True\n"
            f"{prefix}_p1,{prefix}_p1__swap_0__a__b,,False\n"
            f"{prefix}_p2,{prefix}_p2__swap_1__c__d,,True\n"
        ),
    )


def _write_object_size(path: Path, prefix: str, *, both_smaller: bool) -> None:
    first_delta = "-4" if both_smaller else "0"
    second_delta = "0" if both_smaller else "8"
    _write_text(
        path,
        (
            "program,candidate_id,source,text_delta,text_delta_pct,"
            "p5_same_as_anchor,compile_failure_kind,size_failure_kind,pass_a,pass_b\n"
            f"{prefix}_p1,{prefix}_p1__swap_0__a__b,single_swap,{first_delta},{first_delta}.000000,False,,,a,b\n"
            f"{prefix}_p2,{prefix}_p2__swap_1__c__d,single_swap,{second_delta},{second_delta}.000000,False,,,c,d\n"
        ),
    )


def _write_codegen_compare(
    path: Path,
    prefix: str,
    *,
    both_smaller: bool,
    include_depth2_both_smaller: bool,
) -> None:
    first_llc = "smaller" if both_smaller else "equal"
    first_clang = "smaller" if both_smaller else "equal"
    rows = [
        (
            f"{prefix}_p1",
            f"{prefix}_p1__swap_0__a__b",
            "single_swap",
            first_llc,
            first_clang,
            "True",
            "-4.000000",
            "-1.000000",
        ),
        (
            f"{prefix}_p2",
            f"{prefix}_p2__swap_1__c__d",
            "single_swap",
            "equal",
            "equal" if both_smaller else "larger",
            "True" if both_smaller else "False",
            "0.000000",
            "0.000000" if both_smaller else "2.000000",
        ),
    ]
    if include_depth2_both_smaller:
        rows.append(
            (
                f"{prefix}_p1",
                f"{prefix}_p1__two_swap",
                "two_swap",
                "smaller",
                "smaller",
                "True",
                "-8.000000",
                "-8.000000",
            )
        )
    text = [
        (
            "program,candidate_id,source,llc_direction,clang_direction,"
            "direction_agree,llc_text_delta_pct,clang_text_delta_pct"
        )
    ]
    text.extend(",".join(row) for row in rows)
    _write_text(path, "\n".join(text) + "\n")


def _write_attribution(path: Path, prefix: str, rows: int) -> None:
    lines = ["program,pair\n"]
    for index in range(rows):
        lines.append(f"{prefix}_attr_{index},\"a,b\"\n")
    _write_text(path, "".join(lines))


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
