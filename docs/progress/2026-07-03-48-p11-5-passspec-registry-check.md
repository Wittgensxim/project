# ECPOR 进度记录：P11.5 PassSpec registry cross-check

## 2026-07-03：检查 PassSpec / pipeline / LLVM registry 三者 pass identity 一致性

### 当前目标

P11 已经把当前 LLVM 工具链的 `opt --print-passes` 固化为 registry snapshot。P11.5 的目标是把这个 snapshot 和项目内部的两个 pass 身份来源做交叉检查：

```text
configs/passspec.yaml
configs/pipeline_scalar.yaml
data/outputs/pass_registry_snapshot/pass_registry_snapshot.json
```

本阶段只回答：

```text
PassSpec 中声明的 pass 是否在当前 registry snapshot 中存在？
pipeline 中使用的 pass 是否都在 PassSpec 中声明？
P11 snapshot 的 expected pass 是否都在 PassSpec 中声明？
```

本阶段仍然不做：

```text
自动推断 may_produce / may_consume
自动修改 passspec
static filter 行为修改
新 certificate
新 benchmark
search
runtime benchmark
Alive2
PassInstrumentation
```

### 已完成内容

- [x] 新增 `src/ecpor/passspec_registry_check.py`。
- [x] 新增 `tests/test_passspec_registry_check.py`。
- [x] 扩展 `src/ecpor/manifest_builders.py`：
  - `build_passspec_registry_check_manifest()`
- [x] 扩展 `src/ecpor/manifest_cli.py`：
  - `passspec-registry-check`
- [x] 生成真实 P11.5 cross-check 输出：
  - `data/outputs/passspec_registry_check/passspec_registry_check.csv`
  - `data/outputs/passspec_registry_check/passspec_registry_check_report.md`
- [x] 生成 tracked manifest：
  - `docs/results/passspec_registry_check_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

RED 测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_passspec_registry_check.py tests\test_result_manifest.py -q
```

预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.passspec_registry_check'
ImportError: cannot import name 'build_passspec_registry_check_manifest'
AttributeError: module 'ecpor.result_manifest' has no attribute 'build_passspec_registry_check_manifest'
```

实现后相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_passspec_registry_check.py tests\test_result_manifest.py -q
```

结果：

```text
19 passed in 1.01s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
137 passed in 23.76s
```

### 真实生成命令

生成 P11.5 CSV/report：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.passspec_registry_check import main; raise SystemExit(main(['--passspec', 'configs/passspec.yaml', '--pipeline', 'configs/pipeline_scalar.yaml', '--registry-snapshot', 'data/outputs/pass_registry_snapshot/pass_registry_snapshot.json', '--out-dir', 'data/outputs/passspec_registry_check']))"
```

生成 tracked manifest：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.manifest_cli import main; raise SystemExit(main(['passspec-registry-check', '--out-manifest', 'docs/results/passspec_registry_check_manifest.json', '--passspec', 'configs/passspec.yaml', '--pipeline-config', 'configs/pipeline_scalar.yaml', '--registry-snapshot', 'data/outputs/pass_registry_snapshot/pass_registry_snapshot.json', '--output-dir', 'data/outputs/passspec_registry_check', '--repo-root', '.', '--result-generated-from-commit', '3f035f8be0288be21a3e281f38b1a52a460ec3c1']))"
```

### P11.5 真实结果

`data/outputs/passspec_registry_check/passspec_registry_check_report.md` 的关键结果：

```text
PassSpecPasses: 8
PipelinePasses: 8
RegistryExpectedPasses: 8
MissingPassSpecPassesInRegistry: 0
PipelinePassesMissingInPassSpec: 0
RegistryExpectedPassesMissingInPassSpec: 0
RegistryMissingExpectedPasses: 0
Status: pass
```

CSV 中 8 个 pass 全部为 `ok`：

```text
adce: ok
dce: ok
early-cse: ok
gvn: ok
instcombine: ok
reassociate: ok
simplifycfg: ok
sroa: ok
```

### manifest 关键字段

`docs/results/passspec_registry_check_manifest.json`：

```text
stage = P11.5
result_generated_from_commit = 3f035f8be0288be21a3e281f38b1a52a460ec3c1
ecpor_git_commit = 3f035f8be0288be21a3e281f38b1a52a460ec3c1
ecpor_git_dirty = false
metadata_only = true
registry_cross_check_only = true
static_filter_behavior_change = false
passspec_behavior_change = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
```

### 代码快照：cross-check 核心逻辑

`src/ecpor/passspec_registry_check.py` 读取 normalized PassSpec、pipeline pass list 和 P11 snapshot，只生成 pass identity 行：

```python
def build_registry_check(
    *,
    passspec_path: str | Path,
    pipeline_config_path: str | Path,
    registry_snapshot_path: str | Path,
) -> dict[str, Any]:
    passspec = load_normalized_passspec(passspec_path)
    pipeline_passes = load_expected_passes(pipeline_config_path)
    snapshot = _load_snapshot(registry_snapshot_path)
    rows = build_check_rows(
        passspec=passspec,
        pipeline_passes=pipeline_passes,
        registry_snapshot=snapshot,
    )
    return {
        "summary": summarize_rows(
            rows,
            passspec_passes=passspec.keys(),
            pipeline_passes=pipeline_passes,
            registry_snapshot=snapshot,
        ),
        "rows": rows,
    }
```

状态分类只表达身份一致性，不表达语义：

```python
def _status(
    *,
    in_passspec: bool,
    in_pipeline: bool,
    in_registry: bool,
    in_registry_expected: bool,
) -> str:
    if in_passspec and not in_registry:
        return "missing_in_registry"
    if in_pipeline and not in_passspec:
        return "pipeline_pass_missing_in_passspec"
    if in_registry_expected and not in_passspec:
        return "missing_in_passspec"
    return "ok"
```

### 代码快照：报告边界

P11.5 report 固定写清楚它不是语义推断，也不是 hard-prune 证据：

```python
lines = [
    "# PassSpec Registry Cross-Check",
    "",
    "This report checks whether PassSpec and the MVP pipeline refer to passes",
    "that are present in the current LLVM opt --print-passes snapshot.",
    "",
    "It does not infer pass semantics.",
    "It does not change static filter behavior.",
    "It does not certify independence.",
    "",
]
```

### 代码快照：manifest builder

P11.5 manifest 明确记录 `registry_cross_check_only`：

```python
def build_passspec_registry_check_manifest(
    *,
    passspec_path: str | Path,
    pipeline_config_path: str | Path,
    registry_snapshot_path: str | Path,
    output_dir: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "passspec_registry_check_report.md"
    return build_result_manifest(
        stage="P11.5",
        description="PassSpec, MVP pipeline, and LLVM registry snapshot cross-check.",
        inputs={
            "passspec": passspec_path,
            "pipeline_config": pipeline_config_path,
            "registry_snapshot": registry_snapshot_path,
        },
        outputs={
            "output_dir": out,
            "passspec_registry_check_csv": out / "passspec_registry_check.csv",
            "passspec_registry_check_report": report,
        },
        tools={},
        summary=_filter_keys(
            _parse_key_value_report(report),
            PASSSPEC_REGISTRY_CHECK_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "metadata_only": True,
                "registry_cross_check_only": True,
                "static_filter_behavior_change": False,
                "passspec_behavior_change": False,
                "new_experiments": False,
                "new_certificates": False,
                "new_search": False,
                "runtime_benchmarks": False,
            }
        },
    )
```

### 风险与备注

1. P11.5 只证明项目声明的 8 个 pass 名称与当前 LLVM registry snapshot 对齐，不证明 PassSpec hint 正确。
2. P11.5 不枚举所有 LLVM pass，也不判断哪些 registry pass 应该纳入 MVP；这属于未来 PassSpecDB 或 P12 之后的设计问题。
3. hard pruning 仍然只能来自 state-indexed AB/BA certificate，不能来自 registry cross-check。
4. `data/outputs/passspec_registry_check/` 属于 retained metadata 输出，保留 CSV/report；tracked manifest 在 `docs/results/passspec_registry_check_manifest.json`。

### 下一步

建议进入 P12 interaction graph v1。

P12 第一版仍然不新增实验，只读取已有 P4/P5/P6/P8/P9/P10/P11 证据，输出：

```text
pass_interaction_edges.csv
pass_interaction_graph.json
pass_interaction_graph_report.md
docs/results/interaction_graph_v1_manifest.json
```

P12 的重点是把已有 `certified_independent`、`not_certified_independent`、objective-layer both-smaller 和 attribution case 组织成 pass interaction graph，回到最初的“证明哪些顺序不用搜、解释哪些顺序必须保留”的主线。
