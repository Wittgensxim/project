# ECPOR 进度记录：P10.5 PassSpec trust report / methods note

## 2026-07-03：把 P10 provenance audit 转成可读的可信度说明

### 当前目标

P10 已经把 `passspec.yaml` 升级为可审计 metadata 表，并生成 audit。P10.5 的目标不是继续搜索，也不是继续扩展实验，而是把 P10 的 audit 结果整理成论文/报告方法部分可以引用的说明：

```text
PassSpec 是什么？
5 条 empirical repair hint 来自哪里？
59 条 legacy hint 应该怎样解释？
P10 是否改变 static filter 行为？
PassSpec 后续怎样演进？
```

本阶段仍然不做：

```text
two-swap
depth=3
beam/searcher
runtime benchmark
Alive2
PassInstrumentation
loop/inline/module pass
新 certificate
```

### 已完成内容

- [x] 新增 `src/ecpor/passspec_trust_report.py`。
- [x] 新增 `tests/test_passspec_trust_report.py`。
- [x] 扩展 `src/ecpor/manifest_builders.py`：
  - `build_passspec_trust_report_manifest()`
- [x] 扩展 `src/ecpor/manifest_cli.py`：
  - `passspec-trust-report`
- [x] 生成：
  - `docs/passspec_trust_report.md`
  - `docs/results/passspec_trust_report_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

RED 测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_passspec_trust_report.py tests/test_result_manifest.py::ResultManifestTests::test_builds_passspec_trust_report_manifest tests/test_result_manifest.py::ResultManifestTests::test_result_manifest_split_modules_keep_compatibility_exports -q
```

预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.passspec_trust_report'
ImportError: cannot import name 'build_passspec_trust_report_manifest'
AttributeError: module 'ecpor.result_manifest' has no attribute 'build_passspec_trust_report_manifest'
```

实现后相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_passspec_schema.py tests/test_passspec_audit.py tests/test_passspec_trust_report.py tests/test_result_manifest.py tests/test_static_filter.py -q
```

结果：

```text
32 passed in 1.03s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
127 passed in 22.87s
```

### 真实生成命令

生成 trust report：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.passspec_trust_report import main; raise SystemExit(main(['--passspec', 'configs/passspec.yaml', '--audit-manifest', 'docs/results/passspec_audit_manifest.json', '--out', 'docs/passspec_trust_report.md']))"
```

生成 tracked manifest：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.manifest_cli import main; raise SystemExit(main(['passspec-trust-report', '--out-manifest', 'docs/results/passspec_trust_report_manifest.json', '--passspec', 'configs/passspec.yaml', '--audit-manifest', 'docs/results/passspec_audit_manifest.json', '--trust-report', 'docs/passspec_trust_report.md', '--repo-root', '.', '--result-generated-from-commit', 'df2aa6c002fb6212c954e1949b42384c4ef737ed']))"
```

### P10.5 report 摘要

`docs/passspec_trust_report.md` 的核心结论：

```text
TotalPasses: 8
TotalHints: 64
RequiresAnyHints: 10
MayConsumeHints: 30
MayProduceHints: 24
ManualHints: 0
EmpiricalRepairHints: 5
LegacyHintsWithoutExplicitProvenance: 59
UnknownConfidenceHints: 59
HintsWithSupportCases: 5
```

5 条 empirical repair hint：

```text
sroa.may_produce.scalar_cfg_opportunity
sroa.may_produce.dce_opportunity
early-cse.may_produce.scalar_cfg_opportunity
simplifycfg.may_consume.scalar_cfg_opportunity
gvn.may_produce.scalar_cfg_opportunity
```

report 明确说明：

```text
PassSpec is an auditable metadata layer for static candidate generation.
These hints can prioritize dynamic AB/BA validation, but they never certify independence.
The support cases explain why a hint was added; they are not sufficient proof.
```

### manifest 关键字段

`docs/results/passspec_trust_report_manifest.json`：

```text
stage = P10.5
result_generated_from_commit = df2aa6c002fb6212c954e1949b42384c4ef737ed
ecpor_git_commit = df2aa6c002fb6212c954e1949b42384c4ef737ed
ecpor_git_dirty = false
report_only = true
metadata_only = true
static_filter_behavior_change = false
passspec_behavior_change = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
```

### 代码快照：trust report 生成器

`src/ecpor/passspec_trust_report.py` 从 `configs/passspec.yaml` 读取 normalized provenance，自动生成报告，不手写 5 条 hint 表。

```python
def build_trust_report(
    passspec_path: str | Path,
    *,
    audit_manifest_path: str | Path | None = None,
) -> str:
    passspec = load_normalized_passspec(passspec_path)
    rows = build_hint_rows(passspec)
    stats = summarize_hint_rows(rows, pass_count=len(passspec))
    empirical = [
        (pass_name, category, provenance)
        for pass_name, category, provenance in iter_hint_provenance(passspec)
        if provenance.source == "empirical_false_negative_repair"
    ]
```

报告开头固定写清边界：

```python
lines = [
    "# PassSpec Trust Report",
    "",
    "PassSpec is an auditable metadata layer for static candidate generation.",
    "It records conservative hints about possible pass opportunities and interactions.",
    "These hints can prioritize dynamic AB/BA validation, but they never certify independence.",
    "",
    "## Audit Summary",
    "",
]
```

### 代码快照：empirical repair hint 表

```python
lines.extend(
    [
        "",
        "## Empirical Repair Hints",
        "",
        "| hint | source | stage | support cases | meaning |",
        "| --- | --- | --- | ---: | --- |",
    ]
)
for pass_name, category, provenance in empirical:
    lines.append(
        "| {hint} | {source} | {stage} | {support_count} | {meaning} |".format(
            hint=_escape_table(f"{pass_name}.{category}.{provenance.name}"),
            source=_escape_table(provenance.source),
            stage=_escape_table(provenance.created_in_stage or "unknown"),
            support_count=len(provenance.support),
            meaning=_escape_table(provenance.note or "Empirical repair hint."),
        )
    )
```

### 代码快照：manifest builder

```python
def build_passspec_trust_report_manifest(
    *,
    passspec_path: str | Path,
    audit_manifest_path: str | Path,
    trust_report_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    return build_result_manifest(
        stage="P10.5",
        description="PassSpec trust report for paper-facing methods notes.",
        inputs={
            "passspec": passspec_path,
            "passspec_audit_manifest": audit_manifest_path,
        },
        outputs={
            "passspec_trust_report": trust_report_path,
        },
        tools={},
        summary=_filter_keys(
            _parse_key_value_report(trust_report_path),
            PASSSPEC_TRUST_REPORT_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "report_only": True,
                "metadata_only": True,
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

### data 保留情况

P10.5 没有新增 `data/` 目录产物。

新增 tracked 文档：

```text
docs/passspec_trust_report.md
docs/results/passspec_trust_report_manifest.json
```

原因：本阶段是 report-only / metadata-only，不运行 LLVM、不生成 certificate、不新增 search。

### 语义边界

1. P10.5 是方法说明，不是实验阶段。
2. `PassSpec` 仍然只是 high-recall candidate-generation metadata。
3. `support cases` 只说明 hint 为什么被加入，不构成充分性证明。
4. 59 条 legacy hint 被公开标记为没有显式 provenance，而不是隐藏。
5. hard pruning 仍然只来自 state-indexed certificate，不来自 static filter。

### 下一步

建议进入 P11：

```text
pass_registry_snapshot.py
```

P11 第一版只做：

```text
调用 opt --print-passes
保存 raw snapshot hash
检查 MVP 8 pass 是否存在：
  sroa
  early-cse
  instcombine
  simplifycfg
  reassociate
  gvn
  dce
  adce
```

仍然不要做：

```text
two-swap
depth=3
beam/searcher
runtime benchmark
Alive2
PassInstrumentation
loop/inline/module pass
更多 benchmark
```
