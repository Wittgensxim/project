"""Run full candidate pipelines and summarize their IR outputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .candidate_pipeline import CandidatePipeline
from .feature_scan import scan_ir_file
from .runner import OptPath, run_opt


PIPELINE_RUN_FIELDS = [
    "program",
    "candidate_id",
    "pipeline",
    "exit_code",
    "failure_kind",
    "hard_hash",
    "same_as_anchor",
    "num_instructions",
    "num_basic_blocks",
    "num_load",
    "num_store",
    "num_branch",
]


@dataclass(frozen=True)
class PipelineRunRecord:
    program: str
    candidate_id: str
    pipeline: str
    exit_code: int
    failure_kind: str | None
    hard_hash: str | None
    same_as_anchor: bool
    num_instructions: int
    num_basic_blocks: int
    num_load: int
    num_store: int
    num_branch: int


def run_pipeline_candidate(
    input_ir: str | Path,
    candidate: CandidatePipeline,
    *,
    opt_path: OptPath,
    output_dir: str | Path,
    anchor_hash: str | None = None,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> PipelineRunRecord:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / f"{_safe_name(candidate.candidate_id)}.ll"
    pipeline = _pipeline(nesting, _split_pipeline(candidate.candidate_pipeline))
    result = run_opt(
        input_ir,
        pipeline,
        output_path,
        opt_path=opt_path,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    features = _scan_features_if_available(output_path, result.hard_hash)
    if anchor_hash is not None:
        same_as_anchor = result.hard_hash == anchor_hash
    else:
        same_as_anchor = candidate.source == "anchor" and result.hard_hash is not None
    return PipelineRunRecord(
        program=candidate.program,
        candidate_id=candidate.candidate_id,
        pipeline=pipeline,
        exit_code=result.exit_code,
        failure_kind=result.failure_kind,
        hard_hash=result.hard_hash,
        same_as_anchor=same_as_anchor,
        num_instructions=int(features.get("num_instructions", 0)),
        num_basic_blocks=int(features.get("num_basic_blocks", 0)),
        num_load=int(features.get("num_load", 0)),
        num_store=int(features.get("num_store", 0)),
        num_branch=int(features.get("num_branch", 0)),
    )


def write_pipeline_runs_csv(
    path: str | Path, records: Sequence[PipelineRunRecord]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PIPELINE_RUN_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_row(record))


def _pipeline(nesting: str, passes: Sequence[str]) -> str:
    joined = ",".join(passes)
    if nesting:
        return f"{nesting}({joined})"
    return joined


def _split_pipeline(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _scan_features_if_available(
    output_path: Path, hard_hash: str | None
) -> dict[str, int | bool]:
    if hard_hash is None or not output_path.exists():
        return {}
    return scan_ir_file(output_path)


def _record_to_row(record: PipelineRunRecord) -> dict[str, str]:
    return {
        "program": record.program,
        "candidate_id": record.candidate_id,
        "pipeline": record.pipeline,
        "exit_code": str(record.exit_code),
        "failure_kind": record.failure_kind or "",
        "hard_hash": record.hard_hash or "",
        "same_as_anchor": str(record.same_as_anchor),
        "num_instructions": str(record.num_instructions),
        "num_basic_blocks": str(record.num_basic_blocks),
        "num_load": str(record.num_load),
        "num_store": str(record.num_store),
        "num_branch": str(record.num_branch),
    }


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)
