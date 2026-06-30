"""Structured runner for LLVM opt pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Sequence

from .normalizer import hard_hash


OptPath = str | Path | Sequence[str | Path]


@dataclass(frozen=True)
class RunResult:
    command: list[str]
    input_path: Path
    output_path: Path
    pipeline: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float
    opt_success: bool
    output_exists: bool
    verify_each_enabled: bool
    verifier_ok: bool | None
    failure_kind: str | None
    timed_out: bool = False
    hard_hash: str | None = None


def build_opt_command(
    input_ll: str | Path,
    passes: str,
    output_ll: str | Path,
    *,
    opt_path: OptPath = "opt",
    extra_flags: Sequence[str] | None = None,
) -> list[str]:
    command = _normalize_opt_path(opt_path)
    command.extend(
        [
            str(input_ll),
            "-S",
            "-o",
            str(output_ll),
            f"-passes={passes}",
            "-verify-each",
        ]
    )
    if extra_flags:
        command.extend(extra_flags)
    return command


def run_opt(
    input_ll: str | Path,
    passes: str,
    output_ll: str | Path,
    *,
    opt_path: OptPath = "opt",
    extra_flags: Sequence[str] | None = None,
    timeout_sec: float = 30.0,
) -> RunResult:
    input_path = Path(input_ll)
    output_path = Path(output_ll)
    command = build_opt_command(
        input_path,
        passes,
        output_path,
        opt_path=opt_path,
        extra_flags=extra_flags,
    )

    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        opt_success = completed.returncode == 0
        output_exists = output_path.exists()
        verify_each_enabled = "-verify-each" in command
        success = opt_success and output_exists
        result_hash = hard_hash(output_path) if success else None
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_ms=elapsed_ms,
            opt_success=opt_success,
            output_exists=output_exists,
            verify_each_enabled=verify_each_enabled,
            verifier_ok=success if verify_each_enabled else None,
            failure_kind=_failure_kind(opt_success, output_exists),
            hard_hash=result_hash,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        output_exists = output_path.exists()
        verify_each_enabled = "-verify-each" in command
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=-1,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nTimed out after {timeout_sec} seconds.",
            elapsed_ms=elapsed_ms,
            opt_success=False,
            output_exists=output_exists,
            verify_each_enabled=verify_each_enabled,
            verifier_ok=False,
            failure_kind="timeout",
            timed_out=True,
        )
    except OSError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        output_exists = output_path.exists()
        verify_each_enabled = "-verify-each" in command
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=-1,
            stdout="",
            stderr=str(exc),
            elapsed_ms=elapsed_ms,
            opt_success=False,
            output_exists=output_exists,
            verify_each_enabled=verify_each_enabled,
            verifier_ok=False,
            failure_kind="os_error",
        )


def _normalize_opt_path(opt_path: OptPath) -> list[str]:
    if isinstance(opt_path, (str, Path)):
        return [str(opt_path)]
    return [str(part) for part in opt_path]


def _failure_kind(opt_success: bool, output_exists: bool) -> str | None:
    if opt_success and output_exists:
        return None
    if opt_success and not output_exists:
        return "output_missing"
    if not opt_success and output_exists:
        return "opt_failed_output_exists"
    return "opt_failed"
