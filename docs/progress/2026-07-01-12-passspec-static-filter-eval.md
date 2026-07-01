# ECPOR 进度记录：P3 passspec 与 static filter 评估

## 2026-07-01：P3 high-recall static filter

### 当前目标

按最新 review 要求，本轮进入 P3，但仍不做 searcher。目标是建立第一版高召回静态过滤层：

- 新增 `configs/passspec.yaml`，作为 8-pass function scalar MVP pipeline 的 high-recall hint。
- 新增 `src/ecpor/static_filter.py`，输出 `candidate / low_priority / frozen`，不输出 hard proof。
- 为 8 个 pass 生成完整 unordered pair universe：`8 * 7 / 2 = 28`。
- 跑 3 个 Stanford 输入 × 28 个 pair 的 full matrix，共 84 个 certificate。
- 用 full matrix 评估 static filter 的 observed recall 和 reduction。

### 已完成内容

- [x] 新增 `configs/passspec.yaml`：
  - 覆盖 `sroa`
  - 覆盖 `early-cse`
  - 覆盖 `instcombine`
  - 覆盖 `simplifycfg`
  - 覆盖 `reassociate`
  - 覆盖 `gvn`
  - 覆盖 `dce`
  - 覆盖 `adce`
- [x] 新增 `src/ecpor/static_filter.py`：
  - `load_pipeline_config()`
  - `load_passspec()`
  - `enumerate_unordered_pairs()`
  - `classify_pair()`
  - `build_static_filter_decisions()`
  - `aggregate_program_features()`
  - `evaluate_static_filter()`
  - `build_static_filter_report()`
- [x] 输出静态过滤 CSV：
  - `data/outputs/static_filter_decisions.csv`
- [x] 输出静态过滤评估报告：
  - `data/outputs/static_filter_report.md`
- [x] 扩展 `src/ecpor/batch_certificates.py`：
  - 新增 `SCALAR_PIPELINE_PASSES`
  - 新增 `FULL_SCALAR_PASS_PAIRS`
  - 新增 CLI preset `stanford-3x28`
- [x] 更新 `README.md`：
  - 记录 3×28 matrix 命令
  - 记录 static filter 命令
- [x] 更新 `docs/project_progress.md` 第 12 个进度索引。

### 静态过滤语义边界

`static_filter.py` 只生成 candidate hints，不生成 certificate，也不做 hard pruning。

当前决策只允许：

```text
candidate
low_priority
frozen
```

当前决策不允许：

```text
certified_independent
dependent
```

hard pruning 仍然只依赖 AB/BA hard canonical hash equality 与 certificate reproduction。

### TDD 验证

RED 测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_static_filter.py -q
```

初始失败符合预期：

```text
6 failed
```

失败原因：

- `src/ecpor/static_filter.py` 尚不存在。
- `configs/passspec.yaml` 尚不存在。
- batch 生成器尚无 `FULL_SCALAR_PASS_PAIRS`。

实现后局部测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_static_filter.py tests/test_batch_certificates.py -q
```

结果：

```text
9 passed in 1.17s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
39 passed in 2.93s
```

### 3×28 full matrix

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.batch_certificates import DEFAULT_STANFORD_PROGRAMS, FULL_SCALAR_PASS_PAIRS, run_certificate_matrix, summarize_rows; rows=run_certificate_matrix(programs=DEFAULT_STANFORD_PROGRAMS, pass_pairs=FULL_SCALAR_PASS_PAIRS, opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests', cert_dir='data/certs/pair_tests', summary_csv='data/outputs/cert_summary.csv', env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e', llvm_version='23.0.0git'); print(summarize_rows(rows)); print(len(rows))"
```

结果：

```text
{'not_certified_independent': 22, 'certified_independent': 62, 'total': 84, 'reproduced': 84, 'hard_false_independent': 0, 'certified_feature_mismatch': 0}
84
```

summary report 关键输出：

```text
Total certificates: 84
Reproduced: 84 / 84 = 100.00%
HardFalseIndependent: 0
CertifiedFeatureMismatchCount: 0

Label counts:
  certified_independent: 62
  not_certified_independent: 22
  run_failed: 0

Certificates with any failure: 0 / 84
Failure directions:
  total_directions: 168
  no_failure: 168 / 168
```

### Static filter 评估

第一次评估发现 3 个 observed false negative：

```text
sroa,simplifycfg on testsuite_stanford_bubblesort
simplifycfg,gvn on testsuite_stanford_bubblesort
sroa,simplifycfg on testsuite_stanford_intmm
```

修复方式：

- 在 `sroa.may_produce` 中加入 `scalar_cfg_opportunity`。
- 在 `gvn.may_produce` 中加入 `scalar_cfg_opportunity`。
- 在 `simplifycfg.may_consume` 中加入 `scalar_cfg_opportunity`。
- 新增回归测试，要求真实 passspec 将 `sroa,simplifycfg` 与 `simplifycfg,gvn` 判为 `candidate`。

校准后运行：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.static_filter import main; raise SystemExit(main(['--program-preset','stanford-3','--observed-summary','data/outputs/cert_summary.csv','--out-csv','data/outputs/static_filter_decisions.csv','--out-report','data/outputs/static_filter_report.md','--window-size','7']))"
```

最终结果：

```text
Pipeline: mvp_function_scalar
Pass count: 8
All unordered pairs: 28
Programs: 3
Full matrix certificates: 84

Static decisions:
  candidate: 22
  low_priority: 6
  frozen: 0

Observed matrix:
  certified_independent: 62
  not_certified_independent: 22
  run_failed: 0
  reproduced: 84 / 84
  HardFalseIndependent: 0
  CertifiedFeatureMismatchCount: 0

Static filter quality:
  StaticCandidateRecall: 100.00%
  StaticFalseNegativeObserved: 0
  StaticCandidateReduction: 21.43%

False negatives: none
```

### 风险与备注

- `passspec.yaml` 是 high-recall hint，不是 formal semantics。
- `static_filter.py` 的 `candidate` 只表示“值得动态测试”，不表示 dependent。
- `low_priority` 只表示“当前静态 hint 下优先级较低”，不表示 independent。
- 当前 recall 只是在 3 个 Stanford observed input states 上评估得到，不能推广成全局结论。
- 为消除 observed false negative 而加入的 `scalar_cfg_opportunity` 是经验性 hint，后续需要在更大输入集合上继续校准。

### 下一步

- 暂不进入完整 searcher。
- 可以先做 lazy validation / local search 的最小接口设计。
- 如果继续推进 P3，应保留当前验收指标：
  - `HardFalseIndependent = 0`
  - `CertificateReproductionRate = 100%`
  - `StaticFalseNegativeObserved = 0`
  - `StaticCandidateRecall = 100%`
- 如果后续扩大 benchmark，先重跑 static filter evaluation；出现 false negative 时优先修 `passspec.yaml`。

### 本次代码快照：`configs/passspec.yaml` 关键片段

```yaml
passes:
  sroa:
    level: function
    requires_any:
      - has_alloca
    may_consume:
      - alloca
      - aggregate
      - memory_access
    may_produce:
      - scalar_value
      - simplified_load_store
      - load_store
      - scalar_cfg_opportunity
      - instcombine_opportunity
      - early_cse_opportunity
    tags:
      - scalar
      - memory

  simplifycfg:
    level: function
    requires_any:
      - has_branch
    may_consume:
      - branch
      - phi
      - unreachable
      - cfg
      - scalar_cfg_opportunity
    may_produce:
      - simplified_cfg
      - instcombine_opportunity
      - dce_opportunity
    tags:
      - cfg

  gvn:
    level: function
    requires_any:
      - instruction
    may_consume:
      - repeated_expr
      - load_store
      - scalar_value
      - simplified_expr
    may_produce:
      - dead_instruction
      - simplified_expr
      - dce_opportunity
      - scalar_cfg_opportunity
    tags:
      - scalar
      - memory
      - cse
```

### 本次代码快照：`src/ecpor/static_filter.py` 分类核心

```python
def classify_pair(
    pair_a: str,
    pair_b: str,
    passspec: PassSpec,
    *,
    program_features: dict[str, Any],
    distance: int,
    window_size: int,
) -> DecisionRow:
    spec_a = passspec[pair_a]
    spec_b = passspec[pair_b]
    level_a = str(spec_a["level"])
    level_b = str(spec_b["level"])
    shared_tags = sorted(set(spec_a["tags"]) & set(spec_b["tags"]))
    producer_consumer = _producer_consumer_reason(pair_a, pair_b, spec_a, spec_b)
    gate_a = _feature_gate(pair_a, spec_a, program_features)
    gate_b = _feature_gate(pair_b, spec_b, program_features)

    base = {
        "pair_a": pair_a,
        "pair_b": pair_b,
        "level_a": level_a,
        "level_b": level_b,
        "shared_tags": ",".join(shared_tags),
        "producer_consumer": producer_consumer,
        "program_feature_gate": _format_feature_gate(gate_a, gate_b),
    }

    if level_a != level_b:
        return {
            **base,
            "decision": "frozen",
            "reason": f"level_mismatch:{level_a}!={level_b}",
        }
    if not gate_a[0] or not gate_b[0]:
        return {
            **base,
            "decision": "low_priority",
            "reason": "feature_gate_missing",
        }
    if producer_consumer:
        return {**base, "decision": "candidate", "reason": "producer_consumer"}
    if shared_tags and distance <= window_size:
        return {**base, "decision": "candidate", "reason": "shared_tags_in_window"}
    return {**base, "decision": "low_priority", "reason": "no_static_hint"}
```

### 本次代码快照：`src/ecpor/static_filter.py` 评估核心

```python
def evaluate_static_filter(
    decisions: Sequence[DecisionRow],
    observed_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    decision_by_pair = {
        _pair_key(row["pair_a"], row["pair_b"]): row["decision"] for row in decisions
    }
    label_counts = Counter(row.get("label", "") for row in observed_rows)
    candidate_pairs = sum(1 for row in decisions if row["decision"] == "candidate")
    low_priority_pairs = sum(1 for row in decisions if row["decision"] == "low_priority")
    frozen_pairs = sum(1 for row in decisions if row["decision"] == "frozen")
    observed_interacting = [
        row for row in observed_rows if row.get("label") == "not_certified_independent"
    ]
    candidate_observed_interacting = [
        row
        for row in observed_interacting
        if decision_by_pair.get(_pair_key(row.get("pair_a", ""), row.get("pair_b", "")))
        == "candidate"
    ]
    false_negative_rows = [
        row
        for row in observed_interacting
        if decision_by_pair.get(_pair_key(row.get("pair_a", ""), row.get("pair_b", "")))
        != "candidate"
    ]
    all_pairs = len(decisions)
    observed_count = len(observed_interacting)
    recall = (
        len(candidate_observed_interacting) / observed_count
        if observed_count
        else 1.0
    )
    reduction = 1.0 - (candidate_pairs / all_pairs) if all_pairs else 0.0
```

### 本次代码快照：`src/ecpor/batch_certificates.py` 3×28 preset

```python
SCALAR_PIPELINE_PASSES = [
    "sroa",
    "early-cse",
    "instcombine",
    "simplifycfg",
    "reassociate",
    "gvn",
    "dce",
    "adce",
]

FULL_SCALAR_PASS_PAIRS: list[PassPair] = [
    (left, right) for left, right in combinations(SCALAR_PIPELINE_PASSES, 2)
]


def _preset_pass_pairs(preset: str) -> list[PassPair]:
    if preset == "stanford-3x3":
        return STANFORD_3X3_PASS_PAIRS
    if preset == "stanford-3x28":
        return FULL_SCALAR_PASS_PAIRS
    return DEFAULT_PASS_PAIRS
```
