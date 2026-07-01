"""Compile LLVM IR to objects and collect llvm-size metrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Literal, Sequence


ToolPath = str | Path | Sequence[str | Path]
CompileMode = Literal["llc", "clang"]


@dataclass(frozen=True)
class ObjectSizeRecord:
    program: str
    candidate_id: str
    ir_path: str
    object_path: str
    compile_exit_code: int
    compile_failure_kind: str | None
    size_exit_code: int
    text_size: int | None
    data_size: int | None
    bss_size: int | None
    total_size: int | None
    size_tool_output: str
    size_failure_kind: str | None = None


def measure_object_size(
    *,
    program: str,
    candidate_id: str,
    ir_path: str | Path,
    object_path: str | Path,
    llc_path: ToolPath = "llc",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
    compile_mode: CompileMode = "llc",
) -> ObjectSizeRecord:
    ir = Path(ir_path)
    obj = Path(object_path)
    obj.parent.mkdir(parents=True, exist_ok=True)
    compile_result = _run_compile(ir, obj, llc_path, timeout_sec, compile_mode)
    compile_failure = _compile_failure_kind(
        compile_result.returncode,
        obj.exists(),
        compile_result.timed_out,
        compile_result.os_error,
    )
    if compile_failure:
        return ObjectSizeRecord(
            program=program,
            candidate_id=candidate_id,
            ir_path=str(ir),
            object_path=str(obj),
            compile_exit_code=compile_result.returncode,
            compile_failure_kind=compile_failure,
            size_exit_code=-1,
            text_size=None,
            data_size=None,
            bss_size=None,
            total_size=None,
            size_tool_output=compile_result.output,
            size_failure_kind="object_unavailable",
        )

    size_result = _run_size(obj, llvm_size_path, timeout_sec)
    size_output = size_result.output
    parsed = (
        None
        if size_result.returncode != 0 or size_result.timed_out or size_result.os_error
        else parse_llvm_size_output(size_output)
    )
    if parsed is None:
        size_failure = _size_failure_kind(size_result)
        return ObjectSizeRecord(
            program=program,
            candidate_id=candidate_id,
            ir_path=str(ir),
            object_path=str(obj),
            compile_exit_code=compile_result.returncode,
            compile_failure_kind=None,
            size_exit_code=size_result.returncode,
            text_size=None,
            data_size=None,
            bss_size=None,
            total_size=None,
            size_tool_output=size_output,
            size_failure_kind=size_failure,
        )
    text_size, data_size, bss_size, total_size = parsed
    return ObjectSizeRecord(
        program=program,
        candidate_id=candidate_id,
        ir_path=str(ir),
        object_path=str(obj),
        compile_exit_code=compile_result.returncode,
        compile_failure_kind=None,
        size_exit_code=size_result.returncode,
        text_size=text_size,
        data_size=data_size,
        bss_size=bss_size,
        total_size=total_size,
        size_tool_output=size_output,
        size_failure_kind=None,
    )


def parse_llvm_size_output(text: str) -> tuple[int, int, int, int] | None:
    for raw_line in text.splitlines():
        parts = raw_line.split()
        if len(parts) < 4:
            continue
        try:
            text_size = int(parts[0], 0)
            data_size = int(parts[1], 0)
            bss_size = int(parts[2], 0)
            total_size = int(parts[3], 0)
        except ValueError:
            continue
        return text_size, data_size, bss_size, total_size
    return None


@dataclass(frozen=True)
class _CommandResult:
    returncode: int
    output: str
    elapsed_ms: float
    timed_out: bool = False
    os_error: bool = False


def _run_compile(
    ir_path: Path,
    object_path: Path,
    llc_path: ToolPath,
    timeout_sec: float,
    compile_mode: CompileMode,
) -> _CommandResult:
    if compile_mode == "clang":
        command = [
            *_normalize_tool_path(llc_path),
            "-x",
            "ir",
            "-c",
            str(ir_path),
            "-o",
            str(object_path),
        ]
    else:
        command = [
            *_normalize_tool_path(llc_path),
            str(ir_path),
            "-filetype=obj",
            "-o",
            str(object_path),
        ]
    return _run_command(command, timeout_sec)


def _run_size(
    object_path: Path, llvm_size_path: ToolPath, timeout_sec: float
) -> _CommandResult:
    return _run_command([*_normalize_tool_path(llvm_size_path), str(object_path)], timeout_sec)


def _run_command(command: list[str], timeout_sec: float) -> _CommandResult:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
        return _CommandResult(
            returncode=completed.returncode,
            output=completed.stdout + completed.stderr,
            elapsed_ms=(time.perf_counter() - start) * 1000.0,
        )
    except subprocess.TimeoutExpired as exc:
        return _CommandResult(
            returncode=-1,
            output=(exc.stdout or "") + (exc.stderr or "") + "\nTimed out.",
            elapsed_ms=(time.perf_counter() - start) * 1000.0,
            timed_out=True,
        )
    except OSError as exc:
        return _CommandResult(
            returncode=-1,
            output=str(exc),
            elapsed_ms=(time.perf_counter() - start) * 1000.0,
            os_error=True,
        )


def _normalize_tool_path(tool_path: ToolPath) -> list[str]:
    if isinstance(tool_path, (str, Path)):
        return [str(tool_path)]
    return [str(part) for part in tool_path]


def _compile_failure_kind(
    exit_code: int, output_exists: bool, timed_out: bool, os_error: bool
) -> str | None:
    if timed_out:
        return "compile_timeout"
    if os_error:
        return "compile_os_error"
    if exit_code == 0 and output_exists:
        return None
    if exit_code == 0 and not output_exists:
        return "compile_output_missing"
    if exit_code != 0 and output_exists:
        return "compile_failed_output_exists"
    return "compile_failed"


def _size_failure_kind(result: _CommandResult) -> str:
    if result.timed_out:
        return "size_timeout"
    if result.os_error:
        return "size_os_error"
    if result.returncode != 0:
        return "size_failed"
    return "size_parse_failed"
