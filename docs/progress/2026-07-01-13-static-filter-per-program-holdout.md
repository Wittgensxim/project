# ECPOR 进度记录：P3.5 per-program static filter 与 hold-out 验证

## 2026-07-01：P3.5 静态过滤泛化验证

### 当前目标

本轮不进入完整 searcher，而是先完成 P3.5 收尾：

- 将 static filter 从 aggregate program features 扩展到 per-program mode。
- 增加 5 个 Stanford hold-out 输入，形成 `8 programs x 28 pass pairs = 224 certificates`。
- 分开报告 calibration 和 hold-out 的静态过滤 recall。
- 如果 hold-out 出现 false negative，先记录调整前结果，再根据证据保守更新 `passspec.yaml`，最后复跑报告。

### 已完成内容

- [x] 新增 `src/ecpor/static_filter.py` 的 per-program 决策路径：
  - `build_static_filter_decisions_for_programs()`
  - `scan_program_features()`
  - per-program `evaluate_static_filter()`
  - `program_groups` 报告，用于区分 Calibration 与 Hold-out
- [x] `static_filter.py` CLI 新增：
  - `--mode aggregate`
  - `--mode per-program`
  - `--program-preset stanford-8`
- [x] `src/ecpor/batch_certificates.py` 新增：
  - `HOLDOUT_STANFORD_PROGRAMS`
  - `STANFORD_8_PROGRAMS`
  - CLI preset `stanford-8x28`
- [x] 从 `E:\llvm-test-suite\SingleSource\Benchmarks\Stanford` 生成 5 个 hold-out LLVM IR：
  - `data/inputs/testsuite_stanford_oscar.ll`
  - `data/inputs/testsuite_stanford_puzzle.ll`
  - `data/inputs/testsuite_stanford_queens.ll`
  - `data/inputs/testsuite_stanford_quicksort.ll`
  - `data/inputs/testsuite_stanford_towers.ll`
- [x] 运行 8x28 真实 certificate matrix。
- [x] 生成 per-program static filter CSV 和报告：
  - `data/outputs/static_filter_decisions_per_program.csv`
  - `data/outputs/static_filter_report_per_program.md`
- [x] 更新 `README.md` 和 `docs/project_progress.md`。

### 8x28 certificate matrix 结果

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.batch_certificates import main; raise SystemExit(main(['--preset','stanford-8x28','--opt','E:/llvm/build/bin/opt.exe','--out','data/outputs/pair_tests','--cert-dir','data/certs/pair_tests','--summary','data/outputs/cert_summary.csv','--env-id','3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e','--llvm-version','23.0.0git']))"
```

结果：

```text
total=224 reproduced=224 hard_false_independent=0 certified_feature_mismatch=0
certified_independent=144
not_certified_independent=80
```

summary report 关键结果：

```text
Total certificates: 224
Reproduced: 224 / 224 = 100.00%
HardFalseIndependent: 0
CertifiedFeatureMismatchCount: 0

Label counts:
  certified_independent: 144
  not_certified_independent: 80
  run_failed: 0

Certificates with any failure: 0 / 224
Failure directions:
  total_directions: 448
  no_failure: 448 / 448
```

### 调整前：hold-out 暴露 1 个 false negative

第一次 per-program static filter 评估命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.static_filter import main; raise SystemExit(main(['--program-preset','stanford-8','--mode','per-program','--observed-summary','data/outputs/cert_summary.csv','--out-csv','data/outputs/static_filter_decisions_per_program.csv','--out-report','data/outputs/static_filter_report_per_program.md','--window-size','7']))"
```

调整前结果：

```text
Static decisions:
  candidate: 176
  low_priority: 48
  frozen: 0

Static filter quality:
  StaticCandidateRecall: 98.75%
  MacroStaticCandidateRecall: 99.04%
  StaticFalseNegativeObserved: 1
  StaticCandidateReduction: 21.43%

Program groups:
  Calibration:
    observed_interacting: 22
    false_negative: 0
    micro_recall: 100.00%
    macro_recall: 100.00%
  Hold-out:
    observed_interacting: 58
    false_negative: 1
    micro_recall: 98.28%
    macro_recall: 98.46%

False negatives:
  early-cse,simplifycfg on testsuite_stanford_queens
```

对应 evidence：

```text
testsuite_stanford_queens,early-cse,simplifycfg,low_priority,no_static_hint
testsuite_stanford_queens,early-cse,simplifycfg,not_certified_independent
feature_delta: num_instructions=-1;num_load=-1
```

这个结果说明：旧 `passspec.yaml` 在 calibration set 上没有漏报，但在 hold-out 的 Queens 上暴露了一个 scalar/CSE 与 CFG 简化之间的交互。

### passspec 调整

本次只做保守放宽，不把 static filter 变成证明系统。调整为：

```yaml
  early-cse:
    level: function
    requires_any:
      - has_load_store
      - has_call
      - instruction
    may_consume:
      - repeated_expr
      - load_store
      - scalar_value
      - early_cse_opportunity
    may_produce:
      - dead_instruction
      - simplified_expr
      - scalar_cfg_opportunity
```

语义：`early-cse` 可能简化 load 或 scalar expression，从而改变后续 `simplifycfg` 可观察到的 CFG 简化机会。这个 hint 只影响 candidate/low_priority 排序，不产生 hard pruning。

### 调整后：calibration 与 hold-out 都归零 false negative

调整后重新运行 per-program static filter，结果：

```text
Static decisions:
  candidate: 184
  low_priority: 40
  frozen: 0

Static filter quality:
  StaticCandidateRecall: 100.00%
  MacroStaticCandidateRecall: 100.00%
  StaticFalseNegativeObserved: 0
  StaticCandidateReduction: 17.86%

Program groups:
  Calibration:
    programs: 3
    observed_interacting: 22
    false_negative: 0
    micro_recall: 100.00%
    macro_recall: 100.00%
    candidate_reduction: 17.86%
  Hold-out:
    programs: 5
    observed_interacting: 58
    false_negative: 0
    micro_recall: 100.00%
    macro_recall: 100.00%
    candidate_reduction: 17.86%

False negatives: none
```

代价：candidate 每个程序从 22/28 增加到 23/28，过滤 reduction 从 `21.43%` 降到 `17.86%`。这是有意的保守放宽，因为当前 static filter 的第一优先级是高召回，而不是激进剪枝。

### TDD 验证

本轮新增 RED 测试覆盖：

- per-program 决策可以因程序特征不同而不同。
- per-program evaluation 按 `(program, pair)` 匹配 observed matrix。
- `stanford-8` 程序集合包含 3 个 calibration 和 5 个 hold-out。
- `static_filter.py --mode per-program` 输出 CSV 时带 `program` 字段。
- 真实 `passspec.yaml` 必须把 `early-cse,simplifycfg` 判为 `candidate`。

验证命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_static_filter.py tests\test_batch_certificates.py -q
```

结果：

```text
13 passed in 1.19s
```

全量测试命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
42 passed in 3.39s
```

### 本次代码快照：`src/ecpor/batch_certificates.py` hold-out preset

```python
HOLDOUT_STANFORD_PROGRAMS: list[Program] = [
    ("testsuite_stanford_oscar", "data/inputs/testsuite_stanford_oscar.ll"),
    ("testsuite_stanford_puzzle", "data/inputs/testsuite_stanford_puzzle.ll"),
    ("testsuite_stanford_queens", "data/inputs/testsuite_stanford_queens.ll"),
    ("testsuite_stanford_quicksort", "data/inputs/testsuite_stanford_quicksort.ll"),
    ("testsuite_stanford_towers", "data/inputs/testsuite_stanford_towers.ll"),
]

STANFORD_8_PROGRAMS: list[Program] = [
    *DEFAULT_STANFORD_PROGRAMS,
    *HOLDOUT_STANFORD_PROGRAMS,
]
```

```python
def _preset_pass_pairs(preset: str) -> list[PassPair]:
    if preset == "stanford-3x3":
        return STANFORD_3X3_PASS_PAIRS
    if preset in {"stanford-3x28", "stanford-8x28"}:
        return FULL_SCALAR_PASS_PAIRS
    return DEFAULT_PASS_PAIRS


def _preset_programs(preset: str) -> list[Program]:
    if preset == "stanford-8x28":
        return STANFORD_8_PROGRAMS
    return DEFAULT_STANFORD_PROGRAMS
```

### 本次代码快照：`src/ecpor/static_filter.py` per-program 决策

```python
def build_static_filter_decisions_for_programs(
    passes: Sequence[str],
    passspec: PassSpec,
    *,
    program_features_by_name: dict[str, dict[str, Any]],
    window_size: int,
) -> list[DecisionRow]:
    rows: list[DecisionRow] = []
    for program, program_features in program_features_by_name.items():
        for row in build_static_filter_decisions(
            passes,
            passspec,
            program_features=program_features,
            window_size=window_size,
        ):
            rows.append({"program": program, **row})
    return rows
```

### 本次代码快照：`src/ecpor/static_filter.py` per-program 评估入口

```python
def evaluate_static_filter(
    decisions: Sequence[DecisionRow],
    observed_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    if any(row.get("program") for row in decisions):
        return _evaluate_static_filter_per_program(decisions, observed_rows)
    return _evaluate_static_filter_aggregate(decisions, observed_rows)
```

### 本次代码快照：`src/ecpor/static_filter.py` CSV 字段选择

```python
def write_decisions_csv(path: str | Path, rows: Sequence[DecisionRow]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        PROGRAM_DECISION_FIELDS
        if any("program" in row for row in rows)
        else DECISION_FIELDS
    )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
```

### 本次代码快照：`tests/test_static_filter.py` hold-out 回归点

```python
early_cse_simplifycfg = classify_pair(
    "early-cse",
    "simplifycfg",
    passspec,
    program_features=features,
    distance=2,
    window_size=7,
)

self.assertEqual(early_cse_simplifycfg["decision"], "candidate")
```

### 风险与备注

- 当前 `StaticCandidateRecall = 100%` 只覆盖 8 个 Stanford 输入的初始 IR state，不能外推到所有程序或 pipeline prefix state。
- per-program mode 是当前主报告模式；aggregate mode 仍可用于粗略 sanity check，但不应作为 P3.5 主结论。
- `low_priority` 仍然不表示 independent，只表示当前静态 hint 下优先级较低。
- `candidate` 也不表示 dependent，只表示值得动态 certificate validation。
- 本轮为了消除 hold-out false negative，牺牲了一部分 reduction；这是符合 high-recall static filter 目标的。

### 下一步

- 进入 P4 minimal lazy validation / local search。
- 优先做：
  - `certificate_db.py`
  - `lazy_validator.py`
  - 小窗口相邻 swap 的 on-demand certificate reuse
- 暂不做：
  - 完整 searcher
  - code size evaluator
  - Alive2
  - loop pass
  - inline
  - 完整 O2/O3
