import csv
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CoreEvidenceMisc8Tests(unittest.TestCase):
    def test_builds_misc8_depth1_supplement(self):
        from ecpor.core_evidence_misc8 import run_core_evidence_misc8

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "misc8_core"
            p4_attempts = root / "attempts.csv"
            p5_candidates = root / "candidates.csv"
            p6_object_size = root / "object_size.csv"
            p8a_compare = root / "compare.csv"
            depth1_report = root / "depth1_analysis_report.md"
            attribution_report = root / "attribution_report.md"
            feature_deltas = root / "feature_deltas.csv"
            opcode_delta = root / "opcode_delta.csv"
            attribution_object_size = root / "attribution_object_size.csv"
            _write_attempts(p4_attempts)
            _write_candidates(p5_candidates)
            _write_object_size(p6_object_size)
            _write_compare(p8a_compare)
            _write_depth1_report(depth1_report)
            _write_attribution_report(attribution_report)
            _write_feature_deltas(feature_deltas)
            _write_opcode_delta(opcode_delta)
            _write_attribution_object_size(attribution_object_size)

            result = run_core_evidence_misc8(
                p4_attempts_csv=p4_attempts,
                p5_candidates_csv=p5_candidates,
                p6_object_size_csv=p6_object_size,
                p8a_compare_csv=p8a_compare,
                depth1_analysis_report=depth1_report,
                output_dir=output_dir,
                attribution_report=attribution_report,
                attribution_feature_deltas_csv=feature_deltas,
                attribution_opcode_delta_csv=opcode_delta,
                attribution_object_size_csv=attribution_object_size,
            )
            validation = _read_csv(output_dir / "misc8_validation_funnel.csv")
            propagation = _read_csv(output_dir / "misc8_candidate_propagation_funnel.csv")
            objective = _read_csv(output_dir / "misc8_objective_layer_summary.csv")
            attribution = _read_csv(output_dir / "misc8_attribution_summary.csv")
            report = (output_dir / "ecpor_misc8_depth1_evidence_report.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(validation[0]["attempted_swaps"], "3")
        self.assertEqual(validation[0]["certified_independent_events"], "1")
        self.assertEqual(propagation[0]["single_swap_candidates"], "2")
        self.assertEqual(propagation[0]["object_size_evaluated_candidates"], "2")
        self.assertEqual(objective[0]["both_smaller"], "1")
        self.assertEqual(attribution[0]["program"], "testsuite_misc_ffbench")
        self.assertEqual(attribution[0]["pair"], "instcombine,simplifycfg")
        self.assertEqual(result.summary["BothSmallerPrograms"], 1)
        self.assertIn("Misc8 repeats the Stanford pattern", report)
        self.assertIn("AttributionCases: 1", report)


def _write_attempts(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["program", "action", "label", "dynamic_test", "cache_hit"])
        writer.writeheader()
        writer.writerows(
            [
                {"program": "ffbench", "action": "dynamic_test", "label": "certified_independent", "dynamic_test": "True", "cache_hit": "False"},
                {"program": "ffbench", "action": "dynamic_test", "label": "not_certified_independent", "dynamic_test": "True", "cache_hit": "False"},
                {"program": "other", "action": "skipped_low_priority", "label": "skipped_low_priority", "dynamic_test": "False", "cache_hit": "False"},
            ]
        )


def _write_candidates(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["program", "candidate_id", "source"])
        writer.writeheader()
        writer.writerows(
            [
                {"program": "ffbench", "candidate_id": "ffbench__anchor", "source": "anchor"},
                {"program": "ffbench", "candidate_id": "ffbench__swap", "source": "single_swap"},
                {"program": "other", "candidate_id": "other__swap", "source": "single_swap"},
            ]
        )


def _write_object_size(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "source", "text_delta", "text_delta_pct", "compile_failure_kind", "size_failure_kind"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {"program": "ffbench", "candidate_id": "ffbench__swap", "source": "single_swap", "text_delta": "-16", "text_delta_pct": "-1.000000", "compile_failure_kind": "", "size_failure_kind": ""},
                {"program": "other", "candidate_id": "other__swap", "source": "single_swap", "text_delta": "0", "text_delta_pct": "0.000000", "compile_failure_kind": "", "size_failure_kind": ""},
            ]
        )


def _write_compare(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "source", "llc_direction", "clang_direction", "direction_agree"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {"program": "ffbench", "candidate_id": "ffbench__swap", "source": "single_swap", "llc_direction": "smaller", "clang_direction": "smaller", "direction_agree": "True"},
                {"program": "other", "candidate_id": "other__swap", "source": "single_swap", "llc_direction": "equal", "clang_direction": "equal", "direction_agree": "True"},
            ]
        )


def _write_depth1_report(path: Path) -> None:
    _write_text(
        path,
        textwrap.dedent(
            """
            # Misc8 Depth1 Analysis

            Depth1BothSmallerPrograms: 1
            IRDifferentButTextEqualRate: 50.00%
            """
        ).strip()
        + "\n",
    )


def _write_attribution_report(path: Path) -> None:
    _write_text(
        path,
        textwrap.dedent(
            """
            # Effect Attribution: testsuite_misc_ffbench

            Program: testsuite_misc_ffbench
            Pair: instcombine,simplifycfg
            LocalInstructionDelta: -1
            FinalInstructionDelta: -1
            FinalOpcodeDeltaNonZero: num_add_delta=-1
            BothCodegenSmaller: True
            """
        ).strip()
        + "\n",
    )


def _write_feature_deltas(path: Path) -> None:
    _write_text(
        path,
        "comparison,num_instructions_delta\nlocal_AB_vs_BA,-1\nfinal_AB_vs_BA,-1\n",
    )


def _write_opcode_delta(path: Path) -> None:
    _write_text(path, "comparison,num_add_delta\nfinal_AB_vs_BA,-1\n")


def _write_attribution_object_size(path: Path) -> None:
    _write_text(
        path,
        "program,state_name,compile_mode,text_delta_pct,direction\n"
        "testsuite_misc_ffbench,BA_final,llc,-1.000000,smaller\n"
        "testsuite_misc_ffbench,BA_final,clang,-0.100000,smaller\n",
    )


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
