"""Command-line interface for result manifest generation."""

from __future__ import annotations

import argparse
from typing import Sequence

from .manifest_builders import (
    build_benchmark_ingest_manifest,
    build_core_evidence_manifest,
    build_core_evidence_misc8_manifest,
    build_depth1_analysis_manifest,
    build_effect_attribution_manifest,
    build_passspec_audit_manifest,
    build_pass_registry_snapshot_manifest,
    build_passspec_registry_check_manifest,
    build_passspec_trust_report_manifest,
    build_p6_5_manifest,
    build_p7a_manifest,
    build_p7b_analysis_manifest,
    build_p8a_codegen_sensitivity_manifest,
    build_p8b_bounded_local_manifest,
    build_p8b_codegen_sensitivity_manifest,
    build_p8b_code_size_manifest,
    build_p8b_lazy_validation_manifest,
    build_p8b_matrix_manifest,
    build_p8b_static_filter_repair_manifest,
    build_queens_effect_attribution_manifest,
)
from .manifest_common import write_manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build tracked result manifests.")
    subparsers = parser.add_subparsers(dest="stage", required=True)

    p7a = subparsers.add_parser("p7a", help="Build a P7a/P7b two-swap manifest.")
    p7a.add_argument("--out-manifest", required=True)
    p7a.add_argument("--p5-candidates", required=True)
    p7a.add_argument("--p5-pipeline-runs", required=True)
    p7a.add_argument("--p6-object-size", required=True)
    p7a.add_argument("--passspec", required=True)
    p7a.add_argument("--output-dir", required=True)
    p7a.add_argument("--cert-dir", required=True)
    p7a.add_argument("--opt", required=True)
    p7a.add_argument("--llc", required=True)
    p7a.add_argument("--llvm-size", required=True)
    p7a.add_argument("--repo-root", default=".")
    p7a.add_argument("--result-generated-from-commit")
    p7a.add_argument("--stage-name", default="P7a")
    p7a.add_argument(
        "--description",
        default="Bounded two-swap smoke test seeded from P6 one-swap candidates.",
    )

    p65 = subparsers.add_parser("p6-5", help="Build a P6.5 code-size manifest.")
    p65.add_argument("--out-manifest", required=True)
    p65.add_argument("--p4-attempts", required=True)
    p65.add_argument("--p5-dir", required=True)
    p65.add_argument("--p6-dir", required=True)
    p65.add_argument("--llc", required=True)
    p65.add_argument("--llvm-size", required=True)
    p65.add_argument("--repo-root", default=".")
    p65.add_argument("--result-generated-from-commit")

    p7b_analysis = subparsers.add_parser(
        "p7b-analysis", help="Build a P7b.5 two-swap analysis manifest."
    )
    p7b_analysis.add_argument("--out-manifest", required=True)
    p7b_analysis.add_argument("--p7-dir", required=True)
    p7b_analysis.add_argument("--p6-object-size", required=True)
    p7b_analysis.add_argument("--analysis-dir", required=True)
    p7b_analysis.add_argument("--repo-root", default=".")
    p7b_analysis.add_argument("--result-generated-from-commit")

    p8a = subparsers.add_parser(
        "p8a-codegen", help="Build a P8a codegen-sensitivity manifest."
    )
    p8a.add_argument("--out-manifest", required=True)
    p8a.add_argument("--p6-object-size", required=True)
    p8a.add_argument("--p7-object-size", required=True)
    p8a.add_argument("--output-dir", required=True)
    p8a.add_argument("--clang", required=True)
    p8a.add_argument("--llvm-size", required=True)
    p8a.add_argument("--repo-root", default=".")
    p8a.add_argument("--result-generated-from-commit")

    core = subparsers.add_parser(
        "core-evidence", help="Build a P8a.6 core evidence manifest."
    )
    core.add_argument("--out-manifest", required=True)
    core.add_argument("--p4-attempts", required=True)
    core.add_argument("--p5-candidates", required=True)
    core.add_argument("--p5-pipeline-runs", required=True)
    core.add_argument("--p6-object-size", required=True)
    core.add_argument("--p7b-attempts", required=True)
    core.add_argument("--p7b-candidates", required=True)
    core.add_argument("--p7b-object-size", required=True)
    core.add_argument("--p7b-analysis-report", required=True)
    core.add_argument("--p8a-compare", required=True)
    core.add_argument("--p8c-attribution-report")
    core.add_argument("--p8c-feature-deltas")
    core.add_argument("--p8c-opcode-delta")
    core.add_argument("--p8c-object-size")
    core.add_argument("--output-dir", required=True)
    core.add_argument("--repo-root", default=".")
    core.add_argument("--result-generated-from-commit")

    p8b_ingest = subparsers.add_parser(
        "benchmark-ingest", help="Build a P8b-0 benchmark ingestion manifest."
    )
    p8b_ingest.add_argument("--out-manifest", required=True)
    p8b_ingest.add_argument("--source-root", required=True)
    p8b_ingest.add_argument("--config", required=True)
    p8b_ingest.add_argument("--output-dir", required=True)
    p8b_ingest.add_argument("--clang", required=True)
    p8b_ingest.add_argument("--opt", required=True)
    p8b_ingest.add_argument("--llc", required=True)
    p8b_ingest.add_argument("--llvm-size", required=True)
    p8b_ingest.add_argument("--repo-root", default=".")
    p8b_ingest.add_argument("--result-generated-from-commit")
    p8b_ingest.add_argument("--stage-name", default="P8b-0")
    p8b_ingest.add_argument(
        "--description",
        default="Benchmark ingestion for P8b expansion from llvm-test-suite.",
    )

    p8b_matrix = subparsers.add_parser(
        "p8b-matrix", help="Build a P8b-1 Misc8 pair-matrix manifest."
    )
    p8b_matrix.add_argument("--out-manifest", required=True)
    p8b_matrix.add_argument("--benchmark-config", required=True)
    p8b_matrix.add_argument("--pipeline-config", required=True)
    p8b_matrix.add_argument("--passspec", required=True)
    p8b_matrix.add_argument("--output-dir", required=True)
    p8b_matrix.add_argument("--cert-dir", required=True)
    p8b_matrix.add_argument("--summary-csv", required=True)
    p8b_matrix.add_argument("--summary-report", required=True)
    p8b_matrix.add_argument("--static-decisions", required=True)
    p8b_matrix.add_argument("--static-report", required=True)
    p8b_matrix.add_argument("--opt", required=True)
    p8b_matrix.add_argument("--repo-root", default=".")
    p8b_matrix.add_argument("--result-generated-from-commit")
    p8b_matrix.add_argument("--stage-name", default="P8b-1")
    p8b_matrix.add_argument(
        "--description",
        default="P8b Misc8 by 28 unordered pass-pair certificate matrix.",
    )
    p8b_matrix.add_argument("--benchmark-set", default="P8b-Misc8")
    p8b_matrix.add_argument("--program-count", type=int, default=8)
    p8b_matrix.add_argument("--pass-pair-count", type=int, default=28)

    p8b_repair = subparsers.add_parser(
        "p8b-static-repair",
        help="Build a P8b-2 static-filter repair manifest.",
    )
    p8b_repair.add_argument("--out-manifest", required=True)
    p8b_repair.add_argument("--observed-summary", required=True)
    p8b_repair.add_argument("--passspec", required=True)
    p8b_repair.add_argument("--pre-static-decisions", required=True)
    p8b_repair.add_argument("--pre-static-report", required=True)
    p8b_repair.add_argument("--post-static-decisions", required=True)
    p8b_repair.add_argument("--post-static-report", required=True)
    p8b_repair.add_argument("--repair-report", required=True)
    p8b_repair.add_argument("--repo-root", default=".")
    p8b_repair.add_argument("--result-generated-from-commit")

    p8b_lazy = subparsers.add_parser(
        "p8b-lazy-validation",
        help="Build a P8b-3a Misc8 lazy-validation manifest.",
    )
    p8b_lazy.add_argument("--out-manifest", required=True)
    p8b_lazy.add_argument("--pipeline-config", required=True)
    p8b_lazy.add_argument("--passspec", required=True)
    p8b_lazy.add_argument("--output-dir", required=True)
    p8b_lazy.add_argument("--cert-dir", required=True)
    p8b_lazy.add_argument("--attempts-csv", required=True)
    p8b_lazy.add_argument("--report", required=True)
    p8b_lazy.add_argument("--opt", required=True)
    p8b_lazy.add_argument("--repo-root", default=".")
    p8b_lazy.add_argument("--result-generated-from-commit")
    p8b_lazy.add_argument("--stage-name", default="P8b-3a")
    p8b_lazy.add_argument(
        "--description",
        default="P8b Misc8 prefix-state adjacent lazy validation.",
    )
    p8b_lazy.add_argument("--benchmark-set", default="P8b-Misc8")
    p8b_lazy.add_argument("--program-count", type=int, default=8)
    p8b_lazy.add_argument("--anchor-adjacent-swaps-per-program", type=int, default=7)

    p8b_bounded = subparsers.add_parser(
        "p8b-bounded-local",
        help="Build a P8b-3b Misc8 bounded-local manifest.",
    )
    p8b_bounded.add_argument("--out-manifest", required=True)
    p8b_bounded.add_argument("--pipeline-config", required=True)
    p8b_bounded.add_argument("--p4-attempts", required=True)
    p8b_bounded.add_argument("--p5-dir", required=True)
    p8b_bounded.add_argument("--opt", required=True)
    p8b_bounded.add_argument("--repo-root", default=".")
    p8b_bounded.add_argument("--result-generated-from-commit")
    p8b_bounded.add_argument("--stage-name", default="P8b-3b")
    p8b_bounded.add_argument(
        "--description",
        default="P8b Misc8 bounded local one-swap exploration.",
    )
    p8b_bounded.add_argument("--benchmark-set", default="P8b-Misc8")
    p8b_bounded.add_argument("--program-count", type=int, default=8)

    p8b_size = subparsers.add_parser(
        "p8b-code-size",
        help="Build a P8b-3c Misc8 code-size manifest.",
    )
    p8b_size.add_argument("--out-manifest", required=True)
    p8b_size.add_argument("--p5-dir", required=True)
    p8b_size.add_argument("--p6-dir", required=True)
    p8b_size.add_argument("--llc", required=True)
    p8b_size.add_argument("--llvm-size", required=True)
    p8b_size.add_argument("--repo-root", default=".")
    p8b_size.add_argument("--result-generated-from-commit")
    p8b_size.add_argument("--stage-name", default="P8b-3c")
    p8b_size.add_argument(
        "--description",
        default="P8b Misc8 llc object-size check for depth1 candidates.",
    )
    p8b_size.add_argument("--benchmark-set", default="P8b-Misc8")
    p8b_size.add_argument("--program-count", type=int, default=8)

    p8b_codegen = subparsers.add_parser(
        "p8b-codegen",
        help="Build a P8b-3d Misc8 clang-codegen manifest.",
    )
    p8b_codegen.add_argument("--out-manifest", required=True)
    p8b_codegen.add_argument("--p6-object-size", required=True)
    p8b_codegen.add_argument("--p7-object-size")
    p8b_codegen.add_argument("--output-dir", required=True)
    p8b_codegen.add_argument("--clang", required=True)
    p8b_codegen.add_argument("--llvm-size", required=True)
    p8b_codegen.add_argument("--repo-root", default=".")
    p8b_codegen.add_argument("--result-generated-from-commit")
    p8b_codegen.add_argument("--stage-name", default="P8b-3d")
    p8b_codegen.add_argument(
        "--description",
        default="P8b Misc8 clang -c sensitivity check for depth1 candidates.",
    )
    p8b_codegen.add_argument("--benchmark-set", default="P8b-Misc8")
    p8b_codegen.add_argument("--program-count", type=int, default=8)

    depth1 = subparsers.add_parser(
        "depth1-analysis", help="Build a P8b-3.5a depth1-analysis manifest."
    )
    depth1.add_argument("--out-manifest", required=True)
    depth1.add_argument("--p4-attempts", required=True)
    depth1.add_argument("--p5-candidates", required=True)
    depth1.add_argument("--p5-pipeline-runs", required=True)
    depth1.add_argument("--p6-object-size", required=True)
    depth1.add_argument("--p8a-compare", required=True)
    depth1.add_argument("--output-dir", required=True)
    depth1.add_argument("--repo-root", default=".")
    depth1.add_argument("--result-generated-from-commit")
    depth1.add_argument("--stage-name", default="P8b-3.5a")
    depth1.add_argument(
        "--description",
        default="Misc8 depth-1 result analysis from existing P4-P8a outputs.",
    )
    depth1.add_argument("--benchmark-set", default="P8b-Misc8")

    effect = subparsers.add_parser(
        "effect-attribution", help="Build a generic effect-attribution manifest."
    )
    effect.add_argument("--out-manifest", required=True)
    effect.add_argument("--input-ir", required=True)
    effect.add_argument("--output-dir", required=True)
    effect.add_argument("--opt", required=True)
    effect.add_argument("--llc", required=True)
    effect.add_argument("--clang", required=True)
    effect.add_argument("--llvm-size", required=True)
    effect.add_argument("--program", required=True)
    effect.add_argument("--pass-a", required=True)
    effect.add_argument("--pass-b", required=True)
    effect.add_argument("--stage-name", default="P8b-3.5b")
    effect.add_argument(
        "--description",
        default="Observed effect attribution for one adjacent pass-pair case.",
    )
    effect.add_argument("--repo-root", default=".")
    effect.add_argument("--result-generated-from-commit")

    misc8_core = subparsers.add_parser(
        "core-evidence-misc8",
        help="Build a P8b-3.5c Misc8 core-evidence supplement manifest.",
    )
    misc8_core.add_argument("--out-manifest", required=True)
    misc8_core.add_argument("--p4-attempts", required=True)
    misc8_core.add_argument("--p5-candidates", required=True)
    misc8_core.add_argument("--p6-object-size", required=True)
    misc8_core.add_argument("--p8a-compare", required=True)
    misc8_core.add_argument("--depth1-analysis-report", required=True)
    misc8_core.add_argument("--output-dir", required=True)
    misc8_core.add_argument("--attribution-report")
    misc8_core.add_argument("--attribution-feature-deltas")
    misc8_core.add_argument("--attribution-opcode-delta")
    misc8_core.add_argument("--attribution-object-size")
    misc8_core.add_argument("--repo-root", default=".")
    misc8_core.add_argument("--result-generated-from-commit")

    passspec_audit = subparsers.add_parser(
        "passspec-audit", help="Build a P10 PassSpec provenance audit manifest."
    )
    passspec_audit.add_argument("--out-manifest", required=True)
    passspec_audit.add_argument("--passspec", required=True)
    passspec_audit.add_argument("--output-dir", required=True)
    passspec_audit.add_argument("--repo-root", default=".")
    passspec_audit.add_argument("--result-generated-from-commit")

    passspec_trust = subparsers.add_parser(
        "passspec-trust-report",
        help="Build a P10.5 PassSpec trust report manifest.",
    )
    passspec_trust.add_argument("--out-manifest", required=True)
    passspec_trust.add_argument("--passspec", required=True)
    passspec_trust.add_argument("--audit-manifest", required=True)
    passspec_trust.add_argument("--trust-report", required=True)
    passspec_trust.add_argument("--repo-root", default=".")
    passspec_trust.add_argument("--result-generated-from-commit")

    pass_registry = subparsers.add_parser(
        "pass-registry-snapshot",
        help="Build a P11 LLVM pass registry snapshot manifest.",
    )
    pass_registry.add_argument("--out-manifest", required=True)
    pass_registry.add_argument("--opt", required=True)
    pass_registry.add_argument("--pipeline-config", required=True)
    pass_registry.add_argument("--output-dir", required=True)
    pass_registry.add_argument("--repo-root", default=".")
    pass_registry.add_argument("--result-generated-from-commit")

    passspec_registry = subparsers.add_parser(
        "passspec-registry-check",
        help="Build a P11.5 PassSpec registry cross-check manifest.",
    )
    passspec_registry.add_argument("--out-manifest", required=True)
    passspec_registry.add_argument("--passspec", required=True)
    passspec_registry.add_argument("--pipeline-config", required=True)
    passspec_registry.add_argument("--registry-snapshot", required=True)
    passspec_registry.add_argument("--output-dir", required=True)
    passspec_registry.add_argument("--repo-root", default=".")
    passspec_registry.add_argument("--result-generated-from-commit")

    p8c = subparsers.add_parser(
        "p8c-attribution", help="Build a P8c Queens attribution manifest."
    )
    p8c.add_argument("--out-manifest", required=True)
    p8c.add_argument("--input-ir", required=True)
    p8c.add_argument("--output-dir", required=True)
    p8c.add_argument("--opt", required=True)
    p8c.add_argument("--llc", required=True)
    p8c.add_argument("--clang", required=True)
    p8c.add_argument("--llvm-size", required=True)
    p8c.add_argument("--repo-root", default=".")
    p8c.add_argument("--result-generated-from-commit")

    args = parser.parse_args(argv)
    if args.stage == "p7a":
        manifest = build_p7a_manifest(
            p5_candidates_csv=args.p5_candidates,
            p5_pipeline_runs_csv=args.p5_pipeline_runs,
            p6_object_size_csv=args.p6_object_size,
            passspec_path=args.passspec,
            output_dir=args.output_dir,
            cert_dir=args.cert_dir,
            opt_path=args.opt,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
        )
    elif args.stage == "p6-5":
        manifest = build_p6_5_manifest(
            p4_attempts_csv=args.p4_attempts,
            p5_dir=args.p5_dir,
            p6_dir=args.p6_dir,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "p7b-analysis":
        manifest = build_p7b_analysis_manifest(
            p7_dir=args.p7_dir,
            p6_object_size_csv=args.p6_object_size,
            analysis_dir=args.analysis_dir,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "p8a-codegen":
        manifest = build_p8a_codegen_sensitivity_manifest(
            p6_object_size_csv=args.p6_object_size,
            p7_object_size_csv=args.p7_object_size,
            output_dir=args.output_dir,
            clang_path=args.clang,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "core-evidence":
        manifest = build_core_evidence_manifest(
            p4_attempts_csv=args.p4_attempts,
            p5_candidates_csv=args.p5_candidates,
            p5_pipeline_runs_csv=args.p5_pipeline_runs,
            p6_object_size_csv=args.p6_object_size,
            p7b_attempts_csv=args.p7b_attempts,
            p7b_candidates_csv=args.p7b_candidates,
            p7b_object_size_csv=args.p7b_object_size,
            p7b_analysis_report=args.p7b_analysis_report,
            p8a_compare_csv=args.p8a_compare,
            output_dir=args.output_dir,
            p8c_attribution_report=args.p8c_attribution_report,
            p8c_feature_deltas_csv=args.p8c_feature_deltas,
            p8c_opcode_delta_csv=args.p8c_opcode_delta,
            p8c_object_size_csv=args.p8c_object_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "benchmark-ingest":
        manifest = build_benchmark_ingest_manifest(
            source_root=args.source_root,
            config_path=args.config,
            output_dir=args.output_dir,
            clang_path=args.clang,
            opt_path=args.opt,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
        )
    elif args.stage == "p8b-matrix":
        manifest = build_p8b_matrix_manifest(
            benchmark_config_path=args.benchmark_config,
            pipeline_config_path=args.pipeline_config,
            passspec_path=args.passspec,
            output_dir=args.output_dir,
            cert_dir=args.cert_dir,
            summary_csv=args.summary_csv,
            summary_report=args.summary_report,
            static_decisions_csv=args.static_decisions,
            static_report=args.static_report,
            opt_path=args.opt,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
            program_count=args.program_count,
            pass_pair_count=args.pass_pair_count,
        )
    elif args.stage == "p8b-static-repair":
        manifest = build_p8b_static_filter_repair_manifest(
            observed_summary_csv=args.observed_summary,
            passspec_path=args.passspec,
            pre_static_decisions_csv=args.pre_static_decisions,
            pre_static_report=args.pre_static_report,
            post_static_decisions_csv=args.post_static_decisions,
            post_static_report=args.post_static_report,
            repair_report=args.repair_report,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "p8b-lazy-validation":
        manifest = build_p8b_lazy_validation_manifest(
            pipeline_config_path=args.pipeline_config,
            passspec_path=args.passspec,
            output_dir=args.output_dir,
            cert_dir=args.cert_dir,
            attempts_csv=args.attempts_csv,
            report_path=args.report,
            opt_path=args.opt,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
            program_count=args.program_count,
            anchor_adjacent_swaps_per_program=args.anchor_adjacent_swaps_per_program,
        )
    elif args.stage == "p8b-bounded-local":
        manifest = build_p8b_bounded_local_manifest(
            pipeline_config_path=args.pipeline_config,
            p4_attempts_csv=args.p4_attempts,
            p5_dir=args.p5_dir,
            opt_path=args.opt,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
            program_count=args.program_count,
        )
    elif args.stage == "p8b-code-size":
        manifest = build_p8b_code_size_manifest(
            p5_dir=args.p5_dir,
            p6_dir=args.p6_dir,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
            program_count=args.program_count,
        )
    elif args.stage == "p8b-codegen":
        manifest = build_p8b_codegen_sensitivity_manifest(
            p6_object_size_csv=args.p6_object_size,
            p7_object_size_csv=args.p7_object_size,
            output_dir=args.output_dir,
            clang_path=args.clang,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
            program_count=args.program_count,
        )
    elif args.stage == "depth1-analysis":
        manifest = build_depth1_analysis_manifest(
            p4_attempts_csv=args.p4_attempts,
            p5_candidates_csv=args.p5_candidates,
            p5_pipeline_runs_csv=args.p5_pipeline_runs,
            p6_object_size_csv=args.p6_object_size,
            p8a_compare_csv=args.p8a_compare,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
            stage=args.stage_name,
            description=args.description,
            benchmark_set=args.benchmark_set,
        )
    elif args.stage == "effect-attribution":
        manifest = build_effect_attribution_manifest(
            input_ir=args.input_ir,
            output_dir=args.output_dir,
            opt_path=args.opt,
            llc_path=args.llc,
            clang_path=args.clang,
            llvm_size_path=args.llvm_size,
            program=args.program,
            pass_a=args.pass_a,
            pass_b=args.pass_b,
            stage=args.stage_name,
            description=args.description,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "core-evidence-misc8":
        manifest = build_core_evidence_misc8_manifest(
            p4_attempts_csv=args.p4_attempts,
            p5_candidates_csv=args.p5_candidates,
            p6_object_size_csv=args.p6_object_size,
            p8a_compare_csv=args.p8a_compare,
            depth1_analysis_report=args.depth1_analysis_report,
            output_dir=args.output_dir,
            attribution_report=args.attribution_report,
            attribution_feature_deltas_csv=args.attribution_feature_deltas,
            attribution_opcode_delta_csv=args.attribution_opcode_delta,
            attribution_object_size_csv=args.attribution_object_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "passspec-audit":
        manifest = build_passspec_audit_manifest(
            passspec_path=args.passspec,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "passspec-trust-report":
        manifest = build_passspec_trust_report_manifest(
            passspec_path=args.passspec,
            audit_manifest_path=args.audit_manifest,
            trust_report_path=args.trust_report,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "pass-registry-snapshot":
        manifest = build_pass_registry_snapshot_manifest(
            opt_path=args.opt,
            pipeline_config_path=args.pipeline_config,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "passspec-registry-check":
        manifest = build_passspec_registry_check_manifest(
            passspec_path=args.passspec,
            pipeline_config_path=args.pipeline_config,
            registry_snapshot_path=args.registry_snapshot,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "p8c-attribution":
        manifest = build_queens_effect_attribution_manifest(
            input_ir=args.input_ir,
            output_dir=args.output_dir,
            opt_path=args.opt,
            llc_path=args.llc,
            clang_path=args.clang,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    else:
        raise ValueError(f"unsupported manifest stage: {args.stage}")
    write_manifest(args.out_manifest, manifest)
    return 0



