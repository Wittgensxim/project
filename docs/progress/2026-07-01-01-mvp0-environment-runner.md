# ECPOR 进度记录：MVP-0/P0 环境与 Runner 基础

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
