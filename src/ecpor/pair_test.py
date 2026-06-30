"""Lazy adjacent-swap pair testing."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from .cert import PairCertificate, load_certificate, make_cert_id
from .environment import DEFAULT_EXECUTION_MODEL, git_info
from .normalizer import NORMALIZER_VERSION, hard_hash
from .runner import OptPath, RunResult, run_opt


__test__ = False


def test_adjacent_swap(
    state_ll: str | Path,
    pass_a: str,
    pass_b: str,
    *,
    opt_path: OptPath = "opt",
    output_dir: str | Path = "data/outputs",
    env_id: str = "unknown-env",
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    llvm_version: str = "unknown",
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] | None = None,
    pass_a_instance: str | None = None,
    pass_b_instance: str | None = None,
    region_id: str = "function_scalar_mvp",
    ecpor_git_commit: str | None = None,
    ecpor_git_dirty: bool | None = None,
    timeout_sec: float = 30.0,
) -> PairCertificate:
    state_path = Path(state_ll)
    out_dir = Path(output_dir)
    flags = list(extra_flags or [])

    pipeline_ab = _pipeline(nesting, [pass_a, pass_b])
    pipeline_ba = _pipeline(nesting, [pass_b, pass_a])
    input_state_hash = hard_hash(state_path)
    pass_a_instance = pass_a_instance or f"{pass_a}@unknown"
    pass_b_instance = pass_b_instance or f"{pass_b}@unknown"
    cert_id = make_cert_id(
        pass_a=pass_a,
        pass_b=pass_b,
        pass_a_instance=pass_a_instance,
        pass_b_instance=pass_b_instance,
        region_id=region_id,
        input_state_hash=input_state_hash,
        env_id=env_id,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
        nesting=nesting,
        pipeline_ab=pipeline_ab,
        pipeline_ba=pipeline_ba,
        extra_flags=flags,
    )
    cert_dir = out_dir / cert_id
    cert_dir.mkdir(parents=True, exist_ok=True)
    output_ab = cert_dir / "ab.ll"
    output_ba = cert_dir / "ba.ll"
    (cert_dir / "input_hash.txt").write_text(input_state_hash + "\n", encoding="utf-8")

    result_ab = run_opt(
        state_path,
        pipeline_ab,
        output_ab,
        opt_path=opt_path,
        extra_flags=flags,
        timeout_sec=timeout_sec,
    )
    result_ba = run_opt(
        state_path,
        pipeline_ba,
        output_ba,
        opt_path=opt_path,
        extra_flags=flags,
        timeout_sec=timeout_sec,
    )
    _write_run_artifacts(cert_dir, "ab", result_ab)
    _write_run_artifacts(cert_dir, "ba", result_ba)

    hard_equal = (
        result_ab.hard_hash is not None
        and result_ba.hard_hash is not None
        and result_ab.hard_hash == result_ba.hard_hash
    )
    label, reason = _classify(result_ab, result_ba, hard_equal)
    repo_git = git_info(Path(__file__).resolve().parents[2])
    ecpor_git_commit = ecpor_git_commit or repo_git.commit
    if ecpor_git_dirty is None:
        ecpor_git_dirty = repo_git.dirty

    cert = PairCertificate(
        cert_id=cert_id,
        label=label,
        reason=reason,
        pass_a=pass_a,
        pass_b=pass_b,
        input_state_hash=input_state_hash,
        env_id=env_id,
        execution_model=execution_model,
        llvm_version=llvm_version,
        command_ab=result_ab.command,
        command_ba=result_ba.command,
        input_ir_path=str(state_path),
        output_ab=str(output_ab),
        output_ba=str(output_ba),
        hash_ab=result_ab.hard_hash,
        hash_ba=result_ba.hard_hash,
        hard_equal=hard_equal,
        normalizer_version=normalizer_version,
        verifier_ab=result_ab.verifier_ok,
        verifier_ba=result_ba.verifier_ok,
        exit_code_ab=result_ab.exit_code,
        exit_code_ba=result_ba.exit_code,
        nesting=nesting,
        pipeline_ab=pipeline_ab,
        pipeline_ba=pipeline_ba,
        extra_flags=flags,
        pass_a_instance=pass_a_instance,
        pass_b_instance=pass_b_instance,
        region_id=region_id,
        ecpor_git_commit=ecpor_git_commit,
        ecpor_git_dirty=ecpor_git_dirty,
    )
    cert.save(cert_dir / "cert.json")
    return cert


@dataclass(frozen=True)
class CertificateReproduction:
    original_cert_id: str
    reproduced_cert_id: str
    reproduced: bool
    original_label: str
    reproduced_label: str
    original_hash_ab: str | None
    reproduced_hash_ab: str | None
    original_hash_ba: str | None
    reproduced_hash_ba: str | None
    reason: str


def reproduce_certificate(
    cert_path: str | Path,
    *,
    opt_path: OptPath | None = None,
    output_dir: str | Path | None = None,
    timeout_sec: float = 30.0,
) -> CertificateReproduction:
    original = load_certificate(cert_path)
    replay_opt_path = opt_path or _infer_opt_path(original)
    replay_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else Path(original.output_ab).parent.parent / f"{original.cert_id}_repro"
    )
    reproduced_cert = test_adjacent_swap(
        original.input_ir_path,
        original.pass_a,
        original.pass_b,
        opt_path=replay_opt_path,
        output_dir=replay_output_dir,
        env_id=original.env_id,
        execution_model=original.execution_model,
        llvm_version=original.llvm_version,
        normalizer_version=original.normalizer_version,
        nesting=original.nesting,
        extra_flags=original.extra_flags,
        pass_a_instance=original.pass_a_instance,
        pass_b_instance=original.pass_b_instance,
        region_id=original.region_id,
        ecpor_git_commit=original.ecpor_git_commit,
        ecpor_git_dirty=original.ecpor_git_dirty,
        timeout_sec=timeout_sec,
    )
    reproduced = (
        original.label == reproduced_cert.label
        and original.hard_equal == reproduced_cert.hard_equal
        and original.hash_ab == reproduced_cert.hash_ab
        and original.hash_ba == reproduced_cert.hash_ba
    )
    reason = "label and hashes match" if reproduced else "label or hashes differ"
    return CertificateReproduction(
        original_cert_id=original.cert_id,
        reproduced_cert_id=reproduced_cert.cert_id,
        reproduced=reproduced,
        original_label=original.label,
        reproduced_label=reproduced_cert.label,
        original_hash_ab=original.hash_ab,
        reproduced_hash_ab=reproduced_cert.hash_ab,
        original_hash_ba=original.hash_ba,
        reproduced_hash_ba=reproduced_cert.hash_ba,
        reason=reason,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an adjacent-swap pair test.")
    parser.add_argument("--state", required=True, help="Input LLVM IR state.")
    parser.add_argument("--A", dest="pass_a", required=True, help="First pass.")
    parser.add_argument("--B", dest="pass_b", required=True, help="Second pass.")
    parser.add_argument("--opt", default="opt", help="opt executable or command prefix.")
    parser.add_argument(
        "--opt-arg",
        action="append",
        default=[],
        help="Additional opt command-prefix argument, used for wrappers such as python fake_opt.py.",
    )
    parser.add_argument("--out", default="data/outputs/pair_tests", help="Output root.")
    parser.add_argument("--cert", help="Certificate JSON path.")
    parser.add_argument("--env-id", default="unknown-env")
    parser.add_argument("--llvm-version", default="unknown")
    parser.add_argument("--execution-model", default=DEFAULT_EXECUTION_MODEL)
    parser.add_argument("--normalizer-version", default=NORMALIZER_VERSION)
    parser.add_argument("--nesting", default="function")
    parser.add_argument("--extra-flag", action="append", default=[])
    parser.add_argument("--pass-a-instance")
    parser.add_argument("--pass-b-instance")
    parser.add_argument("--region-id", default="function_scalar_mvp")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    args = parser.parse_args(argv)

    opt_path: OptPath
    if args.opt_arg:
        opt_path = [args.opt, *args.opt_arg]
    else:
        opt_path = args.opt

    cert = test_adjacent_swap(
        args.state,
        args.pass_a,
        args.pass_b,
        opt_path=opt_path,
        output_dir=args.out,
        env_id=args.env_id,
        execution_model=args.execution_model,
        llvm_version=args.llvm_version,
        normalizer_version=args.normalizer_version,
        nesting=args.nesting,
        extra_flags=args.extra_flag,
        pass_a_instance=args.pass_a_instance,
        pass_b_instance=args.pass_b_instance,
        region_id=args.region_id,
        timeout_sec=args.timeout_sec,
    )
    if args.cert:
        cert.save(args.cert)

    print(cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba)
    return 0


def _classify(result_ab, result_ba, hard_equal: bool) -> tuple[str, str]:
    if result_ab.exit_code != 0 or result_ba.exit_code != 0:
        failed = []
        if result_ab.exit_code != 0:
            failed.append(f"AB failed with exit code {result_ab.exit_code}")
        if result_ba.exit_code != 0:
            failed.append(f"BA failed with exit code {result_ba.exit_code}")
        stderr = " ".join(
            text.strip() for text in [result_ab.stderr, result_ba.stderr] if text.strip()
        )
        reason = "; ".join(failed)
        if stderr:
            reason = f"{reason}: {stderr}"
        return "run_failed", reason
    if not result_ab.verifier_ok or not result_ba.verifier_ok:
        return "verifier_failed", "at least one direction failed verifier"
    if hard_equal:
        return "certified_independent", "hard hash equal"
    return "not_certified_independent", "hard hash differs"


def _pipeline(nesting: str, passes: Sequence[str]) -> str:
    joined = ",".join(passes)
    if nesting:
        return f"{nesting}({joined})"
    return joined


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _write_run_artifacts(cert_dir: Path, stem: str, result: RunResult) -> None:
    (cert_dir / f"stdout_{stem}.txt").write_text(result.stdout, encoding="utf-8")
    (cert_dir / f"stderr_{stem}.txt").write_text(result.stderr, encoding="utf-8")


def _infer_opt_path(cert: PairCertificate) -> OptPath:
    command = cert.command_ab
    try:
        input_index = command.index(cert.input_ir_path)
    except ValueError:
        return command[0]
    prefix = command[:input_index]
    if len(prefix) == 1:
        return prefix[0]
    return prefix


if __name__ == "__main__":
    raise SystemExit(main())
