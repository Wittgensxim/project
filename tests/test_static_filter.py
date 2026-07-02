import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class StaticFilterTests(unittest.TestCase):
    def test_passspec_covers_scalar_pipeline_passes(self):
        from ecpor.static_filter import load_passspec, load_pipeline_config

        pipeline = load_pipeline_config("configs/pipeline_scalar.yaml")
        passspec = load_passspec("configs/passspec.yaml")

        self.assertEqual(len(pipeline["passes"]), 8)
        self.assertEqual(set(passspec), set(pipeline["passes"]))
        self.assertEqual(passspec["sroa"]["level"], "function")
        self.assertIn("has_alloca", passspec["sroa"]["requires_any"])

    def test_enumerate_unordered_pairs_returns_full_8_pass_universe(self):
        from ecpor.static_filter import enumerate_unordered_pairs

        pairs = enumerate_unordered_pairs(
            [
                "sroa",
                "early-cse",
                "instcombine",
                "simplifycfg",
                "reassociate",
                "gvn",
                "dce",
                "adce",
            ]
        )

        self.assertEqual(len(pairs), 28)
        self.assertEqual(pairs[0], ("sroa", "early-cse"))
        self.assertEqual(pairs[-1], ("dce", "adce"))

    def test_classify_pair_uses_feature_gates_and_producer_consumer_hints(self):
        from ecpor.static_filter import classify_pair

        passspec = {
            "sroa": {
                "level": "function",
                "requires_any": ["has_alloca"],
                "may_consume": ["alloca"],
                "may_produce": ["scalar_value"],
                "tags": ["scalar"],
            },
            "early-cse": {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": ["scalar_value"],
                "may_produce": ["dead_instruction"],
                "tags": ["scalar"],
            },
            "module-pass": {
                "level": "module",
                "requires_any": ["instruction"],
                "may_consume": [],
                "may_produce": [],
                "tags": [],
            },
        }

        candidate = classify_pair(
            "sroa",
            "early-cse",
            passspec,
            program_features={"has_alloca": True, "num_instructions": 4},
            distance=1,
            window_size=2,
        )
        low_priority = classify_pair(
            "sroa",
            "early-cse",
            passspec,
            program_features={"has_alloca": False, "num_instructions": 4},
            distance=1,
            window_size=2,
        )
        frozen = classify_pair(
            "sroa",
            "module-pass",
            passspec,
            program_features={"has_alloca": True, "num_instructions": 4},
            distance=1,
            window_size=2,
        )

        self.assertEqual(candidate["decision"], "candidate")
        self.assertIn("producer_consumer", candidate["reason"])
        self.assertEqual(candidate["producer_consumer"], "sroa->early-cse:scalar_value")
        self.assertEqual(low_priority["decision"], "low_priority")
        self.assertIn("feature_gate_missing", low_priority["reason"])
        self.assertEqual(frozen["decision"], "frozen")
        self.assertIn("level_mismatch", frozen["reason"])

    def test_build_static_filter_decisions_outputs_candidate_hints_only(self):
        from ecpor.static_filter import build_static_filter_decisions

        passspec = {
            "a": {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": [],
                "may_produce": ["x"],
                "tags": ["scalar"],
            },
            "b": {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": ["x"],
                "may_produce": [],
                "tags": ["scalar"],
            },
            "c": {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": [],
                "may_produce": [],
                "tags": ["cfg"],
            },
        }

        decisions = build_static_filter_decisions(
            ["a", "b", "c"],
            passspec,
            program_features={"num_instructions": 1},
            window_size=1,
        )

        self.assertEqual(len(decisions), 3)
        self.assertEqual(decisions[0]["decision"], "candidate")
        self.assertTrue(
            all(row["decision"] in {"candidate", "low_priority", "frozen"} for row in decisions)
        )
        self.assertFalse(any(row["decision"] == "certified_independent" for row in decisions))

    def test_build_static_filter_decisions_for_programs_can_differ_by_program(self):
        from ecpor.static_filter import build_static_filter_decisions_for_programs

        passspec = {
            "sroa": {
                "level": "function",
                "requires_any": ["has_alloca"],
                "may_consume": ["alloca"],
                "may_produce": ["scalar_value"],
                "tags": ["scalar"],
            },
            "early-cse": {
                "level": "function",
                "requires_any": ["instruction"],
                "may_consume": ["scalar_value"],
                "may_produce": ["dead_instruction"],
                "tags": ["scalar"],
            },
        }

        decisions = build_static_filter_decisions_for_programs(
            ["sroa", "early-cse"],
            passspec,
            program_features_by_name={
                "with_alloca": {"has_alloca": True, "num_instructions": 3},
                "without_alloca": {"has_alloca": False, "num_instructions": 3},
            },
            window_size=1,
        )

        self.assertEqual(len(decisions), 2)
        self.assertEqual(decisions[0]["program"], "with_alloca")
        self.assertEqual(decisions[0]["decision"], "candidate")
        self.assertEqual(decisions[1]["program"], "without_alloca")
        self.assertEqual(decisions[1]["decision"], "low_priority")

    def test_p8b_misc8_program_preset_scans_ingested_inputs(self):
        import argparse

        from ecpor.static_filter import _load_program_feature_map_for_args

        args = argparse.Namespace(features_json=None, program_preset="p8b-misc8")

        feature_map, program_count = _load_program_feature_map_for_args(
            args,
            observed_rows=[],
        )

        self.assertEqual(program_count, 8)
        self.assertEqual(len(feature_map), 8)
        self.assertIn("testsuite_misc_ffbench", feature_map)
        self.assertGreater(feature_map["testsuite_misc_ffbench"]["num_instructions"], 0)

    def test_benchmark_config_scans_program_feature_map(self):
        import argparse

        from ecpor.static_filter import _load_program_feature_map_for_args

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            first = tmp_path / "first.ll"
            second = tmp_path / "second.ll"
            config = tmp_path / "benchmarks.yaml"
            first.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
            second.write_text("define void @g() {\nentry:\n  br label %exit\nexit:\n  ret void\n}\n", encoding="utf-8")
            config.write_text(
                f"""
programs:
  - id: configured_first
    ir: {first.as_posix()}
  - id: configured_second
    ir: {second.as_posix()}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                features_json=None,
                program_preset=None,
                benchmark_config=config,
            )

            feature_map, program_count = _load_program_feature_map_for_args(
                args,
                observed_rows=[],
            )

        self.assertEqual(program_count, 2)
        self.assertEqual(set(feature_map), {"configured_first", "configured_second"})
        self.assertGreater(feature_map["configured_first"]["num_instructions"], 0)

    def test_real_passspec_marks_observed_false_negative_pairs_candidate(self):
        from ecpor.static_filter import classify_pair, load_passspec

        passspec = load_passspec("configs/passspec.yaml")
        features = {
            "has_alloca": True,
            "has_branch": True,
            "has_load_store": True,
            "num_instructions": 100,
        }

        sroa_simplifycfg = classify_pair(
            "sroa",
            "simplifycfg",
            passspec,
            program_features=features,
            distance=3,
            window_size=7,
        )
        simplifycfg_gvn = classify_pair(
            "simplifycfg",
            "gvn",
            passspec,
            program_features=features,
            distance=2,
            window_size=7,
        )
        early_cse_simplifycfg = classify_pair(
            "early-cse",
            "simplifycfg",
            passspec,
            program_features=features,
            distance=2,
            window_size=7,
        )
        sroa_dce = classify_pair(
            "sroa",
            "dce",
            passspec,
            program_features=features,
            distance=6,
            window_size=7,
        )
        sroa_adce = classify_pair(
            "sroa",
            "adce",
            passspec,
            program_features=features,
            distance=7,
            window_size=7,
        )

        self.assertEqual(sroa_simplifycfg["decision"], "candidate")
        self.assertEqual(simplifycfg_gvn["decision"], "candidate")
        self.assertEqual(early_cse_simplifycfg["decision"], "candidate")
        self.assertEqual(sroa_dce["decision"], "candidate")
        self.assertEqual(sroa_dce["reason"], "producer_consumer")
        self.assertEqual(sroa_adce["decision"], "candidate")
        self.assertEqual(sroa_adce["reason"], "producer_consumer")

    def test_evaluate_static_filter_reports_recall_reduction_and_false_negatives(self):
        from ecpor.static_filter import evaluate_static_filter, build_static_filter_report

        decisions = [
            _decision("sroa", "early-cse", "candidate"),
            _decision("simplifycfg", "instcombine", "low_priority"),
            _decision("dce", "adce", "low_priority"),
        ]
        observed_rows = [
            _summary_row("p1", "sroa", "early-cse", "not_certified_independent"),
            _summary_row("p2", "simplifycfg", "instcombine", "not_certified_independent"),
            _summary_row("p1", "dce", "adce", "certified_independent"),
        ]

        metrics = evaluate_static_filter(decisions, observed_rows)
        report = build_static_filter_report(
            pipeline_name="mvp",
            pass_count=3,
            program_count=2,
            decisions=decisions,
            observed_rows=observed_rows,
            metrics=metrics,
        )

        self.assertEqual(metrics["all_pairs"], 3)
        self.assertEqual(metrics["candidate_pairs"], 1)
        self.assertEqual(metrics["observed_interacting"], 2)
        self.assertEqual(metrics["static_false_negative_observed"], 1)
        self.assertAlmostEqual(metrics["static_candidate_recall"], 0.5)
        self.assertAlmostEqual(metrics["static_candidate_reduction"], 2 / 3)
        self.assertIn("StaticCandidateRecall: 50.00%", report)
        self.assertIn("simplifycfg,instcombine", report)
        self.assertIn("Static filter is candidate generation only.", report)

    def test_evaluate_static_filter_uses_program_specific_decisions(self):
        from ecpor.static_filter import evaluate_static_filter, build_static_filter_report

        decisions = [
            _decision("sroa", "early-cse", "candidate", program="p1"),
            _decision("sroa", "early-cse", "low_priority", program="p2"),
        ]
        observed_rows = [
            _summary_row("p1", "sroa", "early-cse", "not_certified_independent"),
            _summary_row("p2", "sroa", "early-cse", "not_certified_independent"),
        ]

        metrics = evaluate_static_filter(decisions, observed_rows)
        report = build_static_filter_report(
            pipeline_name="mvp",
            pass_count=2,
            program_count=2,
            decisions=decisions,
            observed_rows=observed_rows,
            metrics=metrics,
            program_groups={
                "Calibration": ["p1"],
                "Hold-out": ["p2"],
            },
        )

        self.assertEqual(metrics["all_pairs"], 1)
        self.assertEqual(metrics["decision_rows"], 2)
        self.assertEqual(metrics["static_false_negative_observed"], 1)
        self.assertAlmostEqual(metrics["static_candidate_recall"], 0.5)
        self.assertAlmostEqual(metrics["macro_static_candidate_recall"], 0.5)
        self.assertEqual(metrics["per_program"]["p1"]["static_false_negative_observed"], 0)
        self.assertEqual(metrics["per_program"]["p2"]["static_false_negative_observed"], 1)
        self.assertIn("Per-program static decisions:", report)
        self.assertIn("p1: candidate=1 low_priority=0 frozen=0", report)
        self.assertIn("p2: candidate=0 low_priority=1 frozen=0", report)
        self.assertIn("Calibration:", report)
        self.assertIn("Hold-out:", report)

    def test_main_writes_decisions_and_report(self):
        from ecpor.static_filter import main

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pipeline = tmp_path / "pipeline.yaml"
            passspec = tmp_path / "passspec.yaml"
            features = tmp_path / "features.json"
            observed = tmp_path / "cert_summary.csv"
            decisions_csv = tmp_path / "static_filter_decisions.csv"
            report_md = tmp_path / "static_filter_report.md"

            pipeline.write_text("name: test\npasses:\n  - a\n  - b\n", encoding="utf-8")
            passspec.write_text(
                """
passes:
  a:
    level: function
    requires_any:
      - instruction
    may_consume: []
    may_produce:
      - x
    tags:
      - scalar
  b:
    level: function
    requires_any:
      - instruction
    may_consume:
      - x
    may_produce: []
    tags:
      - scalar
""".strip(),
                encoding="utf-8",
            )
            features.write_text('{"num_instructions": 1}', encoding="utf-8")
            with observed.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "program",
                        "pair_a",
                        "pair_b",
                        "label",
                        "reproduced",
                        "hard_equal",
                    ],
                )
                writer.writeheader()
                writer.writerow(_summary_row("p", "a", "b", "not_certified_independent"))

            exit_code = main(
                [
                    "--pipeline",
                    str(pipeline),
                    "--passspec",
                    str(passspec),
                    "--features-json",
                    str(features),
                    "--observed-summary",
                    str(observed),
                    "--out-csv",
                    str(decisions_csv),
                    "--out-report",
                    str(report_md),
                    "--window-size",
                    "1",
                    "--mode",
                    "per-program",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("candidate", decisions_csv.read_text(encoding="utf-8"))
            self.assertIn("StaticCandidateRecall: 100.00%", report_md.read_text(encoding="utf-8"))
            self.assertIn("program", decisions_csv.read_text(encoding="utf-8").splitlines()[0])


def _decision(
    pair_a: str, pair_b: str, decision: str, *, program: str = ""
) -> dict[str, str]:
    return {
        "program": program,
        "pair_a": pair_a,
        "pair_b": pair_b,
        "decision": decision,
        "reason": decision,
        "level_a": "function",
        "level_b": "function",
        "shared_tags": "",
        "producer_consumer": "",
        "program_feature_gate": "satisfied",
    }


def _summary_row(program: str, pair_a: str, pair_b: str, label: str) -> dict[str, str]:
    return {
        "program": program,
        "pair_a": pair_a,
        "pair_b": pair_b,
        "label": label,
        "reproduced": "True",
        "hard_equal": str(label == "certified_independent"),
    }


if __name__ == "__main__":
    unittest.main()
