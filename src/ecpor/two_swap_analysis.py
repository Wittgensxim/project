"""Offline analysis for bounded two-swap experiment outputs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Sequence

from .pipeline_dedup import pipeline_sequence_hash


PROGRAM_SUMMARY_FIELDS = [
    "program",
    "selected_seeds",
    "selected_smaller_seeds",
    "selected_equal_seeds",
    "attempted_second_swaps",
    "static_candidate_second_swaps",
    "low_priority_skipped",
    "validated_second_swaps",
    "certified_independent",
    "not_certified_independent",
    "raw_depth2_candidates",
    "duplicate_sequences",
    "unique_depth2_candidates",
    "depth2_smaller_text",
    "depth2_equal_text",
    "depth2_larger_text",
    "best_depth1_text_delta_pct",
    "best_depth2_text_delta_pct",
    "depth2_improves_program_depth1_best",
]

PAIR_SUMMARY_FIELDS = [
    "pass_a",
    "pass_b",
    "attempts",
    "certified_independent",
    "not_certified_independent",
    "raw_depth2_candidates",
    "unique_depth2_candidates",
    "depth2_smaller_text",
    "depth2_equal_text",
    "depth2_larger_text",
    "avg_text_delta_pct",
    "best_text_delta_pct",
]

DEPTH2_DETAIL_FIELDS = [
    "program",
    "candidate_id",
    "parent_candidate_id",
    "parent_text_delta_pct",
    "depth2_text_delta_pct",
    "delta_pct_vs_parent",
    "swap_path",
    "second_swap_index",
    "pass_a",
    "pass_b",
    "candidate_pipeline",
    "parent_pipeline",
    "pipeline_sequence_hash",
    "depth2_improves_program_depth1_best",
    "depth2_improves_global_depth1_best",
]

CACHE_AUDIT_FIELDS = [
    "program",
    "seed_candidate_id",
    "swap_index",
    "pass_a",
    "pass_b",
    "prefix_state_hash",
    "env_id",
    "execution_model",
    "normalizer_version",
    "nesting",
    "region_id",
    "extra_flags",
    "cache_hit",
    "cert_id",
    "matched_previous_program",
    "matched_previous_seed_candidate_id",
    "matched_previous_swap_index",
]

DUPLICATE_AUDIT_FIELDS = [
    "pipeline_sequence_hash",
    "kept_candidate_id",
    "duplicate_candidate_id",
    "kept_parent",
    "duplicate_parent",
    "kept_swap_path",
    "duplicate_swap_path",
    "candidate_pipeline",
    "duplicate_type",
]


@dataclass(frozen=True)
class TwoSwapAnalysis:
    program_rows: list[dict[str, str]]
    pair_rows: list[dict[str, str]]
    depth2_detail_rows: list[dict[str, str]]
    cache_audit_rows: list[dict[str, str]]
    duplicate_audit_rows: list[dict[str, str]]
    summary: dict[str, Any]


def run_two_swap_analysis(
    *,
    seeds_csv: str | Path,
    attempts_csv: str | Path,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    object_size_csv: str | Path,
    p6_object_size_csv: str | Path,
    output_dir: str | Path,
) -> TwoSwapAnalysis:
    seeds = _load_csv(seeds_csv)
    attempts = _load_csv(attempts_csv)
    candidates = _load_csv(candidates_csv)
    pipeline_runs = _load_csv(pipeline_runs_csv)
    object_rows = _load_csv(object_size_csv)
    p6_rows = _load_csv(p6_object_size_csv)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    raw_depth2_rows = _raw_depth2_rows(attempts, seeds=seeds, p6_rows=p6_rows)
    depth2_rows = [row for row in candidates if row.get("source") == "two_swap"]
    program_rows = _build_program_summary(
        seeds=seeds,
        attempts=attempts,
        depth2_rows=depth2_rows,
        object_rows=object_rows,
        p6_rows=p6_rows,
        raw_depth2_rows=raw_depth2_rows,
    )
    pair_rows = _build_pair_summary(
        attempts=attempts,
        depth2_rows=depth2_rows,
        object_rows=object_rows,
        raw_depth2_rows=raw_depth2_rows,
    )
    depth2_detail_rows = _build_depth2_details(
        seeds=seeds,
        depth2_rows=depth2_rows,
        object_rows=object_rows,
        p6_rows=p6_rows,
    )
    cache_audit_rows = _build_cache_audit(attempts)
    duplicate_audit_rows = _build_duplicate_audit(
        raw_depth2_rows=raw_depth2_rows,
        depth2_rows=depth2_rows,
    )
    summary = _build_summary(
        program_rows=program_rows,
        pair_rows=pair_rows,
        depth2_detail_rows=depth2_detail_rows,
        cache_audit_rows=cache_audit_rows,
        duplicate_audit_rows=duplicate_audit_rows,
        pipeline_runs=pipeline_runs,
    )

    _write_csv(output_root / "p7b_program_summary.csv", program_rows, PROGRAM_SUMMARY_FIELDS)
    _write_csv(output_root / "p7b_pair_summary.csv", pair_rows, PAIR_SUMMARY_FIELDS)
    _write_csv(
        output_root / "p7b_depth2_details.csv",
        depth2_detail_rows,
        DEPTH2_DETAIL_FIELDS,
    )
    _write_csv(output_root / "p7b_cache_audit.csv", cache_audit_rows, CACHE_AUDIT_FIELDS)
    _write_csv(
        output_root / "p7b_duplicate_audit.csv",
        duplicate_audit_rows,
        DUPLICATE_AUDIT_FIELDS,
    )
    (output_root / "p7b_analysis_report.md").write_text(
        build_analysis_report(summary, program_rows, depth2_detail_rows),
        encoding="utf-8",
    )
    return TwoSwapAnalysis(
        program_rows=program_rows,
        pair_rows=pair_rows,
        depth2_detail_rows=depth2_detail_rows,
        cache_audit_rows=cache_audit_rows,
        duplicate_audit_rows=duplicate_audit_rows,
        summary=summary,
    )


def build_analysis_report(
    summary: dict[str, Any],
    program_rows: Sequence[dict[str, str]],
    depth2_detail_rows: Sequence[dict[str, str]],
) -> str:
    lines = [
        "# P7b.5 Two-Swap Analysis Report",
        "",
        "P7b.5 explains the existing P7b bounded two-swap results.",
        "It does not run LLVM and it does not generate new certificates.",
        "",
        f"Programs: {summary['programs']}",
        f"SelectedSeeds: {summary['selected_seeds']}",
        f"RawDepth2Candidates: {summary['raw_depth2_candidates']}",
        f"UniqueDepth2Candidates: {summary['unique_depth2_candidates']}",
        f"DuplicateSequences: {summary['duplicate_sequences']}",
        f"DuplicateSequenceRate: {summary['duplicate_sequence_rate'] * 100.0:.2f}%",
        f"Depth2SmallerText: {summary['depth2_smaller_text']}",
        f"Depth2EqualText: {summary['depth2_equal_text']}",
        f"Depth2LargerText: {summary['depth2_larger_text']}",
        f"Depth2SmallerPrograms: {summary['depth2_smaller_programs']}",
        "Depth2SmallerFromSameParent: "
        f"{summary['depth2_smaller_from_same_parent']}",
        "Depth2ImprovesProgramDepth1Best: "
        f"{summary['depth2_improves_program_depth1_best_count']}",
        "Depth2ImprovesGlobalDepth1Best: "
        f"{summary['depth2_improves_global_depth1_best_count']}",
        f"FirstRunCacheHits: {summary['first_run_cache_hits']}",
        f"PipelineRuns: {summary['pipeline_runs']}",
        f"PipelineRunFailed: {summary['pipeline_run_failed']}",
        "",
        "## Per-program",
    ]
    for row in program_rows:
        lines.append(
            "{program}: seeds={seeds} raw_depth2={raw} unique_depth2={unique} "
            "smaller={smaller} best_depth1={d1} best_depth2={d2} improves={improves}".format(
                program=row["program"],
                seeds=row["selected_seeds"],
                raw=row["raw_depth2_candidates"],
                unique=row["unique_depth2_candidates"],
                smaller=row["depth2_smaller_text"],
                d1=row["best_depth1_text_delta_pct"],
                d2=row["best_depth2_text_delta_pct"],
                improves=row["depth2_improves_program_depth1_best"],
            )
        )
    smaller = [
        row
        for row in depth2_detail_rows
        if (_parse_optional_float(row.get("depth2_text_delta_pct")) or 0.0) < 0.0
    ]
    lines.extend(["", "## Smaller Depth2 Candidates"])
    if not smaller:
        lines.append("none")
    for row in smaller:
        lines.append(
            "{program}: {candidate_id} parent={parent} pair={a},{b} "
            "parent_delta={parent_delta} depth2_delta={depth2_delta} "
            "vs_parent={vs_parent} program_best={program_best}".format(
                program=row["program"],
                candidate_id=row["candidate_id"],
                parent=row["parent_candidate_id"],
                a=row["pass_a"],
                b=row["pass_b"],
                parent_delta=row["parent_text_delta_pct"],
                depth2_delta=row["depth2_text_delta_pct"],
                vs_parent=row["delta_pct_vs_parent"],
                program_best=row["depth2_improves_program_depth1_best"],
            )
        )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze P7b two-swap outputs.")
    parser.add_argument("--p7-dir", default="data/outputs/bounded_two_swap_p7b")
    parser.add_argument(
        "--p6-object-size",
        default="data/outputs/code_size_p6_final/object_size.csv",
    )
    parser.add_argument("--out", default="data/outputs/bounded_two_swap_p7b_analysis")
    args = parser.parse_args(argv)

    p7_dir = Path(args.p7_dir)
    result = run_two_swap_analysis(
        seeds_csv=p7_dir / "two_swap_seeds.csv",
        attempts_csv=p7_dir / "two_swap_attempts.csv",
        candidates_csv=p7_dir / "two_swap_candidates.csv",
        pipeline_runs_csv=p7_dir / "two_swap_pipeline_runs.csv",
        object_size_csv=p7_dir / "two_swap_object_size.csv",
        p6_object_size_csv=args.p6_object_size,
        output_dir=args.out,
    )
    print(
        build_analysis_report(
            result.summary,
            result.program_rows,
            result.depth2_detail_rows,
        ),
        end="",
    )
    return 0


def _build_program_summary(
    *,
    seeds: Sequence[dict[str, str]],
    attempts: Sequence[dict[str, str]],
    depth2_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    p6_rows: Sequence[dict[str, str]],
    raw_depth2_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    programs = sorted(
        {
            row.get("program", "")
            for row in [*seeds, *attempts, *depth2_rows, *p6_rows]
            if row.get("program", "")
        }
    )
    depth2_object_by_id = {
        row.get("candidate_id", ""): row
        for row in object_rows
        if row.get("source") == "two_swap"
    }
    depth2_by_program = _group_by(depth2_rows, "program")
    raw_by_program = _group_by(raw_depth2_rows, "program")
    rows: list[dict[str, str]] = []
    for program in programs:
        program_seeds = [row for row in seeds if row.get("program") == program]
        program_attempts = [row for row in attempts if row.get("program") == program]
        program_depth2 = depth2_by_program.get(program, [])
        depth2_object_rows = [
            depth2_object_by_id.get(row.get("candidate_id", ""), {})
            for row in program_depth2
        ]
        raw_count = len(raw_by_program.get(program, []))
        unique_count = len(program_depth2)
        best_depth1 = _best_depth1(program, p6_rows)
        best_depth2 = _best_text_delta(depth2_object_rows)
        rows.append(
            {
                "program": program,
                "selected_seeds": str(len(program_seeds)),
                "selected_smaller_seeds": str(_count_delta(program_seeds, "smaller")),
                "selected_equal_seeds": str(_count_delta(program_seeds, "equal")),
                "attempted_second_swaps": str(len(program_attempts)),
                "static_candidate_second_swaps": str(
                    _count_value(program_attempts, "static_decision", "candidate")
                ),
                "low_priority_skipped": str(
                    _count_value(program_attempts, "action", "skipped_low_priority")
                ),
                "validated_second_swaps": str(
                    sum(
                        1
                        for row in program_attempts
                        if row.get("cache_hit") == "True"
                        or row.get("dynamic_test") == "True"
                    )
                ),
                "certified_independent": str(
                    _count_value(program_attempts, "label", "certified_independent")
                ),
                "not_certified_independent": str(
                    _count_value(
                        program_attempts,
                        "label",
                        "not_certified_independent",
                    )
                ),
                "raw_depth2_candidates": str(raw_count),
                "duplicate_sequences": str(max(raw_count - unique_count, 0)),
                "unique_depth2_candidates": str(unique_count),
                "depth2_smaller_text": str(
                    _count_delta(depth2_object_rows, "smaller")
                ),
                "depth2_equal_text": str(_count_delta(depth2_object_rows, "equal")),
                "depth2_larger_text": str(_count_delta(depth2_object_rows, "larger")),
                "best_depth1_text_delta_pct": _format_optional_float(best_depth1),
                "best_depth2_text_delta_pct": _format_optional_float(best_depth2),
                "depth2_improves_program_depth1_best": str(
                    best_depth1 is not None
                    and best_depth2 is not None
                    and best_depth2 < best_depth1
                ),
            }
        )
    return rows


def _build_pair_summary(
    *,
    attempts: Sequence[dict[str, str]],
    depth2_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    raw_depth2_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    pair_keys = sorted(
        {
            _pair_key(row.get("pass_a", ""), row.get("pass_b", ""))
            for row in [*attempts, *depth2_rows]
            if row.get("pass_a", "") and row.get("pass_b", "")
        }
    )
    depth2_by_id = {row.get("candidate_id", ""): row for row in depth2_rows}
    object_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in object_rows:
        candidate = depth2_by_id.get(row.get("candidate_id", ""))
        if not candidate:
            continue
        object_by_pair[_pair_key(candidate["pass_a"], candidate["pass_b"])].append(row)
    rows: list[dict[str, str]] = []
    for pair in pair_keys:
        pair_attempts = [
            row for row in attempts if _pair_key(row.get("pass_a", ""), row.get("pass_b", "")) == pair
        ]
        pair_depth2 = [
            row for row in depth2_rows if _pair_key(row.get("pass_a", ""), row.get("pass_b", "")) == pair
        ]
        pair_raw = [
            row for row in raw_depth2_rows if _pair_key(row.get("pass_a", ""), row.get("pass_b", "")) == pair
        ]
        pct_values = [
            value
            for value in (
                _parse_optional_float(row.get("text_delta_pct"))
                for row in object_by_pair.get(pair, [])
            )
            if value is not None
        ]
        object_pair_rows = object_by_pair.get(pair, [])
        rows.append(
            {
                "pass_a": pair[0],
                "pass_b": pair[1],
                "attempts": str(len(pair_attempts)),
                "certified_independent": str(
                    _count_value(pair_attempts, "label", "certified_independent")
                ),
                "not_certified_independent": str(
                    _count_value(pair_attempts, "label", "not_certified_independent")
                ),
                "raw_depth2_candidates": str(len(pair_raw)),
                "unique_depth2_candidates": str(len(pair_depth2)),
                "depth2_smaller_text": str(
                    _count_delta(object_pair_rows, "smaller")
                ),
                "depth2_equal_text": str(_count_delta(object_pair_rows, "equal")),
                "depth2_larger_text": str(_count_delta(object_pair_rows, "larger")),
                "avg_text_delta_pct": _format_optional_float(
                    mean(pct_values) if pct_values else None
                ),
                "best_text_delta_pct": _format_optional_float(
                    min(pct_values) if pct_values else None
                ),
            }
        )
    return rows


def _build_depth2_details(
    *,
    seeds: Sequence[dict[str, str]],
    depth2_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
    p6_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    seed_by_id = {
        row.get("seed_candidate_id") or row.get("candidate_id", ""): row
        for row in seeds
    }
    p6_by_id = {row.get("candidate_id", ""): row for row in p6_rows}
    object_by_id = {row.get("candidate_id", ""): row for row in object_rows}
    global_best_depth1 = _best_depth1(None, p6_rows)
    rows: list[dict[str, str]] = []
    for row in depth2_rows:
        candidate_id = row.get("candidate_id", "")
        parent_id = row.get("parent_candidate_id", "")
        object_row = object_by_id.get(candidate_id, {})
        depth2_pct = _parse_optional_float(object_row.get("text_delta_pct"))
        parent_pct = _parse_optional_float(p6_by_id.get(parent_id, {}).get("text_delta_pct"))
        program_best = _best_depth1(row.get("program", ""), p6_rows)
        delta_vs_parent = (
            None if depth2_pct is None or parent_pct is None else depth2_pct - parent_pct
        )
        sequence_hash = row.get("pipeline_sequence_hash") or pipeline_sequence_hash(
            _split_pipeline(row.get("candidate_pipeline", ""))
        )
        rows.append(
            {
                "program": row.get("program", ""),
                "candidate_id": candidate_id,
                "parent_candidate_id": parent_id,
                "parent_text_delta_pct": _format_optional_float(parent_pct),
                "depth2_text_delta_pct": _format_optional_float(depth2_pct),
                "delta_pct_vs_parent": _format_optional_float(delta_vs_parent),
                "swap_path": row.get("swap_path", ""),
                "second_swap_index": row.get("swap_index", ""),
                "pass_a": row.get("pass_a", ""),
                "pass_b": row.get("pass_b", ""),
                "candidate_pipeline": row.get("candidate_pipeline", ""),
                "parent_pipeline": seed_by_id.get(parent_id, {}).get("seed_pipeline", ""),
                "pipeline_sequence_hash": sequence_hash,
                "depth2_improves_program_depth1_best": str(
                    depth2_pct is not None
                    and program_best is not None
                    and depth2_pct < program_best
                ),
                "depth2_improves_global_depth1_best": str(
                    depth2_pct is not None
                    and global_best_depth1 is not None
                    and depth2_pct < global_best_depth1
                ),
            }
        )
    return rows


def _build_cache_audit(attempts: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    previous_by_key: dict[tuple[str, tuple[str, str], str, str, str, str, str, str], dict[str, str]] = {}
    rows: list[dict[str, str]] = []
    for attempt in attempts:
        key = (
            attempt.get("state_hash", ""),
            _pair_key(attempt.get("pass_a", ""), attempt.get("pass_b", "")),
            attempt.get("env_id", ""),
            attempt.get("execution_model", ""),
            attempt.get("normalizer_version", ""),
            attempt.get("nesting", ""),
            attempt.get("region_id", ""),
            attempt.get("extra_flags", ""),
        )
        previous = previous_by_key.get(key, {})
        rows.append(
            {
                "program": attempt.get("program", ""),
                "seed_candidate_id": attempt.get("seed_candidate_id", ""),
                "swap_index": attempt.get("swap_index", ""),
                "pass_a": attempt.get("pass_a", ""),
                "pass_b": attempt.get("pass_b", ""),
                "prefix_state_hash": attempt.get("state_hash", ""),
                "env_id": attempt.get("env_id", ""),
                "execution_model": attempt.get("execution_model", ""),
                "normalizer_version": attempt.get("normalizer_version", ""),
                "nesting": attempt.get("nesting", ""),
                "region_id": attempt.get("region_id", ""),
                "extra_flags": attempt.get("extra_flags", ""),
                "cache_hit": attempt.get("cache_hit", ""),
                "cert_id": attempt.get("cert_id", ""),
                "matched_previous_program": previous.get("program", ""),
                "matched_previous_seed_candidate_id": previous.get(
                    "seed_candidate_id", ""
                ),
                "matched_previous_swap_index": previous.get("swap_index", ""),
            }
        )
        if attempt.get("cert_id"):
            previous_by_key.setdefault(key, attempt)
    return rows


def _build_duplicate_audit(
    *,
    raw_depth2_rows: Sequence[dict[str, str]],
    depth2_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    kept_by_key = {
        (row.get("program", ""), row.get("pipeline_sequence_hash", "")): row
        for row in _ensure_sequence_hash(depth2_rows)
    }
    rows: list[dict[str, str]] = []
    for raw in _ensure_sequence_hash(raw_depth2_rows):
        key = (raw.get("program", ""), raw.get("pipeline_sequence_hash", ""))
        kept = kept_by_key.get(key)
        if kept and kept.get("candidate_id", "") == raw.get("candidate_id", ""):
            continue
        rows.append(
            {
                "pipeline_sequence_hash": raw.get("pipeline_sequence_hash", ""),
                "kept_candidate_id": kept.get("candidate_id", "") if kept else "",
                "duplicate_candidate_id": raw.get("candidate_id", ""),
                "kept_parent": kept.get("parent_candidate_id", "") if kept else "",
                "duplicate_parent": raw.get("parent_candidate_id", ""),
                "kept_swap_path": kept.get("swap_path", "") if kept else "",
                "duplicate_swap_path": raw.get("swap_path", ""),
                "candidate_pipeline": raw.get("candidate_pipeline", ""),
                "duplicate_type": "depth2_duplicate" if kept else "reserved_or_existing_sequence",
            }
        )
    return rows


def _build_summary(
    *,
    program_rows: Sequence[dict[str, str]],
    pair_rows: Sequence[dict[str, str]],
    depth2_detail_rows: Sequence[dict[str, str]],
    cache_audit_rows: Sequence[dict[str, str]],
    duplicate_audit_rows: Sequence[dict[str, str]],
    pipeline_runs: Sequence[dict[str, str]],
) -> dict[str, Any]:
    raw = sum(_parse_int(row["raw_depth2_candidates"]) for row in program_rows)
    unique = sum(_parse_int(row["unique_depth2_candidates"]) for row in program_rows)
    duplicate = len(duplicate_audit_rows)
    return {
        "programs": len(program_rows),
        "selected_seeds": sum(_parse_int(row["selected_seeds"]) for row in program_rows),
        "selected_smaller_seeds": sum(
            _parse_int(row["selected_smaller_seeds"]) for row in program_rows
        ),
        "selected_equal_seeds": sum(
            _parse_int(row["selected_equal_seeds"]) for row in program_rows
        ),
        "attempted_second_swaps": sum(
            _parse_int(row["attempted_second_swaps"]) for row in program_rows
        ),
        "validated_second_swaps": sum(
            _parse_int(row["validated_second_swaps"]) for row in program_rows
        ),
        "raw_depth2_candidates": raw,
        "unique_depth2_candidates": unique,
        "duplicate_sequences": duplicate,
        "duplicate_sequence_rate": duplicate / raw if raw else 0.0,
        "depth2_smaller_text": sum(
            _parse_int(row["depth2_smaller_text"]) for row in program_rows
        ),
        "depth2_equal_text": sum(
            _parse_int(row["depth2_equal_text"]) for row in program_rows
        ),
        "depth2_larger_text": sum(
            _parse_int(row["depth2_larger_text"]) for row in program_rows
        ),
        "depth2_smaller_programs": sum(
            1 for row in program_rows if _parse_int(row["depth2_smaller_text"]) > 0
        ),
        "depth2_smaller_from_same_parent": _max_smaller_from_same_parent(
            depth2_detail_rows
        ),
        "depth2_improves_program_depth1_best_count": sum(
            1
            for row in depth2_detail_rows
            if row.get("depth2_improves_program_depth1_best") == "True"
        ),
        "depth2_improves_global_depth1_best_count": sum(
            1
            for row in depth2_detail_rows
            if row.get("depth2_improves_global_depth1_best") == "True"
        ),
        "first_run_cache_hits": sum(
            1 for row in cache_audit_rows if row.get("cache_hit") == "True"
        ),
        "pair_rows": len(pair_rows),
        "pipeline_runs": len(pipeline_runs),
        "pipeline_run_failed": sum(
            1 for row in pipeline_runs if row.get("failure_kind", "")
        ),
    }


def _max_smaller_from_same_parent(rows: Sequence[dict[str, str]]) -> int:
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        delta = _parse_optional_float(row.get("depth2_text_delta_pct"))
        if delta is None or delta >= 0.0:
            continue
        counts[(row.get("program", ""), row.get("parent_candidate_id", ""))] += 1
    return max(counts.values(), default=0)


def _raw_depth2_rows(
    attempts: Sequence[dict[str, str]],
    *,
    seeds: Sequence[dict[str, str]],
    p6_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    p6_by_id = {row.get("candidate_id", ""): row for row in p6_rows}
    rows: list[dict[str, str]] = []
    for attempt in attempts:
        if attempt.get("label") != "not_certified_independent":
            continue
        seed_pipeline = _split_pipeline(attempt.get("seed_pipeline", ""))
        swap_index = _parse_optional_int(attempt.get("swap_index"))
        if swap_index is None or swap_index >= len(seed_pipeline) - 1:
            continue
        candidate_passes = list(seed_pipeline)
        candidate_passes[swap_index], candidate_passes[swap_index + 1] = (
            candidate_passes[swap_index + 1],
            candidate_passes[swap_index],
        )
        candidate_pipeline = ",".join(candidate_passes)
        seed_id = attempt.get("seed_candidate_id", "")
        seed_swap = p6_by_id.get(seed_id, {}).get("swap_index", "")
        swap_path = ";".join(
            part for part in [seed_swap, str(swap_index)] if part not in {"", None}
        )
        rows.append(
            {
                "program": attempt.get("program", ""),
                "candidate_id": (
                    f"{_safe_name(attempt.get('program', ''))}__depth2__"
                    f"{_safe_name(seed_id)}__swap_{swap_index}__"
                    f"{_safe_name(attempt.get('pass_a', ''))}__"
                    f"{_safe_name(attempt.get('pass_b', ''))}"
                ),
                "depth": "2",
                "parent_candidate_id": seed_id,
                "source": "two_swap",
                "candidate_pipeline": candidate_pipeline,
                "pipeline_sequence_hash": pipeline_sequence_hash(candidate_passes),
                "swap_index": str(swap_index),
                "pass_a": attempt.get("pass_a", ""),
                "pass_b": attempt.get("pass_b", ""),
                "prefix_state_hash": attempt.get("state_hash", ""),
                "validation_label": attempt.get("label", ""),
                "cert_id": attempt.get("cert_id", ""),
                "swap_path": swap_path,
            }
        )
    return rows


def _ensure_sequence_hash(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for row in rows:
        sequence_hash = row.get("pipeline_sequence_hash") or pipeline_sequence_hash(
            _split_pipeline(row.get("candidate_pipeline", ""))
        )
        result.append({**row, "pipeline_sequence_hash": sequence_hash})
    return result


def _best_depth1(program: str | None, rows: Sequence[dict[str, str]]) -> float | None:
    values = [
        value
        for value in (
            _parse_optional_float(row.get("text_delta_pct"))
            for row in rows
            if row.get("source") == "single_swap"
            and (program is None or row.get("program") == program)
        )
        if value is not None
    ]
    return min(values) if values else None


def _best_text_delta(rows: Sequence[dict[str, str]]) -> float | None:
    values = [
        value
        for value in (_parse_optional_float(row.get("text_delta_pct")) for row in rows)
        if value is not None
    ]
    return min(values) if values else None


def _count_delta(rows: Sequence[dict[str, str]], kind: str) -> int:
    count = 0
    for row in rows:
        value = _parse_optional_float(
            row.get("seed_text_delta_pct") or row.get("text_delta_pct")
        )
        if value is None:
            continue
        if kind == "smaller" and value < 0.0:
            count += 1
        elif kind == "equal" and value == 0.0:
            count += 1
        elif kind == "larger" and value > 0.0:
            count += 1
    return count


def _count_value(rows: Sequence[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if row.get(field) == value)


def _group_by(
    rows: Sequence[dict[str, str]], field: str
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field, "")].append(row)
    return grouped


def _pair_key(pass_a: str, pass_b: str) -> tuple[str, str]:
    return tuple(sorted((pass_a, pass_b)))


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _split_pipeline(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _parse_int(value: str | int | None) -> int:
    if value in {None, ""}:
        return 0
    return int(value)


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value))


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


if __name__ == "__main__":
    raise SystemExit(main())
