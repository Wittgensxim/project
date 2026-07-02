# ECPOR 进度记录：P9-2 result_manifest.py 轻量拆分

## 2026-07-02：工程收敛，不新增实验

### 当前目标

P9-1 已经生成 MVP 总结表，本轮进入 P9-2：只做 `result_manifest.py` 的轻量拆分，降低 manifest/report glue 的单文件复杂度。

明确不做：

```text
不新增实验
不新增 certificate
不重跑 LLVM pipeline
不改 manifest 语义
不改 CLI 行为
不改 CSV/report 结果口径
```

### 已完成内容

- [x] 将原 `src/ecpor/result_manifest.py` 拆分为：
  - `src/ecpor/manifest_common.py`
  - `src/ecpor/manifest_builders.py`
  - `src/ecpor/manifest_cli.py`
  - `src/ecpor/result_manifest.py` 兼容入口
- [x] 保留旧导入路径：
  - `from ecpor.result_manifest import build_p7a_manifest`
  - `from ecpor.result_manifest import write_manifest`
  - `python -m ecpor.result_manifest ...`
- [x] 新增结构性测试，验证拆分模块和旧入口导出同一对象。
- [x] 重跑 P9-1 MVP summary，确认拆分后汇总输出语义不变。
- [x] 更新 `docs/results/mvp_summary_manifest.json`，让它记录拆分后的 clean commit。

### 文件行数变化

拆分后：

```text
src/ecpor/result_manifest.py     16 lines
src/ecpor/manifest_common.py     75 lines
src/ecpor/manifest_builders.py   1375 lines
src/ecpor/manifest_cli.py        468 lines
```

`result_manifest.py` 已从约 1874 行降为兼容 wrapper。`manifest_builders.py` 仍然较大，但 P9-2 的目标是低风险拆分入口，不在同一轮继续做 builder 内部重构。

### TDD 验证

先写结构性 RED test：

```python
def test_result_manifest_split_modules_keep_compatibility_exports(self):
    from ecpor import manifest_builders, manifest_cli, manifest_common
    from ecpor import result_manifest

    self.assertIs(
        result_manifest.build_result_manifest,
        manifest_common.build_result_manifest,
    )
    self.assertIs(result_manifest.write_manifest, manifest_common.write_manifest)
    self.assertIs(
        result_manifest.build_p8b_matrix_manifest,
        manifest_builders.build_p8b_matrix_manifest,
    )
    self.assertIs(
        result_manifest.build_depth1_analysis_manifest,
        manifest_builders.build_depth1_analysis_manifest,
    )
    self.assertIs(result_manifest.main, manifest_cli.main)
```

初始失败符合预期：

```text
ImportError: cannot import name 'manifest_builders' from 'ecpor'
```

拆分后 targeted test：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_result_manifest_split_modules_keep_compatibility_exports
```

结果：

```text
1 passed in 0.05s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py tests\test_mvp_summary.py
```

结果：

```text
12 passed in 0.81s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
107 passed in 15.64s
```

### CLI 验证

旧入口仍可用：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest --help
```

输出仍包含原有 stage：

```text
p7a
p6-5
p7b-analysis
p8a-codegen
core-evidence
benchmark-ingest
p8b-matrix
p8b-static-repair
p8b-lazy-validation
p8b-bounded-local
p8b-code-size
p8b-codegen
depth1-analysis
effect-attribution
core-evidence-misc8
p8c-attribution
```

### P9-1 汇总重跑

拆分后重跑：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.mvp_summary --out data\outputs\final_mvp_summary --manifest docs\results\mvp_summary_manifest.json
```

关键结果保持不变：

```text
BenchmarkSets = 2
TotalPrograms = 16
TotalPairMatrixCertificates = 448
TotalReproducedCertificates = 448
TotalHardFalseIndependent = 0
TotalAdjacentAttempts = 112
TotalCertifiedEvents = 64
TotalNotCertifiedEvents = 32
TotalOneSwapCandidates = 32
TotalBothSmallerPrograms = 2
AttributionCases = 2
NoNewExperiments = True
```

`docs/results/mvp_summary_manifest.json` 已更新到：

```text
result_generated_from_commit = 63406df2d6c66300d57a09480b9fc9571fc5ef55
ecpor_git_dirty = false
new_experiments = false
llvm_pipeline_rerun = false
```

### 代码快照

`result_manifest.py` 现在只是兼容入口：

```python
"""Compatibility wrapper for result manifest builders and CLI.

The implementation is split across manifest_common, manifest_builders, and
manifest_cli. This module keeps the old `ecpor.result_manifest` import path and
`python -m ecpor.result_manifest ...` command stable.
"""

from __future__ import annotations

from .manifest_builders import *  # noqa: F401,F403
from .manifest_cli import main
from .manifest_common import build_result_manifest, write_manifest


if __name__ == "__main__":
    raise SystemExit(main())
```

`manifest_common.py` 承接通用 manifest 生成逻辑：

```python
def build_result_manifest(
    *,
    stage: str,
    description: str,
    inputs: Mapping[str, str | Path],
    outputs: Mapping[str, str | Path],
    tools: Mapping[str, str | Path],
    summary: Mapping[str, Any],
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo_git = git_info(repo_root)
    generated_from = result_generated_from_commit or repo_git.commit
```

`manifest_cli.py` 承接旧 CLI：

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build tracked result manifests.")
    subparsers = parser.add_subparsers(dest="stage", required=True)
```

### 解释与结论

P9-2 没有改变研究结果，只降低了入口复杂度：

```text
原来 result_manifest.py 同时承担 common helpers、stage builders、CLI；
现在旧入口保留，内部拆成 common/builders/cli。
```

这让后续 P9-3 README / 项目报告整理更容易：读者可以先看 `result_manifest.py` 入口，再按需进入 builder 或 CLI。

### 风险备注

- `manifest_builders.py` 仍然偏大，后续可以再按 stage family 拆，但本轮不继续扩大 refactor 范围。
- 历史进度文档仍会提到“扩展 result_manifest.py”，这是历史记录，不回写旧文档。
- 本轮没有新实验，因此 `data/outputs/` 无新增保留目录。

### 下一步

建议进入 P9-3：

```text
整理 README / 项目主报告；
把 P9-1 MVP 总表作为主入口；
写清楚当前支持什么、不支持什么、证据等级是什么。
```
