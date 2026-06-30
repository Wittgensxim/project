"""Batch adjacent-swap certificate generation."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Sequence

from .environment import DEFAULT_EXECUTION_MODEL
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

DEFAULT_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("simplifycfg", "instcombine"),
    ("sroa", "early-cse"),
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
    summary = dict(label_counts)
    summary["total"] = len(rows)
    summary["reproduced"] = reproduced_count
    summary["hard_false_independent"] = hard_false_independent
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a certificate matrix.")
    parser.add_argument(
        "--preset",
        choices=["stanford-3x3"],
        default="stanford-3x3",
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

    rows = run_certificate_matrix(
        programs=DEFAULT_STANFORD_PROGRAMS,
        pass_pairs=DEFAULT_PASS_PAIRS,
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
        "total={total} reproduced={reproduced} hard_false_independent={hard_false_independent}".format(
            **summary
        )
    )
    for label, count in sorted(summary.items()):
        if label not in {"total", "reproduced", "hard_false_independent"}:
            print(f"{label}={count}")
    return 0


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


if __name__ == "__main__":
    raise SystemExit(main())
