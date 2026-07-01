"""High-recall static pair filtering for candidate generation."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Sequence

import yaml

from .batch_certificates import DEFAULT_STANFORD_PROGRAMS
from .feature_scan import scan_ir_file
from .summary_report import load_summary_csv


DECISION_FIELDS = [
    "pair_a",
    "pair_b",
    "decision",
    "reason",
    "level_a",
    "level_b",
    "shared_tags",
    "producer_consumer",
    "program_feature_gate",
]

DecisionRow = dict[str, str]
PassSpec = dict[str, dict[str, Any]]
Program = tuple[str, str | Path]


def load_pipeline_config(path: str | Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    passes = data.get("passes", [])
    if not isinstance(passes, list) or not all(isinstance(item, str) for item in passes):
        raise ValueError(f"pipeline config must contain a string list 'passes': {path}")
    return data


def load_passspec(path: str | Path) -> PassSpec:
    data = _load_yaml_mapping(path)
    passes = data.get("passes", {})
    if not isinstance(passes, dict):
        raise ValueError(f"passspec must contain a mapping 'passes': {path}")
    return {
        str(name): _normalize_pass_info(name, info)
        for name, info in passes.items()
    }


def enumerate_unordered_pairs(passes: Sequence[str]) -> list[tuple[str, str]]:
    return [(left, right) for left, right in combinations(passes, 2)]


def classify_pair(
    pair_a: str,
    pair_b: str,
    passspec: PassSpec,
    *,
    program_features: dict[str, Any],
    distance: int,
    window_size: int,
) -> DecisionRow:
    spec_a = passspec[pair_a]
    spec_b = passspec[pair_b]
    level_a = str(spec_a["level"])
    level_b = str(spec_b["level"])
    shared_tags = sorted(set(spec_a["tags"]) & set(spec_b["tags"]))
    producer_consumer = _producer_consumer_reason(pair_a, pair_b, spec_a, spec_b)
    gate_a = _feature_gate(pair_a, spec_a, program_features)
    gate_b = _feature_gate(pair_b, spec_b, program_features)

    base = {
        "pair_a": pair_a,
        "pair_b": pair_b,
        "level_a": level_a,
        "level_b": level_b,
        "shared_tags": ",".join(shared_tags),
        "producer_consumer": producer_consumer,
        "program_feature_gate": _format_feature_gate(gate_a, gate_b),
    }

    if level_a != level_b:
        return {
            **base,
            "decision": "frozen",
            "reason": f"level_mismatch:{level_a}!={level_b}",
        }
    if not gate_a[0] or not gate_b[0]:
        return {
            **base,
            "decision": "low_priority",
            "reason": "feature_gate_missing",
        }
    if producer_consumer:
        return {**base, "decision": "candidate", "reason": "producer_consumer"}
    if shared_tags and distance <= window_size:
        return {**base, "decision": "candidate", "reason": "shared_tags_in_window"}
    return {**base, "decision": "low_priority", "reason": "no_static_hint"}


def build_static_filter_decisions(
    passes: Sequence[str],
    passspec: PassSpec,
    *,
    program_features: dict[str, Any],
    window_size: int,
) -> list[DecisionRow]:
    index = {name: position for position, name in enumerate(passes)}
    rows: list[DecisionRow] = []
    for pair_a, pair_b in enumerate_unordered_pairs(passes):
        rows.append(
            classify_pair(
                pair_a,
                pair_b,
                passspec,
                program_features=program_features,
                distance=abs(index[pair_b] - index[pair_a]),
                window_size=window_size,
            )
        )
    return rows


def aggregate_program_features(programs: Sequence[Program]) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    for _name, path in programs:
        features = scan_ir_file(path)
        for key, value in features.items():
            if isinstance(value, bool):
                aggregate[key] = bool(aggregate.get(key, False)) or value
            elif isinstance(value, (int, float)):
                aggregate[key] = int(aggregate.get(key, 0)) + int(value)
            else:
                aggregate[key] = value
    return aggregate


def evaluate_static_filter(
    decisions: Sequence[DecisionRow],
    observed_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    decision_by_pair = {
        _pair_key(row["pair_a"], row["pair_b"]): row["decision"] for row in decisions
    }
    label_counts = Counter(row.get("label", "") for row in observed_rows)
    candidate_pairs = sum(1 for row in decisions if row["decision"] == "candidate")
    low_priority_pairs = sum(1 for row in decisions if row["decision"] == "low_priority")
    frozen_pairs = sum(1 for row in decisions if row["decision"] == "frozen")
    observed_interacting = [
        row for row in observed_rows if row.get("label") == "not_certified_independent"
    ]
    candidate_observed_interacting = [
        row
        for row in observed_interacting
        if decision_by_pair.get(_pair_key(row.get("pair_a", ""), row.get("pair_b", "")))
        == "candidate"
    ]
    false_negative_rows = [
        row
        for row in observed_interacting
        if decision_by_pair.get(_pair_key(row.get("pair_a", ""), row.get("pair_b", "")))
        != "candidate"
    ]
    all_pairs = len(decisions)
    observed_count = len(observed_interacting)
    recall = (
        len(candidate_observed_interacting) / observed_count
        if observed_count
        else 1.0
    )
    reduction = 1.0 - (candidate_pairs / all_pairs) if all_pairs else 0.0

    return {
        "all_pairs": all_pairs,
        "candidate_pairs": candidate_pairs,
        "low_priority_pairs": low_priority_pairs,
        "frozen_pairs": frozen_pairs,
        "observed_total": len(observed_rows),
        "observed_certified_independent": label_counts["certified_independent"],
        "observed_interacting": observed_count,
        "observed_run_failed": label_counts["run_failed"],
        "reproduced": sum(
            1 for row in observed_rows if row.get("reproduced", "").lower() == "true"
        ),
        "hard_false_independent": sum(
            1
            for row in observed_rows
            if row.get("label") == "certified_independent"
            and row.get("hard_equal") != "True"
        ),
        "certified_feature_mismatch": sum(
            1
            for row in observed_rows
            if row.get("label") == "certified_independent"
            and _has_nonzero_feature_delta(row.get("feature_delta", ""))
        ),
        "static_candidate_recall": recall,
        "static_false_negative_observed": len(false_negative_rows),
        "static_candidate_reduction": reduction,
        "false_negative_rows": false_negative_rows,
    }


def build_static_filter_report(
    *,
    pipeline_name: str,
    pass_count: int,
    program_count: int,
    decisions: Sequence[DecisionRow],
    observed_rows: Sequence[dict[str, str]],
    metrics: dict[str, Any],
) -> str:
    decision_counts = Counter(row["decision"] for row in decisions)
    lines = [
        "# Static Filter Report",
        "",
        "Static filter is candidate generation only.",
        "It is not used for hard pruning and does not produce certificates.",
        "",
        f"Pipeline: {pipeline_name}",
        f"Pass count: {pass_count}",
        f"All unordered pairs: {metrics['all_pairs']}",
        f"Programs: {program_count}",
        f"Full matrix certificates: {metrics['observed_total']}",
        "",
        "Static decisions:",
        f"  candidate: {decision_counts['candidate']}",
        f"  low_priority: {decision_counts['low_priority']}",
        f"  frozen: {decision_counts['frozen']}",
        "",
        "Observed matrix:",
        f"  certified_independent: {metrics['observed_certified_independent']}",
        f"  not_certified_independent: {metrics['observed_interacting']}",
        f"  run_failed: {metrics['observed_run_failed']}",
        f"  reproduced: {metrics['reproduced']} / {metrics['observed_total']}",
        f"  HardFalseIndependent: {metrics['hard_false_independent']}",
        f"  CertifiedFeatureMismatchCount: {metrics['certified_feature_mismatch']}",
        "",
        "Static filter quality:",
        f"  StaticCandidateRecall: {_format_percent(metrics['static_candidate_recall'])}",
        f"  StaticFalseNegativeObserved: {metrics['static_false_negative_observed']}",
        f"  StaticCandidateReduction: {_format_percent(metrics['static_candidate_reduction'])}",
    ]

    false_negatives = metrics["false_negative_rows"]
    if false_negatives:
        lines.extend(["", "False negatives:"])
        for row in false_negatives:
            lines.append(
                "  {pair_a},{pair_b} on {program}".format(
                    pair_a=row.get("pair_a", ""),
                    pair_b=row.get("pair_b", ""),
                    program=row.get("program", ""),
                )
            )
    else:
        lines.extend(["", "False negatives: none"])

    return "\n".join(lines) + "\n"


def write_decisions_csv(path: str | Path, rows: Sequence[DecisionRow]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate high-recall static pair-filter decisions."
    )
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--features-json")
    parser.add_argument(
        "--program-preset",
        choices=["stanford-3"],
        help="Scan a built-in program set to build aggregate program features.",
    )
    parser.add_argument("--observed-summary")
    parser.add_argument("--out-csv", default="data/outputs/static_filter_decisions.csv")
    parser.add_argument("--out-report", default="data/outputs/static_filter_report.md")
    parser.add_argument("--window-size", type=int, default=7)
    args = parser.parse_args(argv)

    pipeline = load_pipeline_config(args.pipeline)
    passspec = load_passspec(args.passspec)
    program_features, program_count = _load_program_features_for_args(args)
    passes = list(pipeline["passes"])
    decisions = build_static_filter_decisions(
        passes,
        passspec,
        program_features=program_features,
        window_size=args.window_size,
    )
    write_decisions_csv(args.out_csv, decisions)

    observed_rows = (
        load_summary_csv(args.observed_summary) if args.observed_summary else []
    )
    metrics = evaluate_static_filter(decisions, observed_rows)
    report = build_static_filter_report(
        pipeline_name=str(pipeline.get("name", "")),
        pass_count=len(passes),
        program_count=program_count,
        decisions=decisions,
        observed_rows=observed_rows,
        metrics=metrics,
    )
    output_report = Path(args.out_report)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


def _load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data


def _normalize_pass_info(name: object, info: object) -> dict[str, Any]:
    if not isinstance(info, dict):
        raise ValueError(f"passspec entry must be a mapping: {name}")
    return {
        "level": str(info.get("level", "")),
        "requires_any": _string_list(info.get("requires_any", [])),
        "may_consume": _string_list(info.get("may_consume", [])),
        "may_produce": _string_list(info.get("may_produce", [])),
        "tags": _string_list(info.get("tags", [])),
    }


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"expected list, got {type(value).__name__}")
    return [str(item) for item in value]


def _producer_consumer_reason(
    pair_a: str,
    pair_b: str,
    spec_a: dict[str, Any],
    spec_b: dict[str, Any],
) -> str:
    parts: list[str] = []
    forward = sorted(set(spec_a["may_produce"]) & set(spec_b["may_consume"]))
    backward = sorted(set(spec_b["may_produce"]) & set(spec_a["may_consume"]))
    if forward:
        parts.append(f"{pair_a}->{pair_b}:{','.join(forward)}")
    if backward:
        parts.append(f"{pair_b}->{pair_a}:{','.join(backward)}")
    return ";".join(parts)


def _feature_gate(
    pass_name: str, pass_info: dict[str, Any], program_features: dict[str, Any]
) -> tuple[bool, str]:
    requirements = pass_info["requires_any"]
    if not requirements:
        return True, f"{pass_name}:none"
    satisfied = [
        requirement
        for requirement in requirements
        if _feature_token_satisfied(requirement, program_features)
    ]
    if satisfied:
        return True, f"{pass_name}:{'|'.join(satisfied)}"
    return False, f"{pass_name}:missing({'|'.join(requirements)})"


def _format_feature_gate(
    gate_a: tuple[bool, str], gate_b: tuple[bool, str]
) -> str:
    status = "satisfied" if gate_a[0] and gate_b[0] else "missing"
    return f"{status};{gate_a[1]};{gate_b[1]}"


def _feature_token_satisfied(token: str, features: dict[str, Any]) -> bool:
    if token == "instruction":
        return _numeric_feature(features, "num_instructions") > 0
    if token in features:
        return bool(features[token])
    if token.startswith("has_"):
        return bool(features.get(token, False))
    if token == "load_store":
        return bool(features.get("has_load_store", False))
    if token in {"alloca", "branch", "phi", "call"}:
        return bool(features.get(f"has_{token}", False)) or _numeric_feature(
            features, f"num_{token}"
        ) > 0
    return _numeric_feature(features, f"num_{token}") > 0


def _numeric_feature(features: dict[str, Any], key: str) -> float:
    value = features.get(key, 0)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _pair_key(pair_a: str, pair_b: str) -> tuple[str, str]:
    return tuple(sorted((pair_a, pair_b)))


def _has_nonzero_feature_delta(raw_delta: str) -> bool:
    if not raw_delta.strip():
        return False
    try:
        delta = json.loads(raw_delta)
    except json.JSONDecodeError:
        return True
    if not isinstance(delta, dict):
        return bool(delta)
    return any(_is_nonzero_delta(value) for value in delta.values())


def _is_nonzero_delta(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return value is not None


def _format_percent(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def _load_program_features_for_args(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.features_json:
        return (
            json.loads(Path(args.features_json).read_text(encoding="utf-8")),
            0,
        )
    if args.program_preset == "stanford-3":
        return aggregate_program_features(DEFAULT_STANFORD_PROGRAMS), len(
            DEFAULT_STANFORD_PROGRAMS
        )
    return {}, 0


if __name__ == "__main__":
    raise SystemExit(main())
