"""LLVM environment discovery and fingerprinting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, NamedTuple


DEFAULT_EXECUTION_MODEL = "materialized_ir_fresh_opt"
DEFAULT_DEBUG_POLICY = "strip_at_input"
DEFAULT_METADATA_POLICY = "preserve_optimization_metadata"
DEFAULT_NORMALIZER_VERSION = "hard-normalizer-v1"


@dataclass(frozen=True)
class LLVMEnvironment:
    opt_path: str
    clang_path: str
    llvm_size_path: str
    llvm_config_path: str
    llvm_version: str
    clang_version: str
    clang_commit: str
    target_triple: str
    host_cpu: str
    execution_model: str = DEFAULT_EXECUTION_MODEL
    debug_policy: str = DEFAULT_DEBUG_POLICY
    metadata_policy: str = DEFAULT_METADATA_POLICY
    normalizer_version: str = DEFAULT_NORMALIZER_VERSION
    opt_sha256: str = "unknown"
    clang_sha256: str = "unknown"
    llvm_size_sha256: str = "unknown"
    llvm_config_sha256: str = "unknown"
    llvm_source_root: str = "E:/llvm"
    llvm_source_git_commit: str = "unknown"
    llvm_source_git_dirty: bool | None = None
    llvm_build_type: str = "unknown"
    llvm_assertions: str = "unknown"
    cmake_cache_sha256: str = "unknown"

    @property
    def env_id(self) -> str:
        return compute_env_id(self)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["env_id"] = self.env_id
        return data


def parse_opt_version(text: str) -> dict[str, str]:
    return {
        "llvm_version": _match_or_unknown(r"LLVM version\s+([^\r\n]+)", text),
        "target_triple": _match_or_unknown(r"Default target:\s+([^\r\n]+)", text),
        "host_cpu": _match_or_unknown(r"Host CPU:\s+([^\r\n]+)", text),
    }


def parse_clang_version(text: str) -> dict[str, str]:
    version = _match_or_unknown(r"clang version\s+(\S+)", text)
    commit = _match_or_unknown(r"llvm-project\.git\s+([0-9a-fA-F]+)", text)
    return {
        "clang_version": version,
        "clang_commit": commit,
    }


def compute_env_id(env: LLVMEnvironment) -> str:
    payload = json.dumps(asdict(env), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def detect_environment(
    bin_dir: str | Path = "E:/llvm/build/bin",
    *,
    llvm_source_root: str | Path = "E:/llvm",
) -> LLVMEnvironment:
    root = Path(bin_dir)
    opt = root / "opt.exe"
    clang = root / "clang.exe"
    llvm_size = root / "llvm-size.exe"
    llvm_config = root / "llvm-config.exe"
    source_root = Path(llvm_source_root)
    cmake_cache = root.parent / "CMakeCache.txt"

    opt_info = parse_opt_version(_run_text([str(opt), "--version"]))
    clang_info = parse_clang_version(_run_text([str(clang), "--version"]))
    source_git = git_info(source_root)
    cmake_values = _parse_cmake_cache(cmake_cache)

    return LLVMEnvironment(
        opt_path=_path_text(opt),
        clang_path=_path_text(clang),
        llvm_size_path=_path_text(llvm_size),
        llvm_config_path=_path_text(llvm_config),
        llvm_version=opt_info["llvm_version"],
        clang_version=clang_info["clang_version"],
        clang_commit=clang_info["clang_commit"],
        target_triple=opt_info["target_triple"],
        host_cpu=opt_info["host_cpu"],
        opt_sha256=_file_sha256_or_unknown(opt),
        clang_sha256=_file_sha256_or_unknown(clang),
        llvm_size_sha256=_file_sha256_or_unknown(llvm_size),
        llvm_config_sha256=_file_sha256_or_unknown(llvm_config),
        llvm_source_root=_path_text(source_root),
        llvm_source_git_commit=source_git.commit,
        llvm_source_git_dirty=source_git.dirty,
        llvm_build_type=cmake_values.get("CMAKE_BUILD_TYPE", "unknown"),
        llvm_assertions=cmake_values.get("LLVM_ENABLE_ASSERTIONS", "unknown"),
        cmake_cache_sha256=_file_sha256_or_unknown(cmake_cache),
    )


class GitInfo(NamedTuple):
    commit: str
    dirty: bool | None


def git_info(root: str | Path) -> GitInfo:
    root_path = Path(root)
    if not root_path.exists():
        return GitInfo("unknown", None)

    commit = _run_git(root_path, ["rev-parse", "HEAD"]).strip()
    if not commit:
        return GitInfo("unknown", None)

    status = _run_git(root_path, ["status", "--porcelain"])
    return GitInfo(commit, bool(status.strip()))


def _match_or_unknown(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        return "unknown"
    return match.group(1).strip()


def _path_text(path: Path) -> str:
    return path.as_posix()


def _run_text(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    return result.stdout + result.stderr


def _run_git(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _file_sha256_or_unknown(path: Path) -> str:
    if not path.exists():
        return "unknown"
    return file_sha256(path)


def _parse_cmake_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line or raw_line.startswith(("#", "//")) or "=" not in raw_line:
            continue
        key_with_type, value = raw_line.split("=", 1)
        key = key_with_type.split(":", 1)[0]
        values[key] = value
    return values
