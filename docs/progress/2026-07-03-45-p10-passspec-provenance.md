# ECPOR 进度记录：P10 PassSpec provenance v2 与 audit

## 2026-07-03：把 PassSpec 从手工 hint 表升级为可审计 metadata 表

### 当前目标

P9-6 已经完成阶段报告和论文草稿入口。P10 不继续扩大搜索，也不新增实验，而是补强 static filter 的可信度边界：

```text
目标：PassSpec provenance v2
范围：metadata / audit only
不做：two-swap、depth=3、beam/searcher、runtime benchmark、Alive2、新 certificate
```

本阶段只做三件事：

1. 让 `configs/passspec.yaml` 同时支持旧 list schema 和新 provenance schema。
2. 给历史 false-negative repair 相关 hint 补 `source/confidence/support/created_in_stage/note`。
3. 生成 audit summary 和 tracked manifest，说明哪些 hint 有证据，哪些仍是 legacy 默认元数据。

### 已完成内容

- [x] 新增 `src/ecpor/passspec_schema.py`。
- [x] 新增 `src/ecpor/passspec_audit.py`。
- [x] `static_filter.py` 改为通过 normalized hint names 读取 PassSpec，分类逻辑不变。
- [x] `configs/passspec.yaml` 中 5 条经验性 repair hint 已带 provenance：
  - `sroa.may_produce.scalar_cfg_opportunity`
  - `sroa.may_produce.dce_opportunity`
  - `early-cse.may_produce.scalar_cfg_opportunity`
  - `simplifycfg.may_consume.scalar_cfg_opportunity`
  - `gvn.may_produce.scalar_cfg_opportunity`
- [x] 新增 `ecpor.result_manifest passspec-audit`。
- [x] 生成：
  - `data/outputs/passspec_audit/passspec_hint_summary.csv`
  - `data/outputs/passspec_audit/passspec_audit_report.md`
  - `docs/results/passspec_audit_manifest.json`
- [x] 更新 `README.md`、`docs/project_progress.md`、`docs/data_retention_manifest.md`。

### 验证结果

TDD RED 阶段：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_passspec_schema.py tests/test_passspec_audit.py tests/test_static_filter.py::StaticFilterTests::test_load_passspec_accepts_provenance_mapping_without_behavior_change tests/test_result_manifest.py::ResultManifestTests::test_builds_passspec_audit_manifest -q
```

预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.passspec_schema'
ModuleNotFoundError: No module named 'ecpor.passspec_audit'
ValueError: expected list, got dict
ImportError: cannot import name 'build_passspec_audit_manifest'
```

实现后相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_passspec_schema.py tests/test_passspec_audit.py tests/test_static_filter.py tests/test_result_manifest.py -q
```

结果：

```text
29 passed in 1.10s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
124 passed in 25.25s
```

### P10 audit 结果

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.passspec_audit import main; raise SystemExit(main(['--passspec', 'configs/passspec.yaml', '--out-dir', 'data/outputs/passspec_audit']))"
```

audit report：

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

manifest 生成命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.manifest_cli import main; raise SystemExit(main(['passspec-audit', '--out-manifest', 'docs/results/passspec_audit_manifest.json', '--passspec', 'configs/passspec.yaml', '--output-dir', 'data/outputs/passspec_audit', '--repo-root', '.', '--result-generated-from-commit', '9291115ab1f764c6a0b7bbced0d64b69ce594ec8']))"
```

manifest 关键字段：

```text
stage = P10
result_generated_from_commit = 9291115ab1f764c6a0b7bbced0d64b69ce594ec8
ecpor_git_dirty = false
metadata_only = true
static_filter_behavior_change = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
```

### 代码快照：PassSpec schema 规范化

`src/ecpor/passspec_schema.py` 的核心设计是：无论输入是旧 list schema、新 mapping schema，还是只给个别 hint 加 metadata 的混合 list，输出给 static filter 的仍然是字符串列表；provenance 只挂在 `_hint_provenance` 下。

```python
HINT_CATEGORIES = ("requires_any", "may_consume", "may_produce")

ALLOWED_SOURCES = {
    "manual_domain_knowledge",
    "empirical_false_negative_repair",
    "llvm_doc_hint",
    "source_static_hint",
    "generated_registry",
    "unknown_legacy",
}

@dataclass(frozen=True)
class HintProvenance:
    name: str
    source: str = "unknown_legacy"
    confidence: str = "unknown"
    support: tuple[dict[str, str], ...] = ()
    note: str = ""
    created_in_stage: str = ""
    explicit_provenance: bool = False
```

```python
def normalize_passspec(raw: Mapping[str, Any]) -> NormalizedPassSpec:
    passes = raw.get("passes", {})
    if not isinstance(passes, Mapping):
        raise ValueError("passspec must contain a mapping 'passes'")

    normalized: NormalizedPassSpec = {}
    for raw_name, raw_info in passes.items():
        pass_name = str(raw_name)
        if not isinstance(raw_info, Mapping):
            raise ValueError(f"passspec entry must be a mapping: {pass_name}")
        entry: dict[str, Any] = {
            "level": str(raw_info.get("level", "")),
            "tags": _string_list(raw_info.get("tags", []), context=f"{pass_name}.tags"),
        }
        provenance: dict[str, dict[str, HintProvenance]] = {}
        for category in HINT_CATEGORIES:
            names, records = normalize_hint_collection(
                raw_info.get(category, []),
                pass_name=pass_name,
                category=category,
            )
            entry[category] = names
            provenance[category] = records
        entry["_hint_provenance"] = provenance
        normalized[pass_name] = entry
    return normalized
```

### 代码快照：static filter 行为保持不变

`src/ecpor/static_filter.py` 只替换了 loader。`classify_pair()`、`_producer_consumer_reason()`、feature gate、candidate/low_priority/frozen 逻辑都没有改变。

```python
from .passspec_schema import load_normalized_passspec


def load_passspec(path: str | Path) -> PassSpec:
    return load_normalized_passspec(path)
```

行为兼容回归测试：

```python
decision = classify_pair(
    "a",
    "b",
    passspec,
    program_features={"num_instructions": 1},
    distance=1,
    window_size=1,
)

self.assertEqual(decision["decision"], "candidate")
self.assertEqual(decision["reason"], "producer_consumer")
```

### 代码快照：PassSpec audit

`src/ecpor/passspec_audit.py` 只读 YAML、写 CSV/Markdown，不调用 LLVM。

```python
def summarize_hint_rows(
    rows: Sequence[Mapping[str, str]],
    *,
    pass_count: int,
) -> dict[str, int]:
    category_counts = Counter(row.get("category", "") for row in rows)
    return {
        "TotalPasses": pass_count,
        "TotalHints": len(rows),
        "RequiresAnyHints": category_counts["requires_any"],
        "MayConsumeHints": category_counts["may_consume"],
        "MayProduceHints": category_counts["may_produce"],
        "ManualHints": sum(
            1 for row in rows if row.get("source") == "manual_domain_knowledge"
        ),
        "EmpiricalRepairHints": sum(
            1
            for row in rows
            if row.get("source") == "empirical_false_negative_repair"
        ),
        "LegacyHintsWithoutExplicitProvenance": sum(
            1 for row in rows if row.get("explicit_provenance") != "True"
        ),
        "UnknownConfidenceHints": sum(
            1 for row in rows if row.get("confidence") == "unknown"
        ),
        "HintsWithSupportCases": sum(
            1 for row in rows if row.get("support_cases", "") not in {"", "0"}
        ),
    }
```

### 代码快照：passspec.yaml provenance 示例

```yaml
sroa:
  may_produce:
    - scalar_cfg_opportunity:
        source: empirical_false_negative_repair
        confidence: medium
        created_in_stage: P3
        support:
          - program: testsuite_stanford_bubblesort
            pair: sroa,simplifycfg
            observed_label: not_certified_independent
          - program: testsuite_stanford_intmm
            pair: sroa,simplifycfg
            observed_label: not_certified_independent
        note: P3 static-filter repair for scalar producer to CFG simplification.
    - dce_opportunity:
        source: empirical_false_negative_repair
        confidence: medium
        created_in_stage: P8b-2
        support:
          - program: testsuite_misc_ffbench
            pair: sroa,adce
            observed_label: not_certified_independent
        note: P8b-2 repair; sroa can expose cleanup opportunities consumed by dce/adce.
```

### 语义边界

1. P10 是 metadata trust upgrade，不是算法升级。
2. static filter 的 `candidate / low_priority / frozen` 行为保持不变。
3. `source = empirical_false_negative_repair` 表示该 hint 来自历史 observed false negative 修复，不表示 LLVM 官方语义或形式化事实。
4. `support` 只记录当前项目已经观察到的支持案例，不构成充分性证明。
5. 仍有 59 条 hint 没有显式 provenance；audit 把这个缺口公开记录下来，避免把旧手工知识误读成已证明事实。

### data 保留情况

新增保留：

```text
data/outputs/passspec_audit/passspec_hint_summary.csv
data/outputs/passspec_audit/passspec_audit_report.md
docs/results/passspec_audit_manifest.json
```

原因：这三份文件是 P10 provenance audit 的最小可复查证据。它们体积小，且直接回答“哪些 PassSpec hint 有来源和 support，哪些仍是 legacy 默认”的问题。

### 下一步

建议进入 P10.5：

```text
PassSpec trust report / paper-facing methods note
```

目标是把 P10 audit 翻译成论文/报告可读的说明：

- 5 条 empirical repair hint 分别来自哪个阶段、哪个 false-negative case。
- 59 条 legacy hint 为什么仍不能宣称为 LLVM 官方事实。
- static filter 只做 candidate generation，不做 hard pruning。
- 后续若扩展 PassSpec，应先追加 provenance，再做行为评估。

当前仍不建议继续：

```text
two-swap
depth=3
beam/searcher
runtime benchmark
Alive2
PassInstrumentation
loop/inline/module pass
```
