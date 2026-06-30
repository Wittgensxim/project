# ECPOR 进度记录：安装 pytest，并继续 P1/P2 证书闭环

## 2026-07-01：安装 pytest，并继续 P1/P2 证书闭环

### 当前目标

安装 `pytest`，并继续下一步 P1/P2：实现 state-indexed adjacent-swap certificate 的第一版闭环。

### 已完成内容

- [x] 检查当前 `python` 环境。
- [x] 发现 `C:\msys64\ucrt64\bin\python.exe` 没有 `pip` 模块。
- [x] 确认 `D:\Miniconda\python.exe` 可用，版本为 Python 3.13.12。
- [x] 在 `D:\Miniconda` 环境中安装 `pytest 9.1.1`。
- [x] 编写 RED 测试：
  - `tests/test_cert.py`
  - `tests/test_pair_test.py`
- [x] 确认 RED 阶段失败原因正确：
  - `ModuleNotFoundError: No module named 'ecpor.cert'`
  - `ModuleNotFoundError: No module named 'ecpor.pair_test'`
- [x] 新增 `src/ecpor/cert.py`。
- [x] 新增 `src/ecpor/pair_test.py`。
- [x] 更新 `src/ecpor/__init__.py`，导出 `cert` 和 `pair_test`。
- [x] 更新 `README.md`，测试命令改为 `D:\Miniconda\python.exe -m pytest -q`。
- [x] 生成第一份真实 LLVM adjacent-swap certificate：
  - `data/certs/testsuite_stanford_bubblesort__instcombine__dce.json`

### 验证结果

- 安装 pytest：

```powershell
D:\Miniconda\python.exe -m pip install pytest
```

结果：安装成功，`pytest 9.1.1` 和 `iniconfig 2.3.0` 已安装到 `D:\Miniconda` 环境。

- RED 测试：

```powershell
D:\Miniconda\python.exe -m pytest tests/test_cert.py tests/test_pair_test.py -q
```

结果：5 个测试按预期失败，失败原因是 `ecpor.cert` 和 `ecpor.pair_test` 尚不存在。

- GREEN 测试：

```powershell
D:\Miniconda\python.exe -m pytest tests/test_cert.py tests/test_pair_test.py -q
```

结果：`5 passed in 0.28s`

- 全量 pytest：

```powershell
D:\Miniconda\python.exe -m pytest -q
```

结果：`14 passed in 0.33s`

- 真实 LLVM pair test：

```powershell
D:\Miniconda\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.pair_test import test_adjacent_swap; cert=test_adjacent_swap('data/inputs/testsuite_stanford_bubblesort.ll','instcombine','dce',opt_path='E:/llvm/build/bin/opt.exe',output_dir='data/outputs/pair_tests',env_id='b87a818a5b1ba7b3913d179fd1bee2d02ece540ff5552aacce4ef5a77fec6c84',llvm_version='23.0.0git'); cert.save('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json'); print(cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba)"
```

结果：

```text
certified_independent True 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56
```

### 风险与备注

- 当前默认 `python` 仍是 `C:\msys64\ucrt64\bin\python.exe`，它没有 `pip`，所以后续 pytest 命令应显式使用 `D:\Miniconda\python.exe`。
- `pair_test.py` 是生产模块，但文件名符合 pytest 的收集模式；已在模块中设置 `__test__ = False`，防止 pytest 把生产函数 `test_adjacent_swap` 当测试函数收集。
- 当前证书标签是第一版最小分类：
  - `certified_independent`
  - `not_certified_independent`
  - `run_failed`
  - `verifier_failed`
- 当前证书 ID 绑定 `pass_a/pass_b/input_state_hash/env_id/execution_model/normalizer_version`，满足状态索引约束的第一版要求。

### 下一步

1. 给 `pair_test.py` 增加 CLI：
   - `python -m ecpor.pair_test --state ... --A ... --B ...`
2. 添加 certificate reproduction 测试：
   - 读取已有 JSON certificate，复跑 AB/BA，确认 label 和 hash 可复现。
3. 增加 `feature_scan.py` 第一版，为后续 soft evidence 和报告准备输入特征。
4. 生成至少 3 个 test-suite 输入 × 3 个 pair 的证书小表。

---
## 本次代码快照：P1/P2 证书闭环

### `src/ecpor/cert.py`

```python
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


def make_cert_id(
    *,
    pass_a: str,
    pass_b: str,
    input_state_hash: str,
    env_id: str,
    execution_model: str,
    normalizer_version: str,
) -> str:
    payload = {
        "pass_a": pass_a,
        "pass_b": pass_b,
        "input_state_hash": input_state_hash,
        "env_id": env_id,
        "execution_model": execution_model,
        "normalizer_version": normalizer_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
```

### `src/ecpor/pair_test.py`

```python
"""Lazy adjacent-swap pair testing."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

from .cert import PairCertificate, make_cert_id
from .environment import DEFAULT_EXECUTION_MODEL
from .normalizer import NORMALIZER_VERSION, hard_hash
from .runner import OptPath, run_opt


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
    timeout_sec: float = 30.0,
) -> PairCertificate:
    state_path = Path(state_ll)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = _safe_name(state_path.stem)
    safe_a = _safe_name(pass_a)
    safe_b = _safe_name(pass_b)
    output_ab = out_dir / f"{stem}__{safe_a}__{safe_b}.ll"
    output_ba = out_dir / f"{stem}__{safe_b}__{safe_a}.ll"

    pipeline_ab = _pipeline(nesting, [pass_a, pass_b])
    pipeline_ba = _pipeline(nesting, [pass_b, pass_a])

    result_ab = run_opt(
        state_path,
        pipeline_ab,
        output_ab,
        opt_path=opt_path,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    result_ba = run_opt(
        state_path,
        pipeline_ba,
        output_ba,
        opt_path=opt_path,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )

    hard_equal = (
        result_ab.hard_hash is not None
        and result_ba.hard_hash is not None
        and result_ab.hard_hash == result_ba.hard_hash
    )
    label, reason = _classify(result_ab, result_ba, hard_equal)
    input_state_hash = hard_hash(state_path)
    cert_id = make_cert_id(
        pass_a=pass_a,
        pass_b=pass_b,
        input_state_hash=input_state_hash,
        env_id=env_id,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
    )

    return PairCertificate(
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
    )


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
```

### `tests/test_cert.py`

```python
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CertificateTests(unittest.TestCase):
    def test_pair_certificate_round_trips_to_json(self):
        from ecpor.cert import PairCertificate

        cert = PairCertificate(
            cert_id="cert-1",
            label="certified_independent",
            reason="hard hash equal",
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="input-hash",
            env_id="env-1",
            execution_model="materialized_ir_fresh_opt",
            llvm_version="23.0.0git",
            command_ab=["opt", "input.ll", "-passes=function(instcombine,dce)"],
            command_ba=["opt", "input.ll", "-passes=function(dce,instcombine)"],
            output_ab="ab.ll",
            output_ba="ba.ll",
            hash_ab="same",
            hash_ba="same",
            hard_equal=True,
            normalizer_version="hard-normalizer-v1",
            verifier_ab=True,
            verifier_ba=True,
            exit_code_ab=0,
            exit_code_ba=0,
        )

        data = json.loads(cert.to_json())

        self.assertEqual(data["label"], "certified_independent")
        self.assertEqual(data["claim"], "certified_independent")
        self.assertEqual(data["pass_a"], "instcombine")
        self.assertEqual(data["pass_b"], "dce")
        self.assertTrue(data["hard_equal"])
        self.assertEqual(data["scope"], "state-specific")

    def test_make_cert_id_is_stable_and_state_sensitive(self):
        from ecpor.cert import make_cert_id

        base = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-1",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
        )
        again = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-1",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
        )
        changed = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-2",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
        )

        self.assertEqual(base, again)
        self.assertNotEqual(base, changed)


if __name__ == "__main__":
    unittest.main()
```

### `tests/test_pair_test.py`

```python
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PairTesterTests(unittest.TestCase):
    def test_adjacent_swap_equal_outputs_is_certified_independent(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="same")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "certified_independent")
            self.assertTrue(cert.hard_equal)
            self.assertEqual(cert.reason, "hard hash equal")
            self.assertTrue(Path(cert.output_ab).exists())
            self.assertTrue(Path(cert.output_ba).exists())

    def test_adjacent_swap_different_outputs_is_not_certified(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="different")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "not_certified_independent")
            self.assertFalse(cert.hard_equal)
            self.assertEqual(cert.reason, "hard hash differs")

    def test_adjacent_swap_failed_run_is_run_failed(self):
        from ecpor.pair_test import test_adjacent_swap

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_opt = _write_fake_opt(tmp_path, mode="fail_ba")
            state = _write_state(tmp_path)

            cert = test_adjacent_swap(
                state,
                "instcombine",
                "dce",
                opt_path=[sys.executable, str(fake_opt)],
                output_dir=tmp_path / "outputs",
                env_id="env-1",
                llvm_version="test-llvm",
            )

            self.assertEqual(cert.label, "run_failed")
            self.assertFalse(cert.hard_equal)
            self.assertIn("BA failed", cert.reason)


def _write_state(tmp_path: Path) -> Path:
    state = tmp_path / "state.ll"
    state.write_text("define void @f() {\n  ret void\n}\n", encoding="utf-8")
    return state


def _write_fake_opt(tmp_path: Path, mode: str) -> Path:
    fake_opt = tmp_path / "fake_opt.py"
    fake_opt.write_text(
        textwrap.dedent(
            f"""
            import pathlib
            import sys

            mode = {mode!r}
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            pass_arg = next(arg for arg in sys.argv if arg.startswith("-passes="))

            if mode == "fail_ba" and "dce,instcombine" in pass_arg:
                print("BA failed", file=sys.stderr)
                sys.exit(5)

            if mode == "different" and "dce,instcombine" in pass_arg:
                output.write_text("define void @f() {{\\n  ret void\\n}}\\n; BA\\n", encoding="utf-8")
            else:
                output.write_text("define void @f() {{\\n  ret void\\n}}\\n", encoding="utf-8")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_opt


if __name__ == "__main__":
    unittest.main()
```

---
