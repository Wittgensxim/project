"""P8b-0 benchmark ingestion from llvm-test-suite C sources."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Sequence

from .feature_scan import scan_ir_file
from .object_size_runner import ToolPath, measure_object_size
from .runner import OptPath, run_opt


DEFAULT_SOURCE_DIRS = [
    "SingleSource/Benchmarks/Misc",
    "SingleSource/Regression/C",
    "SingleSource/UnitTests",
]

DEFAULT_SCALAR_PIPELINE = (
    "function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)"
)

INGEST_SUMMARY_FIELDS = [
    "program",
    "family",
    "source_path",
    "input_ir",
    "status",
    "failure_stage",
    "failure_kind",
    "num_functions",
    "num_instructions",
    "num_basic_blocks",
    "scalar_pipeline_ok",
    "llc_object_ok",
    "clang_object_ok",
    "size_parse_ok",
]


@dataclass(frozen=True)
class BenchmarkIngestResult:
    rows: list[dict[str, str]]
    accepted_rows: list[dict[str, str]]
    rejected_rows: list[dict[str, str]]
    summary: dict[str, Any]


@dataclass(frozen=True)
class _CommandResult:
    returncode: int
    output: str
    elapsed_ms: float
    timed_out: bool = False
    os_error: bool = False


def run_benchmark_ingest(
    *,
    source_roots: Sequence[str | Path],
    input_dir: str | Path = "data/inputs",
    output_dir: str | Path = "data/outputs/benchmark_ingest_p8b",
    config_path: str | Path = "configs/benchmarks_p8b.yaml",
    clang_path: ToolPath = "E:/llvm/build/bin/clang.exe",
    opt_path: OptPath = "E:/llvm/build/bin/opt.exe",
    llc_path: ToolPath = "E:/llvm/build/bin/llc.exe",
    llvm_size_path: ToolPath = "E:/llvm/build/bin/llvm-size.exe",
    scalar_pipeline: str = DEFAULT_SCALAR_PIPELINE,
    accepted_limit: int = 8,
    min_scanned: int = 20,
    max_programs_per_family: int | None = None,
    stratify_source_dirs: bool = False,
    program_prefix: str = "testsuite_misc",
    stage_name: str = "P8b-0",
    instruction_limit: int = 5000,
    timeout_sec: float = 30.0,
    config_input_prefix: str = "data/inputs",
    keep_scratch: bool = False,
) -> BenchmarkIngestResult:
    sources = discover_c_sources(
        source_roots,
        stratify_source_dirs=stratify_source_dirs,
    )
    output_root = Path(output_dir)
    input_root = Path(input_dir)
    scratch_root = output_root / "_scratch"
    ir_root = scratch_root / "ir_candidates"
    scalar_root = scratch_root / "scalar_outputs"
    object_root = scratch_root / "object_outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    input_root.mkdir(parents=True, exist_ok=True)
    ir_root.mkdir(parents=True, exist_ok=True)
    scalar_root.mkdir(parents=True, exist_ok=True)
    object_root.mkdir(parents=True, exist_ok=True)

    used_ids: dict[str, int] = {}
    rows: list[dict[str, str]] = []
    accepted_rows: list[dict[str, str]] = []
    rejected_rows: list[dict[str, str]] = []
    accepted_family_counts: dict[str, int] = {}
    for source in sources:
        if len(accepted_rows) >= accepted_limit and len(rows) >= min_scanned:
            break
        program = _program_id(source, used_ids, program_prefix=program_prefix)
        family = _program_family(program)
        if len(accepted_rows) >= accepted_limit:
            row = _row(
                program=program,
                family=family,
                source=source,
                status="rejected",
                failure_stage="selection",
                failure_kind="accepted_limit_reached",
            )
        elif (
            max_programs_per_family is not None
            and accepted_family_counts.get(family, 0) >= max_programs_per_family
        ):
            row = _row(
                program=program,
                family=family,
                source=source,
                status="rejected",
                failure_stage="selection",
                failure_kind="family_limit_reached",
            )
        else:
            row = _ingest_one_source(
                source=source,
                program=program,
                family=family,
                input_root=input_root,
                ir_root=ir_root,
                scalar_root=scalar_root,
                object_root=object_root,
                clang_path=clang_path,
                opt_path=opt_path,
                llc_path=llc_path,
                llvm_size_path=llvm_size_path,
                scalar_pipeline=scalar_pipeline,
                instruction_limit=instruction_limit,
                timeout_sec=timeout_sec,
            )
        rows.append(row)
        if row["status"] == "accepted":
            accepted_rows.append(row)
            accepted_family_counts[family] = accepted_family_counts.get(family, 0) + 1
        else:
            rejected_rows.append(row)

    _write_csv(output_root / "ingest_summary.csv", rows, INGEST_SUMMARY_FIELDS)
    _write_report(
        output_root / "report.md",
        rows,
        accepted_rows,
        rejected_rows,
        stage_name=stage_name,
        max_programs_per_family=max_programs_per_family,
    )
    _write_config(
        Path(config_path),
        accepted_rows,
        stage_name=stage_name,
        source_roots=source_roots,
        scalar_pipeline=scalar_pipeline,
        instruction_limit=instruction_limit,
        max_programs_per_family=max_programs_per_family,
        config_input_prefix=config_input_prefix,
    )
    if not keep_scratch:
        shutil.rmtree(scratch_root, ignore_errors=True)

    return BenchmarkIngestResult(
        rows=rows,
        accepted_rows=accepted_rows,
        rejected_rows=rejected_rows,
        summary=_summary(
            rows,
            accepted_rows,
            rejected_rows,
            max_programs_per_family=max_programs_per_family,
        ),
    )


def discover_c_sources(
    source_roots: Sequence[str | Path],
    *,
    stratify_source_dirs: bool = False,
) -> list[Path]:
    buckets: list[list[Path]] = []
    for root in source_roots:
        candidate = Path(root)
        if candidate.is_file() and candidate.suffix.lower() == ".c":
            buckets.append([candidate])
        elif candidate.exists():
            buckets.append(
                sorted(
                    (
                        path
                        for path in candidate.rglob("*.c")
                        if path.is_file() and not path.name.startswith(".")
                    ),
                    key=lambda path: path.as_posix().lower(),
                )
            )
    if stratify_source_dirs:
        return _round_robin_sources(buckets)
    return sorted(
        (path for bucket in buckets for path in bucket),
        key=lambda path: path.as_posix().lower(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest small P8b benchmarks.")
    parser.add_argument("--suite-root", default="E:/llvm-test-suite")
    parser.add_argument(
        "--source-dir",
        action="append",
        dest="source_dirs",
        help="Source directory relative to --suite-root. Can be repeated.",
    )
    parser.add_argument("--input-dir", default="data/inputs")
    parser.add_argument("--out", default="data/outputs/benchmark_ingest_p8b")
    parser.add_argument("--config", default="configs/benchmarks_p8b.yaml")
    parser.add_argument("--clang", default="E:/llvm/build/bin/clang.exe")
    parser.add_argument("--opt", default="E:/llvm/build/bin/opt.exe")
    parser.add_argument("--llc", default="E:/llvm/build/bin/llc.exe")
    parser.add_argument("--llvm-size", default="E:/llvm/build/bin/llvm-size.exe")
    parser.add_argument("--accepted-limit", type=int, default=8)
    parser.add_argument("--min-scanned", type=int, default=20)
    parser.add_argument("--max-programs-per-family", type=int)
    parser.add_argument("--stratify-source-dirs", action="store_true")
    parser.add_argument("--program-prefix", default="testsuite_misc")
    parser.add_argument("--stage-name", default="P8b-0")
    parser.add_argument("--instruction-limit", type=int, default=5000)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument("--keep-scratch", action="store_true")
    args = parser.parse_args(argv)

    suite_root = Path(args.suite_root)
    source_dirs = args.source_dirs or DEFAULT_SOURCE_DIRS
    source_roots = [suite_root / source_dir for source_dir in source_dirs]
    result = run_benchmark_ingest(
        source_roots=source_roots,
        input_dir=args.input_dir,
        output_dir=args.out,
        config_path=args.config,
        clang_path=args.clang,
        opt_path=args.opt,
        llc_path=args.llc,
        llvm_size_path=args.llvm_size,
        accepted_limit=args.accepted_limit,
        min_scanned=args.min_scanned,
        max_programs_per_family=args.max_programs_per_family,
        stratify_source_dirs=args.stratify_source_dirs,
        program_prefix=args.program_prefix,
        stage_name=args.stage_name,
        instruction_limit=args.instruction_limit,
        timeout_sec=args.timeout_sec,
        keep_scratch=args.keep_scratch,
    )
    print(
        _report_text(
            result.rows,
            result.accepted_rows,
            result.rejected_rows,
            stage_name=args.stage_name,
            max_programs_per_family=args.max_programs_per_family,
        ),
        end="",
    )
    return 0


def _ingest_one_source(
    *,
    source: Path,
    program: str,
    family: str,
    input_root: Path,
    ir_root: Path,
    scalar_root: Path,
    object_root: Path,
    clang_path: ToolPath,
    opt_path: OptPath,
    llc_path: ToolPath,
    llvm_size_path: ToolPath,
    scalar_pipeline: str,
    instruction_limit: int,
    timeout_sec: float,
) -> dict[str, str]:
    candidate_ir = ir_root / f"{program}.ll"
    accepted_ir = input_root / f"{program}.ll"
    scalar_ir = scalar_root / f"{program}.scalar.ll"
    features: dict[str, int | bool] = {}
    ir_result = _run_clang_emit_llvm(source, candidate_ir, clang_path, timeout_sec)
    if _compile_failure_kind(ir_result, candidate_ir):
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="ir_generation",
            failure_kind=_compile_failure_kind(ir_result, candidate_ir) or "",
        )

    ir_text = candidate_ir.read_text(encoding="utf-8", errors="replace")
    if "optnone" in ir_text:
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="ir_validation",
            failure_kind="optnone_present",
        )

    features = scan_ir_file(candidate_ir)
    if int(features.get("num_instructions", 0)) >= instruction_limit:
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="ir_validation",
            failure_kind="ir_too_large",
            features=features,
        )

    scalar_result = run_opt(
        candidate_ir,
        scalar_pipeline,
        scalar_ir,
        opt_path=opt_path,
        timeout_sec=timeout_sec,
    )
    if scalar_result.failure_kind:
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="scalar_pipeline",
            failure_kind=scalar_result.failure_kind,
            features=features,
        )

    llc_record = measure_object_size(
        program=program,
        candidate_id=program,
        ir_path=scalar_ir,
        object_path=object_root / f"{program}.llc.o",
        llc_path=llc_path,
        llvm_size_path=llvm_size_path,
        timeout_sec=timeout_sec,
        compile_mode="llc",
    )
    if llc_record.compile_failure_kind or llc_record.size_failure_kind:
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="llc_object",
            failure_kind=llc_record.compile_failure_kind
            or llc_record.size_failure_kind
            or "",
            features=features,
            scalar_pipeline_ok=True,
        )

    clang_record = measure_object_size(
        program=program,
        candidate_id=program,
        ir_path=scalar_ir,
        object_path=object_root / f"{program}.clang.o",
        compiler_path=clang_path,
        llvm_size_path=llvm_size_path,
        timeout_sec=timeout_sec,
        compile_mode="clang",
    )
    if clang_record.compile_failure_kind or clang_record.size_failure_kind:
        return _row(
            program=program,
            family=family,
            source=source,
            status="rejected",
            failure_stage="clang_object",
            failure_kind=clang_record.compile_failure_kind
            or clang_record.size_failure_kind
            or "",
            features=features,
            scalar_pipeline_ok=True,
            llc_object_ok=True,
        )

    shutil.copyfile(candidate_ir, accepted_ir)
    return _row(
        program=program,
        family=family,
        source=source,
        input_ir=accepted_ir,
        status="accepted",
        features=features,
        scalar_pipeline_ok=True,
        llc_object_ok=True,
        clang_object_ok=True,
        size_parse_ok=True,
    )


def _run_clang_emit_llvm(
    source: Path, output_ir: Path, clang_path: ToolPath, timeout_sec: float
) -> _CommandResult:
    output_ir.parent.mkdir(parents=True, exist_ok=True)
    command = [
        *_normalize_tool_path(clang_path),
        "-g0",
        "-O0",
        "-Xclang",
        "-disable-O0-optnone",
        "-S",
        "-emit-llvm",
        str(source),
        "-o",
        str(output_ir),
    ]
    return _run_command(command, timeout_sec)


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


def _compile_failure_kind(result: _CommandResult, output_path: Path) -> str | None:
    output_exists = output_path.exists()
    if result.timed_out:
        return "clang_timeout"
    if result.os_error:
        return "clang_os_error"
    if result.returncode == 0 and output_exists:
        return None
    if result.returncode == 0 and not output_exists:
        return "clang_output_missing"
    if result.returncode != 0 and output_exists:
        return "clang_failed_output_exists"
    return "clang_failed"


def _row(
    *,
    program: str,
    family: str,
    source: Path,
    status: str,
    failure_stage: str = "",
    failure_kind: str = "",
    input_ir: Path | None = None,
    features: dict[str, int | bool] | None = None,
    scalar_pipeline_ok: bool = False,
    llc_object_ok: bool = False,
    clang_object_ok: bool = False,
    size_parse_ok: bool = False,
) -> dict[str, str]:
    feature_values = features or {}
    return {
        "program": program,
        "family": family,
        "source_path": str(source),
        "input_ir": str(input_ir) if input_ir else "",
        "status": status,
        "failure_stage": failure_stage,
        "failure_kind": failure_kind,
        "num_functions": str(int(feature_values.get("num_functions", 0))),
        "num_instructions": str(int(feature_values.get("num_instructions", 0))),
        "num_basic_blocks": str(int(feature_values.get("num_basic_blocks", 0))),
        "scalar_pipeline_ok": str(scalar_pipeline_ok),
        "llc_object_ok": str(llc_object_ok),
        "clang_object_ok": str(clang_object_ok),
        "size_parse_ok": str(size_parse_ok),
    }


def _write_csv(
    path: str | Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    path: str | Path,
    rows: Sequence[dict[str, str]],
    accepted_rows: Sequence[dict[str, str]],
    rejected_rows: Sequence[dict[str, str]],
    *,
    stage_name: str,
    max_programs_per_family: int | None,
) -> None:
    Path(path).write_text(
        _report_text(
            rows,
            accepted_rows,
            rejected_rows,
            stage_name=stage_name,
            max_programs_per_family=max_programs_per_family,
        ),
        encoding="utf-8",
    )


def _report_text(
    rows: Sequence[dict[str, str]],
    accepted_rows: Sequence[dict[str, str]],
    rejected_rows: Sequence[dict[str, str]],
    *,
    stage_name: str = "P8b-0",
    max_programs_per_family: int | None = None,
) -> str:
    summary = _summary(
        rows,
        accepted_rows,
        rejected_rows,
        max_programs_per_family=max_programs_per_family,
    )
    lines = [
        f"# {stage_name} Benchmark Ingest Report",
        "",
        "Benchmark ingestion only; no pair matrix and no new certificate.",
        "",
        f"CandidateSourceFilesScanned: {len(rows)}",
        f"AcceptedPrograms: {len(accepted_rows)}",
        f"RejectedPrograms: {len(rejected_rows)}",
        f"MaxProgramsPerFamily: {summary['MaxProgramsPerFamily']}",
        f"MaxAcceptedFamilyCount: {summary['MaxAcceptedFamilyCount']}",
        f"FamilyLimitViolations: {summary['FamilyLimitViolations']}",
        f"IRGenerationOk: {_count_stage_ok(rows, 'ir_generation')}",
        f"ScalarPipelineOk: {sum(1 for row in rows if row['scalar_pipeline_ok'] == 'True')}",
        f"LlcObjectOk: {sum(1 for row in rows if row['llc_object_ok'] == 'True')}",
        f"ClangObjectOk: {sum(1 for row in rows if row['clang_object_ok'] == 'True')}",
        f"SizeParseOk: {sum(1 for row in rows if row['size_parse_ok'] == 'True')}",
        "",
        "## Failure Distribution",
        "",
    ]
    for key, count in sorted(_failure_distribution(rejected_rows).items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Accepted Programs", ""])
    for row in accepted_rows:
        lines.append(
            f"- {row['program']}: family={row['family']} instructions={row['num_instructions']} ir={row['input_ir']}"
        )
    return "\n".join(lines) + "\n"


def _write_config(
    path: Path,
    accepted_rows: Sequence[dict[str, str]],
    *,
    stage_name: str,
    source_roots: Sequence[str | Path],
    scalar_pipeline: str,
    instruction_limit: int,
    max_programs_per_family: int | None,
    config_input_prefix: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"stage: {stage_name}",
        "source: llvm-test-suite",
        "source_roots:",
    ]
    lines.extend(f'  - "{Path(root).as_posix()}"' for root in source_roots)
    lines.extend(
        [
            f"instruction_limit: {instruction_limit}",
            f"max_programs_per_family: {max_programs_per_family or ''}",
            f'scalar_pipeline: "{scalar_pipeline}"',
            "programs:",
        ]
    )
    for row in accepted_rows:
        ir_path = f"{config_input_prefix.rstrip('/')}/{Path(row['input_ir']).name}"
        lines.extend(
            [
                f"  - id: {row['program']}",
                f"    family: {row['family']}",
                f'    source: "{Path(row["source_path"]).as_posix()}"',
                f"    ir: {ir_path}",
                f"    num_functions: {row['num_functions']}",
                f"    num_instructions: {row['num_instructions']}",
                f"    num_basic_blocks: {row['num_basic_blocks']}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary(
    rows: Sequence[dict[str, str]],
    accepted_rows: Sequence[dict[str, str]],
    rejected_rows: Sequence[dict[str, str]],
    *,
    max_programs_per_family: int | None = None,
) -> dict[str, Any]:
    family_counts: dict[str, int] = {}
    for row in accepted_rows:
        family = row.get("family", "")
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "CandidateSourceFilesScanned": len(rows),
        "AcceptedPrograms": len(accepted_rows),
        "RejectedPrograms": len(rejected_rows),
        "MaxProgramsPerFamily": max_programs_per_family or 0,
        "MaxAcceptedFamilyCount": max(family_counts.values(), default=0),
        "FamilyLimitViolations": sum(
            1 for row in rejected_rows if row["failure_kind"] == "family_limit_reached"
        ),
        "IRGenerationOk": _count_stage_ok(rows, "ir_generation"),
        "ScalarPipelineOk": sum(
            1 for row in rows if row["scalar_pipeline_ok"] == "True"
        ),
        "LlcObjectOk": sum(1 for row in rows if row["llc_object_ok"] == "True"),
        "ClangObjectOk": sum(1 for row in rows if row["clang_object_ok"] == "True"),
        "SizeParseOk": sum(1 for row in rows if row["size_parse_ok"] == "True"),
    }


def _failure_distribution(rows: Sequence[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = f"{row['failure_stage']}:{row['failure_kind']}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _count_stage_ok(rows: Sequence[dict[str, str]], stage: str) -> int:
    if stage == "ir_generation":
        return sum(1 for row in rows if row["failure_stage"] != "ir_generation")
    return 0


def _program_id(
    source: Path, used_ids: dict[str, int], *, program_prefix: str = "testsuite_misc"
) -> str:
    prefix = program_prefix.strip("_")
    normalized_stem = re.sub(r"[^a-z0-9]+", "_", source.stem.lower()).strip("_")
    base = f"{prefix}_{normalized_stem}" if prefix else normalized_stem
    count = used_ids.get(base, 0)
    used_ids[base] = count + 1
    if count == 0:
        return base
    return f"{base}_{count + 1}"


def _program_family(program: str) -> str:
    return re.sub(r"(?:_\d+|\d+)$", "", program)


def _round_robin_sources(buckets: Sequence[Sequence[Path]]) -> list[Path]:
    sources: list[Path] = []
    max_len = max((len(bucket) for bucket in buckets), default=0)
    for index in range(max_len):
        for bucket in buckets:
            if index < len(bucket):
                sources.append(bucket[index])
    return sources


def _normalize_tool_path(tool_path: ToolPath | OptPath) -> list[str]:
    if isinstance(tool_path, (str, Path)):
        return [str(tool_path)]
    return [str(part) for part in tool_path]


if __name__ == "__main__":
    raise SystemExit(main())
