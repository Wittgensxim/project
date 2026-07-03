import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PairFamilyAnalysisTests(unittest.TestCase):
    def test_builds_direction_insensitive_pair_family_summary(self):
        from ecpor.pair_family_analysis import build_pair_family_analysis

        analysis = build_pair_family_analysis(
            pair_a="instcombine",
            pair_b="simplifycfg",
            full_matrix_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "pair_a": "instcombine",
                    "pair_b": "simplifycfg",
                    "label": "not_certified_independent",
                    "hard_equal": "False",
                    "feature_delta": '{"num_instructions": -1}',
                    "cert_id": "cert-a",
                },
                {
                    "benchmark_set": "SetA",
                    "program": "prog_b",
                    "pair_a": "simplifycfg",
                    "pair_b": "instcombine",
                    "label": "certified_independent",
                    "hard_equal": "True",
                    "feature_delta": "{}",
                    "cert_id": "cert-b",
                },
                {
                    "benchmark_set": "SetA",
                    "program": "prog_c",
                    "pair_a": "sroa",
                    "pair_b": "dce",
                    "label": "not_certified_independent",
                },
            ],
            prefix_attempt_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "pass_a": "simplifycfg",
                    "pass_b": "instcombine",
                    "label": "not_certified_independent",
                    "state_hash": "state-a",
                    "cert_id": "prefix-a",
                },
                {
                    "benchmark_set": "SetA",
                    "program": "prog_b",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                    "label": "certified_independent",
                    "state_hash": "state-b",
                    "cert_id": "prefix-b",
                },
            ],
            candidate_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "candidate_id": "prog_a__swap_2__instcombine__simplifycfg",
                    "source": "single_swap",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                    "prefix_state_hash": "state-a",
                    "validation_label": "not_certified_independent",
                    "cert_id": "prefix-a",
                }
            ],
            object_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "candidate_id": "prog_a__swap_2__instcombine__simplifycfg",
                    "source": "single_swap",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                    "p5_same_as_anchor": "False",
                    "text_delta_pct": "-2.000000",
                }
            ],
            codegen_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "candidate_id": "prog_a__swap_2__instcombine__simplifycfg",
                    "depth": "1",
                    "source": "single_swap",
                    "llc_direction": "smaller",
                    "clang_direction": "smaller",
                    "llc_text_delta_pct": "-2.000000",
                    "clang_text_delta_pct": "-1.000000",
                    "direction_agree": "True",
                }
            ],
            attribution_rows=[
                {
                    "benchmark_set": "SetA",
                    "program": "prog_a",
                    "pair": "simplifycfg,instcombine",
                    "opcode_delta": "num_select_delta=-1;num_or_delta=1",
                    "final_feature_delta": "num_instructions_delta=0",
                    "llc_text_delta_pct": "-2.000000",
                    "clang_text_delta_pct": "-1.000000",
                    "evidence_level": "observed attribution, not causal proof",
                }
            ],
        )

        self.assertEqual(analysis["summary"]["PairFamily"], "instcombine,simplifycfg")
        self.assertEqual(analysis["summary"]["Programs"], 2)
        self.assertEqual(analysis["summary"]["FullMatrixCertified"], 1)
        self.assertEqual(analysis["summary"]["FullMatrixNotCertified"], 1)
        self.assertEqual(analysis["summary"]["PrefixCertified"], 1)
        self.assertEqual(analysis["summary"]["PrefixNotCertified"], 1)
        self.assertEqual(analysis["summary"]["OneSwapCandidates"], 1)
        self.assertEqual(analysis["summary"]["FinalIrDifferent"], 1)
        self.assertEqual(analysis["summary"]["BothSmallerPrograms"], 1)
        self.assertEqual(analysis["summary"]["AttributionCases"], 1)
        self.assertEqual(analysis["summary"]["SelectRelatedAttributionCases"], 1)

    def test_program_summary_keeps_input_prefix_and_objective_layers_separate(self):
        from ecpor.pair_family_analysis import build_pair_family_analysis

        analysis = build_pair_family_analysis(
            pair_a="instcombine",
            pair_b="simplifycfg",
            full_matrix_rows=[
                {
                    "program": "testsuite_stanford_queens",
                    "pair_a": "instcombine",
                    "pair_b": "simplifycfg",
                    "label": "certified_independent",
                    "hard_equal": "True",
                }
            ],
            prefix_attempt_rows=[
                {
                    "program": "testsuite_stanford_queens",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                    "label": "not_certified_independent",
                }
            ],
            candidate_rows=[
                {
                    "program": "testsuite_stanford_queens",
                    "candidate_id": "queens__swap_2__instcombine__simplifycfg",
                    "source": "single_swap",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                }
            ],
            object_rows=[
                {
                    "program": "testsuite_stanford_queens",
                    "candidate_id": "queens__swap_2__instcombine__simplifycfg",
                    "source": "single_swap",
                    "pass_a": "instcombine",
                    "pass_b": "simplifycfg",
                    "p5_same_as_anchor": "False",
                }
            ],
            codegen_rows=[
                {
                    "program": "testsuite_stanford_queens",
                    "candidate_id": "queens__swap_2__instcombine__simplifycfg",
                    "depth": "1",
                    "source": "single_swap",
                    "llc_direction": "smaller",
                    "clang_direction": "smaller",
                    "llc_text_delta_pct": "-4.4",
                    "clang_text_delta_pct": "-1.6",
                    "direction_agree": "True",
                }
            ],
            attribution_rows=[],
        )

        row = analysis["program_summary"][0]
        self.assertEqual(row["benchmark_set"], "Stanford-8")
        self.assertEqual(row["full_matrix_label"], "certified_independent")
        self.assertEqual(row["prefix_label"], "not_certified_independent")
        self.assertEqual(row["generated_one_swap"], "True")
        self.assertEqual(row["final_ir_different"], "True")
        self.assertEqual(row["llc_direction"], "smaller")
        self.assertEqual(row["clang_direction"], "smaller")
        self.assertEqual(row["both_smaller"], "True")

    def test_attribution_compare_extracts_removed_added_opcodes(self):
        from ecpor.pair_family_analysis import build_pair_family_analysis

        analysis = build_pair_family_analysis(
            pair_a="instcombine",
            pair_b="simplifycfg",
            full_matrix_rows=[],
            prefix_attempt_rows=[],
            candidate_rows=[],
            object_rows=[],
            codegen_rows=[],
            attribution_rows=[
                {
                    "program": "testsuite_misc_ffbench",
                    "pair": "instcombine,simplifycfg",
                    "final_opcode_delta_nonzero": "num_select_delta=-1;num_or_delta=1",
                    "final_instruction_delta": "0",
                    "llc_text_delta_pct": "-1.005025",
                    "clang_text_delta_pct": "-0.127280",
                    "both_codegen_smaller": "True",
                    "evidence_level": "observed_attribution_not_causal_proof",
                }
            ],
        )

        row = analysis["attribution_compare"][0]
        self.assertEqual(row["benchmark_set"], "Misc8")
        self.assertEqual(row["removed_opcodes"], "select")
        self.assertEqual(row["added_opcodes"], "or")
        self.assertEqual(row["net_instruction_delta"], "0")
        self.assertEqual(row["evidence_level"], "observed_attribution_not_causal_proof")

    def test_writes_pair_family_outputs(self):
        from ecpor.pair_family_analysis import write_pair_family_analysis_outputs

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            outputs = write_pair_family_analysis_outputs(
                output_dir=out_dir,
                pair_a="instcombine",
                pair_b="simplifycfg",
                full_matrix_rows=[
                    {
                        "program": "prog",
                        "benchmark_set": "SetA",
                        "pair_a": "instcombine",
                        "pair_b": "simplifycfg",
                        "label": "not_certified_independent",
                    }
                ],
                prefix_attempt_rows=[],
                candidate_rows=[],
                object_rows=[],
                codegen_rows=[],
                attribution_rows=[],
            )
            with outputs["program_summary"].open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            analysis = json.loads(outputs["analysis_json"].read_text(encoding="utf-8"))
            report = outputs["report"].read_text(encoding="utf-8")

        self.assertEqual(rows[0]["program"], "prog")
        self.assertEqual(analysis["stage"], "P14")
        self.assertIn("NewExperiments: False", report)
        self.assertIn("not a global ordering rule", report)
        self.assertIn("pair_family_events.csv", {path.name for path in outputs.values()})


if __name__ == "__main__":
    unittest.main()
