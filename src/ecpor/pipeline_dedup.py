"""Small helpers for pass-sequence hashing and candidate deduplication."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Sequence


@dataclass(frozen=True)
class PipelineDeduplicationResult:
    unique_rows: list[dict[str, str]]
    duplicate_rows: list[dict[str, str]]
    sequence_to_candidate_ids: dict[str, list[str]]


def pipeline_sequence_hash(passes: Sequence[str]) -> str:
    joined = ",".join(part.strip() for part in passes if part.strip())
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def deduplicate_pipeline_rows(
    rows: Sequence[dict[str, str]],
    *,
    pipeline_field: str = "candidate_pipeline",
) -> PipelineDeduplicationResult:
    seen: set[str] = set()
    unique_rows: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []
    sequence_to_candidate_ids: dict[str, list[str]] = {}
    for row in rows:
        normalized = _split_pipeline(row.get(pipeline_field, ""))
        sequence_hash = row.get("pipeline_sequence_hash") or pipeline_sequence_hash(
            normalized
        )
        enriched = {**row, "pipeline_sequence_hash": sequence_hash}
        sequence_to_candidate_ids.setdefault(sequence_hash, []).append(
            row.get("candidate_id", "")
        )
        if sequence_hash in seen:
            duplicate_rows.append(enriched)
            continue
        seen.add(sequence_hash)
        unique_rows.append(enriched)
    return PipelineDeduplicationResult(
        unique_rows=unique_rows,
        duplicate_rows=duplicate_rows,
        sequence_to_candidate_ids=sequence_to_candidate_ids,
    )


def _split_pipeline(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]
