"""PassSpec v1/v2 normalization with hint provenance metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

import yaml


HINT_CATEGORIES = ("requires_any", "may_consume", "may_produce")

ALLOWED_SOURCES = {
    "manual_domain_knowledge",
    "empirical_false_negative_repair",
    "llvm_doc_hint",
    "source_static_hint",
    "generated_registry",
    "unknown_legacy",
}

ALLOWED_CONFIDENCES = {"unknown", "low", "medium", "high"}


@dataclass(frozen=True)
class HintProvenance:
    name: str
    source: str = "unknown_legacy"
    confidence: str = "unknown"
    support: tuple[dict[str, str], ...] = ()
    note: str = ""
    created_in_stage: str = ""
    explicit_provenance: bool = False


NormalizedPassSpec = dict[str, dict[str, Any]]


def load_passspec_document(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"passspec must contain a mapping: {path}")
    return data


def load_normalized_passspec(path: str | Path) -> NormalizedPassSpec:
    return normalize_passspec(load_passspec_document(path))


def normalize_passspec(raw: Mapping[str, Any]) -> NormalizedPassSpec:
    passes = raw.get("passes", {})
    if not isinstance(passes, Mapping):
        raise ValueError("passspec must contain a mapping 'passes'")

    normalized: NormalizedPassSpec = {}
    for raw_name, raw_info in passes.items():
        pass_name = str(raw_name)
        if not isinstance(raw_info, Mapping):
            raise ValueError(f"passspec entry must be a mapping: {pass_name}")
        entry: dict[str, Any] = {
            "level": str(raw_info.get("level", "")),
            "tags": _string_list(raw_info.get("tags", []), context=f"{pass_name}.tags"),
        }
        provenance: dict[str, dict[str, HintProvenance]] = {}
        for category in HINT_CATEGORIES:
            names, records = normalize_hint_collection(
                raw_info.get(category, []),
                pass_name=pass_name,
                category=category,
            )
            entry[category] = names
            provenance[category] = records
        entry["_hint_provenance"] = provenance
        normalized[pass_name] = entry
    return normalized


def normalize_hint_collection(
    value: object,
    *,
    pass_name: str = "<pass>",
    category: str = "<hints>",
) -> tuple[list[str], dict[str, HintProvenance]]:
    if value is None:
        return [], {}

    names: list[str] = []
    provenance: dict[str, HintProvenance] = {}
    if isinstance(value, list):
        for item in value:
            hint_name, metadata = _hint_item_to_metadata(
                item,
                context=f"{pass_name}.{category}",
            )
            _append_hint(
                hint_name,
                metadata,
                names=names,
                provenance=provenance,
                pass_name=pass_name,
                category=category,
            )
        return names, provenance

    if isinstance(value, Mapping):
        for raw_hint, raw_metadata in value.items():
            hint_name = str(raw_hint)
            metadata = _metadata_mapping(
                raw_metadata,
                context=f"{pass_name}.{category}.{hint_name}",
            )
            _append_hint(
                hint_name,
                metadata,
                names=names,
                provenance=provenance,
                pass_name=pass_name,
                category=category,
            )
        return names, provenance

    raise ValueError(
        f"{pass_name}.{category} must be a list or mapping, got {type(value).__name__}"
    )


def hint_names(value: object) -> list[str]:
    names, _records = normalize_hint_collection(value)
    return names


def iter_hint_provenance(
    passspec: Mapping[str, Mapping[str, Any]],
) -> Iterator[tuple[str, str, HintProvenance]]:
    for pass_name, pass_info in passspec.items():
        provenance = pass_info.get("_hint_provenance", {})
        if not isinstance(provenance, Mapping):
            continue
        for category in HINT_CATEGORIES:
            category_records = provenance.get(category, {})
            if not isinstance(category_records, Mapping):
                continue
            for hint_name in pass_info.get(category, []):
                record = category_records.get(hint_name)
                if isinstance(record, HintProvenance):
                    yield str(pass_name), category, record


def _append_hint(
    hint_name: str,
    metadata: Mapping[str, Any],
    *,
    names: list[str],
    provenance: dict[str, HintProvenance],
    pass_name: str,
    category: str,
) -> None:
    if hint_name in provenance:
        raise ValueError(f"duplicate hint {pass_name}.{category}.{hint_name}")
    names.append(hint_name)
    provenance[hint_name] = _provenance_from_metadata(
        hint_name,
        metadata,
        context=f"{pass_name}.{category}.{hint_name}",
    )


def _hint_item_to_metadata(item: object, *, context: str) -> tuple[str, Mapping[str, Any]]:
    if isinstance(item, Mapping):
        if len(item) != 1:
            raise ValueError(f"{context} metadata list item must have exactly one hint key")
        raw_hint, raw_metadata = next(iter(item.items()))
        return str(raw_hint), _metadata_mapping(
            raw_metadata,
            context=f"{context}.{raw_hint}",
        )
    return str(item), {}


def _metadata_mapping(value: object, *, context: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} metadata must be a mapping")
    return value


def _provenance_from_metadata(
    hint_name: str,
    metadata: Mapping[str, Any],
    *,
    context: str,
) -> HintProvenance:
    explicit = _has_explicit_provenance(metadata)
    source = str(metadata.get("source", "unknown_legacy"))
    confidence = str(metadata.get("confidence", "unknown")).lower()
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"{context}.source has unsupported value: {source}")
    if confidence not in ALLOWED_CONFIDENCES:
        raise ValueError(f"{context}.confidence has unsupported value: {confidence}")
    return HintProvenance(
        name=hint_name,
        source=source,
        confidence=confidence,
        support=_support_tuple(metadata.get("support", []), context=context),
        note=str(metadata.get("note", "")),
        created_in_stage=str(metadata.get("created_in_stage", "")),
        explicit_provenance=explicit,
    )


def _has_explicit_provenance(metadata: Mapping[str, Any]) -> bool:
    return any(
        key in metadata
        for key in ("source", "confidence", "support", "note", "created_in_stage")
    )


def _support_tuple(value: object, *, context: str) -> tuple[dict[str, str], ...]:
    if value is None or value == "":
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{context}.support must be a list")
    support: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.support[{index}] must be a mapping")
        support.append({str(key): str(raw_value) for key, raw_value in item.items()})
    return tuple(support)


def _string_list(value: object, *, context: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{context} must be a list")
    return [str(item) for item in value]
