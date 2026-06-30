"""Human-readable feature-delta reports for not-certified certificates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Sequence

from .summary_report import load_summary_csv


DIFF_SUMMARY_FIELDS = [
    "program",
    "pair_a",
    "pair_b",
    "input_state_hash",
    "pipeline_ab",
    "pipeline_ba",
    "hash_ab",
    "hash_ba",
    "nonzero_feature_delta",
    "elapsed_ab_ms",
    "elapsed_ba_ms",
    "cert_id",
]


def build_not_certified_diff_report(rows: Sequence[dict[str, str]]) -> str:
    report_rows = _not_certified_rows(rows)
    lines = [
        "# Not-Certified Feature Delta Report",
        "",
        "Feature delta is soft evidence only.",
        "It is not used for hard pruning.",
        "Delta convention: feature_delta = features_ba - features_ab",
        "",
        f"Not-certified certificates: {len(report_rows)}",
    ]

    if not report_rows:
        lines.append("")
        lines.append("No not-certified certificates found.")
        return "\n".join(lines) + "\n"

    for row in report_rows:
        features_ab = _parse_json_object(row.get("features_ab", ""))
        features_ba = _parse_json_object(row.get("features_ba", ""))
        feature_delta = _parse_json_object(row.get("feature_delta", ""))
        nonzero = _nonzero_delta_items(feature_delta)

        lines.extend(
            [
                "",
                f"## {row.get('program', '')} :: {row.get('pair_a', '')} -> {row.get('pair_b', '')}",
                "",
                f"Label: {row.get('label', '')}",
                "Reason: hard hash differs",
                "Delta convention: BA - AB",
                "",
                f"- input_state_hash: `{row.get('input_state_hash', '')}`",
                f"- pipeline_ab: `{row.get('pipeline_ab', '')}`",
                f"- pipeline_ba: `{row.get('pipeline_ba', '')}`",
                f"- hash_ab: `{row.get('hash_ab', '')}`",
                f"- hash_ba: `{row.get('hash_ba', '')}`",
                f"- elapsed_ab_ms: {row.get('elapsed_ab_ms', '')}",
                f"- elapsed_ba_ms: {row.get('elapsed_ba_ms', '')}",
                f"- cert_id: `{row.get('cert_id', '')}`",
                "",
            ]
        )
        if nonzero:
            lines.extend(
                [
                    "| feature | AB | BA | delta |",
                    "|---|---:|---:|---:|",
                ]
            )
            for key, delta_value in nonzero:
                lines.append(
                    "| {feature} | {ab} | {ba} | {delta} |".format(
                        feature=key,
                        ab=_format_value(features_ab.get(key, "")),
                        ba=_format_value(features_ba.get(key, "")),
                        delta=_format_delta(delta_value),
                    )
                )
        else:
            lines.append("No nonzero feature delta.")

    return "\n".join(lines) + "\n"


def build_not_certified_diff_summary(
    rows: Sequence[dict[str, str]]
) -> list[dict[str, str]]:
    summary_rows: list[dict[str, str]] = []
    for row in _not_certified_rows(rows):
        feature_delta = _parse_json_object(row.get("feature_delta", ""))
        summary_rows.append(
            {
                "program": row.get("program", ""),
                "pair_a": row.get("pair_a", ""),
                "pair_b": row.get("pair_b", ""),
                "input_state_hash": row.get("input_state_hash", ""),
                "pipeline_ab": row.get("pipeline_ab", ""),
                "pipeline_ba": row.get("pipeline_ba", ""),
                "hash_ab": row.get("hash_ab", ""),
                "hash_ba": row.get("hash_ba", ""),
                "nonzero_feature_delta": _format_nonzero_delta_summary(feature_delta),
                "elapsed_ab_ms": row.get("elapsed_ab_ms", ""),
                "elapsed_ba_ms": row.get("elapsed_ba_ms", ""),
                "cert_id": row.get("cert_id", ""),
            }
        )
    return summary_rows


def write_diff_summary_csv(path: str | Path, rows: Sequence[dict[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DIFF_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write not-certified feature-delta reports."
    )
    parser.add_argument("summary_csv", help="Path to cert_summary.csv.")
    parser.add_argument(
        "--out-md",
        default="data/outputs/not_certified_diff_report.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--out-csv",
        default="data/outputs/not_certified_diff_summary.csv",
        help="CSV summary output path.",
    )
    args = parser.parse_args(argv)

    rows = load_summary_csv(args.summary_csv)
    markdown = build_not_certified_diff_report(rows)
    summary_rows = build_not_certified_diff_summary(rows)

    output_md = Path(args.out_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding="utf-8")
    write_diff_summary_csv(args.out_csv, summary_rows)
    print(markdown, end="")
    return 0


def _not_certified_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("label") == "not_certified_independent"]


def _parse_json_object(raw_json: str) -> dict[str, Any]:
    if not raw_json.strip():
        return {}
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _nonzero_delta_items(delta: dict[str, Any]) -> list[tuple[str, Any]]:
    return [(key, delta[key]) for key in sorted(delta) if _is_nonzero_delta(delta[key])]


def _format_nonzero_delta_summary(delta: dict[str, Any]) -> str:
    return ";".join(
        f"{key}={_format_delta(value)}" for key, value in _nonzero_delta_items(delta)
    )


def _is_nonzero_delta(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return value is not None


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _format_delta(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)) and value > 0:
        return f"+{value:g}"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
