"""Summary reports for certificate CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence


KNOWN_LABELS = [
    "certified_independent",
    "not_certified_independent",
    "run_failed",
]

KNOWN_FAILURE_KINDS = [
    "opt_failed",
    "timeout",
    "output_missing",
    "opt_failed_output_exists",
    "os_error",
]


def load_summary_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_summary_report(rows: Sequence[dict[str, str]]) -> str:
    total = len(rows)
    reproduced = sum(1 for row in rows if _is_true(row.get("reproduced", "")))
    reproduction_rate = (reproduced / total * 100.0) if total else 0.0
    hard_false = sum(
        1
        for row in rows
        if row.get("label") == "certified_independent"
        and not _is_true(row.get("hard_equal", ""))
    )
    certified_feature_mismatch = sum(
        1
        for row in rows
        if row.get("label") == "certified_independent"
        and _has_nonzero_feature_delta(row.get("feature_delta", ""))
    )
    label_counts = Counter(row.get("label", "") for row in rows)
    failure_counts = Counter[str]()
    no_failure_directions = 0
    certificates_with_any_failure = 0
    for row in rows:
        row_has_failure = False
        for key in ("failure_kind_ab", "failure_kind_ba"):
            value = row.get(key, "").strip()
            if value and value != "none":
                failure_counts[value] += 1
                row_has_failure = True
            else:
                no_failure_directions += 1
        if row_has_failure:
            certificates_with_any_failure += 1
    total_directions = total * 2

    lines = [
        f"Total certificates: {total}",
        f"Reproduced: {reproduced} / {total} = {reproduction_rate:.2f}%",
        f"HardFalseIndependent: {hard_false}",
        f"CertifiedFeatureMismatchCount: {certified_feature_mismatch}",
        "Feature delta is soft evidence only.",
        "Delta convention: feature_delta = features_ba - features_ab",
        "",
        "Label counts:",
    ]
    for label in KNOWN_LABELS:
        lines.append(f"  {label}: {label_counts[label]}")
    for label in sorted(label_counts):
        if label and label not in KNOWN_LABELS:
            lines.append(f"  {label}: {label_counts[label]}")
    if not label_counts:
        lines.append("  none: 0")

    lines.extend(
        [
            "",
            f"Certificates with any failure: {certificates_with_any_failure} / {total}",
            "Failure directions:",
            f"  total_directions: {total_directions}",
            f"  no_failure: {no_failure_directions} / {total_directions}",
        ]
    )
    for failure_kind in KNOWN_FAILURE_KINDS:
        lines.append(f"  {failure_kind}: {failure_counts[failure_kind]}")
    for failure_kind in sorted(failure_counts):
        if failure_kind not in KNOWN_FAILURE_KINDS:
            lines.append(f"  {failure_kind}: {failure_counts[failure_kind]}")

    lines.extend(
        [
            "",
            f"Average elapsed_ab_ms: {_average(rows, 'elapsed_ab_ms'):.3f}",
            f"Average elapsed_ba_ms: {_average(rows, 'elapsed_ba_ms'):.3f}",
            "",
            "Per pair:",
        ]
    )
    for pair, pair_rows in sorted(_group(rows, ("pair_a", "pair_b")).items()):
        certified = sum(1 for row in pair_rows if row.get("label") == "certified_independent")
        lines.append(f"  {','.join(pair)}: {certified}/{len(pair_rows)} certified")

    lines.append("")
    lines.append("Per program:")
    for (program,), program_rows in sorted(_group(rows, ("program",)).items()):
        certified = sum(
            1 for row in program_rows if row.get("label") == "certified_independent"
        )
        lines.append(f"  {program}: {certified}/{len(program_rows)} certified")

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report certificate summary metrics.")
    parser.add_argument("summary_csv", help="Path to cert_summary.csv.")
    parser.add_argument("--out", help="Optional path to write the text report.")
    args = parser.parse_args(argv)

    report = build_summary_report(load_summary_csv(args.summary_csv))
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


def _is_true(value: str) -> bool:
    return value.lower() == "true"


def _average(rows: Sequence[dict[str, str]], key: str) -> float:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        if not raw:
            continue
        values.append(float(raw))
    if not values:
        return 0.0
    return sum(values) / len(values)


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


def _group(
    rows: Sequence[dict[str, str]], keys: tuple[str, ...]
) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    return grouped


if __name__ == "__main__":
    raise SystemExit(main())
