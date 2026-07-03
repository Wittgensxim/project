"""Build per-program reduced component summaries from retained evidence."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict, deque
from pathlib import Path
from statistics import mean, median
from typing import Any, Mapping, Sequence

from .pass_registry_snapshot import load_expected_passes


COMPONENTS_CSV_NAME = "per_program_components.csv"
SEARCH_SPACE_CSV_NAME = "per_program_search_space_estimate.csv"
SUMMARY_CSV_NAME = "per_benchmark_search_space_summary.csv"
REPORT_NAME = "reduced_components_per_program_report.md"

GRAPH_MODES = ("input_full_matrix", "prefix_adjacent", "objective_sensitive")
SCOPE_WARNINGS = {
    "input_full_matrix": "input_full_matrix_only_not_prefix_safe",
    "prefix_adjacent": "prefix_adjacent_only_not_full_pair_coverage",
    "objective_sensitive": "objective_layer_only_not_hard_prune",
}

DEFAULT_FULL_MATRIX_SOURCES = [
    ("Stanford-8", "data/outputs/cert_summary.csv"),
    ("Misc8", "data/outputs/cert_summary_p8b_misc8_pre.csv"),
    ("Diverse8", "data/outputs/cert_summary_p9_diverse8_pre.csv"),
]
DEFAULT_PREFIX_ATTEMPT_SOURCES = [
    ("Stanford-8", "data/outputs/lazy_validation_p4_e83c409_first.csv"),
    ("Misc8", "data/outputs/lazy_validation_p8b_misc8/attempts.csv"),
    ("Diverse8", "data/outputs/lazy_validation_p9_diverse8/attempts.csv"),
]
DEFAULT_CODEGEN_SOURCES = [
    ("Stanford-8", "data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv"),
    ("Misc8", "data/outputs/codegen_sensitivity_p8b_misc8/p8a_codegen_direction_compare.csv"),
    ("Diverse8", "data/outputs/codegen_sensitivity_p9_diverse8/p8a_codegen_direction_compare.csv"),
]
DEFAULT_ATTRIBUTION_SOURCES = [
    ("Stanford-8", "data/outputs/core_evidence_report/ecpor_attribution_summary.csv"),
    ("Misc8", "data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv"),
]

COMPONENT_FIELDS = [
    "benchmark_set",
    "program",
    "graph_mode",
    "component_id",
    "pass_name",
    "component_size",
    "component_kind",
]
SEARCH_SPACE_FIELDS = [
    "benchmark_set",
    "program",
    "graph_mode",
    "pass_count",
    "edge_count",
    "component_sizes",
    "original_factorial",
    "within_component_factorial_product",
    "reduction_ratio",
    "scope_warning",
]
SUMMARY_FIELDS = [
    "benchmark_set",
    "graph_mode",
    "programs",
    "median_reduction_ratio",
    "mean_reduction_ratio",
    "programs_with_single_component_8",
    "programs_with_multiple_components",
    "median_component_count",
    "max_component_size_median",
]


def build_reduced_components_per_program(
    *,
    pipeline_passes: Sequence[str],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    pass_names = [str(pass_name) for pass_name in pipeline_passes]
    if not pass_names:
        raise ValueError("pipeline_passes must not be empty")

    program_sets = _collect_program_sets(
        full_matrix_rows,
        prefix_attempt_rows,
        codegen_rows,
        attribution_rows,
    )
    programs = sorted(program_sets, key=lambda name: (_benchmark_set_sort_key(program_sets[name]), name))
    edge_sets = {
        "input_full_matrix": _build_not_certified_edges(full_matrix_rows, pass_names),
        "prefix_adjacent": _build_not_certified_edges(prefix_attempt_rows, pass_names),
        "objective_sensitive": _build_objective_edges(
            codegen_rows=codegen_rows,
            attribution_rows=attribution_rows,
            pass_names=pass_names,
        ),
    }

    component_rows: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []
    for program in programs:
        benchmark_set = program_sets[program]
        for mode in GRAPH_MODES:
            edges = edge_sets[mode].get(program, set())
            components = _connected_components(
                pass_names=pass_names,
                edges=edges,
                mode=mode,
            )
            for component in components:
                for pass_name in component["passes"]:
                    component_rows.append(
                        {
                            "benchmark_set": benchmark_set,
                            "program": program,
                            "graph_mode": mode,
                            "component_id": component["component_id"],
                            "pass_name": pass_name,
                            "component_size": component["component_size"],
                            "component_kind": component["component_kind"],
                        }
                    )
            search_rows.append(
                _search_space_row(
                    benchmark_set=benchmark_set,
                    program=program,
                    mode=mode,
                    pass_count=len(pass_names),
                    edge_count=len(edges),
                    components=components,
                )
            )

    summary_rows = _build_benchmark_summary(search_rows)
    summary = _summarize(search_rows)
    return {
        "stage": "P14.5",
        "scope": {
            "summary_only": True,
            "per_program_graph_analysis_only": True,
            "new_experiments": False,
            "new_certificates": False,
            "new_search": False,
            "runtime_benchmarks": False,
            "passspec_behavior_change": False,
            "static_filter_behavior_change": False,
        },
        "per_program_components": _sort_component_rows(component_rows),
        "per_program_search_space": _sort_search_rows(search_rows),
        "per_benchmark_summary": _sort_summary_rows(summary_rows),
        "summary": summary,
        "evidence_boundary": {
            "corpus_union_graph_is_not_program_local_graph": True,
            "input_full_matrix_is_input_state_only": True,
            "prefix_adjacent_has_real_prefix_states_but_not_full_pair_coverage": True,
            "objective_sensitive_is_not_hard_prune_proof": True,
            "no_new_experiments_or_certificates": True,
        },
    }


def write_reduced_components_per_program_outputs(
    *,
    output_dir: str | Path,
    pipeline_passes: Sequence[str],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> dict[str, Path]:
    analysis = build_reduced_components_per_program(
        pipeline_passes=pipeline_passes,
        full_matrix_rows=full_matrix_rows,
        prefix_attempt_rows=prefix_attempt_rows,
        codegen_rows=codegen_rows,
        attribution_rows=attribution_rows,
    )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    components_path = out / COMPONENTS_CSV_NAME
    search_space_path = out / SEARCH_SPACE_CSV_NAME
    summary_path = out / SUMMARY_CSV_NAME
    report_path = out / REPORT_NAME

    _write_csv(components_path, COMPONENT_FIELDS, analysis["per_program_components"])
    _write_csv(search_space_path, SEARCH_SPACE_FIELDS, analysis["per_program_search_space"])
    _write_csv(summary_path, SUMMARY_FIELDS, analysis["per_benchmark_summary"])
    report_path.write_text(render_report(analysis), encoding="utf-8")
    return {
        "components": components_path,
        "search_space": search_space_path,
        "summary": summary_path,
        "report": report_path,
    }


def write_reduced_components_per_program_outputs_from_paths(
    *,
    output_dir: str | Path,
    pipeline_config_path: str | Path,
    full_matrix_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_FULL_MATRIX_SOURCES,
    prefix_attempt_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_PREFIX_ATTEMPT_SOURCES,
    codegen_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_CODEGEN_SOURCES,
    attribution_sources: Sequence[tuple[str | None, str | Path]] = DEFAULT_ATTRIBUTION_SOURCES,
) -> dict[str, Path]:
    return write_reduced_components_per_program_outputs(
        output_dir=output_dir,
        pipeline_passes=load_expected_passes(pipeline_config_path),
        full_matrix_rows=_read_many_labeled_csvs(full_matrix_sources),
        prefix_attempt_rows=_read_many_labeled_csvs(prefix_attempt_sources),
        codegen_rows=_read_many_labeled_csvs(codegen_sources),
        attribution_rows=_read_many_labeled_csvs(attribution_sources),
    )


def render_report(analysis: Mapping[str, Any]) -> str:
    summary = analysis["summary"]
    benchmark_rows = list(analysis["per_benchmark_summary"])
    lines = [
        "# P14.5 Per-Program Reduced Components",
        "",
        "P14.5 reads retained evidence only. It does not run LLVM, create certificates, or start search.",
        "This stage separates the corpus-union graph from the program-local graph.",
        "A component split is a scoped search-space diagnostic, not a hard independence proof.",
        "",
        f"Programs: {summary['Programs']}",
        f"GraphModes: {summary['GraphModes']}",
        f"InputFullMatrixProgramsWithSingleComponent8: {summary['InputFullMatrixProgramsWithSingleComponent8']}",
        f"InputFullMatrixProgramsWithMultipleComponents: {summary['InputFullMatrixProgramsWithMultipleComponents']}",
        f"PrefixAdjacentProgramsWithSingleComponent8: {summary['PrefixAdjacentProgramsWithSingleComponent8']}",
        f"PrefixAdjacentProgramsWithMultipleComponents: {summary['PrefixAdjacentProgramsWithMultipleComponents']}",
        f"ObjectiveSensitiveProgramsWithNonSingletonComponent: {summary['ObjectiveSensitiveProgramsWithNonSingletonComponent']}",
        f"NewExperiments: {summary['NewExperiments']}",
        f"NewCertificates: {summary['NewCertificates']}",
        f"NewSearch: {summary['NewSearch']}",
        "",
        "## Graph Modes",
        "",
        "- input_full_matrix: complete 28-pair coverage per program, input-state only; not prefix-safe.",
        "- prefix_adjacent: real prefix states, but only adjacent swaps from the retained pipeline.",
        "- objective_sensitive: llc/clang both-smaller or attribution hotspots; target-layer signal only.",
        "",
        "## Benchmark Summary",
        "",
        "| benchmark_set | graph_mode | programs | median_reduction_ratio | mean_reduction_ratio | single_component | multiple_components | median_component_count | max_component_size_median |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in benchmark_rows:
        lines.append(
            "| {benchmark_set} | {graph_mode} | {programs} | {median_reduction_ratio} | {mean_reduction_ratio} | {programs_with_single_component_8} | {programs_with_multiple_components} | {median_component_count} | {max_component_size_median} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "P13 reported a corpus-union conservative graph diagnostic. It should not be read as every individual program having no possible component split.",
            "P14 remains a pair-family analysis for the observed objective-sensitive hotspot `instcombine,simplifycfg`; it does not replace this program-local component analysis.",
            "P14.5 is the bridge between those views: it estimates whether each program-local graph splits under three explicit evidence scopes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build P14.5 per-program reduced component summaries."
    )
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument(
        "--out-dir",
        default="data/outputs/reduced_components_per_program",
    )
    parser.add_argument("--full-matrix-csv", action="append")
    parser.add_argument("--prefix-attempt-csv", action="append")
    parser.add_argument("--codegen-csv", action="append")
    parser.add_argument("--attribution-csv", action="append")
    args = parser.parse_args(argv)

    outputs = write_reduced_components_per_program_outputs_from_paths(
        output_dir=args.out_dir,
        pipeline_config_path=args.pipeline,
        full_matrix_sources=_custom_sources(args.full_matrix_csv)
        or DEFAULT_FULL_MATRIX_SOURCES,
        prefix_attempt_sources=_custom_sources(args.prefix_attempt_csv)
        or DEFAULT_PREFIX_ATTEMPT_SOURCES,
        codegen_sources=_custom_sources(args.codegen_csv) or DEFAULT_CODEGEN_SOURCES,
        attribution_sources=_custom_sources(args.attribution_csv)
        or DEFAULT_ATTRIBUTION_SOURCES,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _build_not_certified_edges(
    rows: Sequence[Mapping[str, str]],
    pass_names: Sequence[str],
) -> dict[str, set[tuple[str, str]]]:
    by_program: dict[str, set[tuple[str, str]]] = defaultdict(set)
    pass_set = set(pass_names)
    pass_order = {name: index for index, name in enumerate(pass_names)}
    for row in rows:
        if row.get("label", "") != "not_certified_independent":
            continue
        program = str(row.get("program", "")).strip()
        pair = _row_pair(row, pass_set=pass_set, pass_order=pass_order)
        if program and pair:
            by_program[program].add(pair)
    return by_program


def _build_objective_edges(
    *,
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    pass_names: Sequence[str],
) -> dict[str, set[tuple[str, str]]]:
    by_program: dict[str, set[tuple[str, str]]] = defaultdict(set)
    pass_set = set(pass_names)
    pass_order = {name: index for index, name in enumerate(pass_names)}
    for row in codegen_rows:
        if not _is_depth1_single_swap(row) or not _row_has_both_smaller(row):
            continue
        program = str(row.get("program", "")).strip()
        pair = _row_pair(row, pass_set=pass_set, pass_order=pass_order)
        if program and pair:
            by_program[program].add(pair)
    for row in attribution_rows:
        program = str(row.get("program", "")).strip()
        pair = _row_pair(row, pass_set=pass_set, pass_order=pass_order)
        if program and pair:
            by_program[program].add(pair)
    return by_program


def _connected_components(
    *,
    pass_names: Sequence[str],
    edges: set[tuple[str, str]],
    mode: str,
) -> list[dict[str, Any]]:
    adjacency: dict[str, set[str]] = {name: set() for name in pass_names}
    for left, right in edges:
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)

    order = {name: index for index, name in enumerate(pass_names)}
    visited: set[str] = set()
    components: list[dict[str, Any]] = []
    for pass_name in pass_names:
        if pass_name in visited:
            continue
        queue = deque([pass_name])
        visited.add(pass_name)
        members: list[str] = []
        while queue:
            current = queue.popleft()
            members.append(current)
            for next_pass in sorted(adjacency[current], key=lambda name: order[name]):
                if next_pass not in visited:
                    visited.add(next_pass)
                    queue.append(next_pass)
        members.sort(key=lambda name: order[name])
        size = len(members)
        components.append(
            {
                "graph_mode": mode,
                "component_id": f"{mode}_c{len(components) + 1}",
                "passes": members,
                "component_size": size,
                "component_kind": _component_kind(mode, size),
            }
        )
    return components


def _search_space_row(
    *,
    benchmark_set: str,
    program: str,
    mode: str,
    pass_count: int,
    edge_count: int,
    components: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    sizes = [int(component["component_size"]) for component in components]
    original = math.factorial(pass_count)
    product = 1
    for size in sizes:
        product *= math.factorial(size)
    reduction = 0.0 if original == 0 else (1.0 - (product / original)) * 100.0
    return {
        "benchmark_set": benchmark_set,
        "program": program,
        "graph_mode": mode,
        "pass_count": pass_count,
        "edge_count": edge_count,
        "component_sizes": ";".join(str(size) for size in sizes),
        "original_factorial": original,
        "within_component_factorial_product": product,
        "reduction_ratio": _format_percent(reduction),
        "scope_warning": SCOPE_WARNINGS[mode],
    }


def _build_benchmark_summary(
    search_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in search_rows:
        grouped[(str(row["benchmark_set"]), str(row["graph_mode"]))].append(row)

    result: list[dict[str, Any]] = []
    for (benchmark_set, mode), rows in grouped.items():
        reductions = [_row_reduction_percent(row) for row in rows]
        component_counts = [_component_count(row["component_sizes"]) for row in rows]
        max_sizes = [_max_component_size(row["component_sizes"]) for row in rows]
        pass_counts = {int(row["pass_count"]) for row in rows}
        result.append(
            {
                "benchmark_set": benchmark_set,
                "graph_mode": mode,
                "programs": len(rows),
                "median_reduction_ratio": _format_percent(median(reductions)),
                "mean_reduction_ratio": _format_percent(mean(reductions)),
                "programs_with_single_component_8": sum(
                    1
                    for row in rows
                    if row["component_sizes"] == str(int(row["pass_count"]))
                ),
                "programs_with_multiple_components": sum(
                    1 for row in rows if _component_count(row["component_sizes"]) > 1
                ),
                "median_component_count": _format_decimal(median(component_counts)),
                "max_component_size_median": _format_decimal(median(max_sizes)),
                "pass_counts": ";".join(str(count) for count in sorted(pass_counts)),
            }
        )
    return result


def _summarize(search_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    programs = {str(row["program"]) for row in search_rows}
    rows_by_mode = defaultdict(list)
    for row in search_rows:
        rows_by_mode[str(row["graph_mode"])].append(row)
    return {
        "Programs": len(programs),
        "GraphModes": len(GRAPH_MODES),
        "InputFullMatrixProgramsWithSingleComponent8": _single_component_count(
            rows_by_mode["input_full_matrix"]
        ),
        "InputFullMatrixProgramsWithMultipleComponents": _multiple_component_count(
            rows_by_mode["input_full_matrix"]
        ),
        "PrefixAdjacentProgramsWithSingleComponent8": _single_component_count(
            rows_by_mode["prefix_adjacent"]
        ),
        "PrefixAdjacentProgramsWithMultipleComponents": _multiple_component_count(
            rows_by_mode["prefix_adjacent"]
        ),
        "ObjectiveSensitiveProgramsWithNonSingletonComponent": sum(
            1
            for row in rows_by_mode["objective_sensitive"]
            if _max_component_size(row["component_sizes"]) > 1
        ),
        "NewExperiments": False,
        "NewCertificates": False,
        "NewSearch": False,
    }


def _single_component_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(
        1 for row in rows if row["component_sizes"] == str(int(row["pass_count"]))
    )


def _multiple_component_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _component_count(row["component_sizes"]) > 1)


def _collect_program_sets(
    *groups: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    program_sets: dict[str, str] = {}
    for group in groups:
        for row in group:
            program = str(row.get("program", "")).strip()
            if not program or program in program_sets:
                continue
            program_sets[program] = _benchmark_set(row)
    return program_sets


def _row_pair(
    row: Mapping[str, str],
    *,
    pass_set: set[str],
    pass_order: Mapping[str, int],
) -> tuple[str, str] | None:
    pair_text = str(row.get("pair", "")).strip()
    if pair_text and "," in pair_text:
        left, right = pair_text.split(",", 1)
        return _normalize_pair(left, right, pass_set=pass_set, pass_order=pass_order)
    left = row.get("pass_a") or row.get("pair_a")
    right = row.get("pass_b") or row.get("pair_b")
    if left and right:
        return _normalize_pair(left, right, pass_set=pass_set, pass_order=pass_order)
    candidate_pair = _pair_from_candidate_id(str(row.get("candidate_id", "")))
    if candidate_pair:
        return _normalize_pair(
            candidate_pair[0],
            candidate_pair[1],
            pass_set=pass_set,
            pass_order=pass_order,
        )
    return None


def _normalize_pair(
    left: object,
    right: object,
    *,
    pass_set: set[str],
    pass_order: Mapping[str, int],
) -> tuple[str, str] | None:
    left_name = str(left).strip()
    right_name = str(right).strip()
    if left_name == right_name or left_name not in pass_set or right_name not in pass_set:
        return None
    if pass_order[left_name] <= pass_order[right_name]:
        return (left_name, right_name)
    return (right_name, left_name)


def _pair_from_candidate_id(candidate_id: str) -> tuple[str, str] | None:
    parts = candidate_id.split("__")
    for index, part in enumerate(parts):
        if part.startswith("swap_") and index + 2 < len(parts):
            return (parts[index + 1], parts[index + 2])
    return None


def _is_depth1_single_swap(row: Mapping[str, str]) -> bool:
    source = str(row.get("source", ""))
    if source and source != "single_swap":
        return False
    depth = str(row.get("depth", "")).strip()
    return depth in {"", "1"}


def _row_has_both_smaller(row: Mapping[str, str]) -> bool:
    explicit = str(row.get("both_codegen_smaller", "")).lower()
    if explicit == "true":
        return True
    if row.get("llc_direction") == "smaller" and row.get("clang_direction") == "smaller":
        return True
    llc = _float(row.get("llc_text_delta_pct"))
    clang = _float(row.get("clang_text_delta_pct"))
    return llc is not None and clang is not None and llc < 0 and clang < 0


def _component_kind(mode: str, component_size: int) -> str:
    if component_size == 1:
        return "singleton"
    return f"{mode}_component"


def _component_count(component_sizes: object) -> int:
    text = str(component_sizes)
    if not text:
        return 0
    return len([part for part in text.split(";") if part])


def _max_component_size(component_sizes: object) -> int:
    sizes = [int(part) for part in str(component_sizes).split(";") if part]
    return max(sizes) if sizes else 0


def _parse_percent(value: object) -> float:
    text = str(value).strip().rstrip("%")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _row_reduction_percent(row: Mapping[str, Any]) -> float:
    original = _float(row.get("original_factorial"))
    product = _float(row.get("within_component_factorial_product"))
    if original is None or product is None or original == 0:
        return _parse_percent(row.get("reduction_ratio", "0"))
    return (1.0 - (product / original)) * 100.0


def _format_percent(value: float) -> str:
    return f"{float(value):.4f}%"


def _format_decimal(value: float) -> str:
    return f"{float(value):.4f}"


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _benchmark_set(row: Mapping[str, str]) -> str:
    explicit = str(row.get("benchmark_set", "")).strip()
    if explicit:
        return explicit
    program = str(row.get("program", ""))
    if program.startswith("testsuite_stanford_"):
        return "Stanford-8"
    if program.startswith("testsuite_misc_"):
        return "Misc8"
    if program.startswith("testsuite_diverse_"):
        return "Diverse8"
    return "unknown"


def _benchmark_set_sort_key(name: str) -> tuple[int, str]:
    order = {"Stanford-8": 0, "Misc8": 1, "Diverse8": 2, "unknown": 99}
    return (order.get(name, 50), name)


def _sort_component_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    mode_order = {mode: index for index, mode in enumerate(GRAPH_MODES)}
    return sorted(
        [dict(row) for row in rows],
        key=lambda row: (
            _benchmark_set_sort_key(str(row["benchmark_set"])),
            str(row["program"]),
            mode_order[str(row["graph_mode"])],
            str(row["component_id"]),
            int(row["component_size"]),
            str(row["pass_name"]),
        ),
    )


def _sort_search_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    mode_order = {mode: index for index, mode in enumerate(GRAPH_MODES)}
    return sorted(
        [dict(row) for row in rows],
        key=lambda row: (
            _benchmark_set_sort_key(str(row["benchmark_set"])),
            str(row["program"]),
            mode_order[str(row["graph_mode"])],
        ),
    )


def _sort_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    mode_order = {mode: index for index, mode in enumerate(GRAPH_MODES)}
    return sorted(
        [dict(row) for row in rows],
        key=lambda row: (
            _benchmark_set_sort_key(str(row["benchmark_set"])),
            mode_order[str(row["graph_mode"])],
        ),
    )


def _custom_sources(paths: Sequence[str] | None) -> list[tuple[str | None, str | Path]]:
    if not paths:
        return []
    return [(None, path) for path in paths]


def _read_many_labeled_csvs(
    sources: Sequence[tuple[str | None, str | Path]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for benchmark_set, path in sources:
        for row in _read_csv(path):
            if benchmark_set and not row.get("benchmark_set"):
                row["benchmark_set"] = benchmark_set
            rows.append(row)
    return rows


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


if __name__ == "__main__":
    raise SystemExit(main())
