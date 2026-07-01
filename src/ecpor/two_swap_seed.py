"""Seed selection helpers for bounded two-swap experiments."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence


SEED_MODES = {"smaller-only", "top-k-per-program"}

P7_SEED_FIELDS = [
    "program",
    "candidate_id",
    "source",
    "seed_candidate_id",
    "seed_pipeline",
    "seed_text_delta_pct",
    "seed_rank",
    "seed_reason",
    "text_delta_pct",
]


def select_seed_rows(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
    *,
    seed_mode: str = "smaller-only",
    max_seeds_per_program: int = 3,
) -> list[dict[str, str]]:
    if seed_mode not in SEED_MODES:
        raise ValueError(
            f"unknown seed_mode {seed_mode!r}; expected one of {sorted(SEED_MODES)}"
        )
    if max_seeds_per_program < 1:
        raise ValueError("max_seeds_per_program must be >= 1")
    if seed_mode == "smaller-only":
        return _select_smaller_only(p6_rows, p5_candidate_by_id)
    return _select_top_k_per_program(
        p6_rows,
        p5_candidate_by_id,
        max_seeds_per_program=max_seeds_per_program,
    )


def write_seed_csv(path: str | Path, rows: Sequence[dict[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=P7_SEED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _select_smaller_only(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    seeds = [
        row
        for row in p6_rows
        if row.get("source") == "single_swap"
        and _parse_optional_float(row.get("text_delta_pct")) is not None
        and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) < 0.0
        and row.get("candidate_id", "") in p5_candidate_by_id
    ]
    ordered = sorted(
        seeds, key=lambda row: _parse_optional_float(row["text_delta_pct"]) or 0.0
    )
    return [
        _seed_row(
            row,
            p5_candidate_by_id[row["candidate_id"]],
            rank=index,
            reason="smaller_text",
        )
        for index, row in enumerate(ordered, start=1)
    ]


def _select_top_k_per_program(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
    *,
    max_seeds_per_program: int,
) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in p6_rows:
        text_delta_pct = _parse_optional_float(row.get("text_delta_pct"))
        if (
            row.get("source") != "single_swap"
            or text_delta_pct is None
            or text_delta_pct > 0.0
            or row.get("candidate_id", "") not in p5_candidate_by_id
        ):
            continue
        grouped.setdefault(row.get("program", ""), []).append(row)

    selected: list[dict[str, str]] = []
    for program in sorted(grouped):
        rows = sorted(
            grouped[program],
            key=lambda row: (
                _parse_optional_float(row.get("text_delta_pct")) or 0.0,
                row.get("candidate_id", ""),
            ),
        )
        if not rows:
            continue
        chosen: list[tuple[dict[str, str], str]] = []
        best = rows[0]
        best_pct = _parse_optional_float(best.get("text_delta_pct")) or 0.0
        best_reason = (
            "best_text_delta" if best_pct < 0.0 else "best_equal_text_delta"
        )
        chosen.append((best, best_reason))
        chosen_ids = {best.get("candidate_id", "")}

        equal_rows = [
            row
            for row in rows
            if row.get("candidate_id", "") not in chosen_ids
            and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) == 0.0
        ]
        for row in sorted(equal_rows, key=lambda item: item.get("candidate_id", "")):
            if len(chosen) >= max_seeds_per_program:
                break
            chosen.append((row, "equal_text_representative"))

        for rank, (row, reason) in enumerate(chosen, start=1):
            selected.append(
                _seed_row(
                    row,
                    p5_candidate_by_id[row["candidate_id"]],
                    rank=rank,
                    reason=reason,
                )
            )
    return selected


def _seed_row(
    p6_row: dict[str, str],
    p5_row: dict[str, str],
    *,
    rank: int,
    reason: str,
) -> dict[str, str]:
    text_delta_pct = p6_row.get("text_delta_pct", "")
    return {
        **p6_row,
        "seed_candidate_id": p6_row.get("candidate_id", ""),
        "seed_pipeline": p5_row.get("candidate_pipeline", ""),
        "seed_text_delta_pct": text_delta_pct,
        "seed_rank": str(rank),
        "seed_reason": reason,
        "text_delta_pct": text_delta_pct,
    }


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))
