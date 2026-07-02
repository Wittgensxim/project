"""Build a paper-facing trust report for PassSpec provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .passspec_audit import build_hint_rows, summarize_hint_rows
from .passspec_schema import (
    HintProvenance,
    iter_hint_provenance,
    load_normalized_passspec,
)


def build_trust_report(
    passspec_path: str | Path,
    *,
    audit_manifest_path: str | Path | None = None,
) -> str:
    passspec = load_normalized_passspec(passspec_path)
    rows = build_hint_rows(passspec)
    stats = summarize_hint_rows(rows, pass_count=len(passspec))
    empirical = [
        (pass_name, category, provenance)
        for pass_name, category, provenance in iter_hint_provenance(passspec)
        if provenance.source == "empirical_false_negative_repair"
    ]
    audit_manifest = _load_optional_json(audit_manifest_path)

    lines = [
        "# PassSpec Trust Report",
        "",
        "PassSpec is an auditable metadata layer for static candidate generation.",
        "It records conservative hints about possible pass opportunities and interactions.",
        "These hints can prioritize dynamic AB/BA validation, but they never certify independence.",
        "",
        "## Audit Summary",
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

    if audit_manifest:
        lines.extend(
            [
                "",
                "## Provenance Inputs",
                "",
                f"P10AuditManifestStage: {audit_manifest.get('stage', '')}",
                "P10AuditManifestCommit: "
                f"{audit_manifest.get('result_generated_from_commit', '')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Empirical Repair Hints",
            "",
            "| hint | source | stage | support cases | meaning |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for pass_name, category, provenance in empirical:
        lines.append(
            "| {hint} | {source} | {stage} | {support_count} | {meaning} |".format(
                hint=_escape_table(f"{pass_name}.{category}.{provenance.name}"),
                source=_escape_table(provenance.source),
                stage=_escape_table(provenance.created_in_stage or "unknown"),
                support_count=len(provenance.support),
                meaning=_escape_table(provenance.note or "Empirical repair hint."),
            )
        )

    lines.extend(
        [
            "",
            "The support cases explain why a hint was added; they are not sufficient proof.",
            "",
            "### Support Cases",
            "",
        ]
    )
    if empirical:
        for pass_name, category, provenance in empirical:
            lines.append(f"- `{pass_name}.{category}.{provenance.name}`")
            lines.extend(_support_case_lines(provenance))
    else:
        lines.append("No empirical repair hints are currently recorded.")

    lines.extend(
        [
            "",
            "## Legacy hint limitations",
            "",
            "Legacy hints are intentionally exposed rather than hidden.",
            "They come from MVP-stage manual initialization and currently have no explicit provenance.",
            "Their presence does not affect hard-pruning soundness because static filter decisions never certify independence.",
            "However, they affect candidate recall and dynamic-test cost, so future PassSpecDB work should replace or annotate them using official registry data, source analysis, remarks, or empirical calibration.",
            "",
            "## Behavioral compatibility",
            "",
            "static_filter_behavior_change = false",
            "passspec_behavior_change = false",
            "classify_pair behavior unchanged",
            "provenance metadata is ignored for decisions except for normalized hint names",
            "",
            "## Evolution Roadmap",
            "",
            "PassSpec v2: provenance for empirical repair hints",
            "PassSpec v2.5: provenance for all legacy hints",
            "PassSpec v3: registry snapshot from opt --print-passes",
            "PassSpec v4: source-static extraction of analysis reads / preserved analyses",
            "PassSpec v5: dynamic footprint / remarks / instrumentation",
        ]
    )
    return "\n".join(lines) + "\n"


def write_trust_report(
    *,
    passspec_path: str | Path,
    output_path: str | Path,
    audit_manifest_path: str | Path | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_trust_report(
            passspec_path,
            audit_manifest_path=audit_manifest_path,
        ),
        encoding="utf-8",
    )
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a PassSpec trust report.")
    parser.add_argument("--passspec", default="configs/passspec.yaml")
    parser.add_argument(
        "--audit-manifest",
        default="docs/results/passspec_audit_manifest.json",
    )
    parser.add_argument("--out", default="docs/passspec_trust_report.md")
    args = parser.parse_args(argv)

    output = write_trust_report(
        passspec_path=args.passspec,
        output_path=args.out,
        audit_manifest_path=args.audit_manifest,
    )
    print(output.read_text(encoding="utf-8"), end="")
    return 0


def _support_case_lines(provenance: HintProvenance) -> list[str]:
    if not provenance.support:
        return ["  - support: none recorded"]
    lines: list[str] = []
    for case in provenance.support:
        program = case.get("program", "")
        pair = case.get("pair", "")
        label = case.get("observed_label", "")
        parts = [
            f"program={program}" if program else "",
            f"pair={pair}" if pair else "",
            f"observed_label={label}" if label else "",
        ]
        lines.append("  - " + "; ".join(part for part in parts if part))
    return lines


def _load_optional_json(path: str | Path | None) -> Mapping[str, Any]:
    if path in {None, ""}:
        return {}
    candidate = Path(path)
    if not candidate.exists():
        return {}
    data = json.loads(candidate.read_text(encoding="utf-8"))
    return data if isinstance(data, Mapping) else {}


def _escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
