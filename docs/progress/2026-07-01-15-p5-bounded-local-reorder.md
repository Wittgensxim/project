# ECPOR 进度记录：P5 bounded local reorder exploration

## 2026-07-01：P5 one-swap bounded local exploration

### 当前目标

本轮进入 P5，但仍然不做完整 searcher，也不做 code size evaluator。目标是把 P4 的 lazy validation 结果转化为一个很小的局部重排实验：

- 从 P4 attempts CSV 读取 anchor-adjacent validation 结果。
- 每个程序都保留一个 anchor pipeline candidate。
- 只对 `not_certified_independent` 的相邻 pair 生成 one-swap candidate。
- 对 `certified_independent` 记录 collapse evidence，不生成交换候选。
- 对 `low_priority_skipped` 记录 `frozen_by_static_filter`，不声明 independent，也不生成交换候选。
- 跑完整 candidate pipeline，记录 hard hash 和文本级 IR feature。
- 不使用 `best`、`optimal`、`performance improvement` 语义；本轮只是验证局部互动是否会传播到最终 pipeline 输出。

### 已完成内容

- [x] 修正 P4 报告格式：
  - 当 `dynamic_tests = 0` 时，`CertifiedPruningRatioDynamic` 现在显示为 `N/A`。
  - 避免第二轮全 cache hit 时把无意义的动态比例显示为 `0.00%`。
- [x] 新增 `src/ecpor/candidate_pipeline.py`：
  - 从 P4 attempts 构造 P5 candidates。
  - 输出 `candidates.csv`。
  - candidate CSV 字段为：
    `program,candidate_id,source,base_pipeline,candidate_pipeline,swap_index,pass_a,pass_b,prefix_state_hash,validation_label,cert_id,reason`
- [x] 新增 `src/ecpor/pipeline_runner.py`：
  - 运行完整 candidate pipeline。
  - 输出 `pipeline_runs.csv`。
  - 记录 `hard_hash`、`same_as_anchor`、`num_instructions`、`num_basic_blocks`、`num_load`、`num_store`、`num_branch`。
- [x] 新增 `src/ecpor/bounded_local_driver.py`：
  - 串联 candidate generation 与 pipeline runner。
  - 输出 `candidates.csv`、`pipeline_runs.csv`、`report.md`。
- [x] 新增测试：
  - `tests/test_candidate_pipeline.py`
  - `tests/test_pipeline_runner.py`
  - `tests/test_bounded_local_driver.py`
  - 更新 `tests/test_adjacent_swap_driver.py`

### TDD 验证

RED 测试命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_adjacent_swap_driver.py tests\test_candidate_pipeline.py tests\test_pipeline_runner.py tests\test_bounded_local_driver.py
```

初始失败符合预期：

```text
7 failed, 2 passed
AssertionError: 0.0 is not None
ModuleNotFoundError: No module named 'ecpor.candidate_pipeline'
ModuleNotFoundError: No module named 'ecpor.pipeline_runner'
ModuleNotFoundError: No module named 'ecpor.bounded_local_driver'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_adjacent_swap_driver.py tests\test_candidate_pipeline.py tests\test_pipeline_runner.py tests\test_bounded_local_driver.py
```

结果：

```text
9 passed in 1.16s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
60 passed in 6.27s
```

### P5 真实实验

输入使用 P4 final commit 后的第一轮 attempts：

```text
data/outputs/lazy_validation_p4_e83c409_first.csv
```

运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver --program-preset stanford-8 --pipeline configs\pipeline_scalar.yaml --attempts-csv data\outputs\lazy_validation_p4_e83c409_first.csv --out data\outputs\bounded_local_p5_final --opt E:\llvm\build\bin\opt.exe --timeout-sec 30
```

输出路径：

```text
data/outputs/bounded_local_p5_final/candidates.csv
data/outputs/bounded_local_p5_final/pipeline_runs.csv
data/outputs/bounded_local_p5_final/report.md
```

结果摘要：

```text
P4 attempted_adjacent_swaps: 56
P4 candidate_swaps: 48
P4 low_priority_skipped: 8
P4 dynamic_tests: 48
P4 certified_independent: 32
P4 not_certified_independent: 16
P4 run_failed: 0

anchor_candidates: 8
single_swap_candidates: 16
collapsed_certified_independent: 32
frozen_by_static_filter: 8
invalid_run_failed: 0

pipeline_runs: 24
pipeline_run_failed: 0
same_as_anchor: 8
different_from_anchor: 16
```

说明：

- 8 个 anchor candidate 对应 8 个 Stanford 程序。
- 16 个 single-swap candidate 正好来自 P4 的 16 个 `not_certified_independent`。
- 32 个 `certified_independent` 没有生成候选，只作为已折叠证据。
- 8 个 `low_priority_skipped` 没有生成候选，也没有被计为 independence。
- 24 次完整 pipeline 运行全部成功。
- 当前这批 one-swap candidate 的最终 IR hard hash 全部不同于各自 anchor；这只说明“局部未证明交换在最终 pipeline 输出上仍可观察到差异”，不代表性能或代码体积优劣。

### 运行过的例子

`testsuite_stanford_bubblesort` 的 anchor pipeline：

```text
sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce
```

P4 中 `sroa,early-cse` 在 input state 上是 `not_certified_independent`，所以 P5 生成一个 one-swap candidate：

```text
early-cse,sroa,instcombine,simplifycfg,reassociate,gvn,dce,adce
```

P5 跑完整 pipeline 后：

```text
testsuite_stanford_bubblesort__swap_0__sroa__early-cse
same_as_anchor: False
num_instructions: 102
num_basic_blocks: 5
```

同一程序的 `instcombine,simplifycfg` 在 P4 中是 `certified_independent`，所以 P5 不生成交换候选，只记录：

```text
collapsed_certified_independent
```

`simplifycfg,reassociate` 被 static filter 判为 low priority 并跳过动态测试，所以 P5 记录：

```text
frozen_by_static_filter
```

它也不生成交换候选，不计入 pruning，不计入 independent。

### 本次代码快照：P4 ratio 修正

```python
def summarize_attempts(attempts: Sequence[AdjacentSwapAttempt]) -> dict[str, Any]:
    ...
    return {
        ...
        "certified_pruning_ratio_dynamic": (
            certified / dynamic_tests if dynamic_tests else None
        ),
        ...
    }


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100.0:.2f}%"
```

### 本次代码快照：`src/ecpor/candidate_pipeline.py`

```python
@dataclass(frozen=True)
class CandidatePipeline:
    program: str
    candidate_id: str
    source: str
    base_pipeline: str
    candidate_pipeline: str
    swap_index: int | None
    pass_a: str
    pass_b: str
    prefix_state_hash: str
    validation_label: str
    cert_id: str
    reason: str


def build_candidate_pipelines(
    *,
    programs: Sequence[str],
    anchor_passes: Sequence[str],
    attempts: Sequence[dict[str, str]],
) -> CandidateGeneration:
    ...
    for row in attempts:
        ...
        if label == "not_certified_independent":
            candidate = _single_swap_candidate(base_passes, base_pipeline, row)
            ...
            candidates.append(candidate)
            counts["single_swap"] += 1
        elif label == "certified_independent":
            counts["collapsed_certified_independent"] += 1
        elif action == "skipped_low_priority" or row.get("static_decision") == "low_priority":
            counts["frozen_by_static_filter"] += 1
```

### 本次代码快照：`src/ecpor/pipeline_runner.py`

```python
def run_pipeline_candidate(
    input_ir: str | Path,
    candidate: CandidatePipeline,
    *,
    opt_path: OptPath,
    output_dir: str | Path,
    anchor_hash: str | None = None,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> PipelineRunRecord:
    output_path = output_root / f"{_safe_name(candidate.candidate_id)}.ll"
    pipeline = _pipeline(nesting, _split_pipeline(candidate.candidate_pipeline))
    result = run_opt(...)
    features = _scan_features_if_available(output_path, result.hard_hash)
    same_as_anchor = result.hard_hash == anchor_hash if anchor_hash is not None else (
        candidate.source == "anchor" and result.hard_hash is not None
    )
    return PipelineRunRecord(...)
```

### 本次代码快照：`src/ecpor/bounded_local_driver.py`

```python
def run_bounded_local_exploration(
    *,
    programs: Sequence[Program],
    anchor_passes: Sequence[str],
    attempts_csv: str | Path,
    opt_path: OptPath,
    output_dir: str | Path,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> BoundedLocalRun:
    attempts = load_attempts_csv(attempts_csv)
    generation = build_candidate_pipelines(...)
    write_candidates_csv(output_root / "candidates.csv", generation.candidates)

    records: list[PipelineRunRecord] = []
    anchor_hashes: dict[str, str | None] = {}
    for candidate in generation.candidates:
        if candidate.source == "anchor":
            record = run_pipeline_candidate(...)
            anchor_hashes[candidate.program] = record.hard_hash
        else:
            record = run_pipeline_candidate(..., anchor_hash=anchor_hashes.get(candidate.program))
        records.append(record)

    write_pipeline_runs_csv(output_root / "pipeline_runs.csv", records)
    report = build_bounded_local_report(summary, generation, records)
```

### 风险与备注

- P5 只探索 anchor 的一步相邻交换，不是 BFS/DFS/beam/MCTS，也不是完整 phase ordering search。
- `different_from_anchor` 只比较最终 IR hard hash，不代表代码大小、速度或可执行文件质量。
- `pipeline_runner.py` 当前使用文本级 IR feature scanner，后续 code size evaluator 会另建更严格的对象文件/size 测量。
- `low_priority_skipped` 仍然只是静态过滤下的冻结默认顺序，不是 certificate。
- P5 使用 P4 final commit `e83c409...` 的 attempts CSV；本轮提交后已用最终代码复跑 `bounded_local_p5_final` 输出。

### 下一步

- 提交 P5 实现后，复跑全量测试和 P5 final。
- 下一阶段建议进入 P6：code size evaluator 的最小版，只比较 anchor 与 P5 single-swap candidates 的对象大小。
- 仍暂不进入完整 searcher、Alive2、loop pass、inline 或 O2/O3。
