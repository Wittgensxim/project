"""Cross-check PassSpec and pipeline pass names against a registry snapshot."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Sequence

from .pass_registry_snapshot import load_expected_passes
from .passspec_schema import load_normalized_passspec


CSV_NAME = "passspec_registry_check.csv"
REPORT_NAME = "passspec_registry_check_report.md"
CSV_FIELDS = [
    "pass_name",
    "in_passspec",
    "in_pipeline",
    "in_registry",
    "registry_presence",
    "level_in_passspec",
    "status",
    "notes",
]


def build_registry_check(
    *,
    passspec_path: str | Path,
    pipeline_config_path: str | Path,
    registry_snapshot_path: str | Path,
) -> dict[str, Any]:
    passspec = load_normalized_passspec(passspec_path)
    pipeline_passes = load_expected_passes(pipeline_config_path)
    snapshot = _load_snapshot(registry_snapshot_path)
    rows = build_check_rows(
        passspec=passspec,
        pipeline_passes=pipeline_passes,
        registry_snapshot=snapshot,
    )
    return {
        "summary": summarize_rows(
            rows,
            passspec_passes=passspec.keys(),
            pipeline_passes=pipeline_passes,
            registry_snapshot=snapshot,
        ),
        "rows": rows,
    }


def build_check_rows(
    *,
    passspec: dict[str, dict[str, Any]],
    pipeline_passes: Sequence[str],
    registry_snapshot: dict[str, Any],
) -> list[dict[str, str]]:
    passspec_names = set(passspec)
    pipeline_names = set(pipeline_passes)
    registry_expected = set(_string_list(registry_snapshot.get("expected_passes", [])))
    registry_names = set(_string_list(registry_snapshot.get("all_pass_like_names", [])))
    registry_presence = _registry_presence_map(registry_snapshot, registry_names)
    all_names = sorted(passspec_names | pipeline_names | registry_expected)

    rows: list[dict[str, str]] = []
    for pass_name in all_names:
        in_passspec = pass_name in passspec_names
        in_pipeline = pass_name in pipeline_names
        in_registry = bool(registry_presence.get(pass_name, False))
        status = _status(
            in_passspec=in_passspec,
            in_pipeline=in_pipeline,
            in_registry=in_registry,
            in_registry_expected=pass_name in registry_expected,
        )
        notes = _notes(
            in_passspec=in_passspec,
            in_pipeline=in_pipeline,
            in_registry=in_registry,
            in_registry_expected=pass_name in registry_expected,
        )
        rows.append(
            {
                "pass_name": pass_name,
                "in_passspec": str(in_passspec),
                "in_pipeline": str(in_pipeline),
                "in_registry": str(in_registry),
                "registry_presence": "present" if in_registry else "missing",
                "level_in_passspec": str(passspec.get(pass_name, {}).get("level", "")),
                "status": status,
                "notes": "; ".join(notes),
            }
        )
    return rows


def summarize_rows(
    rows: Sequence[dict[str, str]],
    *,
    passspec_passes: Sequence[str],
    pipeline_passes: Sequence[str],
    registry_snapshot: dict[str, Any],
) -> dict[str, Any]:
    registry_expected = _string_list(registry_snapshot.get("expected_passes", []))
    missing_expected = _string_list(
        registry_snapshot.get("missing_expected_passes", [])
    )
    missing_passspec_in_registry = [
        row
        for row in rows
        if row["in_passspec"] == "True" and row["in_registry"] != "True"
    ]
    pipeline_missing_passspec = [
        row
        for row in rows
        if row["in_pipeline"] == "True" and row["in_passspec"] != "True"
    ]
    registry_expected_missing_passspec = [
        row
        for row in rows
        if row["pass_name"] in registry_expected and row["in_passspec"] != "True"
    ]
    failed = (
        missing_passspec_in_registry
        or pipeline_missing_passspec
        or registry_expected_missing_passspec
        or missing_expected
    )
    return {
        "PassSpecPasses": len(set(passspec_passes)),
        "PipelinePasses": len(set(pipeline_passes)),
        "RegistryExpectedPasses": len(set(registry_expected)),
        "MissingPassSpecPassesInRegistry": len(missing_passspec_in_registry),
        "PipelinePassesMissingInPassSpec": len(pipeline_missing_passspec),
        "RegistryExpectedPassesMissingInPassSpec": len(
            registry_expected_missing_passspec
        ),
        "RegistryMissingExpectedPasses": len(set(missing_expected)),
        "Status": "fail" if failed else "pass",
    }


def write_registry_check_outputs(
    *,
    passspec_path: str | Path,
    pipeline_config_path: str | Path,
    registry_snapshot_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = build_registry_check(
        passspec_path=passspec_path,
        pipeline_config_path=pipeline_config_path,
        registry_snapshot_path=registry_snapshot_path,
    )
    csv_path = out / CSV_NAME
    report_path = out / REPORT_NAME
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(result["rows"])
    report_path.write_text(
        render_report(result["summary"], result["rows"]),
        encoding="utf-8",
    )
    return {"csv": csv_path, "report": report_path}


def render_report(
    summary: dict[str, Any],
    rows: Sequence[dict[str, str]],
) -> str:
    lines = [
        "# PassSpec Registry Cross-Check",
        "",
        "This report checks whether PassSpec and the MVP pipeline refer to passes",
        "that are present in the current LLVM opt --print-passes snapshot.",
        "",
        "It does not infer pass semantics.",
        "It does not change static filter behavior.",
        "It does not certify independence.",
        "",
    ]
    for key in [
        "PassSpecPasses",
        "PipelinePasses",
        "RegistryExpectedPasses",
        "MissingPassSpecPassesInRegistry",
        "PipelinePassesMissingInPassSpec",
        "RegistryExpectedPassesMissingInPassSpec",
        "RegistryMissingExpectedPasses",
        "Status",
    ]:
        lines.append(f"{key}: {summary[key]}")
    lines.extend(
        [
            "",
            "## Pass Rows",
            "",
            "| pass | passspec | pipeline | registry | status |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| `{pass_name}` | {in_passspec} | {in_pipeline} | {in_registry} | {status} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Scope Limits",
            "",
            "metadata_only: True",
            "registry_cross_check_only: True",
            "static_filter_behavior_change: False",
            "passspec_behavior_change: False",
            "new_experiments: False",
            "new_certificates: False",
            "new_search: False",
            "runtime_benchmarks: False",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-check PassSpec registry names.")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--pipeline", default="configs/pipeline_scalar.yaml")
    parser.add_argument(
        "--registry-snapshot",
        default="data/outputs/pass_registry_snapshot/pass_registry_snapshot.json",
    )
    parser.add_argument("--out-dir", default="data/outputs/passspec_registry_check")
    args = parser.parse_args(argv)

    outputs = write_registry_check_outputs(
        passspec_path=args.passspec,
        pipeline_config_path=args.pipeline,
        registry_snapshot_path=args.registry_snapshot,
        output_dir=args.out_dir,
    )
    print(outputs["report"].read_text(encoding="utf-8"), end="")
    return 0


def _status(
    *,
    in_passspec: bool,
    in_pipeline: bool,
    in_registry: bool,
    in_registry_expected: bool,
) -> str:
    if in_passspec and not in_registry:
        return "missing_in_registry"
    if in_pipeline and not in_passspec:
        return "pipeline_pass_missing_in_passspec"
    if in_registry_expected and not in_passspec:
        return "missing_in_passspec"
    return "ok"


def _notes(
    *,
    in_passspec: bool,
    in_pipeline: bool,
    in_registry: bool,
    in_registry_expected: bool,
) -> list[str]:
    notes: list[str] = []
    if in_passspec and not in_registry:
        notes.append("PassSpec pass is not present in registry snapshot")
    if in_pipeline and not in_passspec:
        notes.append("pipeline pass is missing from PassSpec")
    if in_registry_expected and not in_passspec:
        notes.append("registry expected pass is missing from PassSpec")
    return notes


def _load_snapshot(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"registry snapshot must contain a JSON object: {path}")
    return data


def _registry_presence_map(
    snapshot: dict[str, Any],
    registry_names: set[str],
) -> dict[str, bool]:
    presence: dict[str, bool] = {name: True for name in registry_names}
    raw_presence = snapshot.get("expected_pass_presence", {})
    if isinstance(raw_presence, dict):
        for pass_name, value in raw_presence.items():
            presence[str(pass_name)] = bool(value)
    for pass_name in _string_list(snapshot.get("missing_expected_passes", [])):
        presence[pass_name] = False
    return presence


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


if __name__ == "__main__":
    raise SystemExit(main())
