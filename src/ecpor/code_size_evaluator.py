"""Evaluate object code size for P5 bounded local candidates."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any, Sequence

from .environment import file_sha256, git_info
from .object_size_runner import ObjectSizeRecord, ToolPath, measure_object_size


OBJECT_SIZE_FIELDS = [
    "program",
    "candidate_id",
    "source",
    "ir_path",
    "object_path",
    "swap_index",
    "pass_a",
    "pass_b",
    "anchor_candidate_id",
    "text_size",
    "data_size",
    "bss_size",
    "total_size",
    "anchor_text_size",
    "anchor_data_size",
    "anchor_bss_size",
    "anchor_total_size",
    "text_delta",
    "text_delta_pct",
    "data_delta",
    "bss_delta",
    "total_delta",
    "total_delta_pct",
    "p5_same_as_anchor",
    "compile_failure_kind",
    "size_failure_kind",
]


@dataclass(frozen=True)
class CodeSizeEvaluation:
    rows: list[dict[str, str]]
    records: list[ObjectSizeRecord]
    summary: dict[str, Any]
    metadata: dict[str, str]


def run_code_size_evaluation(
    *,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    pipeline_output_dir: str | Path,
    output_dir: str | Path,
    llc_path: ToolPath = "llc",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
    p5_report_path: str | Path | None = None,
) -> CodeSizeEvaluation:
    candidates = _load_csv(candidates_csv)
    pipeline_runs = _load_csv(pipeline_runs_csv)
    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    output_root = Path(output_dir)
    object_root = output_root / "object_outputs"
    ir_root = Path(pipeline_output_dir)
    records: list[ObjectSizeRecord] = []
    for run_row in pipeline_runs:
        candidate = candidate_by_id[run_row["candidate_id"]]
        ir_path = ir_root / f"{_safe_name(run_row['candidate_id'])}.ll"
        object_path = object_root / f"{_safe_name(run_row['candidate_id'])}.o"
        records.append(
            measure_object_size(
                program=run_row["program"],
                candidate_id=run_row["candidate_id"],
                ir_path=ir_path,
                object_path=object_path,
                llc_path=llc_path,
                llvm_size_path=llvm_size_path,
                timeout_sec=timeout_sec,
            )
        )

    rows = _build_rows(candidates, pipeline_runs, records)
    invariant_errors = validate_object_size_invariants(
        rows, pipeline_run_count=len(pipeline_runs)
    )
    if invariant_errors:
        raise ValueError(
            "object size invariant violation: " + "; ".join(invariant_errors)
        )
    write_object_size_csv(output_root / "object_size.csv", rows)
    summary = summarize_object_size_rows(rows)
    metadata = build_code_size_metadata(
        candidates_csv=candidates_csv,
        pipeline_runs_csv=pipeline_runs_csv,
        p5_report_path=p5_report_path or Path(pipeline_runs_csv).parent / "report.md",
        llc_path=llc_path,
        llvm_size_path=llvm_size_path,
    )
    report = build_code_size_report(summary, rows, metadata=metadata)
    (output_root / "code_size_report.md").write_text(report, encoding="utf-8")
    return CodeSizeEvaluation(
        rows=rows,
        records=records,
        summary=summary,
        metadata=metadata,
    )


def write_object_size_csv(path: str | Path, rows: Sequence[dict[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OBJECT_SIZE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def summarize_object_size_rows(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    programs = {row["program"] for row in rows}
    anchor_rows = [row for row in rows if row["source"] == "anchor"]
    single_swap_rows = [row for row in rows if row["source"] == "single_swap"]
    build_failed = sum(1 for row in rows if row["compile_failure_kind"])
    parse_failed = sum(
        1 for row in rows if row["size_failure_kind"] == "size_parse_failed"
    )
    computed = [
        int(row["text_delta"])
        for row in single_swap_rows
        if row["text_delta"] not in {"", None}
    ]
    delta_pcts = [
        float(row["text_delta_pct"])
        for row in single_swap_rows
        if row["text_delta_pct"] not in {"", None}
    ]
    ir_different_rows = [
        row
        for row in single_swap_rows
        if row.get("p5_same_as_anchor", "").lower() == "false"
        and row.get("text_delta", "") != ""
    ]
    ir_different_but_text_equal = [
        row for row in ir_different_rows if int(row["text_delta"]) == 0
    ]
    return {
        "programs": len(programs),
        "object_builds_attempted": len(rows),
        "anchor_object_builds": len(anchor_rows),
        "single_swap_object_builds": len(single_swap_rows),
        "object_build_failed": build_failed,
        "size_parse_failed": parse_failed,
        "anchor_sizes_available": sum(1 for row in anchor_rows if row["text_size"]),
        "single_swap_sizes_available": sum(
            1 for row in single_swap_rows if row["text_size"]
        ),
        "code_size_delta_computed": len(computed),
        "smaller_text": sum(1 for delta in computed if delta < 0),
        "equal_text": sum(1 for delta in computed if delta == 0),
        "larger_text": sum(1 for delta in computed if delta > 0),
        "average_text_delta_pct": mean(delta_pcts) if delta_pcts else 0.0,
        "median_text_delta_pct": median(delta_pcts) if delta_pcts else 0.0,
        "min_text_delta_pct": min(delta_pcts) if delta_pcts else 0.0,
        "max_text_delta_pct": max(delta_pcts) if delta_pcts else 0.0,
        "ir_different_but_text_equal_count": len(ir_different_but_text_equal),
        "ir_different_but_text_equal_rate": (
            len(ir_different_but_text_equal) / len(ir_different_rows)
            if ir_different_rows
            else 0.0
        ),
    }


def build_code_size_report(
    summary: dict[str, Any],
    rows: Sequence[dict[str, str]],
    *,
    metadata: dict[str, str] | None = None,
) -> str:
    lines = [
        "# P6 Code Size Report",
        "",
        "P6 compares object code size for P5 anchor and one-swap candidates.",
        "It does not run runtime benchmarks and it does not perform a full search.",
        "",
    ]
    if metadata:
        lines.extend(
            [
                "## Run metadata",
                f"ecpor_git_commit: {metadata['ecpor_git_commit']}",
                f"ecpor_git_dirty: {metadata['ecpor_git_dirty']}",
                f"p5_report: {metadata['p5_report']}",
                f"p5_report_sha256: {metadata['p5_report_sha256']}",
                f"candidates_csv: {metadata['candidates_csv']}",
                f"candidates_csv_sha256: {metadata['candidates_csv_sha256']}",
                f"pipeline_runs_csv: {metadata['pipeline_runs_csv']}",
                f"pipeline_runs_sha256: {metadata['pipeline_runs_sha256']}",
                f"llc_path: {metadata['llc_path']}",
                f"llc_sha256: {metadata['llc_sha256']}",
                f"llvm_size_path: {metadata['llvm_size_path']}",
                f"llvm_size_sha256: {metadata['llvm_size_sha256']}",
                "",
            ]
        )
    lines.extend(
        [
        f"Programs: {summary['programs']}",
        f"Anchor object builds: {summary['anchor_object_builds']}",
        f"Single-swap object builds: {summary['single_swap_object_builds']}",
        f"Object builds attempted: {summary['object_builds_attempted']}",
        f"ObjectBuildFailed: {summary['object_build_failed']}",
        f"SizeParseFailed: {summary['size_parse_failed']}",
        f"Anchor sizes available: {summary['anchor_sizes_available']}",
        f"Single-swap sizes available: {summary['single_swap_sizes_available']}",
        f"CodeSizeDeltaVsAnchor computed: {summary['code_size_delta_computed']}",
        "",
        "Code size vs anchor:",
        f"  smaller_text: {summary['smaller_text']}",
        f"  equal_text: {summary['equal_text']}",
        f"  larger_text: {summary['larger_text']}",
        f"  average_text_delta_pct: {summary['average_text_delta_pct']:.4f}",
        f"  median_text_delta_pct: {summary['median_text_delta_pct']:.4f}",
        f"  min_text_delta_pct: {summary['min_text_delta_pct']:.4f}",
        f"  max_text_delta_pct: {summary['max_text_delta_pct']:.4f}",
        f"IRDifferentButTextEqualCount: {summary['ir_different_but_text_equal_count']}",
        "IRDifferentButTextEqualRate: "
        f"{summary['ir_different_but_text_equal_rate'] * 100.0:.2f}%",
        ]
    )
    best = _best_smaller_candidate(rows)
    if best:
        lines.extend(
            [
                "",
                "Best smaller candidate:",
                f"  program: {best['program']}",
                f"  pair: {best['pass_a']},{best['pass_b']}",
                f"  candidate_id: {best['candidate_id']}",
                f"  text_delta: {best['text_delta']}",
                f"  text_delta_pct: {float(best['text_delta_pct']):.4f}",
            ]
        )
    pair_rows = [row for row in rows if row["source"] == "single_swap"]
    if pair_rows:
        lines.extend(["", "By adjacent pair:"])
        for pair, group in sorted(_group_by_pair(pair_rows).items()):
            computed = [row for row in group if row["text_delta"]]
            deltas = [int(row["text_delta"]) for row in computed]
            pct = [float(row["text_delta_pct"]) for row in computed]
            lines.append(
                "  {pair}: candidates={count} smaller={smaller} equal={equal} "
                "larger={larger} avg_text_delta_pct={avg:.4f}".format(
                    pair=pair,
                    count=len(group),
                    smaller=sum(1 for delta in deltas if delta < 0),
                    equal=sum(1 for delta in deltas if delta == 0),
                    larger=sum(1 for delta in deltas if delta > 0),
                    avg=mean(pct) if pct else 0.0,
                )
            )
    return "\n".join(lines) + "\n"


def validate_object_size_invariants(
    rows: Sequence[dict[str, str]],
    *,
    pipeline_run_count: int | None = None,
) -> list[str]:
    errors: list[str] = []
    if pipeline_run_count is not None and len(rows) != pipeline_run_count:
        errors.append(
            f"row count mismatch: object_size rows={len(rows)} "
            f"pipeline_runs rows={pipeline_run_count}"
        )

    programs = sorted({row.get("program", "") for row in rows})
    anchor_by_program: dict[str, dict[str, str]] = {}
    for program in programs:
        anchor_rows = [
            row
            for row in rows
            if row.get("program") == program and row.get("source") == "anchor"
        ]
        if len(anchor_rows) != 1:
            errors.append(
                f"program {program} has {len(anchor_rows)} anchor rows; expected 1"
            )
            continue
        anchor = anchor_rows[0]
        anchor_by_program[program] = anchor
        if _parse_optional_int(anchor.get("text_size")) is None:
            errors.append(f"program {program} anchor size missing")

    for row in rows:
        candidate_id = row.get("candidate_id", "")
        source = row.get("source", "")
        program = row.get("program", "")

        text_size = _parse_optional_int(row.get("text_size"))
        data_size = _parse_optional_int(row.get("data_size"))
        bss_size = _parse_optional_int(row.get("bss_size"))
        total_size = _parse_optional_int(row.get("total_size"))
        if None not in {text_size, data_size, bss_size, total_size}:
            expected_total = text_size + data_size + bss_size
            if total_size != expected_total:
                errors.append(
                    f"{candidate_id}: total_size != text+data+bss "
                    f"({total_size} != {expected_total})"
                )

        if source == "single_swap":
            anchor = anchor_by_program.get(program)
            if (
                anchor is None
                or not row.get("anchor_candidate_id")
                or row.get("anchor_candidate_id") != anchor.get("candidate_id")
            ):
                errors.append(f"{candidate_id}: missing program anchor")

        if source == "anchor":
            for field in ("text_delta", "total_delta"):
                delta = _parse_optional_int(row.get(field))
                if delta not in {None, 0}:
                    errors.append(f"{candidate_id}: anchor delta is not zero")

        _validate_delta(
            errors,
            row,
            candidate_id,
            value_field="text_size",
            anchor_field="anchor_text_size",
            delta_field="text_delta",
            pct_field="text_delta_pct",
        )
        _validate_delta(
            errors,
            row,
            candidate_id,
            value_field="total_size",
            anchor_field="anchor_total_size",
            delta_field="total_delta",
            pct_field="total_delta_pct",
        )

        object_path = row.get("object_path", "")
        if object_path and Path(object_path).stem != _safe_name(candidate_id):
            errors.append(
                f"{candidate_id}: object path does not match candidate_id "
                f"({object_path})"
            )

    return errors


def build_code_size_metadata(
    *,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    p5_report_path: str | Path,
    llc_path: ToolPath,
    llvm_size_path: ToolPath,
) -> dict[str, str]:
    git = git_info(Path.cwd())
    return {
        "ecpor_git_commit": git.commit,
        "ecpor_git_dirty": str(git.dirty),
        "p5_report": _path_text(p5_report_path),
        "p5_report_sha256": _file_hash_or_empty(p5_report_path),
        "candidates_csv": _path_text(candidates_csv),
        "candidates_csv_sha256": _file_hash_or_empty(candidates_csv),
        "pipeline_runs_csv": _path_text(pipeline_runs_csv),
        "pipeline_runs_sha256": _file_hash_or_empty(pipeline_runs_csv),
        "llc_path": _tool_path_text(llc_path),
        "llc_sha256": _tool_sha256(llc_path),
        "llvm_size_path": _tool_path_text(llvm_size_path),
        "llvm_size_sha256": _tool_sha256(llvm_size_path),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate object code size for P5 candidates."
    )
    parser.add_argument("--p5-dir", default="data/outputs/bounded_local_p5_final")
    parser.add_argument("--candidates-csv")
    parser.add_argument("--pipeline-runs-csv")
    parser.add_argument("--pipeline-output-dir")
    parser.add_argument("--out", default="data/outputs/code_size_p6")
    parser.add_argument("--llc", default="E:/llvm/build/bin/llc.exe")
    parser.add_argument("--llvm-size", default="E:/llvm/build/bin/llvm-size.exe")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    p5_dir = Path(args.p5_dir)
    result = run_code_size_evaluation(
        candidates_csv=args.candidates_csv or p5_dir / "candidates.csv",
        pipeline_runs_csv=args.pipeline_runs_csv or p5_dir / "pipeline_runs.csv",
        pipeline_output_dir=args.pipeline_output_dir or p5_dir / "pipeline_outputs",
        output_dir=args.out,
        llc_path=args.llc,
        llvm_size_path=args.llvm_size,
        timeout_sec=args.timeout_sec,
        p5_report_path=p5_dir / "report.md",
    )
    print(
        build_code_size_report(
            result.summary,
            result.rows,
            metadata=result.metadata,
        ),
        end="",
    )
    return 0


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _build_rows(
    candidates: Sequence[dict[str, str]],
    pipeline_runs: Sequence[dict[str, str]],
    records: Sequence[ObjectSizeRecord],
) -> list[dict[str, str]]:
    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    pipeline_run_by_id = {row["candidate_id"]: row for row in pipeline_runs}
    record_by_id = {record.candidate_id: record for record in records}
    anchor_by_program: dict[str, ObjectSizeRecord] = {}
    anchor_id_by_program: dict[str, str] = {}
    for candidate in candidates:
        if candidate["source"] != "anchor":
            continue
        record = record_by_id.get(candidate["candidate_id"])
        if record is None:
            continue
        anchor_by_program[candidate["program"]] = record
        anchor_id_by_program[candidate["program"]] = candidate["candidate_id"]

    rows: list[dict[str, str]] = []
    for record in records:
        candidate = candidate_by_id[record.candidate_id]
        pipeline_run = pipeline_run_by_id[record.candidate_id]
        anchor = anchor_by_program.get(record.program)
        rows.append(
            _object_size_row(
                candidate,
                pipeline_run,
                record,
                anchor,
                anchor_id_by_program,
            )
        )
    return rows


def _object_size_row(
    candidate: dict[str, str],
    pipeline_run: dict[str, str],
    record: ObjectSizeRecord,
    anchor: ObjectSizeRecord | None,
    anchor_id_by_program: dict[str, str],
) -> dict[str, str]:
    text_delta = _delta(record.text_size, anchor.text_size if anchor else None)
    data_delta = _delta(record.data_size, anchor.data_size if anchor else None)
    bss_delta = _delta(record.bss_size, anchor.bss_size if anchor else None)
    total_delta = _delta(record.total_size, anchor.total_size if anchor else None)
    return {
        "program": record.program,
        "candidate_id": record.candidate_id,
        "source": candidate.get("source", ""),
        "ir_path": record.ir_path,
        "object_path": record.object_path,
        "swap_index": candidate.get("swap_index", ""),
        "pass_a": candidate.get("pass_a", ""),
        "pass_b": candidate.get("pass_b", ""),
        "anchor_candidate_id": anchor_id_by_program.get(record.program, ""),
        "text_size": _optional_int(record.text_size),
        "data_size": _optional_int(record.data_size),
        "bss_size": _optional_int(record.bss_size),
        "total_size": _optional_int(record.total_size),
        "anchor_text_size": _optional_int(anchor.text_size if anchor else None),
        "anchor_data_size": _optional_int(anchor.data_size if anchor else None),
        "anchor_bss_size": _optional_int(anchor.bss_size if anchor else None),
        "anchor_total_size": _optional_int(anchor.total_size if anchor else None),
        "text_delta": _optional_int(text_delta),
        "text_delta_pct": _optional_float(
            _delta_pct(record.text_size, anchor.text_size if anchor else None)
        ),
        "data_delta": _optional_int(data_delta),
        "bss_delta": _optional_int(bss_delta),
        "total_delta": _optional_int(total_delta),
        "total_delta_pct": _optional_float(
            _delta_pct(record.total_size, anchor.total_size if anchor else None)
        ),
        "p5_same_as_anchor": pipeline_run.get("same_as_anchor", ""),
        "compile_failure_kind": record.compile_failure_kind or "",
        "size_failure_kind": record.size_failure_kind or "",
    }


def _delta(value: int | None, anchor: int | None) -> int | None:
    if value is None or anchor is None:
        return None
    return value - anchor


def _delta_pct(value: int | None, anchor: int | None) -> float | None:
    if value is None or anchor in {None, 0}:
        return None
    return ((value - anchor) / anchor) * 100.0


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


def _validate_delta(
    errors: list[str],
    row: dict[str, str],
    candidate_id: str,
    *,
    value_field: str,
    anchor_field: str,
    delta_field: str,
    pct_field: str,
) -> None:
    value = _parse_optional_int(row.get(value_field))
    anchor = _parse_optional_int(row.get(anchor_field))
    delta = _parse_optional_int(row.get(delta_field))
    if value is None or anchor is None:
        return

    expected_delta = value - anchor
    if delta != expected_delta:
        errors.append(
            f"{candidate_id}: {delta_field} mismatch "
            f"({delta} != {expected_delta})"
        )

    pct = _parse_optional_float(row.get(pct_field))
    if anchor == 0:
        if pct is not None:
            errors.append(f"{candidate_id}: {pct_field} should be empty")
        return
    expected_pct = (expected_delta / anchor) * 100.0
    if pct is None or abs(pct - expected_pct) > 0.0005:
        errors.append(
            f"{candidate_id}: {pct_field} mismatch "
            f"({pct} != {expected_pct:.6f})"
        )


def _best_smaller_candidate(
    rows: Sequence[dict[str, str]],
) -> dict[str, str] | None:
    smaller_rows = [
        row
        for row in rows
        if row.get("source") == "single_swap"
        and _parse_optional_int(row.get("text_delta")) is not None
        and _parse_optional_int(row.get("text_delta")) < 0
    ]
    if not smaller_rows:
        return None
    return min(smaller_rows, key=lambda row: _parse_optional_int(row["text_delta"]) or 0)


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


def _path_text(path: str | Path) -> str:
    return Path(path).as_posix()


def _group_by_pair(rows: Sequence[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        pair = f"{row['pass_a']},{row['pass_b']}"
        grouped.setdefault(pair, []).append(row)
    return grouped


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


if __name__ == "__main__":
    raise SystemExit(main())
