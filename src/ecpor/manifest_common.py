"""Common manifest helpers shared by manifest builders and CLI wrappers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .environment import file_sha256, git_info


def build_result_manifest(
    *,
    stage: str,
    description: str,
    inputs: Mapping[str, str | Path],
    outputs: Mapping[str, str | Path],
    tools: Mapping[str, str | Path],
    summary: Mapping[str, Any],
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo_git = git_info(repo_root)
    generated_from = result_generated_from_commit or repo_git.commit
    manifest: dict[str, Any] = {
        "manifest_schema_version": 1,
        "stage": stage,
        "description": description,
        "result_generated_from_commit": generated_from,
        "ecpor_git_commit": repo_git.commit,
        "ecpor_git_dirty": repo_git.dirty,
        "inputs": _path_map(inputs),
        "outputs": _path_map(outputs),
        "sha256": _sha256_map(inputs) | _sha256_map(outputs) | _sha256_map(tools),
        "tools": _tool_map(tools),
        "summary": dict(summary),
    }
    if extra:
        manifest.update(extra)
    return manifest



def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )





def _path_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {key: _path_text(path) for key, path in paths.items()}


def _tool_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {f"{key}_path": str(path) for key, path in paths.items()}


def _sha256_map(paths: Mapping[str, str | Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, value in paths.items():
        path = Path(value)
        if path.exists() and path.is_file():
            hashes[key] = file_sha256(path)
    return hashes


def _path_text(path: str | Path) -> str:
    return Path(path).as_posix()
