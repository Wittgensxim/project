# ECPOR 项目进度记录

本文件是 ECPOR 原型项目的持续进度记录。后续每次有实质性进展、验证结果、风险变化或下一步任务变化时，都要更新本文件。

## 文档维护规则

1. 本进度文档统一使用中文记录。
2. 每次更新本文件时，都要附上与本次进度相关的代码快照。
3. 代码快照优先附完整源码或完整配置；如果文件过大，可以附关键完整片段，并说明未附全文的原因。
4. 生成产物如 `.ll`、`.o`、大体量报告、批量日志默认不贴全文，只记录路径、命令、hash 和验证结果。
5. 每条进度必须包含：当前目标、完成内容、验证结果、风险/备注、下一步。

---

## 2026-07-01：MVP-0/P0 环境与 Runner 基础

### 当前目标

构建 MVP-0/P0：一个最小、可复现的 LLVM 环境记录与 `opt` runner 基础，为后续 pair certificate 和 phase-ordering 搜索打地基。

### 已确认输入

- 已阅读项目文档：
  - `ecpor_progress_metrics_plan.md`
  - `phase_order_project_doc_revised.md`
- 正式 benchmark 根目录：`E:\llvm-test-suite`
- 本地 LLVM 根目录：`E:\llvm`
- LLVM 工具目录：`E:\llvm\build\bin`
- 检测到 LLVM 版本：`23.0.0git`
- 检测到默认 target：`x86_64-w64-windows-gnu`
- 检测到 clang commit：`aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2`
- MVP scalar pipeline dry-run 已通过：
  - `function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)`
- `E:\llvm-test-suite` 结构已确认：
  - `SingleSource`
  - `MultiSource`
  - `MicroBenchmarks`
  - `CTMark`

### 已完成内容

- [x] 阅读并整理两份项目文档中的 MVP 范围。
- [x] 确认本地 LLVM 工具链路径。
- [x] 确认 MVP scalar pass 名称能被本地 `opt` 接受。
- [x] 编写 RED 测试。
- [x] 实现 MVP-0 核心代码。
- [x] 添加配置、README 和 smoke-test 输入。
- [x] 将正式 benchmark 来源改为 `E:\llvm-test-suite`。
- [x] 生成 3 个 LLVM test-suite Stanford 输入的 `.ll`。
- [x] 完成单元测试和真实 LLVM runner 验证。

### 新增或更新文件

- `README.md`
- `pyproject.toml`
- `configs/env.yaml`
- `configs/benchmarks.yaml`
- `configs/pipeline_scalar.yaml`
- `src/ecpor/__init__.py`
- `src/ecpor/environment.py`
- `src/ecpor/normalizer.py`
- `src/ecpor/runner.py`
- `tests/test_environment.py`
- `tests/test_normalizer.py`
- `tests/test_runner.py`
- `benchmarks/micro/dead_code.c`
- `benchmarks/micro/branch.c`
- `benchmarks/micro/alloca.c`
- `data/inputs/dead_code.ll`
- `data/inputs/branch.ll`
- `data/inputs/alloca.ll`
- `data/inputs/testsuite_stanford_bubblesort.ll`
- `data/inputs/testsuite_stanford_intmm.ll`
- `data/inputs/testsuite_stanford_perm.ll`
- `data/outputs/dead_code.opt.ll`
- `data/outputs/branch.opt.ll`
- `data/outputs/alloca.opt.ll`
- `data/outputs/dead_code.scalar.ll`
- `data/outputs/branch.scalar.ll`
- `data/outputs/alloca.scalar.ll`
- `data/outputs/testsuite_stanford_bubblesort.scalar.ll`
- `data/outputs/testsuite_stanford_intmm.scalar.ll`
- `data/outputs/testsuite_stanford_perm.scalar.ll`

### 验证结果

- RED 测试：
  - 命令：`python -m unittest discover -s tests -v`
  - 结果：实现前失败，出现 9 个 `ModuleNotFoundError`，符合 RED 阶段预期。
- 实现后单元测试：
  - 命令：`python -m unittest discover -s tests -v`
  - 结果：`Ran 9 tests ... OK`
- IR 生成：
  - `benchmarks/micro/dead_code.c`、`benchmarks/micro/branch.c`、`benchmarks/micro/alloca.c` 已用 `clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm` 生成 `.ll`。
  - `E:\llvm-test-suite\SingleSource\Benchmarks\Stanford\Bubblesort.c` 已生成 `data/inputs/testsuite_stanford_bubblesort.ll`。
  - `E:\llvm-test-suite\SingleSource\Benchmarks\Stanford\IntMM.c` 已生成 `data/inputs/testsuite_stanford_intmm.ll`。
  - `E:\llvm-test-suite\SingleSource\Benchmarks\Stanford\Perm.c` 已生成 `data/inputs/testsuite_stanford_perm.ll`。
- 真实 `opt` runner smoke test，pipeline 为 `function(instcombine,dce)`：
  - `dead_code.ll`：`exit_code=0`，`verifier_ok=True`，hash `a301d5f7ae1a8ff8c525f5a086231d3d7a0ab8eaa69775ce16f42a4320a632a1`
  - `branch.ll`：`exit_code=0`，`verifier_ok=True`，hash `2e07e0d68b07050ec21ad08e68b8aaac323af753737bffa07f1f7257b6cf30c1`
  - `alloca.ll`：`exit_code=0`，`verifier_ok=True`，hash `708018e3ec1a15cdc1910c3f2f63dea76ac041c2f47015407206ceafc20cc202`
- 真实 `opt` runner smoke test，pipeline 为 `function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)`：
  - `dead_code.ll`：`exit_code=0`，`verifier_ok=True`，hash `a301d5f7ae1a8ff8c525f5a086231d3d7a0ab8eaa69775ce16f42a4320a632a1`
  - `branch.ll`：`exit_code=0`，`verifier_ok=True`，hash `9ebb32f1d83459e51d6794ac96b8c976d854689e4f0925b6bc05dbeff06b8b93`
  - `alloca.ll`：`exit_code=0`，`verifier_ok=True`，hash `ab3dc2f977bbedb53ee595626373e220017cbff8f1a526d21c4a136010404bc1`
- 真实 `opt` runner smoke test，输入来自 `E:\llvm-test-suite` Stanford，pipeline 为 `function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)`：
  - `testsuite_stanford_bubblesort.ll`：`exit_code=0`，`verifier_ok=True`，hash `a4d1feea43fe4dd9ff80201f4cd0bffdf2b6729635a4e28a3aceaaa94c0b2f4e`
  - `testsuite_stanford_intmm.ll`：`exit_code=0`，`verifier_ok=True`，hash `77b408263749db369b50829dd022e358954c101a315a71fe9a98b3738bda3d1c`
  - `testsuite_stanford_perm.ll`：`exit_code=0`，`verifier_ok=True`，hash `9458f7d299749019905083ade9d2fb427d7c10e2b7734047defa0c42f0979c84`

### 风险与备注

- `E:\project` 当前不是 git 仓库，所以无法用 commit 作为进度边界。
- 当前 Python 环境没有安装 `pytest`，MVP-0 测试使用标准库 `unittest`。
- `benchmarks/micro/*.c` 只作为快速 smoke-test 输入保留；正式 benchmark 来源是 `E:\llvm-test-suite`。
- 当前 hard normalizer 非常保守，只规范化换行和 BOM，不删除优化相关 metadata，不重排 IR 实体。

### 下一步

进入 P1/P2 基础：

1. 添加 `cert.py`，定义 state-indexed certificate schema。
2. 添加 `pair_test.py`，从同一个输入状态运行 `A;B` 和 `B;A`。
3. 写 RED 测试覆盖 `certified_independent`、`not_certified_independent` 和 `run_failed` 标签。
4. 为一个 test-suite 输入和一个 pass pair 生成第一份 JSON certificate。
5. 添加 benchmark ingestion helper，读取 `configs/benchmarks.yaml` 并把选中的 `E:\llvm-test-suite` 条目编译进 `data/inputs`。

---

## 2026-07-01：进度文档规则调整

### 当前目标

按用户要求调整进度记录方式：进度文档必须用中文写，并且每次更新进度文档时同步附上相关代码。

### 已完成内容

- [x] 将 `docs/project_progress.md` 改为中文结构。
- [x] 添加“文档维护规则”。
- [x] 明确后续每次更新进度文档都要附相关代码快照。
- [x] 本次附上 MVP-0 当前核心代码和配置。

### 验证结果

本次只修改文档，没有修改运行代码。文档更新后已执行轻量验证：

```powershell
python -m unittest discover -s tests -v
```

结果：`Ran 9 tests ... OK`

同时复跑了一个真实 LLVM runner 烟测：

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; p='function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)'; r=run_opt('data/inputs/testsuite_stanford_bubblesort.ll', p, 'data/outputs/testsuite_stanford_bubblesort.scalar.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"
```

结果：`0 True a4d1feea43fe4dd9ff80201f4cd0bffdf2b6729635a4e28a3aceaaa94c0b2f4e`

### 下一步

后续任何实现性更新，都在本文件对应日期条目下增加：

- 进度说明
- 验证结果
- 风险/备注
- 下一步
- 相关代码快照

---

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

## 2026-07-01：切换到 dlm Python 环境

### 当前目标

按用户要求，后续测试、开发和运行命令统一使用 `dlm` Python 环境。

### 已完成内容

- [x] 定位 `dlm` 环境：
  - `D:\Miniconda\envs\dlm\python.exe`
- [x] 确认 `dlm` Python 版本：
  - `Python 3.10.20`
- [x] 确认 `dlm` 环境中已有 `pip`：
  - `pip 26.0.1`
- [x] 确认 `dlm` 环境中已有 `pytest`：
  - `pytest 9.1.1`
- [x] 更新 `README.md` 中的测试命令和 smoke-test Python 命令。
- [x] 更新 `docs/superpowers/plans/2026-07-01-mvp0-environment-runner.md` 中的 Python 测试命令。

### 验证结果

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest --version
```

结果：`pytest 9.1.1`

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：`14 passed in 0.42s`

真实 LLVM pair-test 复跑：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.pair_test import test_adjacent_swap; cert=test_adjacent_swap('data/inputs/testsuite_stanford_bubblesort.ll','instcombine','dce',opt_path='E:/llvm/build/bin/opt.exe',output_dir='data/outputs/pair_tests',env_id='b87a818a5b1ba7b3913d179fd1bee2d02ece540ff5552aacce4ef5a77fec6c84',llvm_version='23.0.0git'); print(cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba)"
```

结果：

```text
certified_independent True 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56
```

### 风险与备注

- 系统默认 `python` 仍指向 `C:\msys64\ucrt64\bin\python.exe`，不要依赖裸 `python`。
- 后续命令统一显式使用 `D:\Miniconda\envs\dlm\python.exe`。
- 之前安装到 `D:\Miniconda\python.exe` base 环境的 pytest 保留不动；当前项目以后以 `dlm` 环境为准。

### 下一步

继续 P1/P2：

1. 给 `pair_test.py` 增加 CLI。
2. 增加 certificate reproduction 测试。
3. 增加 `feature_scan.py` 第一版。

---

## 本次代码快照：切换 dlm Python 环境

### `README.md` 相关片段

````markdown
## Unit Tests

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

## Smoke Test

Generate LLVM IR:

```powershell
E:\llvm\build\bin\clang.exe -O0 -Xclang -disable-O0-optnone -S -emit-llvm benchmarks\micro\dead_code.c -o data\inputs\dead_code.ll
```

Run a minimal `opt` pipeline through the Python runner:

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; r = run_opt('data/inputs/dead_code.ll', 'function(instcombine,dce)', 'data/outputs/dead_code.opt.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"
```
````

### `docs/superpowers/plans/2026-07-01-mvp0-environment-runner.md` 相关片段

```markdown
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_environment.py -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_normalizer.py -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_runner.py -q`
- [ ] Run all unit tests: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
```

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

## 本次代码快照：MVP-0 环境与 Runner

### `src/ecpor/environment.py`

```python
"""LLVM environment discovery and fingerprinting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


DEFAULT_EXECUTION_MODEL = "materialized_ir_fresh_opt"
DEFAULT_DEBUG_POLICY = "strip_at_input"
DEFAULT_METADATA_POLICY = "preserve_optimization_metadata"
DEFAULT_NORMALIZER_VERSION = "hard-normalizer-v1"


@dataclass(frozen=True)
class LLVMEnvironment:
    opt_path: str
    clang_path: str
    llvm_size_path: str
    llvm_config_path: str
    llvm_version: str
    clang_version: str
    clang_commit: str
    target_triple: str
    host_cpu: str
    execution_model: str = DEFAULT_EXECUTION_MODEL
    debug_policy: str = DEFAULT_DEBUG_POLICY
    metadata_policy: str = DEFAULT_METADATA_POLICY
    normalizer_version: str = DEFAULT_NORMALIZER_VERSION

    @property
    def env_id(self) -> str:
        return compute_env_id(self)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["env_id"] = self.env_id
        return data


def parse_opt_version(text: str) -> dict[str, str]:
    return {
        "llvm_version": _match_or_unknown(r"LLVM version\s+([^\r\n]+)", text),
        "target_triple": _match_or_unknown(r"Default target:\s+([^\r\n]+)", text),
        "host_cpu": _match_or_unknown(r"Host CPU:\s+([^\r\n]+)", text),
    }


def parse_clang_version(text: str) -> dict[str, str]:
    version = _match_or_unknown(r"clang version\s+(\S+)", text)
    commit = _match_or_unknown(r"llvm-project\.git\s+([0-9a-fA-F]+)", text)
    return {
        "clang_version": version,
        "clang_commit": commit,
    }


def compute_env_id(env: LLVMEnvironment) -> str:
    payload = json.dumps(asdict(env), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def detect_environment(bin_dir: str | Path = "E:/llvm/build/bin") -> LLVMEnvironment:
    root = Path(bin_dir)
    opt = root / "opt.exe"
    clang = root / "clang.exe"
    llvm_size = root / "llvm-size.exe"
    llvm_config = root / "llvm-config.exe"

    opt_info = parse_opt_version(_run_text([str(opt), "--version"]))
    clang_info = parse_clang_version(_run_text([str(clang), "--version"]))

    return LLVMEnvironment(
        opt_path=_path_text(opt),
        clang_path=_path_text(clang),
        llvm_size_path=_path_text(llvm_size),
        llvm_config_path=_path_text(llvm_config),
        llvm_version=opt_info["llvm_version"],
        clang_version=clang_info["clang_version"],
        clang_commit=clang_info["clang_commit"],
        target_triple=opt_info["target_triple"],
        host_cpu=opt_info["host_cpu"],
    )


def _match_or_unknown(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        return "unknown"
    return match.group(1).strip()


def _path_text(path: Path) -> str:
    return path.as_posix()


def _run_text(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    return result.stdout + result.stderr
```

### `src/ecpor/normalizer.py`

```python
"""Conservative IR canonicalization and hard hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


NORMALIZER_VERSION = "hard-normalizer-v1"


def hard_canonicalize(ir_text: str) -> str:
    text = ir_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.endswith("\n"):
        text += "\n"
    return text


def hard_hash_text(ir_text: str) -> str:
    canonical = hard_canonicalize(ir_text)
    return hashlib.sha256(
        canonical.encode("utf-8", errors="surrogateescape")
    ).hexdigest()


def hard_hash(ir_path: str | Path) -> str:
    path = Path(ir_path)
    text = path.read_bytes().decode("utf-8", errors="surrogateescape")
    return hard_hash_text(text)
```

### `src/ecpor/runner.py`

```python
"""Structured runner for LLVM opt pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Sequence

from .normalizer import hard_hash


OptPath = str | Path | Sequence[str | Path]


@dataclass(frozen=True)
class RunResult:
    command: list[str]
    input_path: Path
    output_path: Path
    pipeline: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float
    verifier_ok: bool
    timed_out: bool = False
    hard_hash: str | None = None


def build_opt_command(
    input_ll: str | Path,
    passes: str,
    output_ll: str | Path,
    *,
    opt_path: OptPath = "opt",
    extra_flags: Sequence[str] | None = None,
) -> list[str]:
    command = _normalize_opt_path(opt_path)
    command.extend(
        [
            str(input_ll),
            "-S",
            "-o",
            str(output_ll),
            f"-passes={passes}",
            "-verify-each",
        ]
    )
    if extra_flags:
        command.extend(extra_flags)
    return command


def run_opt(
    input_ll: str | Path,
    passes: str,
    output_ll: str | Path,
    *,
    opt_path: OptPath = "opt",
    extra_flags: Sequence[str] | None = None,
    timeout_sec: float = 30.0,
) -> RunResult:
    input_path = Path(input_ll)
    output_path = Path(output_ll)
    command = build_opt_command(
        input_path,
        passes,
        output_path,
        opt_path=opt_path,
        extra_flags=extra_flags,
    )

    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result_hash = hard_hash(output_path) if completed.returncode == 0 and output_path.exists() else None
        verifier_ok = completed.returncode == 0 and output_path.exists()
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_ms=elapsed_ms,
            verifier_ok=verifier_ok,
            hard_hash=result_hash,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=-1,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nTimed out after {timeout_sec} seconds.",
            elapsed_ms=elapsed_ms,
            verifier_ok=False,
            timed_out=True,
        )
    except OSError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RunResult(
            command=command,
            input_path=input_path,
            output_path=output_path,
            pipeline=passes,
            exit_code=-1,
            stdout="",
            stderr=str(exc),
            elapsed_ms=elapsed_ms,
            verifier_ok=False,
        )


def _normalize_opt_path(opt_path: OptPath) -> list[str]:
    if isinstance(opt_path, (str, Path)):
        return [str(opt_path)]
    return [str(part) for part in opt_path]
```

### `configs/env.yaml`

```yaml
llvm:
  opt_path: "E:/llvm/build/bin/opt.exe"
  clang_path: "E:/llvm/build/bin/clang.exe"
  llvm_size_path: "E:/llvm/build/bin/llvm-size.exe"
  llvm_config_path: "E:/llvm/build/bin/llvm-config.exe"
  llvm_version: "23.0.0git"
  clang_version: "23.0.0git"
  clang_commit: "aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2"
  env_id: "b87a818a5b1ba7b3913d179fd1bee2d02ece540ff5552aacce4ef5a77fec6c84"

target:
  triple: "x86_64-w64-windows-gnu"
  host_cpu: "znver5"

policies:
  execution_model: "materialized_ir_fresh_opt"
  debug_policy: "strip_at_input"
  metadata_policy: "preserve_optimization_metadata"
  normalizer_version: "hard-normalizer-v1"
```

### `configs/pipeline_scalar.yaml`

```yaml
name: "mvp_function_scalar"
pipeline: "function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)"
passes:
  - "sroa"
  - "early-cse"
  - "instcombine"
  - "simplifycfg"
  - "reassociate"
  - "gvn"
  - "dce"
  - "adce"
```

### `configs/benchmarks.yaml`

```yaml
root: "E:/llvm-test-suite"
primary_source: "llvm-test-suite"
notes:
  - "The local benchmarks/micro files are smoke-test inputs only."
  - "Formal MVP benchmark selection should come from E:/llvm-test-suite."

initial_subset:
  suite: "SingleSource/Benchmarks/Stanford"
  compile_mode: "clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm"
  programs:
    - id: "stanford_bubblesort"
      source: "SingleSource/Benchmarks/Stanford/Bubblesort.c"
      ir: "data/inputs/testsuite_stanford_bubblesort.ll"
    - id: "stanford_intmm"
      source: "SingleSource/Benchmarks/Stanford/IntMM.c"
      ir: "data/inputs/testsuite_stanford_intmm.ll"
    - id: "stanford_perm"
      source: "SingleSource/Benchmarks/Stanford/Perm.c"
      ir: "data/inputs/testsuite_stanford_perm.ll"
```

### `benchmarks/micro/dead_code.c`

```c
int dead_code(int x) {
    int a = x + 1;
    int b = a * 2;
    int c = b - b;
    return x + c;
}
```

### `benchmarks/micro/branch.c`

```c
int branch_simplify(int x) {
    int y = 0;
    if (x > 0) {
        y = x;
    } else {
        y = -x;
    }

    if (y >= 0) {
        return y;
    }
    return 0;
}
```

### `benchmarks/micro/alloca.c`

```c
int alloca_sroa(int x) {
    int pair[2];
    pair[0] = x;
    pair[1] = x + 1;
    return pair[0] + pair[1];
}
```

---

## 2026-07-01：加强环境指纹、证书唯一性和复现闭环

### 当前目标

根据最新 review，把当前 P1 certificate 闭环从“能跑通”推进到“更可复现、更不易覆盖、更适合后续批量实验”的状态。优先处理 `env_id`、`cert_id`、输出目录、CLI、reproduction test 和 git 边界。

### 已完成内容

- [x] 将测试和运行环境统一保持为 `D:\Miniconda\envs\dlm\python.exe`。
- [x] 新增 `file_sha256()`，并把 `opt.exe`、`clang.exe`、`llvm-size.exe`、`llvm-config.exe` 的 SHA-256 纳入 `LLVMEnvironment`。
- [x] 将 LLVM build 信息纳入环境记录：`CMAKE_BUILD_TYPE=Release`、`LLVM_ENABLE_ASSERTIONS=OFF`、`CMakeCache.txt` hash。
- [x] 更新 `configs/env.yaml`，新的 `env_id` 为 `3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e`。
- [x] 扩展 `PairCertificate` schema，新增 `input_ir_path`、`nesting`、`pipeline_ab`、`pipeline_ba`、`extra_flags`、pass instance、`region_id`、`ecpor_git_commit`、`ecpor_git_dirty`。
- [x] 扩展 `make_cert_id()`，使证书 ID 对 `nesting`、AB/BA pipeline、`extra_flags`、pass instance 和 region 敏感。
- [x] 将 pair-test 输出目录改为 `data/outputs/pair_tests/<cert_id>/ab.ll` 和 `ba.ll`，并同步写入 `input_hash.txt`、`stdout_*.txt`、`stderr_*.txt`、`cert.json`。
- [x] 增加 `reproduce_certificate()`，可以读取已保存 certificate，复跑 AB/BA，并比较 label 与 hard hash。
- [x] 增加 `python -m ecpor.pair_test` CLI，支持生成 JSON certificate。
- [x] 新增 `.gitignore`，排除 pycache、pytest cache、生成的 outputs/certs 和临时产物。
- [x] 更新 `README.md`，加入 pair-test certificate 和 reproduction 命令。

### 验证结果

单元测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
20 passed in 1.19s
```

真实 LLVM certificate 生成：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.pair_test import test_adjacent_swap; cert=test_adjacent_swap('data/inputs/testsuite_stanford_bubblesort.ll','instcombine','dce',opt_path='E:/llvm/build/bin/opt.exe',output_dir='data/outputs/pair_tests',env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e',llvm_version='23.0.0git'); cert.save('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json'); print(cert.cert_id, cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba, cert.output_ab, cert.output_ba)"
```

结果：

```text
e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954 certified_independent True 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ab.ll data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ba.ll
```

真实 LLVM certificate reproduction：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.pair_test import reproduce_certificate; r=reproduce_certificate('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json', opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests/repro'); print(r.reproduced, r.original_label, r.reproduced_label, r.original_hash_ab, r.reproduced_hash_ab, r.original_hash_ba, r.reproduced_hash_ba, r.reason)"
```

结果：

```text
True certified_independent certified_independent 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 label and hashes match
```

### 风险与备注

- `E:/llvm` 当前没有可读出的 git commit，因此 `llvm_source_git_commit` 仍为 `unknown`，但二进制工具 hash 已经能区分本地 rebuild。
- `verifier_ok` 的语义仍是“`opt` 退出成功且输出存在”，还没有拆成 `opt_success`、`output_exists`、`failure_kind` 等更细字段。
- 测试文件仍通过 `sys.path.insert` 或 CLI 的 `PYTHONPATH=src` 使用本地包；editable install 留到后续整理。
- 本轮保持在 function scalar pass 子集，没有扩展到 loop、CGSCC 或 module 级 pass。

### 下一步

1. 初始化 git 仓库并提交当前 MVP-0/P1 边界。
2. 在 certificate 中进一步区分 runner failure kind，澄清 `verifier_ok` 语义。
3. 生成 3 个 Stanford 输入乘 3 个 pass pair 的最小证书表。
4. 证书闭环稳定后，再进入 `feature_scan.py` 和静态过滤。

### 本次代码快照：`src/ecpor/environment.py` 关键片段

```python
@dataclass(frozen=True)
class LLVMEnvironment:
    opt_path: str
    clang_path: str
    llvm_size_path: str
    llvm_config_path: str
    llvm_version: str
    clang_version: str
    clang_commit: str
    target_triple: str
    host_cpu: str
    execution_model: str = DEFAULT_EXECUTION_MODEL
    debug_policy: str = DEFAULT_DEBUG_POLICY
    metadata_policy: str = DEFAULT_METADATA_POLICY
    normalizer_version: str = DEFAULT_NORMALIZER_VERSION
    opt_sha256: str = "unknown"
    clang_sha256: str = "unknown"
    llvm_size_sha256: str = "unknown"
    llvm_config_sha256: str = "unknown"
    llvm_source_root: str = "E:/llvm"
    llvm_source_git_commit: str = "unknown"
    llvm_source_git_dirty: bool | None = None
    llvm_build_type: str = "unknown"
    llvm_assertions: str = "unknown"
    cmake_cache_sha256: str = "unknown"


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
```

### 本次代码快照：`src/ecpor/cert.py` 关键片段

```python
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
```

```python
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
```

### 本次代码快照：`src/ecpor/pair_test.py` 关键片段

```python
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
```

```python
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
```

### 本次代码快照：`configs/env.yaml`

```yaml
llvm:
  opt_path: "E:/llvm/build/bin/opt.exe"
  clang_path: "E:/llvm/build/bin/clang.exe"
  llvm_size_path: "E:/llvm/build/bin/llvm-size.exe"
  llvm_config_path: "E:/llvm/build/bin/llvm-config.exe"
  llvm_version: "23.0.0git"
  clang_version: "23.0.0git"
  clang_commit: "aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2"
  opt_sha256: "f4a10cdc53c8f1288bb4051318af63ca8b07aae0f0b8ffb13b788fc98ace2543"
  clang_sha256: "7813948a1b853beb1806fd1bb28b09917bcbd9e35d67b43345af02c100b93551"
  llvm_size_sha256: "f425ef87d64380ff5f8fd055ddb52e1f0d38f3031bb2a5bbddd557d71c5bc589"
  llvm_config_sha256: "3622511cbec368b9fbe9bc01fdf6b679cdecf16381c349f447c1ff30f26c1bde"
  env_id: "3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e"

llvm_source:
  root: "E:/llvm"
  git_commit: "unknown"
  git_dirty: null

llvm_build:
  build_type: "Release"
  assertions: "OFF"
  cmake_cache_sha256: "9e56132f8c33227089b371b05906adccfff0ad4f92a72f303cc8ac39eec7b0f2"
```

### 本次代码快照：`.gitignore`

```gitignore
__pycache__/
.pytest_cache/
*.pyc
data/outputs/
data/certs/
*.o
*.obj
*.exe
*.ll.tmp
!data/inputs/*.ll
```
