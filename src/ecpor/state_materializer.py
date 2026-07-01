"""Materialize prefix IR states for anchor-adjacent lazy validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Sequence

from .normalizer import NORMALIZER_VERSION, hard_hash
from .runner import OptPath, RunResult, run_opt


@dataclass(frozen=True)
class MaterializedState:
    path: Path
    state_hash: str
    prefix_passes: list[str]
    pipeline: str
    run_result: RunResult | None
    cache_hit: bool = False


def materialize_prefix_state(
    input_ir: str | Path,
    prefix_passes: Sequence[str],
    *,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    nesting: str = "function",
    normalizer_version: str = NORMALIZER_VERSION,
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> MaterializedState:
    input_path = Path(input_ir)
    passes = list(prefix_passes)
    if not passes:
        return MaterializedState(
            path=input_path,
            state_hash=hard_hash(input_path),
            prefix_passes=[],
            pipeline="input",
            run_result=None,
            cache_hit=False,
        )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    pipeline = _pipeline(nesting, passes)
    cache_key = _prefix_cache_key(
        input_state_hash=hard_hash(input_path),
        prefix_passes=passes,
        env_id=env_id,
        nesting=nesting,
        normalizer_version=normalizer_version,
        extra_flags=extra_flags,
    )
    output_path = output_root / f"{cache_key}.ll"
    if output_path.exists():
        return MaterializedState(
            path=output_path,
            state_hash=hard_hash(output_path),
            prefix_passes=passes,
            pipeline=pipeline,
            run_result=None,
            cache_hit=True,
        )

    result = run_opt(
        input_path,
        pipeline,
        output_path,
        opt_path=opt_path,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    return MaterializedState(
        path=output_path,
        state_hash=result.hard_hash or "",
        prefix_passes=passes,
        pipeline=pipeline,
        run_result=result,
        cache_hit=False,
    )


def _pipeline(nesting: str, passes: Sequence[str]) -> str:
    joined = ",".join(passes)
    if nesting:
        return f"{nesting}({joined})"
    return joined


def _prefix_cache_key(
    *,
    input_state_hash: str,
    prefix_passes: Sequence[str],
    env_id: str,
    nesting: str,
    normalizer_version: str,
    extra_flags: Sequence[str],
) -> str:
    payload = {
        "input_state_hash": input_state_hash,
        "prefix_passes": list(prefix_passes),
        "env_id": env_id,
        "nesting": nesting,
        "normalizer_version": normalizer_version,
        "extra_flags": list(extra_flags),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
