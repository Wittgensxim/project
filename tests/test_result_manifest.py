import csv
import hashlib
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ResultManifestTests(unittest.TestCase):
    def test_builds_p7a_manifest_from_outputs_and_hashes_files(self):
        from ecpor.result_manifest import build_p7a_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p5_candidates = root / "p5_candidates.csv"
            p5_pipeline_runs = root / "p5_pipeline_runs.csv"
            p6_object_size = root / "p6_object_size.csv"
            passspec = root / "passspec.yaml"
            opt = root / "opt.exe"
            llc = root / "llc.exe"
            llvm_size = root / "llvm-size.exe"
            out_dir = root / "p7a"
            cert_dir = root / "certs"
            out_dir.mkdir()
            cert_dir.mkdir()
            _write_text(p5_candidates, "program,candidate_id,source,candidate_pipeline\n")
            _write_text(p5_pipeline_runs, "program,candidate_id,pipeline\n")
            _write_text(passspec, "passes: {}\n")
            _write_text(opt, "opt")
            _write_text(llc, "llc")
            _write_text(llvm_size, "size")
            _write_p6_object_size(p6_object_size)
            _write_p7a_outputs(out_dir)
            expected_p6_object_size_sha256 = _sha256_text(p6_object_size)
            expected_opt_sha256 = _sha256_text(opt)

            manifest = build_p7a_manifest(
                p5_candidates_csv=p5_candidates,
                p5_pipeline_runs_csv=p5_pipeline_runs,
                p6_object_size_csv=p6_object_size,
                passspec_path=passspec,
                output_dir=out_dir,
                cert_dir=cert_dir,
                opt_path=opt,
                llc_path=llc,
                llvm_size_path=llvm_size,
                repo_root=root,
                result_generated_from_commit="abc123",
                stage="P7b",
            )
            manifest_path = root / "manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P7b")
        self.assertEqual(loaded["result_generated_from_commit"], "abc123")
        self.assertEqual(
            loaded["sha256"]["p6_object_size_csv"], expected_p6_object_size_sha256
        )
        self.assertEqual(loaded["sha256"]["opt"], expected_opt_sha256)
        self.assertEqual(loaded["summary"]["static_candidate_second_swaps"], 7)
        self.assertEqual(loaded["summary"]["unique_depth2_candidates"], 3)
        self.assertEqual(loaded["summary"]["selected_seed_candidates"], 3)
        self.assertEqual(loaded["summary"]["budget_skipped_depth2_candidates"], 2)
        self.assertIn("two_swap_seeds_csv", loaded["outputs"])
        self.assertIn("two_swap_seeds_csv", loaded["sha256"])
        self.assertNotIn("ecpor_git_commit", loaded["summary"])
        self.assertNotIn("p5_candidates_csv", loaded["summary"])
        self.assertEqual(loaded["seed"]["candidate_id"], "seed")
        self.assertEqual(
            loaded["depth2_candidates"][0]["text_delta_pct_vs_anchor"], -10.0
        )
        self.assertEqual(loaded["depth2_candidates"][0]["delta_pct_vs_parent"], 0.0)

    def test_builds_p7b_analysis_manifest_from_analysis_outputs(self):
        from ecpor.result_manifest import build_p7b_analysis_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p7_dir = root / "p7b"
            analysis_dir = root / "analysis"
            p7_dir.mkdir()
            analysis_dir.mkdir()
            p6_object_size = root / "p6_object_size.csv"
            _write_text(p6_object_size, "program,candidate_id,source,text_delta_pct\n")
            _write_p7b_base_outputs(p7_dir)
            _write_p7b_analysis_outputs(analysis_dir)

            manifest = build_p7b_analysis_manifest(
                p7_dir=p7_dir,
                p6_object_size_csv=p6_object_size,
                analysis_dir=analysis_dir,
                repo_root=root,
                result_generated_from_commit="def456",
            )
            manifest_path = root / "analysis_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P7b.5")
        self.assertEqual(loaded["result_generated_from_commit"], "def456")
        self.assertIn("p7b_program_summary_csv", loaded["outputs"])
        self.assertIn("p7b_cache_audit_csv", loaded["outputs"])
        self.assertIn("p7b_analysis_report", loaded["sha256"])
        self.assertEqual(loaded["summary"]["Depth2SmallerText"], 3)
        self.assertEqual(loaded["summary"]["DuplicateSequenceRate"], "47.62%")
        self.assertEqual(loaded["summary"]["Depth2SmallerFromSameParent"], 3)
        self.assertNotIn("p1", loaded["summary"])

    def test_builds_p8a_codegen_sensitivity_manifest(self):
        from ecpor.result_manifest import (
            build_p8a_codegen_sensitivity_manifest,
            write_manifest,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p6_object_size = root / "p6_object_size.csv"
            p7_object_size = root / "p7_object_size.csv"
            clang = root / "clang.exe"
            llvm_size = root / "llvm-size.exe"
            out_dir = root / "p8a"
            out_dir.mkdir()
            _write_text(p6_object_size, "program,candidate_id,source\n")
            _write_text(p7_object_size, "program,candidate_id,source\n")
            _write_text(clang, "clang")
            _write_text(llvm_size, "size")
            _write_p8a_outputs(out_dir)

            manifest = build_p8a_codegen_sensitivity_manifest(
                p6_object_size_csv=p6_object_size,
                p7_object_size_csv=p7_object_size,
                output_dir=out_dir,
                clang_path=clang,
                llvm_size_path=llvm_size,
                repo_root=root,
                result_generated_from_commit="fed789",
            )
            manifest_path = root / "p8a_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8a")
        self.assertEqual(loaded["result_generated_from_commit"], "fed789")
        self.assertIn("p8a_clang_object_size_csv", loaded["outputs"])
        self.assertIn("p8a_codegen_direction_compare_csv", loaded["outputs"])
        self.assertIn("clang", loaded["sha256"])
        self.assertEqual(loaded["summary"]["IRInputs"], 46)
        self.assertEqual(loaded["summary"]["DirectionAgreementRate"], "100.00%")
        self.assertNotIn("testsuite_stanford_queens", loaded["summary"])

    def test_builds_core_evidence_manifest(self):
        from ecpor.result_manifest import build_core_evidence_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p4_attempts = root / "p4_attempts.csv"
            p5_candidates = root / "p5_candidates.csv"
            p5_pipeline_runs = root / "p5_pipeline_runs.csv"
            p6_object_size = root / "p6_object_size.csv"
            p7b_attempts = root / "p7b_attempts.csv"
            p7b_candidates = root / "p7b_candidates.csv"
            p7b_object_size = root / "p7b_object_size.csv"
            p7b_analysis_report = root / "p7b_analysis_report.md"
            p8a_compare = root / "p8a_compare.csv"
            p8c_attribution_report = root / "p8c_attribution_report.md"
            p8c_feature_deltas = root / "p8c_feature_deltas.csv"
            p8c_opcode_delta = root / "p8c_opcode_delta.csv"
            p8c_object_size = root / "p8c_object_size.csv"
            out_dir = root / "core"
            out_dir.mkdir()
            for path in [
                p4_attempts,
                p5_candidates,
                p5_pipeline_runs,
                p6_object_size,
                p7b_attempts,
                p7b_candidates,
                p7b_object_size,
                p8a_compare,
            ]:
                _write_text(path, "name\nrow\n")
            _write_text(p7b_analysis_report, "Depth2SmallerText: 3\n")
            _write_text(p8c_attribution_report, "Program: testsuite_stanford_queens\n")
            _write_text(p8c_feature_deltas, "comparison,num_instructions_delta\n")
            _write_text(p8c_opcode_delta, "comparison,num_add_delta\n")
            _write_text(p8c_object_size, "compile_mode,text_delta_pct\n")
            _write_core_evidence_outputs(out_dir)

            manifest = build_core_evidence_manifest(
                p4_attempts_csv=p4_attempts,
                p5_candidates_csv=p5_candidates,
                p5_pipeline_runs_csv=p5_pipeline_runs,
                p6_object_size_csv=p6_object_size,
                p7b_attempts_csv=p7b_attempts,
                p7b_candidates_csv=p7b_candidates,
                p7b_object_size_csv=p7b_object_size,
                p7b_analysis_report=p7b_analysis_report,
                p8a_compare_csv=p8a_compare,
                p8c_attribution_report=p8c_attribution_report,
                p8c_feature_deltas_csv=p8c_feature_deltas,
                p8c_opcode_delta_csv=p8c_opcode_delta,
                p8c_object_size_csv=p8c_object_size,
                output_dir=out_dir,
                repo_root=root,
                result_generated_from_commit="abc999",
            )
            manifest_path = root / "core_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8c.2")
        self.assertEqual(loaded["result_generated_from_commit"], "abc999")
        self.assertIn("ecpor_core_evidence_report", loaded["outputs"])
        self.assertIn("ecpor_validation_funnel_csv", loaded["outputs"])
        self.assertIn("ecpor_candidate_propagation_funnel_csv", loaded["outputs"])
        self.assertIn("ecpor_objective_layer_summary_csv", loaded["outputs"])
        self.assertIn("ecpor_attribution_summary_csv", loaded["outputs"])
        self.assertIn("p8c_attribution_report", loaded["inputs"])
        self.assertIn("p8c_feature_deltas_csv", loaded["inputs"])
        self.assertIn("p8c_opcode_delta_csv", loaded["inputs"])
        self.assertIn("p8c_object_size_csv", loaded["inputs"])
        self.assertIn("ecpor_core_evidence_report", loaded["sha256"])
        self.assertIn("p8c_attribution_report", loaded["sha256"])
        self.assertIn("ecpor_attribution_summary_csv", loaded["sha256"])
        self.assertEqual(loaded["summary"]["DirectionAgreementRate"], "68.42%")
        self.assertEqual(loaded["summary"]["SmallerUnderBothCount"], 4)
        self.assertEqual(loaded["summary"]["AttributionCases"], 1)
        self.assertNotIn("queens", loaded["summary"])

    def test_builds_p8c_queens_attribution_manifest(self):
        from ecpor.result_manifest import (
            build_queens_effect_attribution_manifest,
            write_manifest,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_ir = root / "testsuite_stanford_queens.ll"
            opt = root / "opt.exe"
            llc = root / "llc.exe"
            clang = root / "clang.exe"
            llvm_size = root / "llvm-size.exe"
            out_dir = root / "effect_attribution_queens"
            out_dir.mkdir()
            _write_text(input_ir, "define i32 @main() { ret i32 0 }\n")
            _write_text(opt, "opt")
            _write_text(llc, "llc")
            _write_text(clang, "clang")
            _write_text(llvm_size, "size")
            _write_p8c_outputs(out_dir)

            manifest = build_queens_effect_attribution_manifest(
                input_ir=input_ir,
                output_dir=out_dir,
                opt_path=opt,
                llc_path=llc,
                clang_path=clang,
                llvm_size_path=llvm_size,
                repo_root=root,
                result_generated_from_commit="cafe123",
            )
            manifest_path = root / "queens_effect_attribution_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8c")
        self.assertEqual(loaded["result_generated_from_commit"], "cafe123")
        self.assertIn("states_csv", loaded["outputs"])
        self.assertIn("feature_deltas_csv", loaded["outputs"])
        self.assertIn("opcode_delta_csv", loaded["outputs"])
        self.assertIn("object_size_csv", loaded["outputs"])
        self.assertIn("attribution_report", loaded["sha256"])
        self.assertIn("clang", loaded["sha256"])
        self.assertEqual(loaded["summary"]["BothCodegenSmaller"], True)
        self.assertEqual(loaded["summary"]["LocalABBAHardHashEqual"], False)
        self.assertEqual(loaded["summary"]["FinalOpcodeDeltaNonZero"], "num_add_delta=-1")
        self.assertEqual(loaded["scope_limits"]["single_program"], "testsuite_stanford_queens")

    def test_builds_benchmark_ingest_manifest(self):
        from ecpor.result_manifest import build_benchmark_ingest_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "suite"
            source_root.mkdir()
            clang = root / "clang.exe"
            opt = root / "opt.exe"
            llc = root / "llc.exe"
            llvm_size = root / "llvm-size.exe"
            config = root / "benchmarks_p8b.yaml"
            out_dir = root / "benchmark_ingest_p8b"
            input_ir = root / "data" / "inputs" / "testsuite_misc_good.ll"
            out_dir.mkdir()
            input_ir.parent.mkdir(parents=True)
            _write_text(clang, "clang")
            _write_text(opt, "opt")
            _write_text(llc, "llc")
            _write_text(llvm_size, "size")
            _write_text(input_ir, "define i32 @main() { ret i32 0 }\n")
            _write_text(
                config,
                textwrap.dedent(
                    """
                    stage: P8b-0
                    programs:
                      - id: testsuite_misc_good
                        ir: data/inputs/testsuite_misc_good.ll
                    """
                ).strip()
                + "\n",
            )
            _write_benchmark_ingest_outputs(out_dir, input_ir)

            manifest = build_benchmark_ingest_manifest(
                source_root=source_root,
                config_path=config,
                output_dir=out_dir,
                clang_path=clang,
                opt_path=opt,
                llc_path=llc,
                llvm_size_path=llvm_size,
                repo_root=root,
                result_generated_from_commit="feed123",
            )
            manifest_path = root / "benchmark_ingest_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8b-0")
        self.assertEqual(loaded["result_generated_from_commit"], "feed123")
        self.assertIn("config", loaded["outputs"])
        self.assertIn("ingest_summary_csv", loaded["outputs"])
        self.assertIn("report", loaded["outputs"])
        self.assertIn("accepted_ir_testsuite_misc_good", loaded["outputs"])
        self.assertIn("accepted_ir_testsuite_misc_good", loaded["sha256"])
        self.assertIn("clang", loaded["sha256"])
        self.assertEqual(loaded["summary"]["AcceptedPrograms"], 1)
        self.assertEqual(loaded["summary"]["RejectedPrograms"], 1)
        self.assertEqual(loaded["scope_limits"]["new_certificates"], False)

    def test_builds_p8b_matrix_manifest(self):
        from ecpor.result_manifest import build_p8b_matrix_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "benchmarks_p8b.yaml"
            pipeline = root / "pipeline_scalar.yaml"
            passspec = root / "passspec.yaml"
            opt = root / "opt.exe"
            out_dir = root / "pair_tests_p8b_misc8"
            cert_dir = root / "pair_tests_p8b_misc8_certs"
            summary_csv = root / "cert_summary_p8b_misc8_pre.csv"
            summary_report = root / "cert_summary_report_p8b_misc8_pre.txt"
            static_decisions = root / "static_filter_decisions_p8b_misc8_pre.csv"
            static_report = root / "static_filter_report_p8b_misc8_pre.md"
            out_dir.mkdir()
            cert_dir.mkdir()
            _write_text(config, "stage: P8b-0\nprograms: []\n")
            _write_text(pipeline, "passes:\n  - a\n  - b\n")
            _write_text(passspec, "passes: {}\n")
            _write_text(opt, "opt")
            _write_p8b_matrix_outputs(
                summary_csv=summary_csv,
                summary_report=summary_report,
                static_decisions=static_decisions,
                static_report=static_report,
            )

            manifest = build_p8b_matrix_manifest(
                benchmark_config_path=config,
                pipeline_config_path=pipeline,
                passspec_path=passspec,
                output_dir=out_dir,
                cert_dir=cert_dir,
                summary_csv=summary_csv,
                summary_report=summary_report,
                static_decisions_csv=static_decisions,
                static_report=static_report,
                opt_path=opt,
                repo_root=root,
                result_generated_from_commit="face123",
            )
            manifest_path = root / "p8b_matrix_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8b-1")
        self.assertEqual(loaded["result_generated_from_commit"], "face123")
        self.assertIn("summary_csv", loaded["outputs"])
        self.assertIn("static_report", loaded["outputs"])
        self.assertIn("summary_csv", loaded["sha256"])
        self.assertIn("opt", loaded["sha256"])
        self.assertEqual(loaded["summary"]["TotalCertificates"], 2)
        self.assertEqual(loaded["summary"]["ReproducedCertificates"], 2)
        self.assertEqual(loaded["summary"]["HardFalseIndependent"], 0)
        self.assertEqual(loaded["summary"]["CertifiedFeatureMismatchCount"], 0)
        self.assertEqual(loaded["summary"]["RunFailed"], 0)
        self.assertEqual(loaded["summary"]["NotCertifiedIndependent"], 1)
        self.assertEqual(loaded["summary"]["StaticFalseNegativeObserved"], 0)
        self.assertEqual(loaded["scope_limits"]["passspec_tuning"], False)

    def test_builds_p8b_static_filter_repair_manifest(self):
        from ecpor.result_manifest import (
            build_p8b_static_filter_repair_manifest,
            write_manifest,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observed_summary = root / "cert_summary_p8b_misc8_pre.csv"
            passspec = root / "passspec.yaml"
            pre_decisions = root / "static_filter_decisions_p8b_misc8_pre.csv"
            pre_report = root / "static_filter_report_p8b_misc8_pre.md"
            post_decisions = root / "static_filter_decisions_p8b_misc8_post.csv"
            post_report = root / "static_filter_report_p8b_misc8_post.md"
            repair_report = root / "static_filter_repair_report_p8b_misc8.md"
            _write_text(observed_summary, "program,pair_a,pair_b,label\n")
            _write_text(
                passspec,
                "passes:\n  sroa:\n    may_produce:\n      - dce_opportunity\n",
            )
            _write_text(pre_decisions, "program,pair_a,pair_b,decision\n")
            _write_text(post_decisions, "program,pair_a,pair_b,decision\n")
            _write_static_filter_report(
                pre_report,
                recall="93.42%",
                macro_recall="94.39%",
                false_negatives=5,
                reduction="17.86%",
            )
            _write_static_filter_report(
                post_report,
                recall="100.00%",
                macro_recall="100.00%",
                false_negatives=0,
                reduction="14.29%",
            )
            _write_text(
                repair_report,
                "PassSpecRepair: sroa.may_produce += dce_opportunity\n",
            )

            manifest = build_p8b_static_filter_repair_manifest(
                observed_summary_csv=observed_summary,
                passspec_path=passspec,
                pre_static_decisions_csv=pre_decisions,
                pre_static_report=pre_report,
                post_static_decisions_csv=post_decisions,
                post_static_report=post_report,
                repair_report=repair_report,
                repo_root=root,
                result_generated_from_commit="bead123",
            )
            manifest_path = root / "p8b_static_repair_manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P8b-2")
        self.assertEqual(loaded["result_generated_from_commit"], "bead123")
        self.assertIn("observed_summary_csv", loaded["inputs"])
        self.assertIn("post_static_report", loaded["outputs"])
        self.assertIn("repair_report", loaded["outputs"])
        self.assertIn("passspec", loaded["sha256"])
        self.assertIn("post_static_report", loaded["sha256"])
        self.assertEqual(loaded["summary"]["PreStaticFalseNegativeObserved"], 5)
        self.assertEqual(loaded["summary"]["PostStaticFalseNegativeObserved"], 0)
        self.assertEqual(loaded["summary"]["StaticFalseNegativeDelta"], 5)
        self.assertEqual(loaded["summary"]["PostStaticCandidateRecall"], "100.00%")
        self.assertEqual(
            loaded["summary"]["PassSpecRepair"],
            "sroa.may_produce += dce_opportunity",
        )
        self.assertEqual(loaded["scope_limits"]["new_certificates"], False)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_p6_object_size(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "source", "text_delta_pct"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "source": "anchor",
                    "text_delta_pct": "0.000000",
                },
                {
                    "program": "tiny",
                    "candidate_id": "seed",
                    "source": "single_swap",
                    "text_delta_pct": "-10.000000",
                },
            ]
        )


def _write_p7a_outputs(out_dir: Path) -> None:
    _write_text(
        out_dir / "two_swap_report.md",
        textwrap.dedent(
            """
            # P7a Bounded Two-Swap Smoke Report

            ecpor_git_commit: abc123
            p5_candidates_csv: data/outputs/p5/candidates.csv
            seed_candidates: 1
            attempted_second_swaps: 7
            static_candidate_second_swaps: 7
            validated_second_swaps: 7
            selected_seed_candidates: 3
            selected_smaller_seeds: 1
            selected_equal_seeds: 2
            selected_seed_programs: 1
            seed_mode: top-k-per-program
            max_seeds_per_program: 3
            max_unique_depth2_per_program: 5
            max_total_unique_depth2: 40
            raw_depth2_candidates: 4
            duplicate_sequences: 1
            budget_skipped_depth2_candidates: 2
            unique_depth2_candidates: 3
            anchor_runs: 8
            depth1_seed_runs: 0
            depth2_candidate_runs: 3
            total_pipeline_runs: 11
            best_depth1_text_delta_pct_vs_anchor: -10.0000
            best_depth2_text_delta_pct_vs_anchor: -10.0000
            best_depth2_delta_pct_vs_parent: 0.0000
            """
        ).strip()
        + "\n",
    )
    _write_text(
        out_dir / "two_swap_seeds.csv",
        (
            "program,candidate_id,seed_candidate_id,seed_pipeline,"
            "seed_text_delta_pct,seed_rank,seed_reason\n"
            "tiny,seed,seed,\"a,b,c\",-10.000000,1,best_text_delta\n"
        ),
    )
    _write_text(out_dir / "two_swap_attempts.csv", "program,cache_hit,dynamic_test\n")
    _write_text(out_dir / "two_swap_pipeline_runs.csv", "program,candidate_id\n")
    with (out_dir / "two_swap_candidates.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "depth",
                "parent_candidate_id",
                "source",
                "candidate_pipeline",
                "swap_index",
                "pass_a",
                "pass_b",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "program": "tiny",
                "candidate_id": "tiny__depth2",
                "depth": "2",
                "parent_candidate_id": "seed",
                "source": "two_swap",
                "candidate_pipeline": "b,a,c",
                "swap_index": "1",
                "pass_a": "a",
                "pass_b": "c",
            }
        )
    with (out_dir / "two_swap_object_size.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "text_delta_pct",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "program": "tiny",
                "candidate_id": "tiny__depth2",
                "source": "two_swap",
                "text_delta_pct": "-10.000000",
            }
        )


def _write_p7b_base_outputs(out_dir: Path) -> None:
    for name in [
        "two_swap_seeds.csv",
        "two_swap_attempts.csv",
        "two_swap_candidates.csv",
        "two_swap_pipeline_runs.csv",
        "two_swap_object_size.csv",
        "two_swap_report.md",
    ]:
        _write_text(out_dir / name, f"name\n{name}\n")


def _write_p7b_analysis_outputs(out_dir: Path) -> None:
    for name in [
        "p7b_program_summary.csv",
        "p7b_pair_summary.csv",
        "p7b_depth2_details.csv",
        "p7b_cache_audit.csv",
        "p7b_duplicate_audit.csv",
    ]:
        _write_text(out_dir / name, f"name\n{name}\n")
    _write_text(
        out_dir / "p7b_analysis_report.md",
        textwrap.dedent(
            """
            # P7b.5 Two-Swap Analysis Report

            Programs: 8
            SelectedSeeds: 16
            Depth2SmallerText: 3
            DuplicateSequenceRate: 47.62%
            Depth2SmallerFromSameParent: 3
            p1: seeds=1 raw_depth2=1
            """
        ).strip()
        + "\n",
    )


def _write_p8a_outputs(out_dir: Path) -> None:
    _write_text(
        out_dir / "p8a_clang_object_size.csv",
        "program,candidate_id,source\np,tiny__anchor,anchor\n",
    )
    _write_text(
        out_dir / "p8a_codegen_direction_compare.csv",
        "program,candidate_id,direction_agree\np,tiny__swap,True\n",
    )
    _write_text(
        out_dir / "p8a_codegen_sensitivity_report.md",
        textwrap.dedent(
            """
            # P8a Clang-C Codegen Sensitivity Report

            Programs: 8
            IRInputs: 46
            ClangObjectBuildFailed: 0
            ClangSizeParseFailed: 0
            DirectionComparisonCandidates: 38
            DirectionAgreementCount: 38
            DirectionAgreementRate: 100.00%
            SmallerUnderBothCount: 4
            SmallerOnlyUnderLlcCount: 0
            SmallerOnlyUnderClangCount: 0
            DirectionDisagreementCount: 0
            testsuite_stanford_queens: detail line
            """
        ).strip()
        + "\n",
    )


def _write_core_evidence_outputs(out_dir: Path) -> None:
    _write_text(
        out_dir / "ecpor_validation_funnel.csv",
        "stage,attempted_swaps\nP4,56\n",
    )
    _write_text(
        out_dir / "ecpor_candidate_propagation_funnel.csv",
        "stage,unique_depth2_candidates\nP7b,22\n",
    )
    _write_text(
        out_dir / "ecpor_certified_pruning_summary.csv",
        "stage,evidence_event,count\nP4,certified_independent_events,32\n",
    )
    _write_text(
        out_dir / "ecpor_objective_layer_summary.csv",
        "direction_comparison_candidates,direction_agreement_rate,smaller_under_both\n38,68.42%,4\n",
    )
    _write_text(
        out_dir / "ecpor_attribution_summary.csv",
        (
            "program,pair,scope,local_feature_delta,final_feature_delta,opcode_delta,"
            "llc_text_delta_pct,clang_text_delta_pct,evidence_level\n"
            "testsuite_stanford_queens,\"simplifycfg,instcombine\","
            "single-state observed attribution,num_instructions_delta=-1,"
            "num_instructions_delta=-1,"
            "\"num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1\","
            "-4.401651,-1.673640,\"observed attribution, not causal proof\"\n"
        ),
    )
    _write_text(
        out_dir / "ecpor_core_evidence_report.md",
        textwrap.dedent(
            """
            # ECPOR Core Evidence Report

            DirectionComparisonCandidates: 38
            DirectionAgreementRate: 68.42%
            SmallerUnderBothCount: 4
            AttributionCases: 1
            queens: detail line
            """
        ).strip()
        + "\n",
    )


def _write_p8c_outputs(out_dir: Path) -> None:
    _write_text(
        out_dir / "states.csv",
        "state_name,pipeline,hard_hash\nAB_final,function(a,b),hash-a\n",
    )
    _write_text(
        out_dir / "feature_deltas.csv",
        "comparison,left_state,right_state,num_instructions_delta\n"
        "final_AB_vs_BA,AB_final,BA_final,-1\n",
    )
    _write_text(
        out_dir / "opcode_delta.csv",
        "comparison,left_state,right_state,num_add_delta\n"
        "final_AB_vs_BA,AB_final,BA_final,-1\n",
    )
    _write_text(
        out_dir / "object_size.csv",
        "compile_mode,state_name,text_delta,direction\n"
        "llc,BA_final,-32,smaller\nclang,BA_final,-16,smaller\n",
    )
    _write_text(
        out_dir / "attribution_report.md",
        textwrap.dedent(
            """
            # P8c Queens Effect Attribution

            Program: testsuite_stanford_queens
            StateCount: 7
            LocalABBAHardHashEqual: False
            FinalABBAHardHashEqual: False
            LocalInstructionDelta: -1
            FinalInstructionDelta: -1
            FeatureDeltaPropagation: kept
            LlcTextDelta: -32
            ClangTextDelta: -16
            BothCodegenSmaller: True
            FinalOpcodeDeltaNonZero: num_add_delta=-1
            """
        ).strip()
        + "\n",
    )


def _write_benchmark_ingest_outputs(out_dir: Path, input_ir: Path) -> None:
    _write_text(
        out_dir / "ingest_summary.csv",
        (
            "program,source_path,input_ir,status,failure_stage,failure_kind,"
            "num_functions,num_instructions,num_basic_blocks,scalar_pipeline_ok,"
            "llc_object_ok,clang_object_ok,size_parse_ok\n"
            f"testsuite_misc_good,Good.c,{input_ir.as_posix()},accepted,,,1,1,1,"
            "True,True,True,True\n"
            "testsuite_misc_bad,Bad.c,,rejected,ir_generation,clang_failed,0,0,0,"
            "False,False,False,False\n"
        ),
    )
    _write_text(
        out_dir / "report.md",
        textwrap.dedent(
            """
            # P8b-0 Benchmark Ingest Report

            CandidateSourceFilesScanned: 2
            AcceptedPrograms: 1
            RejectedPrograms: 1
            """
        ).strip()
        + "\n",
    )


def _write_p8b_matrix_outputs(
    *,
    summary_csv: Path,
    summary_report: Path,
    static_decisions: Path,
    static_report: Path,
) -> None:
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "pair_a",
                "pair_b",
                "label",
                "hard_equal",
                "reproduced",
                "feature_delta",
                "failure_kind_ab",
                "failure_kind_ba",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "program": "testsuite_misc_good",
                "pair_a": "a",
                "pair_b": "b",
                "label": "certified_independent",
                "hard_equal": "True",
                "reproduced": "True",
                "feature_delta": "{}",
                "failure_kind_ab": "",
                "failure_kind_ba": "",
            }
        )
        writer.writerow(
            {
                "program": "testsuite_misc_good",
                "pair_a": "b",
                "pair_b": "c",
                "label": "not_certified_independent",
                "hard_equal": "False",
                "reproduced": "True",
                "feature_delta": '{"num_instructions": 1}',
                "failure_kind_ab": "",
                "failure_kind_ba": "",
            }
        )
    _write_text(
        summary_report,
        textwrap.dedent(
            """
            Total certificates: 2
            Reproduced: 2 / 2 = 100.00%
            HardFalseIndependent: 0
            CertifiedFeatureMismatchCount: 0
            """
        ).strip()
        + "\n",
    )
    _write_text(static_decisions, "program,pair_a,pair_b,decision\np,a,b,candidate\n")
    _write_text(
        static_report,
        textwrap.dedent(
            """
            StaticCandidateRecall: 100.00%
            MacroStaticCandidateRecall: 100.00%
            StaticFalseNegativeObserved: 0
            StaticCandidateReduction: 50.00%
            """
        ).strip()
        + "\n",
    )


def _write_static_filter_report(
    path: Path,
    *,
    recall: str,
    macro_recall: str,
    false_negatives: int,
    reduction: str,
) -> None:
    _write_text(
        path,
        textwrap.dedent(
            f"""
            StaticCandidateRecall: {recall}
            MacroStaticCandidateRecall: {macro_recall}
            StaticFalseNegativeObserved: {false_negatives}
            StaticCandidateReduction: {reduction}
            """
        ).strip()
        + "\n",
    )


def _sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
