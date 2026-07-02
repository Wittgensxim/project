# ECPOR 进度记录：P11 pass registry snapshot

## 2026-07-03：把当前 LLVM pass registry 固化为可审计快照

### 当前目标

P10/P10.5 已经把 PassSpec provenance 和 trust boundary 讲清楚。P11 的目标不是继续搜索，也不是扩展实验，而是把当前 LLVM 工具链里的 pass registry 做成可审计 metadata：

```text
调用 opt --print-passes
保存原始输出和 raw hash
检查 MVP 8 个 scalar pass 是否存在
生成 snapshot JSON、report 和 tracked manifest
```

本阶段仍然不做：

```text
two-swap
depth=3
beam/searcher
runtime benchmark
Alive2
PassInstrumentation
PassSpec 行为修改
static filter 行为修改
新 certificate
新 benchmark
```

### 已完成内容

- [x] 新增 `src/ecpor/pass_registry_snapshot.py`。
- [x] 新增 `tests/test_pass_registry_snapshot.py`。
- [x] 扩展 `src/ecpor/manifest_builders.py`：
  - `build_pass_registry_snapshot_manifest()`
- [x] 扩展 `src/ecpor/manifest_cli.py`：
  - `pass-registry-snapshot`
- [x] 生成真实 LLVM registry snapshot：
  - `data/outputs/pass_registry_snapshot/opt_print_passes_raw.txt`
  - `data/outputs/pass_registry_snapshot/pass_registry_snapshot.json`
  - `data/outputs/pass_registry_snapshot/pass_registry_report.md`
- [x] 生成 tracked manifest：
  - `docs/results/pass_registry_snapshot_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

RED 测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_pass_registry_snapshot.py tests\test_result_manifest.py -q
```

预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.pass_registry_snapshot'
ImportError: cannot import name 'build_pass_registry_snapshot_manifest'
AttributeError: module 'ecpor.result_manifest' has no attribute 'build_pass_registry_snapshot_manifest'
```

实现后相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_pass_registry_snapshot.py tests\test_result_manifest.py -q
```

结果：

```text
18 passed in 0.96s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
132 passed in 23.02s
```

### 真实生成命令

生成 P11 snapshot：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.pass_registry_snapshot import main; raise SystemExit(main(['--opt', 'E:/llvm/build/bin/opt.exe', '--pipeline', 'configs/pipeline_scalar.yaml', '--out', 'data/outputs/pass_registry_snapshot']))"
```

生成 tracked manifest：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.manifest_cli import main; raise SystemExit(main(['pass-registry-snapshot', '--out-manifest', 'docs/results/pass_registry_snapshot_manifest.json', '--opt', 'E:/llvm/build/bin/opt.exe', '--pipeline-config', 'configs/pipeline_scalar.yaml', '--output-dir', 'data/outputs/pass_registry_snapshot', '--repo-root', '.', '--result-generated-from-commit', 'd529ed17c0d8dab23113e14a27c845d6194754ce']))"
```

### P11 snapshot 摘要

`data/outputs/pass_registry_snapshot/pass_registry_report.md` 的关键结果：

```text
LLVMVersion: 23.0.0git
OptPath: E:/llvm/build/bin/opt.exe
OptSHA256: f4a10cdc53c8f1288bb4051318af63ca8b07aae0f0b8ffb13b788fc98ace2543
RawOutputSHA256: e0de219d192d1d8f2bac2089793c5992e2aea3b1531104fd62215638eec7989e
ExpectedPasses: 8
PresentExpectedPasses: 8
MissingExpectedPasses: 0
ParseConfidence: raw_snapshot_with_presence_check
```

MVP 8 个 pass 全部存在：

```text
sroa: present
early-cse: present
instcombine: present
simplifycfg: present
reassociate: present
gvn: present
dce: present
adce: present
```

### manifest 关键字段

`docs/results/pass_registry_snapshot_manifest.json`：

```text
stage = P11
result_generated_from_commit = d529ed17c0d8dab23113e14a27c845d6194754ce
ecpor_git_commit = d529ed17c0d8dab23113e14a27c845d6194754ce
ecpor_git_dirty = false
metadata_only = true
registry_snapshot_only = true
static_filter_behavior_change = false
passspec_behavior_change = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
```

### 代码快照：snapshot 生成器

`src/ecpor/pass_registry_snapshot.py` 只解析 `opt --print-passes` 的原始文本，不推断 pass 语义：

```python
def build_registry_snapshot(
    *,
    raw_output: str,
    expected_passes: Sequence[str],
    opt_path: str | Path,
    opt_sha256: str,
    llvm_version: str,
) -> dict[str, Any]:
    pass_names = sorted(_extract_pass_like_names(raw_output))
    pass_name_set = set(pass_names)
    presence = {
        pass_name: pass_name in pass_name_set
        or _contains_pass_token(raw_output, pass_name)
        for pass_name in expected_passes
    }
    missing = [pass_name for pass_name, present in presence.items() if not present]
    return {
        "llvm_version": llvm_version,
        "opt_path": Path(opt_path).as_posix(),
        "opt_sha256": opt_sha256,
        "raw_output_sha256": _sha256_text(raw_output),
        "expected_passes": list(expected_passes),
        "expected_pass_presence": presence,
        "missing_expected_passes": missing,
        "all_pass_like_names": pass_names,
        "parse_confidence": PARSE_CONFIDENCE,
    }
```

raw 文件用 UTF-8 bytes 写入，避免 Windows 文本换行转换导致 raw hash 与文件 hash 不一致：

```python
raw_path.write_bytes(raw_output.encode("utf-8"))
```

### 代码快照：report 边界说明

报告固定写清楚 P11 的语义边界：

```python
lines = [
    "# LLVM Pass Registry Snapshot",
    "",
    f"LLVMVersion: {snapshot.get('llvm_version', 'unknown')}",
    f"OptPath: {snapshot.get('opt_path', '')}",
    f"OptSHA256: {snapshot.get('opt_sha256', '')}",
    f"RawOutputSHA256: {snapshot.get('raw_output_sha256', '')}",
    f"ExpectedPasses: {len(expected)}",
    f"PresentExpectedPasses: {len(expected) - len(missing)}",
    f"MissingExpectedPasses: {len(missing)}",
    f"ParseConfidence: {snapshot.get('parse_confidence', PARSE_CONFIDENCE)}",
    "",
    "This snapshot only records pass availability from the current LLVM toolchain.",
    "It does not infer pass semantics, mutate PassSpec, or change static filter behavior.",
]
```

### 代码快照：manifest builder

`src/ecpor/manifest_builders.py` 中的 P11 manifest 明确是 metadata-only：

```python
def build_pass_registry_snapshot_manifest(
    *,
    opt_path: str | Path,
    pipeline_config_path: str | Path,
    output_dir: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "pass_registry_report.md"
    return build_result_manifest(
        stage="P11",
        description="LLVM opt pass registry snapshot with MVP pass presence check.",
        inputs={
            "pipeline_config": pipeline_config_path,
        },
        outputs={
            "output_dir": out,
            "opt_print_passes_raw": out / "opt_print_passes_raw.txt",
            "pass_registry_snapshot_json": out / "pass_registry_snapshot.json",
            "pass_registry_report": report,
        },
        tools={
            "opt": opt_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            PASS_REGISTRY_SNAPSHOT_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "metadata_only": True,
                "registry_snapshot_only": True,
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

1. P11 只证明当前 `opt.exe` 的 registry 输出中能看到 MVP 8 个 pass，不证明 pass 语义、analysis dependency、preserved analysis 或 PassSpec hint 正确性。
2. `all_pass_like_names` 是保守 token 提取结果，可用于人工检查，不应作为 PassSpec 自动更新来源。
3. hard pruning 边界不变：仍然只能来自 state-indexed AB/BA certificate，不能来自 pass registry snapshot 或 static filter。
4. `data/outputs/pass_registry_snapshot/` 属于 retained metadata 输出，保留 raw/report/json；tracked manifest 在 `docs/results/pass_registry_snapshot_manifest.json`。

### 下一步

建议进入 P11.5：PassSpec registry cross-check。

P11.5 只应该检查：

```text
configs/passspec.yaml 中的 8 个 pass 是否都在 P11 registry snapshot 中存在
是否存在 PassSpec 记录了但 registry 缺失的 pass
是否存在 pipeline_scalar.yaml 与 PassSpec pass set 不一致
```

仍然不要做：

```text
自动推断 may_produce / may_consume
自动修改 passspec
新 certificate
新 benchmark
search / runtime / Alive2 / PassInstrumentation
```
