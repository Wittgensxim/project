"""P8c focused effect attribution for the Queens ordering case."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .feature_scan import FEATURE_FIELDS, scan_ir_file
from .object_size_runner import ObjectSizeRecord, ToolPath, measure_object_size
from .runner import OptPath, run_opt


PROGRAM = "testsuite_stanford_queens"
DEFAULT_PREFIX = ("sroa", "early-cse")
DEFAULT_PASS_A = "instcombine"
DEFAULT_PASS_B = "simplifycfg"
DEFAULT_SUFFIX = ("reassociate", "gvn", "dce", "adce")

NUMERIC_FEATURE_FIELDS = [
    field for field in FEATURE_FIELDS if field.startswith("num_")
]

OPCODE_NAMES = [
    "icmp",
    "select",
    "getelementptr",
    "bitcast",
    "zext",
    "sext",
    "trunc",
    "unreachable",
    "switch",
    "add",
    "sub",
    "mul",
    "shl",
    "or",
    "and",
]

STATE_FIELDS = [
    "program",
    "state_name",
    "pipeline",
    "ir_path",
    "hard_hash",
    "exit_code",
    "failure_kind",
    *NUMERIC_FEATURE_FIELDS,
]

DELTA_FIELDS = [
    "comparison",
    "left_state",
    "right_state",
    "hard_hash_equal",
    *[f"{field}_delta" for field in NUMERIC_FEATURE_FIELDS],
]

OPCODE_DELTA_FIELDS = [
    "comparison",
    "left_state",
    "right_state",
    *[f"num_{opcode}_delta" for opcode in OPCODE_NAMES],
]

OBJECT_SIZE_FIELDS = [
    "program",
    "state_name",
    "compile_mode",
    "ir_path",
    "object_path",
    "text_size",
    "data_size",
    "bss_size",
    "total_size",
    "anchor_state",
    "anchor_text_size",
    "text_delta",
    "text_delta_pct",
    "direction",
    "compile_failure_kind",
    "size_failure_kind",
]


@dataclass(frozen=True)
class EffectAttributionResult:
    state_rows: list[dict[str, str]]
    feature_delta_rows: list[dict[str, str]]
    opcode_delta_rows: list[dict[str, str]]
    object_size_rows: list[dict[str, str]]
    summary: dict[str, Any]


def run_queens_effect_attribution(
    *,
    input_ir: str | Path = "data/inputs/testsuite_stanford_queens.ll",
    output_dir: str | Path = "data/outputs/effect_attribution_queens",
    opt_path: OptPath = "E:/llvm/build/bin/opt.exe",
    llc_path: ToolPath = "E:/llvm/build/bin/llc.exe",
    clang_path: ToolPath = "E:/llvm/build/bin/clang.exe",
    llvm_size_path: ToolPath = "E:/llvm/build/bin/llvm-size.exe",
    timeout_sec: float = 30.0,
) -> EffectAttributionResult:
    return run_effect_attribution(
        program=PROGRAM,
        input_ir=input_ir,
        output_dir=output_dir,
        prefix=DEFAULT_PREFIX,
        pass_a=DEFAULT_PASS_A,
        pass_b=DEFAULT_PASS_B,
        suffix=DEFAULT_SUFFIX,
        opt_path=opt_path,
        llc_path=llc_path,
        clang_path=clang_path,
        llvm_size_path=llvm_size_path,
        timeout_sec=timeout_sec,
    )


def run_effect_attribution(
    *,
    program: str,
    input_ir: str | Path,
    output_dir: str | Path,
    prefix: Sequence[str],
    pass_a: str,
    pass_b: str,
    suffix: Sequence[str],
    opt_path: OptPath,
    llc_path: ToolPath,
    clang_path: ToolPath,
    llvm_size_path: ToolPath,
    timeout_sec: float = 30.0,
) -> EffectAttributionResult:
    output_root = Path(output_dir)
    state_root = output_root / "state_outputs"
    object_root = output_root / "object_outputs"
    state_root.mkdir(parents=True, exist_ok=True)
    object_root.mkdir(parents=True, exist_ok=True)

    definitions = _state_definitions(prefix, pass_a, pass_b, suffix)
    state_rows: list[dict[str, str]] = []
    state_features: dict[str, dict[str, int | bool]] = {}
    state_opcodes: dict[str, dict[str, int]] = {}
    for state_name, passes in definitions.items():
        output_ir = state_root / f"{state_name}.ll"
        pipeline = _pipeline(passes)
        result = run_opt(
            input_ir,
            pipeline,
            output_ir,
            opt_path=opt_path,
            timeout_sec=timeout_sec,
        )
        features: dict[str, int | bool] = {}
        if result.failure_kind is None and output_ir.exists():
            features = scan_ir_file(output_ir)
            state_opcodes[state_name] = scan_opcode_multiset(output_ir)
        else:
            state_opcodes[state_name] = {}
        state_features[state_name] = features
        state_rows.append(
            _state_row(
                program=program,
                state_name=state_name,
                pipeline=pipeline,
                ir_path=output_ir,
                hard_hash=result.hard_hash,
                exit_code=result.exit_code,
                failure_kind=result.failure_kind,
                features=features,
            )
        )

    delta_rows = _feature_delta_rows(state_rows, state_features)
    opcode_delta_rows = _opcode_delta_rows(state_opcodes)
    object_rows = _object_size_rows(
        program=program,
        state_rows=state_rows,
        object_root=object_root,
        llc_path=llc_path,
        clang_path=clang_path,
        llvm_size_path=llvm_size_path,
        timeout_sec=timeout_sec,
    )
    summary = _summary(state_rows, delta_rows, opcode_delta_rows, object_rows)

    _write_csv(output_root / "states.csv", state_rows, STATE_FIELDS)
    _write_csv(output_root / "feature_deltas.csv", delta_rows, DELTA_FIELDS)
    _write_csv(output_root / "opcode_delta.csv", opcode_delta_rows, OPCODE_DELTA_FIELDS)
    _write_csv(output_root / "object_size.csv", object_rows, OBJECT_SIZE_FIELDS)
    (output_root / "attribution_report.md").write_text(
        build_attribution_report(
            summary, state_rows, delta_rows, opcode_delta_rows, object_rows
        ),
        encoding="utf-8",
    )
    return EffectAttributionResult(
        state_rows=state_rows,
        feature_delta_rows=delta_rows,
        opcode_delta_rows=opcode_delta_rows,
        object_size_rows=object_rows,
        summary=summary,
    )


def scan_opcode_multiset(path: str | Path) -> dict[str, int]:
    counts = {f"num_{opcode}": 0 for opcode in OPCODE_NAMES}
    for raw_line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        opcode = _opcode(raw_line)
        key = f"num_{opcode}"
        if key in counts:
            counts[key] += 1
    return counts


def build_attribution_report(
    summary: Mapping[str, Any],
    state_rows: Sequence[dict[str, str]],
    delta_rows: Sequence[dict[str, str]],
    opcode_delta_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
) -> str:
    local = _row_by_key(delta_rows, "comparison", "local_AB_vs_BA")
    final = _row_by_key(delta_rows, "comparison", "final_AB_vs_BA")
    local_opcode = _row_by_key(opcode_delta_rows, "comparison", "local_AB_vs_BA")
    final_opcode = _row_by_key(opcode_delta_rows, "comparison", "final_AB_vs_BA")
    lines = [
        "# P8c Queens Effect Attribution",
        "",
        "本报告只解释当前最稳定的 Queens instcombine/simplifycfg case。",
        "它不新增搜索、不生成 certificate，也不声明跨程序定理。",
        "",
        f"Program: {summary['Program']}",
        f"StateCount: {summary['StateCount']}",
        f"LocalABBAHardHashEqual: {summary['LocalABBAHardHashEqual']}",
        f"FinalABBAHardHashEqual: {summary['FinalABBAHardHashEqual']}",
        f"LocalInstructionDelta: {summary['LocalInstructionDelta']}",
        f"FinalInstructionDelta: {summary['FinalInstructionDelta']}",
        f"FeatureDeltaPropagation: {summary['FeatureDeltaPropagation']}",
        f"LlcTextDelta: {summary['LlcTextDelta']}",
        f"ClangTextDelta: {summary['ClangTextDelta']}",
        f"BothCodegenSmaller: {summary['BothCodegenSmaller']}",
        f"FinalOpcodeDeltaNonZero: {summary['FinalOpcodeDeltaNonZero']}",
        "",
        "## Five Questions",
        "",
        "1. AB 和 BA 在局部 pair 后是否已经 hard hash 不同？",
        f"   结果：{not summary['LocalABBAHardHashEqual']}。",
        "2. 局部 AB/BA 的 feature delta 是什么？",
        f"   num_instructions_delta = {local.get('num_instructions_delta', '')}。",
        f"   opcode delta = {_format_nonzero_opcode_delta(local_opcode)}。",
        "3. 加上 suffix 后，最终 feature delta 是否扩大、缩小或保持？",
        f"   结果：{summary['FeatureDeltaPropagation']}；"
        f"final num_instructions_delta = {final.get('num_instructions_delta', '')}。",
        f"   final opcode delta = {_format_nonzero_opcode_delta(final_opcode)}。",
        "4. llc 和 clang-c 下的 .text delta 是否仍然都是 smaller？",
        f"   结果：{summary['BothCodegenSmaller']}。",
        "5. 根据 feature delta，能提出什么 observed attribution hypothesis？",
        "",
        "## State Feature Table",
        "",
        "| state | instructions | basic blocks | branches | calls | hard hash |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in state_rows:
        lines.append(
            "| {state_name} | {num_instructions} | {num_basic_blocks} | "
            "{num_branch} | {num_call} | {hard_hash} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Opcode Delta",
            "",
            "| comparison | nonzero opcode delta |",
            "| --- | --- |",
        ]
    )
    for row in opcode_delta_rows:
        lines.append(
            "| {comparison} | {delta} |".format(
                comparison=row["comparison"],
                delta=_format_nonzero_opcode_delta(row),
            )
        )
    lines.extend(
        [
            "",
            "## Object Size",
            "",
            "| mode | state | text | anchor text | delta | delta pct | direction |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in object_rows:
        lines.append(
            "| {compile_mode} | {state_name} | {text_size} | {anchor_text_size} | "
            "{text_delta} | {text_delta_pct} | {direction} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Observed Attribution Hypothesis",
            "",
            "在 Queens 的 prefix state 上，交换 simplifycfg 与 instcombine 已经产生局部 IR 差异；",
            "该差异在 suffix 后仍然可见，并且 BA_final 在 llc 与 clang-c 下都对应更小的 .text。",
            "这支持一个观察性假设：该顺序改变了 CFG/scalar cleanup 机会，进而影响目标层 code size。",
            "当前证据只覆盖这个 program 和这个 materialized state，不能外推为全局因果定理。",
        ]
    )
    return "\n".join(lines) + "\n"


def _state_definitions(
    prefix: Sequence[str], pass_a: str, pass_b: str, suffix: Sequence[str]
) -> dict[str, list[str]]:
    base = list(prefix)
    return {
        "S": base,
        "A": [*base, pass_a],
        "B": [*base, pass_b],
        "AB_local": [*base, pass_a, pass_b],
        "BA_local": [*base, pass_b, pass_a],
        "AB_final": [*base, pass_a, pass_b, *suffix],
        "BA_final": [*base, pass_b, pass_a, *suffix],
    }


def _pipeline(passes: Sequence[str]) -> str:
    return f"function({','.join(passes)})"


def _state_row(
    *,
    program: str,
    state_name: str,
    pipeline: str,
    ir_path: Path,
    hard_hash: str | None,
    exit_code: int,
    failure_kind: str | None,
    features: Mapping[str, int | bool],
) -> dict[str, str]:
    row = {
        "program": program,
        "state_name": state_name,
        "pipeline": pipeline,
        "ir_path": str(ir_path),
        "hard_hash": hard_hash or "",
        "exit_code": str(exit_code),
        "failure_kind": failure_kind or "",
    }
    for field in NUMERIC_FEATURE_FIELDS:
        row[field] = str(features.get(field, ""))
    return row


def _comparison_pairs() -> list[tuple[str, str, str]]:
    return [
        ("S_to_A", "S", "A"),
        ("S_to_B", "S", "B"),
        ("local_AB_vs_BA", "AB_local", "BA_local"),
        ("final_AB_vs_BA", "AB_final", "BA_final"),
        ("AB_local_to_final", "AB_local", "AB_final"),
        ("BA_local_to_final", "BA_local", "BA_final"),
    ]


def _feature_delta_rows(
    state_rows: Sequence[dict[str, str]],
    state_features: Mapping[str, Mapping[str, int | bool]],
) -> list[dict[str, str]]:
    state_by_name = {row["state_name"]: row for row in state_rows}
    rows: list[dict[str, str]] = []
    for comparison, left_name, right_name in _comparison_pairs():
        left_features = state_features.get(left_name, {})
        right_features = state_features.get(right_name, {})
        row = {
            "comparison": comparison,
            "left_state": left_name,
            "right_state": right_name,
            "hard_hash_equal": str(
                state_by_name.get(left_name, {}).get("hard_hash", "")
                == state_by_name.get(right_name, {}).get("hard_hash", "")
            ),
        }
        for field in NUMERIC_FEATURE_FIELDS:
            row[f"{field}_delta"] = _delta_text(
                left_features.get(field), right_features.get(field)
            )
        rows.append(row)
    return rows


def _opcode_delta_rows(
    state_opcodes: Mapping[str, Mapping[str, int]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for comparison, left_name, right_name in _comparison_pairs():
        left = state_opcodes.get(left_name, {})
        right = state_opcodes.get(right_name, {})
        row = {
            "comparison": comparison,
            "left_state": left_name,
            "right_state": right_name,
        }
        for opcode in OPCODE_NAMES:
            key = f"num_{opcode}"
            row[f"{key}_delta"] = str(int(right.get(key, 0)) - int(left.get(key, 0)))
        rows.append(row)
    return rows


def _object_size_rows(
    *,
    program: str,
    state_rows: Sequence[dict[str, str]],
    object_root: Path,
    llc_path: ToolPath,
    clang_path: ToolPath,
    llvm_size_path: ToolPath,
    timeout_sec: float,
) -> list[dict[str, str]]:
    final_states = [
        row for row in state_rows if row["state_name"] in {"AB_final", "BA_final"}
    ]
    rows: list[dict[str, str]] = []
    records_by_mode_state: dict[tuple[str, str], ObjectSizeRecord] = {}
    for mode, compiler, compile_mode in [
        ("llc", llc_path, "llc"),
        ("clang", clang_path, "clang"),
    ]:
        for state in final_states:
            state_name = state["state_name"]
            object_path = object_root / f"{mode}__{state_name}.o"
            record = measure_object_size(
                program=program,
                candidate_id=f"{program}__{state_name}__{mode}",
                ir_path=state["ir_path"],
                object_path=object_path,
                compiler_path=compiler if compile_mode == "clang" else None,
                llc_path=compiler,
                llvm_size_path=llvm_size_path,
                timeout_sec=timeout_sec,
                compile_mode=compile_mode,
            )
            records_by_mode_state[(mode, state_name)] = record
    for mode in ("llc", "clang"):
        anchor = records_by_mode_state[(mode, "AB_final")]
        for state_name in ("AB_final", "BA_final"):
            record = records_by_mode_state[(mode, state_name)]
            rows.append(_object_size_row(mode, state_name, record, anchor))
    return rows


def _object_size_row(
    mode: str,
    state_name: str,
    record: ObjectSizeRecord,
    anchor: ObjectSizeRecord,
) -> dict[str, str]:
    text_delta = _optional_delta(record.text_size, anchor.text_size)
    text_delta_pct = _optional_delta_pct(record.text_size, anchor.text_size)
    return {
        "program": record.program,
        "state_name": state_name,
        "compile_mode": mode,
        "ir_path": record.ir_path,
        "object_path": record.object_path,
        "text_size": _optional_int(record.text_size),
        "data_size": _optional_int(record.data_size),
        "bss_size": _optional_int(record.bss_size),
        "total_size": _optional_int(record.total_size),
        "anchor_state": "AB_final",
        "anchor_text_size": _optional_int(anchor.text_size),
        "text_delta": _optional_int(text_delta),
        "text_delta_pct": _optional_float(text_delta_pct),
        "direction": _direction(text_delta),
        "compile_failure_kind": record.compile_failure_kind or "",
        "size_failure_kind": record.size_failure_kind or "",
    }


def _summary(
    state_rows: Sequence[dict[str, str]],
    delta_rows: Sequence[dict[str, str]],
    opcode_delta_rows: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    state_by_name = {row["state_name"]: row for row in state_rows}
    local = _row_by_key(delta_rows, "comparison", "local_AB_vs_BA")
    final = _row_by_key(delta_rows, "comparison", "final_AB_vs_BA")
    llc_ba = _object_row(object_rows, "llc", "BA_final")
    clang_ba = _object_row(object_rows, "clang", "BA_final")
    final_opcode = _row_by_key(opcode_delta_rows, "comparison", "final_AB_vs_BA")
    local_instruction_delta = _parse_optional_int(local.get("num_instructions_delta"))
    final_instruction_delta = _parse_optional_int(final.get("num_instructions_delta"))
    return {
        "Program": PROGRAM,
        "StateCount": len(state_rows),
        "LocalABBAHardHashEqual": _same_hash(
            state_by_name.get("AB_local", {}), state_by_name.get("BA_local", {})
        ),
        "FinalABBAHardHashEqual": _same_hash(
            state_by_name.get("AB_final", {}), state_by_name.get("BA_final", {})
        ),
        "LocalInstructionDelta": local_instruction_delta,
        "FinalInstructionDelta": final_instruction_delta,
        "FeatureDeltaPropagation": _propagation(
            local_instruction_delta, final_instruction_delta
        ),
        "LlcTextDelta": _parse_optional_int(llc_ba.get("text_delta")),
        "ClangTextDelta": _parse_optional_int(clang_ba.get("text_delta")),
        "BothCodegenSmaller": llc_ba.get("direction") == "smaller"
        and clang_ba.get("direction") == "smaller",
        "FinalOpcodeDeltaNonZero": _format_nonzero_opcode_delta(final_opcode),
    }


def _same_hash(left: Mapping[str, str], right: Mapping[str, str]) -> bool:
    left_hash = left.get("hard_hash", "")
    right_hash = right.get("hard_hash", "")
    return bool(left_hash) and left_hash == right_hash


def _propagation(local: int | None, final: int | None) -> str:
    if local is None or final is None:
        return "unknown"
    if abs(final) > abs(local):
        return "expanded"
    if abs(final) < abs(local):
        return "shrunk"
    return "kept"


def _object_row(
    rows: Sequence[dict[str, str]], mode: str, state_name: str
) -> dict[str, str]:
    return next(
        (
            row
            for row in rows
            if row.get("compile_mode") == mode and row.get("state_name") == state_name
        ),
        {},
    )


def _row_by_key(
    rows: Sequence[dict[str, str]], key: str, value: str
) -> dict[str, str]:
    return next((row for row in rows if row.get(key) == value), {})


def _format_nonzero_opcode_delta(row: Mapping[str, str]) -> str:
    deltas: list[str] = []
    for opcode in OPCODE_NAMES:
        key = f"num_{opcode}_delta"
        value = row.get(key, "")
        if value not in {"", "0"}:
            deltas.append(f"{key}={value}")
    return ";".join(deltas) if deltas else "none"


def _opcode(raw_line: str) -> str:
    line = raw_line.split(";", 1)[0].strip()
    if not line or line.startswith(("declare ", "define ")) or line == "}":
        return ""
    if re.match(r"^[A-Za-z$._-][A-Za-z0-9$._-]*:\s*$", line):
        return ""
    if "=" in line:
        line = line.split("=", 1)[1].strip()
    match = re.match(r"([A-Za-z][A-Za-z0-9._-]*)\b", line)
    return "" if match is None else match.group(1)


def _delta_text(left: object, right: object) -> str:
    if not isinstance(left, int) or not isinstance(right, int):
        return ""
    return str(right - left)


def _optional_delta(value: int | None, anchor: int | None) -> int | None:
    if value is None or anchor is None:
        return None
    return value - anchor


def _optional_delta_pct(value: int | None, anchor: int | None) -> float | None:
    if value is None or anchor in {None, 0}:
        return None
    return ((value - anchor) / anchor) * 100.0


def _direction(delta: int | None) -> str:
    if delta is None:
        return "unknown"
    if delta < 0:
        return "smaller"
    if delta > 0:
        return "larger"
    return "equal"


def _optional_int(value: int | None) -> str:
    return "" if value is None else str(value)


def _optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value))


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run P8c Queens effect attribution."
    )
    parser.add_argument(
        "--input-ir", default="data/inputs/testsuite_stanford_queens.ll"
    )
    parser.add_argument("--out", default="data/outputs/effect_attribution_queens")
    parser.add_argument("--opt", default="E:/llvm/build/bin/opt.exe")
    parser.add_argument("--llc", default="E:/llvm/build/bin/llc.exe")
    parser.add_argument("--clang", default="E:/llvm/build/bin/clang.exe")
    parser.add_argument("--llvm-size", default="E:/llvm/build/bin/llvm-size.exe")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)
    result = run_queens_effect_attribution(
        input_ir=args.input_ir,
        output_dir=args.out,
        opt_path=args.opt,
        llc_path=args.llc,
        clang_path=args.clang,
        llvm_size_path=args.llvm_size,
        timeout_sec=args.timeout_sec,
    )
    report = Path(args.out) / "attribution_report.md"
    print(report.read_text(encoding="utf-8"), end="")
    return 0 if result.summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
