"""Text-based LLVM IR feature scanning for soft evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Sequence


FEATURE_FIELDS = [
    "num_functions",
    "num_basic_blocks",
    "num_instructions",
    "num_alloca",
    "num_load",
    "num_store",
    "num_call",
    "num_branch",
    "num_phi",
    "num_ret",
    "has_alloca",
    "has_load_store",
    "has_call",
    "has_branch",
    "has_phi",
]


def scan_ir_file(path: str | Path) -> dict[str, int | bool]:
    return scan_ir_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def scan_ir_text(ir_text: str) -> dict[str, int | bool]:
    counts: dict[str, int | bool] = {
        "num_functions": 0,
        "num_basic_blocks": 0,
        "num_instructions": 0,
        "num_alloca": 0,
        "num_load": 0,
        "num_store": 0,
        "num_call": 0,
        "num_branch": 0,
        "num_phi": 0,
        "num_ret": 0,
        "has_alloca": False,
        "has_load_store": False,
        "has_call": False,
        "has_branch": False,
        "has_phi": False,
    }

    in_function = False
    function_label_count = 0
    function_instruction_count = 0

    for raw_line in ir_text.splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue

        if line.startswith("define ") and "{" in line:
            counts["num_functions"] = int(counts["num_functions"]) + 1
            in_function = True
            function_label_count = 0
            function_instruction_count = 0
            continue

        if not in_function:
            continue

        if line == "}":
            counts["num_basic_blocks"] = int(counts["num_basic_blocks"]) + max(
                1, function_label_count
            )
            in_function = False
            continue

        if _is_label(line):
            function_label_count += 1
            continue

        counts["num_instructions"] = int(counts["num_instructions"]) + 1
        function_instruction_count += 1
        _count_instruction(line, counts)

    if in_function:
        counts["num_basic_blocks"] = int(counts["num_basic_blocks"]) + max(
            1, function_label_count, 1 if function_instruction_count else 0
        )

    counts["has_alloca"] = int(counts["num_alloca"]) > 0
    counts["has_load_store"] = int(counts["num_load"]) > 0 or int(counts["num_store"]) > 0
    counts["has_call"] = int(counts["num_call"]) > 0
    counts["has_branch"] = int(counts["num_branch"]) > 0
    counts["has_phi"] = int(counts["num_phi"]) > 0
    return counts


def diff_features(
    features_ab: dict[str, Any], features_ba: dict[str, Any]
) -> dict[str, int | str]:
    diff: dict[str, int | str] = {}
    for key in sorted(set(features_ab) | set(features_ba)):
        left = features_ab.get(key)
        right = features_ba.get(key)
        if isinstance(left, bool) or isinstance(right, bool):
            diff[key] = "" if left == right else f"{left} -> {right}"
        elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
            diff[key] = right - left
        elif left == right:
            diff[key] = ""
        else:
            diff[key] = f"{left} -> {right}"
    return diff


def features_to_json(features: dict[str, Any]) -> str:
    return json.dumps(features, sort_keys=True, separators=(",", ":"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan text-level LLVM IR features.")
    parser.add_argument("ir", help="LLVM IR file to scan.")
    args = parser.parse_args(argv)

    print(json.dumps(scan_ir_file(args.ir), indent=2, sort_keys=True))
    return 0


def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0]


def _is_label(line: str) -> bool:
    return re.match(r"^[A-Za-z$._-][A-Za-z0-9$._-]*:\s*$", line) is not None


def _count_instruction(line: str, counts: dict[str, int | bool]) -> None:
    opcode = _opcode(line)
    if opcode == "alloca":
        counts["num_alloca"] = int(counts["num_alloca"]) + 1
    elif opcode == "load":
        counts["num_load"] = int(counts["num_load"]) + 1
    elif opcode == "store":
        counts["num_store"] = int(counts["num_store"]) + 1
    elif opcode == "call":
        counts["num_call"] = int(counts["num_call"]) + 1
    elif opcode == "br":
        counts["num_branch"] = int(counts["num_branch"]) + 1
    elif opcode == "phi":
        counts["num_phi"] = int(counts["num_phi"]) + 1
    elif opcode == "ret":
        counts["num_ret"] = int(counts["num_ret"]) + 1


def _opcode(line: str) -> str:
    text = line
    if "=" in text:
        text = text.split("=", 1)[1].strip()
    match = re.match(r"([A-Za-z][A-Za-z0-9._-]*)\b", text)
    if match is None:
        return ""
    return match.group(1)


if __name__ == "__main__":
    raise SystemExit(main())
