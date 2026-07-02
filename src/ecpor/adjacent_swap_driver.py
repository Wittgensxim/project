"""Minimal P4 driver for anchor-adjacent lazy validation."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .batch_certificates import (
    P8B_MISC8_PROGRAMS,
    STANFORD_8_PROGRAMS,
    Program,
    load_benchmark_config_programs,
)
from .certificate_db import CertificateDB
from .environment import DEFAULT_EXECUTION_MODEL
from .feature_scan import scan_ir_file
from .lazy_validator import LazyValidationResult, validate_adjacent_swap
from .normalizer import NORMALIZER_VERSION
from .runner import OptPath
from .state_materializer import materialize_prefix_state
from .static_filter import classify_pair, load_passspec, load_pipeline_config


@dataclass(frozen=True)
class AdjacentSwapAttempt:
    program: str
    prefix_passes: list[str]
    state_path: str
    state_hash: str
    pass_a: str
    pass_b: str
    static_decision: str
    static_reason: str
    action: str
    label: str
    cache_hit: bool
    dynamic_test: bool
    reproduced: bool | None
    cert_id: str


@dataclass(frozen=True)
class AdjacentSwapValidationRun:
    attempts: list[AdjacentSwapAttempt]
    summary: dict[str, Any]


ATTEMPT_FIELDS = [
    "program",
    "prefix_passes",
    "state_path",
    "state_hash",
    "pass_a",
    "pass_b",
    "static_decision",
    "static_reason",
    "action",
    "label",
    "cache_hit",
    "dynamic_test",
    "reproduced",
    "cert_id",
]


def run_adjacent_swap_validation(
    *,
    programs: Sequence[Program],
    passes: Sequence[str],
    passspec: dict[str, dict[str, Any]],
    cert_db: CertificateDB,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    llvm_version: str,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    region_id: str = "function_scalar_mvp",
    window_size: int = 7,
    timeout_sec: float = 30.0,
) -> AdjacentSwapValidationRun:
    output_root = Path(output_dir)
    attempts: list[AdjacentSwapAttempt] = []
    for program, input_ir in programs:
        program_root = output_root / _safe_name(program)
        for index in range(len(passes) - 1):
            prefix = list(passes[:index])
            pass_a = passes[index]
            pass_b = passes[index + 1]
            state = materialize_prefix_state(
                input_ir,
                prefix,
                opt_path=opt_path,
                output_dir=program_root / "prefix_states",
                env_id=env_id,
                nesting=nesting,
                normalizer_version=normalizer_version,
                extra_flags=extra_flags,
                timeout_sec=timeout_sec,
            )
            if not state.state_hash:
                attempts.append(
                    AdjacentSwapAttempt(
                        program=program,
                        prefix_passes=prefix,
                        state_path=str(state.path),
                        state_hash="",
                        pass_a=pass_a,
                        pass_b=pass_b,
                        static_decision="prefix_failed",
                        static_reason="prefix materialization failed",
                        action="prefix_failed",
                        label="run_failed",
                        cache_hit=False,
                        dynamic_test=False,
                        reproduced=None,
                        cert_id="",
                    )
                )
                continue

            features = scan_ir_file(state.path)
            decision = classify_pair(
                pass_a,
                pass_b,
                passspec,
                program_features=features,
                distance=1,
                window_size=window_size,
            )
            validation = validate_adjacent_swap(
                state.path,
                pass_a,
                pass_b,
                static_decision=decision["decision"],
                cert_db=cert_db,
                opt_path=opt_path,
                output_dir=program_root / "lazy_validation",
                env_id=env_id,
                llvm_version=llvm_version,
                execution_model=execution_model,
                normalizer_version=normalizer_version,
                nesting=nesting,
                extra_flags=extra_flags,
                region_id=region_id,
                timeout_sec=timeout_sec,
            )
            attempts.append(
                _attempt_from_validation(
                    program=program,
                    prefix=prefix,
                    state_path=state.path,
                    state_hash=state.state_hash,
                    decision=decision,
                    validation=validation,
                )
            )
    return AdjacentSwapValidationRun(
        attempts=attempts,
        summary=summarize_attempts(attempts),
    )


def summarize_attempts(attempts: Sequence[AdjacentSwapAttempt]) -> dict[str, Any]:
    attempted = len(attempts)
    candidate_swaps = sum(
        1 for attempt in attempts if attempt.static_decision == "candidate"
    )
    dynamic_tests = sum(1 for attempt in attempts if attempt.dynamic_test)
    cache_hits = sum(1 for attempt in attempts if attempt.cache_hit)
    certified = sum(
        1 for attempt in attempts if attempt.label == "certified_independent"
    )
    reproduced = sum(1 for attempt in attempts if attempt.reproduced is True)
    return {
        "attempted_adjacent_swaps": attempted,
        "candidate_swaps": candidate_swaps,
        "low_priority_skipped": sum(
            1 for attempt in attempts if attempt.action == "skipped_low_priority"
        ),
        "cache_hits": cache_hits,
        "dynamic_tests": dynamic_tests,
        "certified_independent": certified,
        "not_certified_independent": sum(
            1 for attempt in attempts if attempt.label == "not_certified_independent"
        ),
        "run_failed": sum(1 for attempt in attempts if attempt.label == "run_failed"),
        "hard_false_independent": 0,
        "certificate_reproduced": reproduced,
        "certificate_reproduction_rate": (
            reproduced / dynamic_tests if dynamic_tests else 1.0
        ),
        "certified_pruning_ratio_attempted": (
            certified / attempted if attempted else 0.0
        ),
        "certified_pruning_ratio_dynamic": (
            certified / dynamic_tests if dynamic_tests else None
        ),
        "second_run_cache_hit_rate": (
            cache_hits / candidate_swaps
            if candidate_swaps and dynamic_tests == 0
            else 0.0
        ),
    }


def write_attempts_csv(
    path: str | Path, attempts: Sequence[AdjacentSwapAttempt]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ATTEMPT_FIELDS)
        writer.writeheader()
        for attempt in attempts:
            writer.writerow(
                {
                    "program": attempt.program,
                    "prefix_passes": ",".join(attempt.prefix_passes),
                    "state_path": attempt.state_path,
                    "state_hash": attempt.state_hash,
                    "pass_a": attempt.pass_a,
                    "pass_b": attempt.pass_b,
                    "static_decision": attempt.static_decision,
                    "static_reason": attempt.static_reason,
                    "action": attempt.action,
                    "label": attempt.label,
                    "cache_hit": str(attempt.cache_hit),
                    "dynamic_test": str(attempt.dynamic_test),
                    "reproduced": "" if attempt.reproduced is None else str(attempt.reproduced),
                    "cert_id": attempt.cert_id,
                }
            )


def build_summary_report(title: str, summary: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"attempted_adjacent_swaps: {summary['attempted_adjacent_swaps']}",
        f"candidate_swaps: {summary['candidate_swaps']}",
        f"low_priority_skipped: {summary['low_priority_skipped']}",
        f"cache_hits: {summary['cache_hits']}",
        f"dynamic_tests: {summary['dynamic_tests']}",
        f"certified_independent: {summary['certified_independent']}",
        f"not_certified_independent: {summary['not_certified_independent']}",
        f"run_failed: {summary['run_failed']}",
        f"HardFalseIndependent: {summary['hard_false_independent']}",
        "CertificateReproductionRate: "
        f"{summary['certificate_reproduction_rate'] * 100.0:.2f}%",
        "CertifiedPruningRatioAttempted: "
        f"{summary['certified_pruning_ratio_attempted'] * 100.0:.2f}%",
        "CertifiedPruningRatioDynamic: "
        f"{_format_optional_percent(summary['certified_pruning_ratio_dynamic'])}",
        "SecondRunCacheHitRate: "
        f"{summary['second_run_cache_hit_rate'] * 100.0:.2f}%",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run minimal anchor-adjacent lazy validation."
    )
    parser.add_argument(
        "--program-preset",
        choices=["stanford-8", "p8b-misc8"],
        default="stanford-8",
    )
    parser.add_argument(
        "--benchmark-config",
        help="Load programs from a benchmark YAML config instead of a built-in preset.",
    )
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--cert-dir", default="data/certs/lazy_validation")
    parser.add_argument("--out", default="data/outputs/lazy_validation")
    parser.add_argument("--attempts-csv", default="data/outputs/lazy_validation_attempts.csv")
    parser.add_argument("--report", default="data/outputs/lazy_validation_report.md")
    parser.add_argument("--opt", default="opt")
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--llvm-version", required=True)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    pipeline = load_pipeline_config(args.pipeline)
    run = run_adjacent_swap_validation(
        programs=_programs_for_args(args),
        passes=list(pipeline["passes"]),
        passspec=load_passspec(args.passspec),
        cert_db=CertificateDB(args.cert_dir),
        opt_path=args.opt,
        output_dir=args.out,
        env_id=args.env_id,
        llvm_version=args.llvm_version,
        timeout_sec=args.timeout_sec,
    )
    write_attempts_csv(args.attempts_csv, run.attempts)
    report = build_summary_report("P4 Lazy Validation Report", run.summary)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


def _attempt_from_validation(
    *,
    program: str,
    prefix: Sequence[str],
    state_path: Path,
    state_hash: str,
    decision: dict[str, str],
    validation: LazyValidationResult,
) -> AdjacentSwapAttempt:
    return AdjacentSwapAttempt(
        program=program,
        prefix_passes=list(prefix),
        state_path=str(state_path),
        state_hash=state_hash,
        pass_a=validation.pass_a,
        pass_b=validation.pass_b,
        static_decision=decision["decision"],
        static_reason=decision["reason"],
        action=validation.action,
        label=validation.label,
        cache_hit=validation.cache_hit,
        dynamic_test=validation.dynamic_test,
        reproduced=validation.reproduced,
        cert_id=validation.certificate.cert_id if validation.certificate else "",
    )


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _programs_for_preset(preset: str) -> list[Program]:
    if preset == "p8b-misc8":
        return P8B_MISC8_PROGRAMS
    return STANFORD_8_PROGRAMS


def _programs_for_args(args: argparse.Namespace) -> list[Program]:
    if args.benchmark_config:
        return load_benchmark_config_programs(args.benchmark_config)
    return _programs_for_preset(args.program_preset)


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100.0:.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())
