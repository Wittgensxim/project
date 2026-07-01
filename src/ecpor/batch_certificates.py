"""Batch adjacent-swap certificate generation."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Sequence

from .environment import DEFAULT_EXECUTION_MODEL
from .feature_scan import diff_features, features_to_json, scan_ir_file
from .normalizer import NORMALIZER_VERSION
from .pair_test import reproduce_certificate, test_adjacent_swap
from .runner import OptPath


Program = tuple[str, str | Path]
PassPair = tuple[str, str]


DEFAULT_STANFORD_PROGRAMS: list[Program] = [
    ("testsuite_stanford_bubblesort", "data/inputs/testsuite_stanford_bubblesort.ll"),
    ("testsuite_stanford_intmm", "data/inputs/testsuite_stanford_intmm.ll"),
    ("testsuite_stanford_perm", "data/inputs/testsuite_stanford_perm.ll"),
]

HOLDOUT_STANFORD_PROGRAMS: list[Program] = [
    ("testsuite_stanford_oscar", "data/inputs/testsuite_stanford_oscar.ll"),
    ("testsuite_stanford_puzzle", "data/inputs/testsuite_stanford_puzzle.ll"),
    ("testsuite_stanford_queens", "data/inputs/testsuite_stanford_queens.ll"),
    ("testsuite_stanford_quicksort", "data/inputs/testsuite_stanford_quicksort.ll"),
    ("testsuite_stanford_towers", "data/inputs/testsuite_stanford_towers.ll"),
]

STANFORD_8_PROGRAMS: list[Program] = [
    *DEFAULT_STANFORD_PROGRAMS,
    *HOLDOUT_STANFORD_PROGRAMS,
]

SCALAR_PIPELINE_PASSES = [
    "sroa",
    "early-cse",
    "instcombine",
    "simplifycfg",
    "reassociate",
    "gvn",
    "dce",
    "adce",
]

STANFORD_3X3_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("simplifycfg", "instcombine"),
    ("sroa", "early-cse"),
]

DEFAULT_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("instcombine", "adce"),
    ("dce", "adce"),
    ("simplifycfg", "instcombine"),
    ("simplifycfg", "dce"),
    ("sroa", "early-cse"),
    ("sroa", "instcombine"),
    ("early-cse", "gvn"),
]

FULL_SCALAR_PASS_PAIRS: list[PassPair] = [
    (left, right) for left, right in combinations(SCALAR_PIPELINE_PASSES, 2)
]

SUMMARY_FIELDS = [
    "program",
    "pair_a",
    "pair_b",
    "label",
    "hard_equal",
    "hash_ab",
    "hash_ba",
    "exit_ab",
    "exit_ba",
    "failure_kind_ab",
    "failure_kind_ba",
    "elapsed_ab_ms",
    "elapsed_ba_ms",
    "cert_id",
    "reproduced",
    "env_id",
    "llvm_version",
    "normalizer_version",
    "execution_model",
    "nesting",
    "region_id",
    "input_state_hash",
    "ecpor_git_commit",
    "input_ir_path",
    "pipeline_ab",
    "pipeline_ba",
    "features_ab",
    "features_ba",
    "feature_delta",
]


def run_certificate_matrix(
    *,
    programs: Sequence[Program],
    pass_pairs: Sequence[PassPair],
    opt_path: OptPath,
    output_dir: str | Path,
    cert_dir: str | Path,
    summary_csv: str | Path,
    env_id: str,
    llvm_version: str,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] | None = None,
    timeout_sec: float = 30.0,
) -> list[dict[str, str]]:
    output_root = Path(output_dir)
    certificate_root = Path(cert_dir)
    certificate_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for program, input_ir in programs:
        for pass_a, pass_b in pass_pairs:
            cert = test_adjacent_swap(
                input_ir,
                pass_a,
                pass_b,
                opt_path=opt_path,
                output_dir=output_root,
                env_id=env_id,
                execution_model=execution_model,
                llvm_version=llvm_version,
                normalizer_version=normalizer_version,
                nesting=nesting,
                extra_flags=extra_flags,
                timeout_sec=timeout_sec,
            )
            cert_path = certificate_root / (
                f"{_safe_name(program)}__{_safe_name(pass_a)}__{_safe_name(pass_b)}.json"
            )
            cert.save(cert_path)

            reproduction = reproduce_certificate(
                cert_path,
                opt_path=opt_path,
                output_dir=output_root / "repro",
                timeout_sec=timeout_sec,
            )
            features_ab = _scan_output_features(cert.output_ab)
            features_ba = _scan_output_features(cert.output_ba)
            rows.append(
                {
                    "program": program,
                    "pair_a": pass_a,
                    "pair_b": pass_b,
                    "label": cert.label,
                    "hard_equal": str(cert.hard_equal),
                    "hash_ab": cert.hash_ab or "",
                    "hash_ba": cert.hash_ba or "",
                    "exit_ab": str(cert.exit_code_ab),
                    "exit_ba": str(cert.exit_code_ba),
                    "failure_kind_ab": cert.failure_kind_ab or "",
                    "failure_kind_ba": cert.failure_kind_ba or "",
                    "elapsed_ab_ms": f"{cert.elapsed_ab_ms:.3f}",
                    "elapsed_ba_ms": f"{cert.elapsed_ba_ms:.3f}",
                    "cert_id": cert.cert_id,
                    "reproduced": str(reproduction.reproduced),
                    "env_id": cert.env_id,
                    "llvm_version": cert.llvm_version,
                    "normalizer_version": cert.normalizer_version,
                    "execution_model": cert.execution_model,
                    "nesting": cert.nesting,
                    "region_id": cert.region_id,
                    "input_state_hash": cert.input_state_hash,
                    "ecpor_git_commit": cert.ecpor_git_commit,
                    "input_ir_path": cert.input_ir_path,
                    "pipeline_ab": cert.pipeline_ab,
                    "pipeline_ba": cert.pipeline_ba,
                    "features_ab": features_to_json(features_ab) if features_ab else "",
                    "features_ba": features_to_json(features_ba) if features_ba else "",
                    "feature_delta": (
                        features_to_json(diff_features(features_ab, features_ba))
                        if features_ab and features_ba
                        else ""
                    ),
                }
            )

    write_summary_csv(summary_csv, rows)
    return rows


def write_summary_csv(path: str | Path, rows: Sequence[dict[str, str]]) -> None:
    summary_path = Path(path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: Sequence[dict[str, str]]) -> dict[str, int]:
    label_counts = Counter(row["label"] for row in rows)
    reproduced_count = sum(1 for row in rows if row["reproduced"] == "True")
    hard_false_independent = sum(
        1
        for row in rows
        if row["label"] == "certified_independent" and row["hard_equal"] != "True"
    )
    certified_feature_mismatch = sum(
        1
        for row in rows
        if row["label"] == "certified_independent"
        and _has_nonzero_feature_delta(row.get("feature_delta", ""))
    )
    summary = dict(label_counts)
    summary["total"] = len(rows)
    summary["reproduced"] = reproduced_count
    summary["hard_false_independent"] = hard_false_independent
    summary["certified_feature_mismatch"] = certified_feature_mismatch
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a certificate matrix.")
    parser.add_argument(
        "--preset",
        choices=["stanford-3x3", "stanford-3x8", "stanford-3x28", "stanford-8x28"],
        default="stanford-3x8",
        help="Program/pass-pair preset to run.",
    )
    parser.add_argument("--opt", default="opt", help="opt executable or command prefix.")
    parser.add_argument(
        "--opt-arg",
        action="append",
        default=[],
        help="Additional opt command-prefix argument.",
    )
    parser.add_argument("--out", default="data/outputs/pair_tests")
    parser.add_argument("--cert-dir", default="data/certs/pair_tests")
    parser.add_argument("--summary", default="data/outputs/cert_summary.csv")
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--llvm-version", required=True)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    opt_path: OptPath
    if args.opt_arg:
        opt_path = [args.opt, *args.opt_arg]
    else:
        opt_path = args.opt

    pass_pairs = _preset_pass_pairs(args.preset)
    programs = _preset_programs(args.preset)
    rows = run_certificate_matrix(
        programs=programs,
        pass_pairs=pass_pairs,
        opt_path=opt_path,
        output_dir=args.out,
        cert_dir=args.cert_dir,
        summary_csv=args.summary,
        env_id=args.env_id,
        llvm_version=args.llvm_version,
        timeout_sec=args.timeout_sec,
    )
    summary = summarize_rows(rows)
    print(
        "total={total} reproduced={reproduced} hard_false_independent={hard_false_independent} certified_feature_mismatch={certified_feature_mismatch}".format(
            **summary
        )
    )
    for label, count in sorted(summary.items()):
        if label not in {
            "total",
            "reproduced",
            "hard_false_independent",
            "certified_feature_mismatch",
        }:
            print(f"{label}={count}")
    return 0


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _preset_pass_pairs(preset: str) -> list[PassPair]:
    if preset == "stanford-3x3":
        return STANFORD_3X3_PASS_PAIRS
    if preset in {"stanford-3x28", "stanford-8x28"}:
        return FULL_SCALAR_PASS_PAIRS
    return DEFAULT_PASS_PAIRS


def _preset_programs(preset: str) -> list[Program]:
    if preset == "stanford-8x28":
        return STANFORD_8_PROGRAMS
    return DEFAULT_STANFORD_PROGRAMS


def _scan_output_features(path: str | Path) -> dict[str, int | bool]:
    output = Path(path)
    if not output.exists():
        return {}
    return scan_ir_file(output)


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


if __name__ == "__main__":
    raise SystemExit(main())
