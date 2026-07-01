import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CoreEvidenceReportTests(unittest.TestCase):
    def test_builds_reduction_funnel_evidence_and_codegen_summary(self):
        from ecpor.core_evidence_report import run_core_evidence_report

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "core"
            p4_attempts = root / "p4_attempts.csv"
            p5_candidates = root / "p5_candidates.csv"
            p5_pipeline_runs = root / "p5_pipeline_runs.csv"
            p6_object_size = root / "p6_object_size.csv"
            p7b_attempts = root / "p7b_attempts.csv"
            p7b_candidates = root / "p7b_candidates.csv"
            p7b_object_size = root / "p7b_object_size.csv"
            p7b_analysis_report = root / "p7b_analysis_report.md"
            p8a_compare = root / "p8a_compare.csv"

            _write_attempts(p4_attempts)
            _write_p5_candidates(p5_candidates)
            _write_pipeline_runs(p5_pipeline_runs)
            _write_object_size(p6_object_size, source="single_swap", delta="-10")
            _write_attempts(p7b_attempts)
            _write_p7b_candidates(p7b_candidates)
            _write_object_size(p7b_object_size, source="two_swap", delta="0")
            _write_text(
                p7b_analysis_report,
                textwrap.dedent(
                    """
                    RawDepth2Candidates: 2
                    UniqueDepth2Candidates: 1
                    DuplicateSequences: 1
                    Depth2SmallerText: 0
                    Depth2SmallerPrograms: 0
                    Depth2ImprovesProgramDepth1Best: 0
                    """
                ).strip()
                + "\n",
            )
            _write_compare(p8a_compare)

            result = run_core_evidence_report(
                p4_attempts_csv=p4_attempts,
                p5_candidates_csv=p5_candidates,
                p5_pipeline_runs_csv=p5_pipeline_runs,
                p6_object_size_csv=p6_object_size,
                p7b_attempts_csv=p7b_attempts,
                p7b_candidates_csv=p7b_candidates,
                p7b_object_size_csv=p7b_object_size,
                p7b_analysis_report=p7b_analysis_report,
                p8a_compare_csv=p8a_compare,
                output_dir=output_dir,
            )
            funnel_rows = _read_csv(output_dir / "ecpor_reduction_funnel.csv")
            evidence_rows = _read_csv(output_dir / "ecpor_certified_pruning_summary.csv")
            codegen_rows = _read_csv(output_dir / "ecpor_codegen_sensitivity_summary.csv")
            report = (output_dir / "ecpor_core_evidence_report.md").read_text(
                encoding="utf-8"
            )

        p4 = next(row for row in funnel_rows if row["stage"] == "P4")
        self.assertEqual(p4["input_count"], "3")
        self.assertEqual(p4["certified_collapsed"], "1")
        self.assertEqual(p4["not_certified_kept"], "1")
        self.assertEqual(p4["low_priority_frozen"], "1")

        p7b = next(row for row in funnel_rows if row["stage"] == "P7b")
        self.assertEqual(p7b["candidate_count"], "2")
        self.assertEqual(p7b["duplicates_removed"], "1")
        self.assertEqual(p7b["unique_candidates"], "1")

        hard = next(row for row in evidence_rows if row["evidence_type"] == "certified_independent")
        self.assertEqual(hard["hard_prune"], "True")
        self.assertEqual(hard["count"], "2")

        codegen = codegen_rows[0]
        self.assertEqual(codegen["direction_comparison_candidates"], "2")
        self.assertEqual(codegen["direction_agreement_count"], "1")
        self.assertEqual(codegen["direction_agreement_rate"], "50.00%")
        self.assertEqual(result.summary["DirectionAgreementRate"], "50.00%")
        self.assertIn("搜索空间坍缩", report)
        self.assertIn("DirectionAgreementRate: 50.00%", report)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_attempts(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "action",
                "label",
                "cache_hit",
                "dynamic_test",
                "failure_kind",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "action": "dynamic_test",
                    "label": "certified_independent",
                    "cache_hit": "False",
                    "dynamic_test": "True",
                    "failure_kind": "",
                },
                {
                    "program": "tiny",
                    "action": "dynamic_test",
                    "label": "not_certified_independent",
                    "cache_hit": "False",
                    "dynamic_test": "True",
                    "failure_kind": "",
                },
                {
                    "program": "tiny",
                    "action": "skipped_low_priority",
                    "label": "skipped_low_priority",
                    "cache_hit": "False",
                    "dynamic_test": "False",
                    "failure_kind": "",
                },
            ]
        )


def _write_p5_candidates(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["program", "candidate_id", "source"])
        writer.writeheader()
        writer.writerows(
            [
                {"program": "tiny", "candidate_id": "tiny__anchor", "source": "anchor"},
                {"program": "tiny", "candidate_id": "tiny__swap", "source": "single_swap"},
            ]
        )


def _write_p7b_candidates(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["program", "candidate_id", "source"])
        writer.writeheader()
        writer.writerows(
            [
                {"program": "tiny", "candidate_id": "tiny__anchor", "source": "anchor"},
                {"program": "tiny", "candidate_id": "tiny__depth2", "source": "two_swap"},
            ]
        )


def _write_pipeline_runs(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "same_as_anchor", "failure_kind"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "same_as_anchor": "True",
                    "failure_kind": "",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap",
                    "same_as_anchor": "False",
                    "failure_kind": "",
                },
            ]
        )


def _write_object_size(path: Path, *, source: str, delta: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "text_delta",
                "text_delta_pct",
                "compile_failure_kind",
                "size_failure_kind",
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
                    "compile_failure_kind": "",
                    "size_failure_kind": "",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__candidate",
                    "source": source,
                    "text_delta": delta,
                    "text_delta_pct": f"{float(delta):.6f}",
                    "compile_failure_kind": "",
                    "size_failure_kind": "",
                },
            ]
        )


def _write_compare(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "llc_direction",
                "clang_direction",
                "direction_agree",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__swap",
                    "source": "single_swap",
                    "llc_direction": "smaller",
                    "clang_direction": "smaller",
                    "direction_agree": "True",
                },
                {
                    "program": "tiny",
                    "candidate_id": "tiny__depth2",
                    "source": "two_swap",
                    "llc_direction": "equal",
                    "clang_direction": "larger",
                    "direction_agree": "False",
                },
            ]
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
