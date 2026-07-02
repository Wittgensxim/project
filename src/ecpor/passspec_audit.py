"""Audit PassSpec hint provenance without running LLVM or experiments."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .passspec_schema import (
    HintProvenance,
    iter_hint_provenance,
    load_normalized_passspec,
)


SUMMARY_CSV_NAME = "passspec_hint_summary.csv"
REPORT_NAME = "passspec_audit_report.md"

AUDIT_FIELDS = [
    "pass",
    "category",
    "hint",
    "source",
    "confidence",
    "explicit_provenance",
    "created_in_stage",
    "support_cases",
    "note",
]


def audit_passspec(
    passspec_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    passspec = load_normalized_passspec(passspec_path)
    rows = build_hint_rows(passspec)
    stats = summarize_hint_rows(rows, pass_count=len(passspec))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary_csv = out / SUMMARY_CSV_NAME
    report_path = out / REPORT_NAME
    write_hint_summary_csv(summary_csv, rows)
    report_path.write_text(build_audit_report(stats), encoding="utf-8")
    return {
        "stats": stats,
        "rows": rows,
        "summary_csv": summary_csv,
        "report": report_path,
    }


def build_hint_rows(passspec: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pass_name, category, provenance in iter_hint_provenance(passspec):
        rows.append(_row_from_provenance(pass_name, category, provenance))
    return rows


def summarize_hint_rows(
    rows: Sequence[Mapping[str, str]],
    *,
    pass_count: int,
) -> dict[str, int]:
    category_counts = Counter(row.get("category", "") for row in rows)
    return {
        "TotalPasses": pass_count,
        "TotalHints": len(rows),
        "RequiresAnyHints": category_counts["requires_any"],
        "MayConsumeHints": category_counts["may_consume"],
        "MayProduceHints": category_counts["may_produce"],
        "ManualHints": sum(
            1 for row in rows if row.get("source") == "manual_domain_knowledge"
        ),
        "EmpiricalRepairHints": sum(
            1
            for row in rows
            if row.get("source") == "empirical_false_negative_repair"
        ),
        "LegacyHintsWithoutExplicitProvenance": sum(
            1 for row in rows if row.get("explicit_provenance") != "True"
        ),
        "UnknownConfidenceHints": sum(
            1 for row in rows if row.get("confidence") == "unknown"
        ),
        "HintsWithSupportCases": sum(
            1 for row in rows if row.get("support_cases", "") not in {"", "0"}
        ),
    }


def write_hint_summary_csv(path: str | Path, rows: Sequence[Mapping[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_audit_report(stats: Mapping[str, int]) -> str:
    lines = [
        "# PassSpec Provenance Audit",
        "",
        "This is a metadata/provenance audit only.",
        "It does not run LLVM, generate certificates, or change static filter behavior.",
        "",
    ]
    for key in [
        "TotalPasses",
        "TotalHints",
        "RequiresAnyHints",
        "MayConsumeHints",
        "MayProduceHints",
        "ManualHints",
        "EmpiricalRepairHints",
        "LegacyHintsWithoutExplicitProvenance",
        "UnknownConfidenceHints",
        "HintsWithSupportCases",
    ]:
        lines.append(f"{key}: {stats.get(key, 0)}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PassSpec hint provenance.")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument("--out-dir", default="data/outputs/passspec_audit")
    args = parser.parse_args(argv)

    result = audit_passspec(args.passspec, args.out_dir)
    print(Path(result["report"]).read_text(encoding="utf-8"), end="")
    return 0


def _row_from_provenance(
    pass_name: str,
    category: str,
    provenance: HintProvenance,
) -> dict[str, str]:
    return {
        "pass": pass_name,
        "category": category,
        "hint": provenance.name,
        "source": provenance.source,
        "confidence": provenance.confidence,
        "explicit_provenance": str(provenance.explicit_provenance),
        "created_in_stage": provenance.created_in_stage,
        "support_cases": str(len(provenance.support)),
        "note": provenance.note,
    }


if __name__ == "__main__":
    raise SystemExit(main())
