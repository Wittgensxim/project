"""Build bounded local pipeline candidates from P4 adjacent-swap evidence."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .static_filter import load_pipeline_config


CANDIDATE_FIELDS = [
    "program",
    "candidate_id",
    "source",
    "base_pipeline",
    "candidate_pipeline",
    "swap_index",
    "pass_a",
    "pass_b",
    "prefix_state_hash",
    "validation_label",
    "cert_id",
    "reason",
]


@dataclass(frozen=True)
class CandidatePipeline:
    program: str
    candidate_id: str
    source: str
    base_pipeline: str
    candidate_pipeline: str
    swap_index: int | None
    pass_a: str
    pass_b: str
    prefix_state_hash: str
    validation_label: str
    cert_id: str
    reason: str


@dataclass(frozen=True)
class CandidateGeneration:
    candidates: list[CandidatePipeline]
    summary: dict[str, int]
    evidence_rows: list[dict[str, str]]


def load_attempts_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_candidate_pipelines(
    *,
    programs: Sequence[str],
    anchor_passes: Sequence[str],
    attempts: Sequence[dict[str, str]],
) -> CandidateGeneration:
    program_names = list(programs)
    program_set = set(program_names)
    base_passes = list(anchor_passes)
    base_pipeline = ",".join(base_passes)
    candidates = [
        CandidatePipeline(
            program=program,
            candidate_id=f"{_safe_name(program)}__anchor",
            source="anchor",
            base_pipeline=base_pipeline,
            candidate_pipeline=base_pipeline,
            swap_index=None,
            pass_a="",
            pass_b="",
            prefix_state_hash="",
            validation_label="anchor",
            cert_id="",
            reason="anchor pipeline",
        )
        for program in program_names
    ]
    evidence_rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter(anchor=len(candidates))

    for row in attempts:
        program = row.get("program", "")
        if program not in program_set:
            continue
        action = row.get("action", "")
        label = row.get("label", "")
        if label == "not_certified_independent":
            candidate = _single_swap_candidate(base_passes, base_pipeline, row)
            if candidate is None:
                counts["invalid_position"] += 1
                evidence_rows.append(
                    _evidence_row(row, "invalid_position", "adjacent pair not in anchor")
                )
                continue
            candidates.append(candidate)
            counts["single_swap"] += 1
        elif label == "certified_independent":
            counts["collapsed_certified_independent"] += 1
            evidence_rows.append(
                _evidence_row(
                    row,
                    "collapsed_certified_independent",
                    "certificate proves adjacent swap equivalent",
                )
            )
        elif action == "skipped_low_priority" or row.get("static_decision") == "low_priority":
            counts["frozen_by_static_filter"] += 1
            evidence_rows.append(
                _evidence_row(
                    row,
                    "frozen_by_static_filter",
                    "static filter did not request dynamic validation",
                )
            )
        elif label == "run_failed":
            counts["invalid_run_failed"] += 1
            evidence_rows.append(_evidence_row(row, "invalid_run_failed", "P4 run failed"))
        else:
            counts["ignored"] += 1
            evidence_rows.append(_evidence_row(row, "ignored", "no P5 candidate rule"))

    return CandidateGeneration(
        candidates=candidates,
        summary={
            "anchor": counts["anchor"],
            "single_swap": counts["single_swap"],
            "collapsed_certified_independent": counts[
                "collapsed_certified_independent"
            ],
            "frozen_by_static_filter": counts["frozen_by_static_filter"],
            "invalid_run_failed": counts["invalid_run_failed"],
            "invalid_position": counts["invalid_position"],
            "ignored": counts["ignored"],
        },
        evidence_rows=evidence_rows,
    )


def write_candidates_csv(
    path: str | Path, candidates: Sequence[CandidatePipeline]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(_candidate_to_row(candidate))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build P5 bounded local candidates from P4 attempts."
    )
    parser.add_argument("--program", action="append", default=[])
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument("--attempts-csv", required=True)
    parser.add_argument("--out", default="data/outputs/bounded_local_p5/candidates.csv")
    args = parser.parse_args(argv)

    pipeline = load_pipeline_config(args.pipeline)
    attempts = load_attempts_csv(args.attempts_csv)
    programs = args.program or sorted({row.get("program", "") for row in attempts if row.get("program", "")})
    generation = build_candidate_pipelines(
        programs=programs,
        anchor_passes=list(pipeline["passes"]),
        attempts=attempts,
    )
    write_candidates_csv(args.out, generation.candidates)
    print(
        "anchors={anchor} single_swap={single_swap} collapsed_certified_independent={collapsed_certified_independent} frozen_by_static_filter={frozen_by_static_filter} invalid_run_failed={invalid_run_failed}".format(
            **generation.summary
        )
    )
    return 0


def _single_swap_candidate(
    base_passes: Sequence[str],
    base_pipeline: str,
    row: dict[str, str],
) -> CandidatePipeline | None:
    pass_a = row.get("pass_a", "")
    pass_b = row.get("pass_b", "")
    index = _adjacent_index(base_passes, pass_a, pass_b)
    if index is None:
        return None
    candidate_passes = list(base_passes)
    candidate_passes[index], candidate_passes[index + 1] = (
        candidate_passes[index + 1],
        candidate_passes[index],
    )
    return CandidatePipeline(
        program=row.get("program", ""),
        candidate_id=(
            f"{_safe_name(row.get('program', ''))}__swap_{index}__"
            f"{_safe_name(pass_a)}__{_safe_name(pass_b)}"
        ),
        source="single_swap",
        base_pipeline=base_pipeline,
        candidate_pipeline=",".join(candidate_passes),
        swap_index=index,
        pass_a=pass_a,
        pass_b=pass_b,
        prefix_state_hash=row.get("state_hash", ""),
        validation_label=row.get("label", ""),
        cert_id=row.get("cert_id", ""),
        reason=row.get("static_reason", "") or row.get("label", ""),
    )


def _adjacent_index(
    passes: Sequence[str], pass_a: str, pass_b: str
) -> int | None:
    for index in range(len(passes) - 1):
        if passes[index] == pass_a and passes[index + 1] == pass_b:
            return index
    return None


def _candidate_to_row(candidate: CandidatePipeline) -> dict[str, str]:
    return {
        "program": candidate.program,
        "candidate_id": candidate.candidate_id,
        "source": candidate.source,
        "base_pipeline": candidate.base_pipeline,
        "candidate_pipeline": candidate.candidate_pipeline,
        "swap_index": "" if candidate.swap_index is None else str(candidate.swap_index),
        "pass_a": candidate.pass_a,
        "pass_b": candidate.pass_b,
        "prefix_state_hash": candidate.prefix_state_hash,
        "validation_label": candidate.validation_label,
        "cert_id": candidate.cert_id,
        "reason": candidate.reason,
    }


def _evidence_row(
    row: dict[str, str],
    evidence_label: str,
    reason: str,
) -> dict[str, str]:
    return {
        "program": row.get("program", ""),
        "pass_a": row.get("pass_a", ""),
        "pass_b": row.get("pass_b", ""),
        "validation_label": row.get("label", ""),
        "evidence_label": evidence_label,
        "cert_id": row.get("cert_id", ""),
        "reason": reason,
    }


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


if __name__ == "__main__":
    raise SystemExit(main())
