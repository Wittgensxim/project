"""Filesystem-backed lookup for state-indexed pair certificates."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .cert import PairCertificate, load_certificate


class CertificateDB:
    def __init__(self, cert_dir: str | Path):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def save(self, cert: PairCertificate) -> Path:
        path = self.cert_dir / f"{cert.cert_id}.json"
        cert.save(path)
        return path

    def lookup(
        self,
        pass_a: str,
        pass_b: str,
        state_hash: str,
        *,
        env_id: str,
        execution_model: str,
        normalizer_version: str,
        nesting: str,
        region_id: str,
        extra_flags: Sequence[str] = (),
    ) -> PairCertificate | None:
        pair_key = _unordered_pair_key(pass_a, pass_b)
        flags = list(extra_flags)
        for path in sorted(self.cert_dir.rglob("*.json")):
            cert = load_certificate(path)
            if _unordered_pair_key(cert.pass_a, cert.pass_b) != pair_key:
                continue
            if cert.input_state_hash != state_hash:
                continue
            if cert.env_id != env_id:
                continue
            if cert.execution_model != execution_model:
                continue
            if cert.normalizer_version != normalizer_version:
                continue
            if cert.nesting != nesting:
                continue
            if cert.region_id != region_id:
                continue
            if cert.extra_flags != flags:
                continue
            return cert
        return None


def _unordered_pair_key(pass_a: str, pass_b: str) -> tuple[str, str]:
    return tuple(sorted((pass_a, pass_b)))
