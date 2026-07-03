"""Smoke-test registry-derived function pass candidates for scalar12."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from statistics import mean
from typing import Any, Callable, Mapping, Sequence

import yaml

from .batch_certificates import (
    P8B_MISC8_PROGRAMS,
    STANFORD_8_PROGRAMS,
    load_benchmark_config_programs,
)
from .normalizer import hard_hash
from .runner import OptPath, RunResult, run_opt


SMOKE_CSV_NAME = "pass_expansion_smoke.csv"
REPORT_NAME = "pass_expansion_smoke_report.md"

SMOKE_FIELDS = [
    "pass_name",
    "candidate_source",
    "expected_level",
    "registry_present",
    "already_in_baseline",
    "programs_attempted",
    "run_failed",
    "timeout",
    "verifier_failed",
    "output_missing",
    "changed_ir_count",
    "noop_count",
    "mean_elapsed_ms",
    "selected_for_scalar12",
    "rejection_reason",
]

DEFAULT_CANDIDATE_CONFIG = "configs/pass_expansion_candidates.yaml"
DEFAULT_REGISTRY_SNAPSHOT = "data/outputs/pass_registry_snapshot/pass_registry_snapshot.json"
DEFAULT_PIPELINE = "configs/pipeline_scalar.yaml"
DEFAULT_PASSSPEC = "configs/passspec.yaml"
DEFAULT_OUTPUT_DIR = "data/outputs/pass_expansion_smoke"
DEFAULT_PIPELINE_SCALAR12 = "configs/pipeline_scalar12.yaml"
DEFAULT_PASSSPEC_SCALAR12 = "configs/passspec_scalar12.yaml"
DEFAULT_OPT = "E:/llvm/build/bin/opt.exe"

Runner = Callable[..., RunResult]
Program = tuple[str, str | Path]


@dataclass(frozen=True)
class PassExpansionCandidate:
    name: str
    expected_level: str
    reason: str
    source: str
    manual_note: str = ""


def load_expansion_candidates(path: str | Path) -> list[PassExpansionCandidate]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError(f"candidate config must contain list 'candidates': {path}")
    loaded: list[PassExpansionCandidate] = []
    for item in candidates:
        if not isinstance(item, Mapping):
            raise ValueError(f"candidate entry must be a mapping: {path}")
        loaded.append(
            PassExpansionCandidate(
                name=str(item.get("name", "")).strip(),
                expected_level=str(item.get("expected_level", "")).strip(),
                reason=str(item.get("reason", "")).strip(),
                source=str(item.get("source", "")).strip(),
                manual_note=str(item.get("manual_note", "")).strip(),
            )
        )
    if any(not candidate.name for candidate in loaded):
        raise ValueError(f"candidate entry missing name: {path}")
    return loaded


def load_registry_passes(path: str | Path) -> set[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    names = data.get("all_pass_like_names", [])
    if not isinstance(names, list):
        raise ValueError(f"registry snapshot missing all_pass_like_names list: {path}")
    return {str(name) for name in names}


def load_pipeline_passes(path: str | Path) -> list[str]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    passes = data.get("passes", [])
    if not isinstance(passes, list):
        raise ValueError(f"pipeline config must contain list 'passes': {path}")
    return [str(pass_name) for pass_name in passes]


def default_24_programs() -> list[Program]:
    return [
        *STANFORD_8_PROGRAMS,
        *P8B_MISC8_PROGRAMS,
        *load_benchmark_config_programs("configs/benchmarks_diverse8.yaml"),
    ]


def build_pass_expansion_smoke(
    *,
    candidates: Sequence[PassExpansionCandidate],
    programs: Sequence[Program],
    registry_passes: set[str],
    baseline_passes: Sequence[str],
    max_selected: int = 4,
    runner: Runner = run_opt,
    opt_path: OptPath = DEFAULT_OPT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    timeout_sec: float = 30.0,
) -> dict[str, Any]:
    baseline_set = set(baseline_passes)
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        registry_present = candidate.name in registry_passes
        already_in_baseline = candidate.name in baseline_set
        can_attempt = (
            registry_present
            and not already_in_baseline
            and candidate.expected_level == "function"
        )
        if can_attempt:
            row = _run_candidate_smoke(
                candidate=candidate,
                programs=programs,
                runner=runner,
                opt_path=opt_path,
                output_dir=Path(output_dir),
                timeout_sec=timeout_sec,
            )
        else:
            row = _skipped_row(
                candidate=candidate,
                registry_present=registry_present,
                already_in_baseline=already_in_baseline,
                rejection_reason=_preflight_rejection_reason(
                    registry_present=registry_present,
                    already_in_baseline=already_in_baseline,
                    expected_level=candidate.expected_level,
                ),
            )
        rows.append(row)

    _mark_selected(rows, max_selected=max_selected)
    summary = _summarize(rows, program_count=len(programs), baseline_pass_count=len(baseline_passes))
    return {
        "stage": "P15",
        "scope": {
            "pass_expansion_protocol_only": True,
            "new_experiments": True,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "loop_passes": False,
            "module_passes": False,
            "inline_passes": False,
        },
        "smoke_rows": rows,
        "summary": summary,
    }


def write_pass_expansion_smoke_outputs(
    *,
    output_dir: str | Path,
    candidates: Sequence[PassExpansionCandidate],
    programs: Sequence[Program],
    registry_passes: set[str],
    baseline_passes: Sequence[str],
    max_selected: int = 4,
    runner: Runner = run_opt,
    opt_path: OptPath = DEFAULT_OPT,
    timeout_sec: float = 30.0,
    keep_pass_outputs: bool = False,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pass_output_dir = out / "pass_outputs"
    analysis = build_pass_expansion_smoke(
        candidates=candidates,
        programs=programs,
        registry_passes=registry_passes,
        baseline_passes=baseline_passes,
        max_selected=max_selected,
        runner=runner,
        opt_path=opt_path,
        output_dir=pass_output_dir,
        timeout_sec=timeout_sec,
    )
    smoke_csv = out / SMOKE_CSV_NAME
    report = out / REPORT_NAME
    _write_csv(smoke_csv, SMOKE_FIELDS, analysis["smoke_rows"])
    report.write_text(render_report(analysis), encoding="utf-8")
    if not keep_pass_outputs and pass_output_dir.exists():
        shutil.rmtree(pass_output_dir)
    return {"smoke_csv": smoke_csv, "report": report}


def write_pass_expansion_smoke_outputs_from_paths(
    *,
    output_dir: str | Path,
    candidate_config_path: str | Path = DEFAULT_CANDIDATE_CONFIG,
    registry_snapshot_path: str | Path = DEFAULT_REGISTRY_SNAPSHOT,
    baseline_pipeline_path: str | Path = DEFAULT_PIPELINE,
    benchmark_configs: Sequence[str | Path] = (),
    opt_path: OptPath = DEFAULT_OPT,
    max_selected: int = 4,
    timeout_sec: float = 30.0,
    keep_pass_outputs: bool = False,
) -> dict[str, Path]:
    programs = _load_programs_for_configs(benchmark_configs)
    return write_pass_expansion_smoke_outputs(
        output_dir=output_dir,
        candidates=load_expansion_candidates(candidate_config_path),
        programs=programs,
        registry_passes=load_registry_passes(registry_snapshot_path),
        baseline_passes=load_pipeline_passes(baseline_pipeline_path),
        max_selected=max_selected,
        opt_path=opt_path,
        timeout_sec=timeout_sec,
        keep_pass_outputs=keep_pass_outputs,
    )


def write_scalar12_configs(
    *,
    baseline_pipeline_path: str | Path,
    baseline_passspec_path: str | Path,
    smoke_csv_path: str | Path,
    pipeline_out_path: str | Path,
    passspec_out_path: str | Path,
) -> dict[str, Path]:
    baseline_pipeline = yaml.safe_load(Path(baseline_pipeline_path).read_text(encoding="utf-8")) or {}
    baseline_passspec = yaml.safe_load(Path(baseline_passspec_path).read_text(encoding="utf-8")) or {}
    baseline_passes = [str(pass_name) for pass_name in baseline_pipeline.get("passes", [])]
    selected = [
        row["pass_name"]
        for row in _read_csv(smoke_csv_path)
        if row.get("selected_for_scalar12", "") == "True"
    ]
    scalar12_passes = [*baseline_passes, *selected]
    pipeline_doc = {
        "name": "scalar12_function_scalar",
        "pipeline": f"function({','.join(scalar12_passes)})",
        "passes": scalar12_passes,
        "source_pipeline": Path(baseline_pipeline_path).as_posix(),
        "created_in_stage": "P15",
    }
    passspec_doc = dict(baseline_passspec)
    passspec_entries = dict(passspec_doc.get("passes", {}))
    for pass_name in selected:
        passspec_entries.setdefault(
            pass_name,
            _generated_passspec_entry(pass_name),
        )
    passspec_doc["passes"] = passspec_entries
    passspec_doc["variant"] = "scalar12"
    passspec_doc["source_passspec"] = Path(baseline_passspec_path).as_posix()
    passspec_doc["created_in_stage"] = "P15"

    pipeline_out = Path(pipeline_out_path)
    passspec_out = Path(passspec_out_path)
    pipeline_out.parent.mkdir(parents=True, exist_ok=True)
    passspec_out.parent.mkdir(parents=True, exist_ok=True)
    pipeline_out.write_text(yaml.safe_dump(pipeline_doc, sort_keys=False), encoding="utf-8")
    passspec_out.write_text(yaml.safe_dump(passspec_doc, sort_keys=False), encoding="utf-8")
    return {"pipeline": pipeline_out, "passspec": passspec_out}


def render_report(analysis: Mapping[str, Any]) -> str:
    summary = analysis["summary"]
    rows = analysis["smoke_rows"]
    selected = [row["pass_name"] for row in rows if row["selected_for_scalar12"] == "True"]
    lines = [
        "# P15 Pass Expansion Smoke",
        "",
        "P15 prepares scalar12. It runs single-pass function(...) smoke only.",
        "It does not create certificates, start search, run runtime benchmarks, or introduce loop/module/inline passes.",
        "",
    ]
    for key in [
        "CandidatePasses",
        "RegistryPresentCandidates",
        "Programs",
        "ProgramsAttempted",
        "SelectedNewPasses",
        "RunFailedCandidates",
        "TimeoutCandidates",
        "VerifierFailedCandidates",
        "ChangedIrCandidates",
        "Scalar12PassCount",
        "NewExperiments",
        "NewCertificates",
        "NewSearch",
    ]:
        lines.append(f"{key}: {summary[key]}")
    lines.extend(
        [
            "",
            "SelectedForScalar12: " + ",".join(selected),
            "",
            "## Candidate Summary",
            "",
            "| pass | attempted | failed | changed_ir | noop | selected | rejection |",
            "| --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {pass_name} | {programs_attempted} | {run_failed} | {changed_ir_count} | {noop_count} | {selected_for_scalar12} | {rejection_reason} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            "This is an expansion protocol and smoke gate. P16 may use scalar12 only after this gate selects stable function-level passes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run P15 scalar12 pass expansion smoke.")
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATE_CONFIG)
    parser.add_argument("--registry-snapshot", default=DEFAULT_REGISTRY_SNAPSHOT)
    parser.add_argument("--baseline-pipeline", default=DEFAULT_PIPELINE)
    parser.add_argument("--baseline-passspec", default=DEFAULT_PASSSPEC)
    parser.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pipeline-scalar12-out", default=DEFAULT_PIPELINE_SCALAR12)
    parser.add_argument("--passspec-scalar12-out", default=DEFAULT_PASSSPEC_SCALAR12)
    parser.add_argument("--benchmark-config", action="append", default=[])
    parser.add_argument("--opt", default=DEFAULT_OPT)
    parser.add_argument("--max-selected", type=int, default=4)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument("--keep-pass-outputs", action="store_true")
    args = parser.parse_args(argv)

    outputs = write_pass_expansion_smoke_outputs_from_paths(
        output_dir=args.out_dir,
        candidate_config_path=args.candidates,
        registry_snapshot_path=args.registry_snapshot,
        baseline_pipeline_path=args.baseline_pipeline,
        benchmark_configs=args.benchmark_config,
        opt_path=args.opt,
        max_selected=args.max_selected,
        timeout_sec=args.timeout_sec,
        keep_pass_outputs=args.keep_pass_outputs,
    )
    write_scalar12_configs(
        baseline_pipeline_path=args.baseline_pipeline,
        baseline_passspec_path=args.baseline_passspec,
        smoke_csv_path=outputs["smoke_csv"],
        pipeline_out_path=args.pipeline_scalar12_out,
        passspec_out_path=args.passspec_scalar12_out,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _run_candidate_smoke(
    *,
    candidate: PassExpansionCandidate,
    programs: Sequence[Program],
    runner: Runner,
    opt_path: OptPath,
    output_dir: Path,
    timeout_sec: float,
) -> dict[str, Any]:
    attempts = 0
    run_failed = 0
    timed_out = 0
    verifier_failed = 0
    output_missing = 0
    changed = 0
    noop = 0
    elapsed: list[float] = []
    for program, input_path in programs:
        attempts += 1
        pipeline = f"function({candidate.name})"
        output_path = output_dir / candidate.name / f"{_safe_name(program)}.ll"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        input_hash = hard_hash(input_path)
        result = runner(
            input_path,
            pipeline,
            output_path,
            opt_path=opt_path,
            timeout_sec=timeout_sec,
        )
        elapsed.append(float(getattr(result, "elapsed_ms", 0.0)))
        failure_kind = getattr(result, "failure_kind", None)
        if failure_kind:
            run_failed += 1
            if failure_kind == "timeout" or bool(getattr(result, "timed_out", False)):
                timed_out += 1
            if failure_kind == "output_missing":
                output_missing += 1
            if _looks_like_verifier_failure(getattr(result, "stderr", "")):
                verifier_failed += 1
            continue
        result_hash = getattr(result, "hard_hash", None)
        if result_hash and result_hash != input_hash:
            changed += 1
        else:
            noop += 1
    return {
        "pass_name": candidate.name,
        "candidate_source": candidate.source,
        "expected_level": candidate.expected_level,
        "registry_present": "True",
        "already_in_baseline": "False",
        "programs_attempted": attempts,
        "run_failed": run_failed,
        "timeout": timed_out,
        "verifier_failed": verifier_failed,
        "output_missing": output_missing,
        "changed_ir_count": changed,
        "noop_count": noop,
        "mean_elapsed_ms": _format_float(mean(elapsed) if elapsed else 0.0),
        "selected_for_scalar12": "False",
        "rejection_reason": "",
    }


def _skipped_row(
    *,
    candidate: PassExpansionCandidate,
    registry_present: bool,
    already_in_baseline: bool,
    rejection_reason: str,
) -> dict[str, Any]:
    return {
        "pass_name": candidate.name,
        "candidate_source": candidate.source,
        "expected_level": candidate.expected_level,
        "registry_present": str(registry_present),
        "already_in_baseline": str(already_in_baseline),
        "programs_attempted": 0,
        "run_failed": 0,
        "timeout": 0,
        "verifier_failed": 0,
        "output_missing": 0,
        "changed_ir_count": 0,
        "noop_count": 0,
        "mean_elapsed_ms": "0.0000",
        "selected_for_scalar12": "False",
        "rejection_reason": rejection_reason,
    }


def _mark_selected(rows: list[dict[str, Any]], *, max_selected: int) -> None:
    selected = 0
    for row in rows:
        if selected >= max_selected:
            if _selection_eligible(row) and not row.get("rejection_reason"):
                row["rejection_reason"] = "selection_limit"
            continue
        if _selection_eligible(row):
            row["selected_for_scalar12"] = "True"
            selected += 1
        elif not row.get("rejection_reason"):
            row["rejection_reason"] = _post_smoke_rejection_reason(row)


def _selection_eligible(row: Mapping[str, Any]) -> bool:
    return (
        row.get("registry_present") == "True"
        and row.get("already_in_baseline") == "False"
        and row.get("expected_level") == "function"
        and int(row.get("programs_attempted", 0)) > 0
        and int(row.get("run_failed", 0)) == 0
        and int(row.get("timeout", 0)) == 0
        and int(row.get("verifier_failed", 0)) == 0
        and int(row.get("changed_ir_count", 0)) > 0
    )


def _preflight_rejection_reason(
    *,
    registry_present: bool,
    already_in_baseline: bool,
    expected_level: str,
) -> str:
    if not registry_present:
        return "not_in_registry_snapshot"
    if already_in_baseline:
        return "already_in_baseline"
    if expected_level != "function":
        return "not_function_level"
    return ""


def _post_smoke_rejection_reason(row: Mapping[str, Any]) -> str:
    if int(row.get("run_failed", 0)) > 0:
        return "run_failed"
    if int(row.get("timeout", 0)) > 0:
        return "timeout"
    if int(row.get("verifier_failed", 0)) > 0:
        return "verifier_failed"
    if int(row.get("changed_ir_count", 0)) == 0:
        return "no_changed_ir"
    return "not_selected"


def _summarize(
    rows: Sequence[Mapping[str, Any]],
    *,
    program_count: int,
    baseline_pass_count: int,
) -> dict[str, Any]:
    selected = sum(1 for row in rows if row["selected_for_scalar12"] == "True")
    return {
        "CandidatePasses": len(rows),
        "RegistryPresentCandidates": sum(1 for row in rows if row["registry_present"] == "True"),
        "Programs": program_count,
        "ProgramsAttempted": sum(int(row["programs_attempted"]) for row in rows),
        "SelectedNewPasses": selected,
        "RunFailedCandidates": sum(1 for row in rows if int(row["run_failed"]) > 0),
        "TimeoutCandidates": sum(1 for row in rows if int(row["timeout"]) > 0),
        "VerifierFailedCandidates": sum(1 for row in rows if int(row["verifier_failed"]) > 0),
        "ChangedIrCandidates": sum(1 for row in rows if int(row["changed_ir_count"]) > 0),
        "Scalar12PassCount": baseline_pass_count + selected,
        "NewExperiments": True,
        "NewCertificates": False,
        "NewSearch": False,
    }


def _generated_passspec_entry(pass_name: str) -> dict[str, Any]:
    return {
        "level": "function",
        "requires_any": ["instruction"],
        "may_consume": ["scalar_value", "instruction"],
        "may_produce": [
            {
                "scalar12_candidate_effect": {
                    "source": "generated_registry",
                    "confidence": "low",
                    "created_in_stage": "P15",
                    "support": [{"pass": pass_name, "evidence": "single_pass_smoke"}],
                    "note": "Generated by P15 pass expansion smoke; not an LLVM semantic claim.",
                }
            }
        ],
        "tags": ["scalar12_candidate"],
    }


def _load_programs_for_configs(benchmark_configs: Sequence[str | Path]) -> list[Program]:
    if benchmark_configs:
        programs: list[Program] = []
        for config in benchmark_configs:
            programs.extend(load_benchmark_config_programs(config))
        return programs
    return default_24_programs()


def _looks_like_verifier_failure(stderr: object) -> bool:
    text = str(stderr)
    return "Broken module found" in text or ("LLVM ERROR" in text and "Verifier" in text)


def _format_float(value: float) -> str:
    return f"{float(value):.4f}"


def _safe_name(value: object) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: str | Path,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


if __name__ == "__main__":
    raise SystemExit(main())
