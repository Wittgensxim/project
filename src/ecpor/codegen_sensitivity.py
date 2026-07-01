"""Compare llc and clang -c object-size directions for saved IR outputs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

from .environment import file_sha256, git_info
from .object_size_runner import ObjectSizeRecord, ToolPath, measure_object_size


CLANG_OBJECT_SIZE_FIELDS = [
    "program",
    "candidate_id",
    "depth",
    "source",
    "compile_mode",
    "ir_path",
    "object_path",
    "text_size",
    "data_size",
    "bss_size",
    "total_size",
    "anchor_text_size",
    "anchor_total_size",
    "text_delta",
    "text_delta_pct",
    "total_delta",
    "total_delta_pct",
    "direction",
    "compile_failure_kind",
    "size_failure_kind",
    "llc_text_size",
    "llc_text_delta",
    "llc_text_delta_pct",
    "llc_direction",
]

CODEGEN_COMPARE_FIELDS = [
    "program",
    "candidate_id",
    "depth",
    "source",
    "llc_text_size",
    "clang_text_size",
    "llc_text_delta",
    "clang_text_delta",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "llc_direction",
    "clang_direction",
    "direction_agree",
]


@dataclass(frozen=True)
class CodegenSensitivityResult:
    clang_rows: list[dict[str, str]]
    compare_rows: list[dict[str, str]]
    records: list[ObjectSizeRecord]
    summary: dict[str, Any]
    metadata: dict[str, str]


def run_codegen_sensitivity(
    *,
    p6_object_size_csv: str | Path,
    p7_object_size_csv: str | Path,
    output_dir: str | Path,
    clang_path: ToolPath = "clang",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
) -> CodegenSensitivityResult:
    p6_rows = _load_csv(p6_object_size_csv)
    p7_rows = _load_csv(p7_object_size_csv)
    selected_rows = _select_input_rows(p6_rows, p7_rows)
    output_root = Path(output_dir)
    object_root = output_root / "clang_object_outputs"
    object_root.mkdir(parents=True, exist_ok=True)

    records: list[ObjectSizeRecord] = []
    for row in selected_rows:
        candidate_id = row["candidate_id"]
        records.append(
            measure_object_size(
                program=row["program"],
                candidate_id=candidate_id,
                ir_path=row["ir_path"],
                object_path=object_root / f"{_safe_name(candidate_id)}.o",
                compiler_path=clang_path,
                llvm_size_path=llvm_size_path,
                timeout_sec=timeout_sec,
                compile_mode="clang",
            )
        )

    clang_rows = _build_clang_rows(selected_rows, records)
    compare_rows = _build_compare_rows(clang_rows)
    summary = _summarize(
        input_rows=selected_rows,
        clang_rows=clang_rows,
        compare_rows=compare_rows,
    )
    metadata = _build_metadata(
        p6_object_size_csv=p6_object_size_csv,
        p7_object_size_csv=p7_object_size_csv,
        clang_path=clang_path,
        llvm_size_path=llvm_size_path,
    )
    _write_csv(
        output_root / "p8a_clang_object_size.csv",
        clang_rows,
        CLANG_OBJECT_SIZE_FIELDS,
    )
    _write_csv(
        output_root / "p8a_codegen_direction_compare.csv",
        compare_rows,
        CODEGEN_COMPARE_FIELDS,
    )
    (output_root / "p8a_codegen_sensitivity_report.md").write_text(
        build_codegen_sensitivity_report(summary, compare_rows, metadata=metadata),
        encoding="utf-8",
    )
    return CodegenSensitivityResult(
        clang_rows=clang_rows,
        compare_rows=compare_rows,
        records=records,
        summary=summary,
        metadata=metadata,
    )


def build_codegen_sensitivity_report(
    summary: Mapping[str, Any],
    compare_rows: Sequence[dict[str, str]],
    *,
    metadata: Mapping[str, str] | None = None,
) -> str:
    lines = [
        "# P8a Clang-C Codegen Sensitivity Report",
        "",
        "P8a compares saved IR outputs under two object-code paths.",
        "It does not generate new certificates and it does not run runtime benchmarks.",
        "",
    ]
    if metadata:
        lines.extend(
            [
                "## Run metadata",
                f"ecpor_git_commit: {metadata['ecpor_git_commit']}",
                f"ecpor_git_dirty: {metadata['ecpor_git_dirty']}",
                f"p6_object_size_csv: {metadata['p6_object_size_csv']}",
                f"p6_object_size_sha256: {metadata['p6_object_size_sha256']}",
                f"p7_object_size_csv: {metadata['p7_object_size_csv']}",
                f"p7_object_size_sha256: {metadata['p7_object_size_sha256']}",
                f"clang_path: {metadata['clang_path']}",
                f"clang_sha256: {metadata['clang_sha256']}",
                f"llvm_size_path: {metadata['llvm_size_path']}",
                f"llvm_size_sha256: {metadata['llvm_size_sha256']}",
                "",
            ]
        )
    lines.extend(
        [
            f"Programs: {summary['Programs']}",
            f"IRInputs: {summary['IRInputs']}",
            f"AnchorInputs: {summary['AnchorInputs']}",
            f"SingleSwapInputs: {summary['SingleSwapInputs']}",
            f"Depth2Inputs: {summary['Depth2Inputs']}",
            f"ClangObjectBuildsAttempted: {summary['ClangObjectBuildsAttempted']}",
            f"ClangObjectBuildFailed: {summary['ClangObjectBuildFailed']}",
            f"ClangSizeParseFailed: {summary['ClangSizeParseFailed']}",
            f"DirectionComparisonCandidates: {summary['DirectionComparisonCandidates']}",
            f"DirectionAgreementCount: {summary['DirectionAgreementCount']}",
            f"DirectionAgreementRate: {summary['DirectionAgreementRate'] * 100.0:.2f}%",
            f"SmallerUnderBothCount: {summary['SmallerUnderBothCount']}",
            f"SmallerOnlyUnderLlcCount: {summary['SmallerOnlyUnderLlcCount']}",
            f"SmallerOnlyUnderClangCount: {summary['SmallerOnlyUnderClangCount']}",
            f"DirectionDisagreementCount: {summary['DirectionDisagreementCount']}",
            "",
            "## Direction disagreements",
        ]
    )
    disagreements = [row for row in compare_rows if row["direction_agree"] == "False"]
    if not disagreements:
        lines.append("none")
    for row in disagreements:
        lines.append(
            "{program}: {candidate_id} source={source} depth={depth} "
            "llc={llc_direction}({llc_pct}) clang={clang_direction}({clang_pct})".format(
                program=row["program"],
                candidate_id=row["candidate_id"],
                source=row["source"],
                depth=row["depth"],
                llc_direction=row["llc_direction"],
                llc_pct=row["llc_text_delta_pct"],
                clang_direction=row["clang_direction"],
                clang_pct=row["clang_text_delta_pct"],
            )
        )
    smaller_both = [row for row in compare_rows if row["llc_direction"] == "smaller" and row["clang_direction"] == "smaller"]
    if smaller_both:
        lines.extend(["", "## Smaller under both"])
        for row in smaller_both:
            lines.append(
                "{program}: {candidate_id} source={source} depth={depth} "
                "llc_delta_pct={llc_pct} clang_delta_pct={clang_pct}".format(
                    program=row["program"],
                    candidate_id=row["candidate_id"],
                    source=row["source"],
                    depth=row["depth"],
                    llc_pct=row["llc_text_delta_pct"],
                    clang_pct=row["clang_text_delta_pct"],
                )
            )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare llc and clang -c codegen size directions."
    )
    parser.add_argument(
        "--p6-object-size",
        default="data/outputs/code_size_p6_final/object_size.csv",
    )
    parser.add_argument(
        "--p7-object-size",
        default="data/outputs/bounded_two_swap_p7b/two_swap_object_size.csv",
    )
    parser.add_argument("--out", default="data/outputs/codegen_sensitivity_p8a")
    parser.add_argument("--clang", default="E:/llvm/build/bin/clang.exe")
    parser.add_argument("--llvm-size", default="E:/llvm/build/bin/llvm-size.exe")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    result = run_codegen_sensitivity(
        p6_object_size_csv=args.p6_object_size,
        p7_object_size_csv=args.p7_object_size,
        output_dir=args.out,
        clang_path=args.clang,
        llvm_size_path=args.llvm_size,
        timeout_sec=args.timeout_sec,
    )
    print(
        build_codegen_sensitivity_report(
            result.summary,
            result.compare_rows,
            metadata=result.metadata,
        ),
        end="",
    )
    return 0


def _select_input_rows(
    p6_rows: Sequence[dict[str, str]],
    p7_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in p6_rows:
        if row.get("source") not in {"anchor", "single_swap"}:
            continue
        if row.get("candidate_id", "") in seen:
            continue
        selected.append(row)
        seen.add(row.get("candidate_id", ""))
    anchor_programs = {row.get("program", "") for row in selected if row.get("source") == "anchor"}
    for row in p7_rows:
        if row.get("source") == "anchor" and row.get("program", "") not in anchor_programs:
            selected.append(row)
            seen.add(row.get("candidate_id", ""))
            anchor_programs.add(row.get("program", ""))
    for row in p7_rows:
        if row.get("source") != "two_swap":
            continue
        if row.get("candidate_id", "") in seen:
            continue
        selected.append(row)
        seen.add(row.get("candidate_id", ""))
    return selected


def _build_clang_rows(
    input_rows: Sequence[dict[str, str]],
    records: Sequence[ObjectSizeRecord],
) -> list[dict[str, str]]:
    record_by_id = {record.candidate_id: record for record in records}
    anchor_by_program = {
        row["program"]: record_by_id.get(row["candidate_id"])
        for row in input_rows
        if row.get("source") == "anchor"
    }
    rows: list[dict[str, str]] = []
    for source_row in input_rows:
        record = record_by_id[source_row["candidate_id"]]
        anchor = anchor_by_program.get(source_row["program"])
        text_delta = _delta(record.text_size, anchor.text_size if anchor else None)
        total_delta = _delta(record.total_size, anchor.total_size if anchor else None)
        text_pct = _delta_pct(record.text_size, anchor.text_size if anchor else None)
        total_pct = _delta_pct(record.total_size, anchor.total_size if anchor else None)
        rows.append(
            {
                "program": record.program,
                "candidate_id": record.candidate_id,
                "depth": _depth_for_source(source_row.get("source", "")),
                "source": source_row.get("source", ""),
                "compile_mode": "clang",
                "ir_path": record.ir_path,
                "object_path": record.object_path,
                "text_size": _optional_int(record.text_size),
                "data_size": _optional_int(record.data_size),
                "bss_size": _optional_int(record.bss_size),
                "total_size": _optional_int(record.total_size),
                "anchor_text_size": _optional_int(anchor.text_size if anchor else None),
                "anchor_total_size": _optional_int(anchor.total_size if anchor else None),
                "text_delta": _optional_int(text_delta),
                "text_delta_pct": _optional_float(text_pct),
                "total_delta": _optional_int(total_delta),
                "total_delta_pct": _optional_float(total_pct),
                "direction": _direction_from_delta(text_delta),
                "compile_failure_kind": record.compile_failure_kind or "",
                "size_failure_kind": record.size_failure_kind or "",
                "llc_text_size": source_row.get("text_size", ""),
                "llc_text_delta": source_row.get("text_delta", ""),
                "llc_text_delta_pct": source_row.get("text_delta_pct", ""),
                "llc_direction": _direction_from_text(source_row.get("text_delta", "")),
            }
        )
    return rows


def _build_compare_rows(clang_rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in clang_rows:
        if row.get("source") not in {"single_swap", "two_swap"}:
            continue
        if row.get("compile_failure_kind") or row.get("size_failure_kind"):
            continue
        llc_direction = row.get("llc_direction", "")
        clang_direction = row.get("direction", "")
        if not llc_direction or not clang_direction:
            continue
        rows.append(
            {
                "program": row["program"],
                "candidate_id": row["candidate_id"],
                "depth": row["depth"],
                "source": row["source"],
                "llc_text_size": row["llc_text_size"],
                "clang_text_size": row["text_size"],
                "llc_text_delta": row["llc_text_delta"],
                "clang_text_delta": row["text_delta"],
                "llc_text_delta_pct": row["llc_text_delta_pct"],
                "clang_text_delta_pct": row["text_delta_pct"],
                "llc_direction": llc_direction,
                "clang_direction": clang_direction,
                "direction_agree": str(llc_direction == clang_direction),
            }
        )
    return rows


def _summarize(
    *,
    input_rows: Sequence[dict[str, str]],
    clang_rows: Sequence[dict[str, str]],
    compare_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    agreement = sum(1 for row in compare_rows if row["direction_agree"] == "True")
    disagreements = len(compare_rows) - agreement
    clang_delta_pcts = [
        value
        for row in clang_rows
        if row.get("source") in {"single_swap", "two_swap"}
        for value in [_parse_optional_float(row.get("text_delta_pct"))]
        if value is not None
    ]
    return {
        "Programs": len({row.get("program", "") for row in input_rows}),
        "IRInputs": len(input_rows),
        "AnchorInputs": sum(1 for row in input_rows if row.get("source") == "anchor"),
        "SingleSwapInputs": sum(1 for row in input_rows if row.get("source") == "single_swap"),
        "Depth2Inputs": sum(1 for row in input_rows if row.get("source") == "two_swap"),
        "ClangObjectBuildsAttempted": len(clang_rows),
        "ClangObjectBuildFailed": sum(1 for row in clang_rows if row["compile_failure_kind"]),
        "ClangSizeParseFailed": sum(1 for row in clang_rows if row["size_failure_kind"] == "size_parse_failed"),
        "DirectionComparisonCandidates": len(compare_rows),
        "DirectionAgreementCount": agreement,
        "DirectionAgreementRate": agreement / len(compare_rows) if compare_rows else 0.0,
        "SmallerUnderBothCount": sum(
            1
            for row in compare_rows
            if row["llc_direction"] == "smaller" and row["clang_direction"] == "smaller"
        ),
        "SmallerOnlyUnderLlcCount": sum(
            1
            for row in compare_rows
            if row["llc_direction"] == "smaller" and row["clang_direction"] != "smaller"
        ),
        "SmallerOnlyUnderClangCount": sum(
            1
            for row in compare_rows
            if row["llc_direction"] != "smaller" and row["clang_direction"] == "smaller"
        ),
        "DirectionDisagreementCount": disagreements,
        "AverageClangTextDeltaPct": (
            mean(clang_delta_pcts) if clang_delta_pcts else 0.0
        ),
    }


def _build_metadata(
    *,
    p6_object_size_csv: str | Path,
    p7_object_size_csv: str | Path,
    clang_path: ToolPath,
    llvm_size_path: ToolPath,
) -> dict[str, str]:
    git = git_info(Path.cwd())
    return {
        "ecpor_git_commit": git.commit,
        "ecpor_git_dirty": str(git.dirty),
        "p6_object_size_csv": Path(p6_object_size_csv).as_posix(),
        "p6_object_size_sha256": _file_hash_or_empty(p6_object_size_csv),
        "p7_object_size_csv": Path(p7_object_size_csv).as_posix(),
        "p7_object_size_sha256": _file_hash_or_empty(p7_object_size_csv),
        "clang_path": _tool_path_text(clang_path),
        "clang_sha256": _tool_sha256(clang_path),
        "llvm_size_path": _tool_path_text(llvm_size_path),
        "llvm_size_sha256": _tool_sha256(llvm_size_path),
    }


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _delta(value: int | None, anchor: int | None) -> int | None:
    if value is None or anchor is None:
        return None
    return value - anchor


def _delta_pct(value: int | None, anchor: int | None) -> float | None:
    if value is None or anchor in {None, 0}:
        return None
    return ((value - anchor) / anchor) * 100.0


def _direction_from_delta(delta: int | None) -> str:
    if delta is None:
        return ""
    if delta < 0:
        return "smaller"
    if delta > 0:
        return "larger"
    return "equal"


def _direction_from_text(value: str | None) -> str:
    parsed = _parse_optional_int(value)
    return _direction_from_delta(parsed)


def _depth_for_source(source: str) -> str:
    if source == "anchor":
        return "0"
    if source == "single_swap":
        return "1"
    if source == "two_swap":
        return "2"
    return ""


def _optional_int(value: int | None) -> str:
    return "" if value is None else str(value)


def _optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def _parse_optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value), 0)


def _parse_optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _file_hash_or_empty(path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    try:
        return file_sha256(candidate)
    except OSError:
        return ""


def _tool_path_text(tool_path: ToolPath) -> str:
    if isinstance(tool_path, (str, Path)):
        return str(tool_path)
    return " ".join(str(part) for part in tool_path)


def _tool_sha256(tool_path: ToolPath) -> str:
    candidates = [tool_path] if isinstance(tool_path, (str, Path)) else list(tool_path)
    for part in candidates:
        path = Path(part)
        if path.exists() and path.is_file():
            return _file_hash_or_empty(path)
    return ""


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


if __name__ == "__main__":
    raise SystemExit(main())
