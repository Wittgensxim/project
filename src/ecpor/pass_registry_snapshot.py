"""Snapshot LLVM pass registry availability from `opt --print-passes`."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Sequence

import yaml

from .environment import file_sha256, parse_opt_version


RAW_OUTPUT_NAME = "opt_print_passes_raw.txt"
SNAPSHOT_NAME = "pass_registry_snapshot.json"
REPORT_NAME = "pass_registry_report.md"
PARSE_CONFIDENCE = "raw_snapshot_with_presence_check"


def build_registry_snapshot(
    *,
    raw_output: str,
    expected_passes: Sequence[str],
    opt_path: str | Path,
    opt_sha256: str,
    llvm_version: str,
) -> dict[str, Any]:
    pass_names = sorted(_extract_pass_like_names(raw_output))
    pass_name_set = set(pass_names)
    presence = {
        pass_name: pass_name in pass_name_set
        or _contains_pass_token(raw_output, pass_name)
        for pass_name in expected_passes
    }
    missing = [pass_name for pass_name, present in presence.items() if not present]
    return {
        "llvm_version": llvm_version,
        "opt_path": Path(opt_path).as_posix(),
        "opt_sha256": opt_sha256,
        "raw_output_sha256": _sha256_text(raw_output),
        "expected_passes": list(expected_passes),
        "expected_pass_presence": presence,
        "missing_expected_passes": missing,
        "all_pass_like_names": pass_names,
        "parse_confidence": PARSE_CONFIDENCE,
    }


def write_registry_snapshot_outputs(
    *,
    raw_output: str,
    expected_passes: Sequence[str],
    output_dir: str | Path,
    opt_path: str | Path,
    opt_sha256: str,
    llvm_version: str,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / RAW_OUTPUT_NAME
    snapshot_path = out / SNAPSHOT_NAME
    report_path = out / REPORT_NAME

    snapshot = build_registry_snapshot(
        raw_output=raw_output,
        expected_passes=expected_passes,
        opt_path=opt_path,
        opt_sha256=opt_sha256,
        llvm_version=llvm_version,
    )
    raw_path.write_bytes(raw_output.encode("utf-8"))
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(snapshot), encoding="utf-8")
    return {
        "raw_output": raw_path,
        "snapshot": snapshot_path,
        "report": report_path,
    }


def render_report(snapshot: dict[str, Any]) -> str:
    expected = snapshot.get("expected_passes", [])
    presence = snapshot.get("expected_pass_presence", {})
    missing = snapshot.get("missing_expected_passes", [])
    lines = [
        "# LLVM Pass Registry Snapshot",
        "",
        f"LLVMVersion: {snapshot.get('llvm_version', 'unknown')}",
        f"OptPath: {snapshot.get('opt_path', '')}",
        f"OptSHA256: {snapshot.get('opt_sha256', '')}",
        f"RawOutputSHA256: {snapshot.get('raw_output_sha256', '')}",
        f"ExpectedPasses: {len(expected)}",
        f"PresentExpectedPasses: {len(expected) - len(missing)}",
        f"MissingExpectedPasses: {len(missing)}",
        f"ParseConfidence: {snapshot.get('parse_confidence', PARSE_CONFIDENCE)}",
        "",
        "This snapshot only records pass availability from the current LLVM toolchain.",
        "It does not infer pass semantics, mutate PassSpec, or change static filter behavior.",
        "",
        "## Expected Pass Presence",
        "",
        "| pass | status |",
        "| --- | --- |",
    ]
    for pass_name in expected:
        status = "present" if presence.get(pass_name, False) else "missing"
        lines.append(f"| `{pass_name}` | {status} |")
        lines.append(f"`{pass_name}`: {status}")
    lines.extend(
        [
            "",
            "## Scope Limits",
            "",
            "metadata_only: True",
            "registry_snapshot_only: True",
            "static_filter_behavior_change: False",
            "passspec_behavior_change: False",
            "new_experiments: False",
            "new_certificates: False",
            "new_search: False",
            "runtime_benchmarks: False",
        ]
    )
    return "\n".join(lines) + "\n"


def load_expected_passes(path: str | Path) -> list[str]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    passes = data.get("passes", [])
    if not isinstance(passes, list):
        raise ValueError(f"pipeline config must contain a list `passes`: {path}")
    return [str(pass_name) for pass_name in passes]


def snapshot_from_opt(
    *,
    opt_path: str | Path,
    pipeline_config_path: str | Path,
    output_dir: str | Path,
    raw_input: str | Path | None = None,
    timeout_sec: float = 30.0,
) -> dict[str, Path]:
    opt = Path(opt_path)
    expected = load_expected_passes(pipeline_config_path)
    if raw_input:
        raw_output = Path(raw_input).read_text(encoding="utf-8")
    else:
        raw_output = _run_tool([str(opt), "--print-passes"], timeout_sec=timeout_sec)
    llvm_version = _read_llvm_version(opt, timeout_sec=timeout_sec)
    opt_sha256 = file_sha256(opt) if opt.exists() and opt.is_file() else "unknown"
    return write_registry_snapshot_outputs(
        raw_output=raw_output,
        expected_passes=expected,
        output_dir=output_dir,
        opt_path=opt,
        opt_sha256=opt_sha256,
        llvm_version=llvm_version,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot opt --print-passes.")
    parser.add_argument("--opt", default="E:/llvm/build/bin/opt.exe")
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument("--out", default="data/outputs/pass_registry_snapshot")
    parser.add_argument("--raw-input")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    outputs = snapshot_from_opt(
        opt_path=args.opt,
        pipeline_config_path=args.pipeline,
        output_dir=args.out,
        raw_input=args.raw_input,
        timeout_sec=args.timeout_sec,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _extract_pass_like_names(raw_output: str) -> set[str]:
    names: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9_.-]+(?:<[^>\s]+>)?", raw_output):
        clean = token.split("<", 1)[0].strip(".,:;()[]{}")
        if not clean or not re.search(r"[A-Za-z]", clean):
            continue
        if clean.lower() in {"passes", "pass", "module", "function", "loop", "cgscc"}:
            continue
        names.add(clean)
    return names


def _contains_pass_token(raw_output: str, pass_name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(pass_name)}(?![A-Za-z0-9_.-])", raw_output) is not None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_tool(command: Sequence[str], *, timeout_sec: float) -> str:
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
    except OSError as exc:
        raise RuntimeError(f"failed to run {' '.join(command)}: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"{' '.join(command)} exited with {result.returncode}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result.stdout + result.stderr


def _read_llvm_version(opt_path: Path, *, timeout_sec: float) -> str:
    if not opt_path.exists():
        return "unknown"
    text = _run_tool([str(opt_path), "--version"], timeout_sec=timeout_sec)
    return parse_opt_version(text)["llvm_version"]


if __name__ == "__main__":
    raise SystemExit(main())
