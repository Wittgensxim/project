"""Build small tracked manifests for generated experiment results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .environment import file_sha256, git_info


P7A_SUMMARY_KEYS = {
    "seed_candidates",
    "selected_seed_candidates",
    "selected_smaller_seeds",
    "selected_equal_seeds",
    "selected_seed_programs",
    "seed_mode",
    "max_seeds_per_program",
    "attempted_second_swaps",
    "static_candidate_second_swaps",
    "low_priority_skipped",
    "validated_second_swaps",
    "cache_hits",
    "dynamic_tests",
    "certified_independent",
    "not_certified_independent",
    "run_failed",
    "raw_depth2_candidates",
    "duplicate_sequences",
    "unique_depth2_candidates_before_budget",
    "budget_skipped_depth2_candidates",
    "unique_depth2_candidates",
    "max_unique_depth2_per_program",
    "max_total_unique_depth2",
    "max_observed_depth2_per_program",
    "anchor_runs",
    "depth1_seed_runs",
    "depth2_candidate_runs",
    "total_pipeline_runs",
    "pipeline_run_failed",
    "object_build_failed",
    "size_parse_failed",
    "depth1_smaller_text",
    "depth1_equal_text",
    "depth1_larger_text",
    "depth2_smaller_text",
    "depth2_equal_text",
    "depth2_larger_text",
    "best_depth1_text_delta_pct_vs_anchor",
    "best_depth2_text_delta_pct_vs_anchor",
    "best_depth2_delta_pct_vs_parent",
    "depth2_improves_over_depth1_best",
    "best_candidate_depth",
}

P7B_ANALYSIS_SUMMARY_KEYS = {
    "Programs",
    "SelectedSeeds",
    "RawDepth2Candidates",
    "UniqueDepth2Candidates",
    "DuplicateSequences",
    "DuplicateSequenceRate",
    "Depth2SmallerText",
    "Depth2EqualText",
    "Depth2LargerText",
    "Depth2SmallerPrograms",
    "Depth2SmallerFromSameParent",
    "Depth2ImprovesProgramDepth1Best",
    "Depth2ImprovesGlobalDepth1Best",
    "FirstRunCacheHits",
    "PipelineRuns",
    "PipelineRunFailed",
}

P8A_CODEGEN_SUMMARY_KEYS = {
    "Programs",
    "IRInputs",
    "AnchorInputs",
    "SingleSwapInputs",
    "Depth2Inputs",
    "ClangObjectBuildsAttempted",
    "ClangObjectBuildFailed",
    "ClangSizeParseFailed",
    "DirectionComparisonCandidates",
    "DirectionAgreementCount",
    "DirectionAgreementRate",
    "SmallerUnderBothCount",
    "SmallerOnlyUnderLlcCount",
    "SmallerOnlyUnderClangCount",
    "DirectionDisagreementCount",
}

CORE_EVIDENCE_SUMMARY_KEYS = {
    "DirectionComparisonCandidates",
    "DirectionAgreementRate",
    "SmallerUnderBothCount",
    "SmallerOnlyUnderLlcCount",
    "SmallerOnlyUnderClangCount",
    "DirectionDisagreementCount",
    "AttributionCases",
    "AttributionObservedButNotCausalProof",
}

P8C_ATTRIBUTION_SUMMARY_KEYS = {
    "Program",
    "StateCount",
    "LocalABBAHardHashEqual",
    "FinalABBAHardHashEqual",
    "LocalInstructionDelta",
    "FinalInstructionDelta",
    "FeatureDeltaPropagation",
    "LlcTextDelta",
    "ClangTextDelta",
    "BothCodegenSmaller",
    "FinalOpcodeDeltaNonZero",
}

P8B_INGEST_SUMMARY_KEYS = {
    "CandidateSourceFilesScanned",
    "AcceptedPrograms",
    "RejectedPrograms",
    "IRGenerationOk",
    "ScalarPipelineOk",
    "LlcObjectOk",
    "ClangObjectOk",
    "SizeParseOk",
}

P8B_MATRIX_STATIC_SUMMARY_KEYS = {
    "StaticCandidateRecall",
    "MacroStaticCandidateRecall",
    "StaticFalseNegativeObserved",
    "StaticCandidateReduction",
}

P8B_STATIC_REPAIR_KEYS = {
    "StaticCandidateRecall",
    "MacroStaticCandidateRecall",
    "StaticFalseNegativeObserved",
    "StaticCandidateReduction",
}

P8B_LAZY_VALIDATION_SUMMARY_KEYS = {
    "attempted_adjacent_swaps",
    "candidate_swaps",
    "low_priority_skipped",
    "cache_hits",
    "dynamic_tests",
    "certified_independent",
    "not_certified_independent",
    "run_failed",
    "HardFalseIndependent",
    "CertificateReproductionRate",
    "CertifiedPruningRatioAttempted",
    "CertifiedPruningRatioDynamic",
    "SecondRunCacheHitRate",
}

P8B_BOUNDED_LOCAL_SUMMARY_KEYS = {
    "attempted_adjacent_swaps",
    "candidate_swaps",
    "low_priority_skipped",
    "dynamic_tests",
    "certified_independent",
    "not_certified_independent",
    "run_failed",
    "anchor_candidates",
    "single_swap_candidates",
    "collapsed_certified_independent",
    "frozen_by_static_filter",
    "invalid_run_failed",
    "pipeline_runs",
    "pipeline_run_failed",
    "same_as_anchor",
    "different_from_anchor",
    "anchor_runs",
    "single_swap_runs",
    "single_swap_same_as_anchor",
    "single_swap_different_from_anchor",
}

P8B_CODE_SIZE_SUMMARY_KEYS = {
    "Programs",
    "ObjectBuildFailed",
    "SizeParseFailed",
    "CodeSizeDeltaVsAnchor",
    "SingleSwapP5SameAsAnchor",
    "SingleSwapP5DifferentFromAnchor",
    "IRDifferentButTextEqualCount",
    "IRDifferentButTextEqualRate",
}


def build_result_manifest(
    *,
    stage: str,
    description: str,
    inputs: Mapping[str, str | Path],
    outputs: Mapping[str, str | Path],
    tools: Mapping[str, str | Path],
    summary: Mapping[str, Any],
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo_git = git_info(repo_root)
    generated_from = result_generated_from_commit or repo_git.commit
    manifest: dict[str, Any] = {
        "manifest_schema_version": 1,
        "stage": stage,
        "description": description,
        "result_generated_from_commit": generated_from,
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": repo_git.dirty,
        "inputs": _path_map(inputs),
        "outputs": _path_map(outputs),
        "sha256": _sha256_map(inputs) | _sha256_map(outputs) | _sha256_map(tools),
        "tools": _tool_map(tools),
        "summary": dict(summary),
    }
    if extra:
        manifest.update(extra)
    return manifest


def build_p7a_manifest(
    *,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    stage: str = "P7a",
    description: str = (
        "Bounded two-swap smoke test seeded from P6 one-swap candidates."
    ),
) -> dict[str, Any]:
    out = Path(output_dir)
    candidates_csv = out / "two_swap_candidates.csv"
    seeds_csv = out / "two_swap_seeds.csv"
    attempts_csv = out / "two_swap_attempts.csv"
    pipeline_runs_csv = out / "two_swap_pipeline_runs.csv"
    object_size_csv = out / "two_swap_object_size.csv"
    report_md = out / "two_swap_report.md"
    p6_rows = _load_csv(p6_object_size_csv)
    seed_rows = _load_csv(seeds_csv)
    p7_candidates = _load_csv(candidates_csv)
    p7_object_rows = _load_csv(object_size_csv)
    extra = {
        "seed": _seed_from_seed_rows(seed_rows) or _seed_from_p6_rows(p6_rows),
        "seeds": _seeds_from_seed_rows(seed_rows),
        "depth2_candidates": _depth2_candidates(
            candidate_rows=p7_candidates,
            object_rows=p7_object_rows,
            p6_rows=p6_rows,
        ),
        "scope_limits": {
            "runtime_benchmarks": False,
            "full_searcher": False,
            "codegen_path": "llc -filetype=obj",
        },
    }
    return build_result_manifest(
        stage=stage,
        description=description,
        inputs={
            "p5_candidates_csv": p5_candidates_csv,
            "p5_pipeline_runs_csv": p5_pipeline_runs_csv,
            "p6_object_size_csv": p6_object_size_csv,
            "passspec": passspec_path,
        },
        outputs={
            "output_dir": output_dir,
            "cert_dir": cert_dir,
            "two_swap_seeds_csv": seeds_csv,
            "two_swap_candidates_csv": candidates_csv,
            "two_swap_attempts_csv": attempts_csv,
            "two_swap_pipeline_runs_csv": pipeline_runs_csv,
            "two_swap_object_size_csv": object_size_csv,
            "two_swap_report": report_md,
        },
        tools={
            "opt": opt_path,
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(_parse_key_value_report(report_md), P7A_SUMMARY_KEYS),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra=extra,
    )


def build_p6_5_manifest(
    *,
    p4_attempts_csv: str | Path,
    p5_dir: str | Path,
    p6_dir: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    p5 = Path(p5_dir)
    p6 = Path(p6_dir)
    code_size_report = p6 / "code_size_report.md"
    return build_result_manifest(
        stage="P6.5",
        description=(
            "Clean P6 code-size run after provenance and candidate-source hardening."
        ),
        inputs={
            "p4_attempts_csv": p4_attempts_csv,
            "p5_output_dir": p5,
            "p6_output_dir": p6,
            "p5_report": p5 / "report.md",
            "candidates_csv": p5 / "candidates.csv",
            "pipeline_runs_csv": p5 / "pipeline_runs.csv",
            "object_size_csv": p6 / "object_size.csv",
            "code_size_report": code_size_report,
        },
        outputs={},
        tools={
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_parse_key_value_report(code_size_report),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "manifest_note": (
                "This tracked manifest records a clean generated-data run. "
                "The generated data under data/outputs is intentionally not tracked."
            )
        },
    )


def build_p7b_analysis_manifest(
    *,
    p7_dir: str | Path,
    p6_object_size_csv: str | Path,
    analysis_dir: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    p7 = Path(p7_dir)
    analysis = Path(analysis_dir)
    report = analysis / "p7b_analysis_report.md"
    return build_result_manifest(
        stage="P7b.5",
        description="P7b two-swap result interpretation and distribution analysis.",
        inputs={
            "p7b_output_dir": p7,
            "p6_object_size_csv": p6_object_size_csv,
            "two_swap_seeds_csv": p7 / "two_swap_seeds.csv",
            "two_swap_attempts_csv": p7 / "two_swap_attempts.csv",
            "two_swap_candidates_csv": p7 / "two_swap_candidates.csv",
            "two_swap_pipeline_runs_csv": p7 / "two_swap_pipeline_runs.csv",
            "two_swap_object_size_csv": p7 / "two_swap_object_size.csv",
            "two_swap_report": p7 / "two_swap_report.md",
        },
        outputs={
            "analysis_dir": analysis,
            "p7b_program_summary_csv": analysis / "p7b_program_summary.csv",
            "p7b_pair_summary_csv": analysis / "p7b_pair_summary.csv",
            "p7b_depth2_details_csv": analysis / "p7b_depth2_details.csv",
            "p7b_cache_audit_csv": analysis / "p7b_cache_audit.csv",
            "p7b_duplicate_audit_csv": analysis / "p7b_duplicate_audit.csv",
            "p7b_analysis_report": report,
        },
        tools={},
        summary=_filter_keys(
            _parse_key_value_report(report),
            P7B_ANALYSIS_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "runtime_benchmarks": False,
                "new_certificates": False,
                "llvm_rerun": False,
                "analysis_only": True,
            }
        },
    )


def build_p8a_codegen_sensitivity_manifest(
    *,
    p6_object_size_csv: str | Path,
    p7_object_size_csv: str | Path,
    output_dir: str | Path,
    clang_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "p8a_codegen_sensitivity_report.md"
    return build_result_manifest(
        stage="P8a",
        description="Clang -c codegen sensitivity check for P6/P7b saved IR outputs.",
        inputs={
            "p6_object_size_csv": p6_object_size_csv,
            "p7_object_size_csv": p7_object_size_csv,
        },
        outputs={
            "output_dir": out,
            "p8a_clang_object_size_csv": out / "p8a_clang_object_size.csv",
            "p8a_codegen_direction_compare_csv": out
            / "p8a_codegen_direction_compare.csv",
            "p8a_codegen_sensitivity_report": report,
        },
        tools={
            "clang": clang_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8A_CODEGEN_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "runtime_benchmarks": False,
                "new_certificates": False,
                "llvm_opt_rerun": False,
                "codegen_path_compared": "clang -c",
            }
        },
    )


def build_core_evidence_manifest(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    p7b_attempts_csv: str | Path,
    p7b_candidates_csv: str | Path,
    p7b_object_size_csv: str | Path,
    p7b_analysis_report: str | Path,
    p8a_compare_csv: str | Path,
    output_dir: str | Path,
    p8c_attribution_report: str | Path | None = None,
    p8c_feature_deltas_csv: str | Path | None = None,
    p8c_opcode_delta_csv: str | Path | None = None,
    p8c_object_size_csv: str | Path | None = None,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "ecpor_core_evidence_report.md"
    inputs: dict[str, str | Path] = {
        "p4_attempts_csv": p4_attempts_csv,
        "p5_candidates_csv": p5_candidates_csv,
        "p5_pipeline_runs_csv": p5_pipeline_runs_csv,
        "p6_object_size_csv": p6_object_size_csv,
        "p7b_attempts_csv": p7b_attempts_csv,
        "p7b_candidates_csv": p7b_candidates_csv,
        "p7b_object_size_csv": p7b_object_size_csv,
        "p7b_analysis_report": p7b_analysis_report,
        "p8a_compare_csv": p8a_compare_csv,
    }
    inputs.update(
        _optional_paths(
            p8c_attribution_report=p8c_attribution_report,
            p8c_feature_deltas_csv=p8c_feature_deltas_csv,
            p8c_opcode_delta_csv=p8c_opcode_delta_csv,
            p8c_object_size_csv=p8c_object_size_csv,
        )
    )
    return build_result_manifest(
        stage="P8c.2",
        description=(
            "Core evidence report with P8c Queens observed attribution summary."
        ),
        inputs=inputs,
        outputs={
            "output_dir": out,
            "ecpor_core_evidence_report": report,
            "ecpor_validation_funnel_csv": out / "ecpor_validation_funnel.csv",
            "ecpor_candidate_propagation_funnel_csv": out
            / "ecpor_candidate_propagation_funnel.csv",
            "ecpor_certified_pruning_summary_csv": out
            / "ecpor_certified_pruning_summary.csv",
            "ecpor_objective_layer_summary_csv": out
            / "ecpor_objective_layer_summary.csv",
            "ecpor_attribution_summary_csv": out / "ecpor_attribution_summary.csv",
        },
        tools={},
        summary=_filter_keys(
            _parse_key_value_report(report),
            CORE_EVIDENCE_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "runtime_benchmarks": False,
                "new_certificates": False,
                "new_search": False,
                "report_only": True,
            }
        },
    )


def build_benchmark_ingest_manifest(
    *,
    source_root: str | Path,
    config_path: str | Path,
    output_dir: str | Path,
    clang_path: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    summary_csv = out / "ingest_summary.csv"
    report = out / "report.md"
    outputs: dict[str, str | Path] = {
        "config": config_path,
        "output_dir": out,
        "ingest_summary_csv": summary_csv,
        "report": report,
    }
    for row in _load_csv(summary_csv):
        if row.get("status") != "accepted" or not row.get("input_ir"):
            continue
        outputs[f"accepted_ir_{_manifest_key(row.get('program', ''))}"] = row[
            "input_ir"
        ]
    return build_result_manifest(
        stage="P8b-0",
        description="Benchmark ingestion for P8b expansion from llvm-test-suite.",
        inputs={
            "source_root": source_root,
        },
        outputs=outputs,
        tools={
            "clang": clang_path,
            "opt": opt_path,
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8B_INGEST_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "new_certificates": False,
                "pair_matrix": False,
                "new_search": False,
                "runtime_benchmarks": False,
                "ingestion_only": True,
            }
        },
    )


def build_p8b_matrix_manifest(
    *,
    benchmark_config_path: str | Path,
    pipeline_config_path: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    summary_csv: str | Path,
    summary_report: str | Path,
    static_decisions_csv: str | Path,
    static_report: str | Path,
    opt_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    summary = _certificate_matrix_summary(summary_csv)
    summary.update(
        _filter_keys(
            _parse_key_value_report(static_report),
            P8B_MATRIX_STATIC_SUMMARY_KEYS,
        )
    )
    return build_result_manifest(
        stage="P8b-1",
        description="P8b Misc8 by 28 unordered pass-pair certificate matrix.",
        inputs={
            "benchmark_config": benchmark_config_path,
            "pipeline_config": pipeline_config_path,
            "passspec": passspec_path,
        },
        outputs={
            "output_dir": output_dir,
            "cert_dir": cert_dir,
            "summary_csv": summary_csv,
            "summary_report": summary_report,
            "static_decisions_csv": static_decisions_csv,
            "static_report": static_report,
        },
        tools={
            "opt": opt_path,
        },
        summary=summary,
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "program_count": 8,
                "pass_pair_count": 28,
                "passspec_tuning": False,
                "new_search": False,
                "runtime_benchmarks": False,
                "code_size_evaluation": False,
                "pre_tuning_static_filter_eval": True,
            }
        },
    )


def build_p8b_static_filter_repair_manifest(
    *,
    observed_summary_csv: str | Path,
    passspec_path: str | Path,
    pre_static_decisions_csv: str | Path,
    pre_static_report: str | Path,
    post_static_decisions_csv: str | Path,
    post_static_report: str | Path,
    repair_report: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    pre_summary = _prefixed_report_summary(
        pre_static_report,
        prefix="Pre",
        keys=P8B_STATIC_REPAIR_KEYS,
    )
    post_summary = _prefixed_report_summary(
        post_static_report,
        prefix="Post",
        keys=P8B_STATIC_REPAIR_KEYS,
    )
    summary: dict[str, Any] = {
        **pre_summary,
        **post_summary,
        "StaticFalseNegativeDelta": _static_false_negative_delta(
            pre_summary,
            post_summary,
        ),
        "PassSpecRepair": "sroa.may_produce += dce_opportunity",
    }
    return build_result_manifest(
        stage="P8b-2",
        description="P8b Misc8 static-filter false-negative repair.",
        inputs={
            "observed_summary_csv": observed_summary_csv,
            "passspec": passspec_path,
            "pre_static_decisions_csv": pre_static_decisions_csv,
            "pre_static_report": pre_static_report,
        },
        outputs={
            "post_static_decisions_csv": post_static_decisions_csv,
            "post_static_report": post_static_report,
            "repair_report": repair_report,
        },
        tools={},
        summary=summary,
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "new_certificates": False,
                "certificate_matrix_rerun": False,
                "new_search": False,
                "runtime_benchmarks": False,
                "code_size_evaluation": False,
                "passspec_tuning": True,
                "repair_source": "empirical_false_negative_repair_p8b1",
            },
            "repair_evidence": [
                "sroa,adce on testsuite_misc_ffbench",
                "sroa,dce on testsuite_misc_flops_1",
                "sroa,adce on testsuite_misc_flops_1",
                "sroa,dce on testsuite_misc_flops_2",
                "sroa,adce on testsuite_misc_flops_2",
            ],
        },
    )


def build_p8b_lazy_validation_manifest(
    *,
    pipeline_config_path: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    attempts_csv: str | Path,
    report_path: str | Path,
    opt_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    return build_result_manifest(
        stage="P8b-3a",
        description="P8b Misc8 prefix-state adjacent lazy validation.",
        inputs={
            "pipeline_config": pipeline_config_path,
            "passspec": passspec_path,
        },
        outputs={
            "output_dir": output_dir,
            "cert_dir": cert_dir,
            "attempts_csv": attempts_csv,
            "report": report_path,
        },
        tools={
            "opt": opt_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report_path),
            P8B_LAZY_VALIDATION_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "program_count": 8,
                "anchor_adjacent_swaps_per_program": 7,
                "two_swap_search": False,
                "full_searcher": False,
                "runtime_benchmarks": False,
                "code_size_evaluation": False,
            }
        },
    )


def build_p8b_bounded_local_manifest(
    *,
    pipeline_config_path: str | Path,
    p4_attempts_csv: str | Path,
    p5_dir: str | Path,
    opt_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    p5 = Path(p5_dir)
    report = p5 / "report.md"
    return build_result_manifest(
        stage="P8b-3b",
        description="P8b Misc8 bounded local one-swap exploration.",
        inputs={
            "pipeline_config": pipeline_config_path,
            "p4_attempts_csv": p4_attempts_csv,
        },
        outputs={
            "output_dir": p5,
            "candidates_csv": p5 / "candidates.csv",
            "pipeline_runs_csv": p5 / "pipeline_runs.csv",
            "report": report,
        },
        tools={
            "opt": opt_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8B_BOUNDED_LOCAL_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "program_count": 8,
                "depth": 1,
                "two_swap_search": False,
                "full_searcher": False,
                "runtime_benchmarks": False,
                "objective_selection": False,
            }
        },
    )


def build_p8b_code_size_manifest(
    *,
    p5_dir: str | Path,
    p6_dir: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    p5 = Path(p5_dir)
    p6 = Path(p6_dir)
    report = p6 / "code_size_report.md"
    return build_result_manifest(
        stage="P8b-3c",
        description="P8b Misc8 llc object-size check for depth1 candidates.",
        inputs={
            "p5_output_dir": p5,
            "p5_report": p5 / "report.md",
            "candidates_csv": p5 / "candidates.csv",
            "pipeline_runs_csv": p5 / "pipeline_runs.csv",
        },
        outputs={
            "output_dir": p6,
            "object_size_csv": p6 / "object_size.csv",
            "code_size_report": report,
        },
        tools={
            "llc": llc_path,
            "llvm_size": llvm_size_path,
        },
        summary=_p8b_code_size_summary(report, p6 / "object_size.csv"),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "program_count": 8,
                "depth": 1,
                "codegen_path": "llc -filetype=obj",
                "two_swap_search": False,
                "full_searcher": False,
                "runtime_benchmarks": False,
            }
        },
    )


def build_p8b_codegen_sensitivity_manifest(
    *,
    p6_object_size_csv: str | Path,
    output_dir: str | Path,
    clang_path: str | Path,
    llvm_size_path: str | Path,
    p7_object_size_csv: str | Path | None = None,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "p8a_codegen_sensitivity_report.md"
    inputs: dict[str, str | Path] = {
        "p6_object_size_csv": p6_object_size_csv,
    }
    inputs.update(_optional_paths(p7_object_size_csv=p7_object_size_csv))
    return build_result_manifest(
        stage="P8b-3d",
        description="P8b Misc8 clang -c sensitivity check for depth1 candidates.",
        inputs=inputs,
        outputs={
            "output_dir": out,
            "p8a_clang_object_size_csv": out / "p8a_clang_object_size.csv",
            "p8a_codegen_direction_compare_csv": out
            / "p8a_codegen_direction_compare.csv",
            "p8a_codegen_sensitivity_report": report,
        },
        tools={
            "clang": clang_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8A_CODEGEN_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "benchmark_set": "P8b-Misc8",
                "program_count": 8,
                "depth": 1,
                "new_certificates": False,
                "llvm_opt_rerun": False,
                "two_swap_search": False,
                "runtime_benchmarks": False,
                "codegen_path_compared": "clang -c",
            }
        },
    )


def build_queens_effect_attribution_manifest(
    *,
    input_ir: str | Path,
    output_dir: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    clang_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "attribution_report.md"
    return build_result_manifest(
        stage="P8c",
        description="Queens instcombine/simplifycfg observed effect attribution.",
        inputs={
            "input_ir": input_ir,
        },
        outputs={
            "output_dir": out,
            "states_csv": out / "states.csv",
            "feature_deltas_csv": out / "feature_deltas.csv",
            "opcode_delta_csv": out / "opcode_delta.csv",
            "object_size_csv": out / "object_size.csv",
            "attribution_report": report,
        },
        tools={
            "opt": opt_path,
            "llc": llc_path,
            "clang": clang_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8C_ATTRIBUTION_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "single_program": "testsuite_stanford_queens",
                "runtime_benchmarks": False,
                "new_certificates": False,
                "new_search": False,
                "observed_attribution_not_causal_proof": True,
            }
        },
    )


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


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
        )
    elif args.stage == "p8b-bounded-local":
        manifest = build_p8b_bounded_local_manifest(
            pipeline_config_path=args.pipeline_config,
            p4_attempts_csv=args.p4_attempts,
            p5_dir=args.p5_dir,
            opt_path=args.opt,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
        )
    elif args.stage == "p8b-code-size":
        manifest = build_p8b_code_size_manifest(
            p5_dir=args.p5_dir,
            p6_dir=args.p6_dir,
            llc_path=args.llc,
            llvm_size_path=args.llvm_size,
            repo_root=args.repo_root,
            result_generated_from_commit=args.result_generated_from_commit,
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
        )
    else:
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
    write_manifest(args.out_manifest, manifest)
    return 0


def _path_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {key: _path_text(path) for key, path in paths.items()}


def _optional_paths(**paths: str | Path | None) -> dict[str, str | Path]:
    return {key: path for key, path in paths.items() if path not in {None, ""}}


def _tool_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {f"{key}_path": str(path) for key, path in paths.items()}


def _sha256_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, value in paths.items():
        path = Path(value)
        if path.exists() and path.is_file():
            hashes[key] = file_sha256(path)
    return hashes


def _parse_key_value_report(path: str | Path) -> dict[str, Any]:
    report = Path(path)
    if not report.exists():
        return {}
    summary: dict[str, Any] = {}
    for raw_line in report.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key or " " in key:
            continue
        summary[key] = _parse_scalar(value.strip())
    return summary


def _filter_keys(
    values: Mapping[str, Any], allowed_keys: set[str]
) -> dict[str, Any]:
    return {key: values[key] for key in allowed_keys if key in values}


def _parse_scalar(value: str) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    if value == "":
        return ""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _seed_from_p6_rows(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    seeds = [
        row
        for row in rows
        if row.get("source") == "single_swap"
        and _parse_optional_float(row.get("text_delta_pct")) is not None
        and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) < 0.0
    ]
    if not seeds:
        return {}
    seed = min(seeds, key=lambda row: _parse_optional_float(row["text_delta_pct"]) or 0.0)
    return {
        "program": seed.get("program", ""),
        "candidate_id": seed.get("candidate_id", ""),
        "depth1_text_delta_pct_vs_anchor": _parse_optional_float(
            seed.get("text_delta_pct")
        ),
    }


def _seed_from_seed_rows(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    seeds = _seeds_from_seed_rows(rows)
    return seeds[0] if seeds else {}


def _seeds_from_seed_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "program": row.get("program", ""),
                "candidate_id": row.get("seed_candidate_id")
                or row.get("candidate_id", ""),
                "seed_pipeline": row.get("seed_pipeline", ""),
                "depth1_text_delta_pct_vs_anchor": _parse_optional_float(
                    row.get("seed_text_delta_pct") or row.get("text_delta_pct")
                ),
                "seed_rank": _parse_optional_int(row.get("seed_rank")),
                "seed_reason": row.get("seed_reason", ""),
            }
        )
    return result


def _depth2_candidates(
    *,
    candidate_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    p6_rows: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    object_by_id = {row.get("candidate_id", ""): row for row in object_rows}
    parent_pct = {
        row.get("candidate_id", ""): _parse_optional_float(row.get("text_delta_pct"))
        for row in p6_rows
    }
    result: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row.get("source") != "two_swap":
            continue
        object_row = object_by_id.get(row.get("candidate_id", ""), {})
        text_pct = _parse_optional_float(object_row.get("text_delta_pct"))
        parent_id = row.get("parent_candidate_id", "")
        parent_text_pct = parent_pct.get(parent_id)
        delta_vs_parent = (
            None
            if text_pct is None or parent_text_pct is None
            else text_pct - parent_text_pct
        )
        result.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "swap_index": _parse_optional_int(row.get("swap_index")),
                "pass_a": row.get("pass_a", ""),
                "pass_b": row.get("pass_b", ""),
                "parent_candidate_id": parent_id,
                "candidate_pipeline": row.get("candidate_pipeline", ""),
                "text_delta_pct_vs_anchor": text_pct,
                "delta_pct_vs_parent": delta_vs_parent,
            }
        )
    return result


def _certificate_matrix_summary(path: str | Path) -> dict[str, Any]:
    rows = _load_csv(path)
    label_counts: dict[str, int] = {}
    for row in rows:
        label = row.get("label", "")
        label_counts[label] = label_counts.get(label, 0) + 1
    total = len(rows)
    reproduced = sum(1 for row in rows if _is_true(row.get("reproduced", "")))
    return {
        "TotalCertificates": total,
        "ReproducedCertificates": reproduced,
        "CertificateReproductionRate": (
            f"{(reproduced / total * 100.0):.2f}%" if total else "0.00%"
        ),
        "CertifiedIndependent": label_counts.get("certified_independent", 0),
        "NotCertifiedIndependent": label_counts.get("not_certified_independent", 0),
        "RunFailed": label_counts.get("run_failed", 0),
        "HardFalseIndependent": sum(
            1
            for row in rows
            if row.get("label") == "certified_independent"
            and not _is_true(row.get("hard_equal", ""))
        ),
        "CertifiedFeatureMismatchCount": sum(
            1
            for row in rows
            if row.get("label") == "certified_independent"
            and _has_nonzero_feature_delta(row.get("feature_delta", ""))
        ),
        "FailureDirections": sum(
            1
            for row in rows
            for key in ("failure_kind_ab", "failure_kind_ba")
            if row.get(key, "").strip()
            and row.get(key, "").strip() != "none"
        ),
    }


def _prefixed_report_summary(
    path: str | Path,
    *,
    prefix: str,
    keys: set[str],
) -> dict[str, Any]:
    raw = _filter_keys(_parse_key_value_report(path), keys)
    return {f"{prefix}{key}": value for key, value in raw.items()}


def _static_false_negative_delta(
    pre_summary: Mapping[str, Any],
    post_summary: Mapping[str, Any],
) -> int | None:
    pre = pre_summary.get("PreStaticFalseNegativeObserved")
    post = post_summary.get("PostStaticFalseNegativeObserved")
    if not isinstance(pre, int) or not isinstance(post, int):
        return None
    return pre - post


def _p8b_code_size_summary(
    report: str | Path,
    object_size_csv: str | Path,
) -> dict[str, Any]:
    summary = _filter_keys(
        _parse_key_value_report(report),
        P8B_CODE_SIZE_SUMMARY_KEYS,
    )
    rows = _load_csv(object_size_csv)
    single_swap_rows = [row for row in rows if row.get("source") == "single_swap"]
    computed_rows = [
        row
        for row in single_swap_rows
        if row.get("text_delta", "") != ""
        and not row.get("compile_failure_kind", "")
        and not row.get("size_failure_kind", "")
    ]
    summary.setdefault("CodeSizeDeltaVsAnchor", len(computed_rows))
    summary.setdefault(
        "SmallerText",
        sum(1 for row in computed_rows if (_parse_optional_float(row.get("text_delta")) or 0.0) < 0.0),
    )
    summary.setdefault(
        "EqualText",
        sum(1 for row in computed_rows if (_parse_optional_float(row.get("text_delta")) or 0.0) == 0.0),
    )
    summary.setdefault(
        "LargerText",
        sum(1 for row in computed_rows if (_parse_optional_float(row.get("text_delta")) or 0.0) > 0.0),
    )
    return summary


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    candidate = Path(path)
    if not candidate.exists():
        return []
    with candidate.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value))


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _is_true(value: str) -> bool:
    return value.lower() == "true"


def _has_nonzero_feature_delta(raw_delta: str) -> bool:
    if not raw_delta.strip():
        return False
    try:
        delta = json.loads(raw_delta)
    except json.JSONDecodeError:
        return True
    if not isinstance(delta, dict):
        return bool(delta)
    return any(_is_nonzero_delta(value) for value in delta.values())


def _is_nonzero_delta(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return value is not None


def _path_text(path: str | Path) -> str:
    return Path(path).as_posix()


def _manifest_key(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
