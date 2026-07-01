"""On-demand adjacent-swap validation with certificate reuse."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .cert import PairCertificate
from .certificate_db import CertificateDB
from .environment import DEFAULT_EXECUTION_MODEL
from .normalizer import NORMALIZER_VERSION, hard_hash
from .pair_test import reproduce_certificate, test_adjacent_swap
from .runner import OptPath


@dataclass(frozen=True)
class LazyValidationResult:
    pass_a: str
    pass_b: str
    state_hash: str
    static_decision: str
    action: str
    label: str
    reason: str
    certificate: PairCertificate | None
    cache_hit: bool
    dynamic_test: bool
    reproduced: bool | None


def validate_adjacent_swap(
    state_ll: str | Path,
    pass_a: str,
    pass_b: str,
    *,
    static_decision: str,
    cert_db: CertificateDB,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    llvm_version: str,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    region_id: str = "function_scalar_mvp",
    timeout_sec: float = 30.0,
) -> LazyValidationResult:
    state_path = Path(state_ll)
    state_hash = hard_hash(state_path)
    cached = cert_db.lookup(
        pass_a,
        pass_b,
        state_hash,
        env_id=env_id,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
        nesting=nesting,
        region_id=region_id,
        extra_flags=extra_flags,
    )
    if cached is not None:
        return LazyValidationResult(
            pass_a=pass_a,
            pass_b=pass_b,
            state_hash=state_hash,
            static_decision=static_decision,
            action="cache_hit",
            label=cached.label,
            reason="certificate cache hit",
            certificate=cached,
            cache_hit=True,
            dynamic_test=False,
            reproduced=None,
        )

    if static_decision != "candidate":
        return LazyValidationResult(
            pass_a=pass_a,
            pass_b=pass_b,
            state_hash=state_hash,
            static_decision=static_decision,
            action="skipped_low_priority",
            label="skipped_low_priority",
            reason="static decision is not candidate; default order frozen",
            certificate=None,
            cache_hit=False,
            dynamic_test=False,
            reproduced=None,
        )

    output_root = Path(output_dir)
    cert = test_adjacent_swap(
        state_path,
        pass_a,
        pass_b,
        opt_path=opt_path,
        output_dir=output_root / "pair_tests",
        env_id=env_id,
        execution_model=execution_model,
        llvm_version=llvm_version,
        normalizer_version=normalizer_version,
        nesting=nesting,
        extra_flags=extra_flags,
        region_id=region_id,
        timeout_sec=timeout_sec,
    )
    cert_path = cert_db.save(cert)
    reproduction = reproduce_certificate(
        cert_path,
        opt_path=opt_path,
        output_dir=output_root / "repro",
        timeout_sec=timeout_sec,
    )
    return LazyValidationResult(
        pass_a=pass_a,
        pass_b=pass_b,
        state_hash=state_hash,
        static_decision=static_decision,
        action="dynamic_test",
        label=cert.label,
        reason=cert.reason,
        certificate=cert,
        cache_hit=False,
        dynamic_test=True,
        reproduced=reproduction.reproduced,
    )
