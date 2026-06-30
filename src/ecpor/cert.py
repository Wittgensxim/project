"""State-indexed adjacent-swap certificates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PairCertificate:
    cert_id: str
    label: str
    reason: str
    pass_a: str
    pass_b: str
    input_state_hash: str
    env_id: str
    execution_model: str
    llvm_version: str
    command_ab: list[str]
    command_ba: list[str]
    input_ir_path: str
    output_ab: str
    output_ba: str
    hash_ab: str | None
    hash_ba: str | None
    hard_equal: bool
    normalizer_version: str
    verifier_ab: bool
    verifier_ba: bool
    exit_code_ab: int
    exit_code_ba: int
    nesting: str
    pipeline_ab: str
    pipeline_ba: str
    extra_flags: list[str]
    pass_a_instance: str
    pass_b_instance: str
    region_id: str
    ecpor_git_commit: str
    ecpor_git_dirty: bool | None
    scope: str = "state-specific"

    @property
    def claim(self) -> str:
        return self.label

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["claim"] = self.claim
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def save(self, path: str | Path) -> None:
        cert_path = Path(path)
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        cert_path.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PairCertificate":
        clean = dict(data)
        clean.pop("claim", None)
        clean.setdefault("input_ir_path", "unknown")
        clean.setdefault("nesting", "function")
        clean.setdefault("pipeline_ab", "unknown")
        clean.setdefault("pipeline_ba", "unknown")
        clean.setdefault("extra_flags", [])
        clean.setdefault("pass_a_instance", f"{clean.get('pass_a', 'pass-a')}@unknown")
        clean.setdefault("pass_b_instance", f"{clean.get('pass_b', 'pass-b')}@unknown")
        clean.setdefault("region_id", "function_scalar_mvp")
        clean.setdefault("ecpor_git_commit", "unknown")
        clean.setdefault("ecpor_git_dirty", None)
        return cls(**clean)


def load_certificate(path: str | Path) -> PairCertificate:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return PairCertificate.from_dict(data)


def make_cert_id(
    *,
    pass_a: str,
    pass_b: str,
    input_state_hash: str,
    env_id: str,
    execution_model: str,
    normalizer_version: str,
    nesting: str,
    pipeline_ab: str,
    pipeline_ba: str,
    extra_flags: list[str] | tuple[str, ...],
    pass_a_instance: str | None = None,
    pass_b_instance: str | None = None,
    region_id: str = "function_scalar_mvp",
) -> str:
    payload = {
        "pass_a": pass_a,
        "pass_b": pass_b,
        "pass_a_instance": pass_a_instance or f"{pass_a}@unknown",
        "pass_b_instance": pass_b_instance or f"{pass_b}@unknown",
        "region_id": region_id,
        "input_state_hash": input_state_hash,
        "env_id": env_id,
        "execution_model": execution_model,
        "normalizer_version": normalizer_version,
        "nesting": nesting,
        "pipeline_ab": pipeline_ab,
        "pipeline_ba": pipeline_ba,
        "extra_flags": list(extra_flags),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
