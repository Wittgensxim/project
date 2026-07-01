# ECPOR 进度记录：P6 code size evaluator 最小版

## 2026-07-01：从 IR 差异推进到 object code size 差异

### 当前目标

本轮进入 P6，但仍然不做完整 searcher、不做 runtime benchmark、不做多步 swap。目标只回答一个问题：

```text
P5 中最终 IR hard hash 不同的 one-swap candidates，是否会传导到 object code size 差异？
```

本轮比较范围固定为：

- P5 的 8 个 anchor candidates。
- P5 的 16 个 single-swap candidates。
- 使用 `llc -filetype=obj` 把最终 `.ll` 编译成 `.o`。
- 使用 `llvm-size` 读取 object size。
- 只计算相对本程序 anchor 的 text/total size delta。

### 已完成内容

- [x] 修正 P5 report 语义：
  - 保留总 `same_as_anchor` / `different_from_anchor`。
  - 新增 `anchor_runs`、`single_swap_runs`。
  - 新增 `single_swap_same_as_anchor`、`single_swap_different_from_anchor`，避免把 anchor 自身的 `same_as_anchor` 误读成 candidate 相同。
- [x] 增强 P5 provenance：
  - `ecpor_git_commit`
  - `ecpor_git_dirty`
  - `env_id`
  - `llvm_version`
  - `normalizer_version`
  - `attempts_csv`
  - `attempts_csv_sha256`
  - `pipeline_config`
  - `pipeline_config_sha256`
- [x] 新增 P5 invariant 检查：
  - single-swap candidate 必须来自 `not_certified_independent`。
  - candidate pass multiset 必须等于 anchor。
  - single-swap candidate 必须只做一次指定相邻交换。
  - anchor candidate 必须与 base pipeline 相同。
- [x] 新增 `src/ecpor/object_size_runner.py`：
  - 编译 `.ll` 到 `.o`。
  - 调用 `llvm-size`。
  - 解析标准 `text data bss dec hex filename` 输出。
  - 显式记录 `compile_failure_kind` 和 `size_failure_kind`。
- [x] 新增 `src/ecpor/code_size_evaluator.py`：
  - 消费 P5 `candidates.csv`、`pipeline_runs.csv` 和 `pipeline_outputs/*.ll`。
  - 输出 `object_size.csv`。
  - 输出 `code_size_report.md`。
  - 按 program anchor 计算 single-swap text/total delta。
- [x] 新增测试：
  - `tests/test_object_size_runner.py`
  - `tests/test_code_size_evaluator.py`
  - 更新 `tests/test_candidate_pipeline.py`
  - 更新 `tests/test_bounded_local_driver.py`

### TDD 验证

RED 测试命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_candidate_pipeline.py tests\test_bounded_local_driver.py tests\test_object_size_runner.py tests\test_code_size_evaluator.py
```

初始失败符合预期：

```text
7 failed, 2 passed
ImportError: cannot import name 'validate_candidate_invariants'
TypeError: run_bounded_local_exploration() got an unexpected keyword argument 'env_id'
ModuleNotFoundError: No module named 'ecpor.object_size_runner'
ModuleNotFoundError: No module named 'ecpor.code_size_evaluator'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_candidate_pipeline.py tests\test_bounded_local_driver.py tests\test_object_size_runner.py tests\test_code_size_evaluator.py
```

结果：

```text
9 passed in 0.57s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
66 passed in 7.33s
```

### P5 provenance 复跑

P5 复跑命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver --program-preset stanford-8 --pipeline configs\pipeline_scalar.yaml --attempts-csv data\outputs\lazy_validation_p4_e83c409_first.csv --out data\outputs\bounded_local_p5_p6_final --opt E:\llvm\build\bin\opt.exe --timeout-sec 30
```

P5 关键结果：

```text
ecpor_git_commit: final P6 commit
ecpor_git_dirty: False
attempts_csv_sha256: ceada53bcb557dfd9a4d9c8217f652b7995f158154d4df5827a1a340acffb777
pipeline_config_sha256: 798fafb5e73bd26036dec30fd6d9592ec4ebf0b51a17bd5d73f81dc3acb8f2cf
anchor_runs: 8
single_swap_runs: 16
single_swap_same_as_anchor: 0
single_swap_different_from_anchor: 16
pipeline_run_failed: 0
```

说明：

- P5 仍只生成 16 个 one-swap candidates。
- `certified_independent` 继续只作为 collapse evidence。
- `low_priority_skipped` 继续只作为 frozen evidence。
- 现在报告不会再把 8 个 anchor 自身的 `same_as_anchor` 误读为 8 个 candidate 与 anchor 相同。

### P6 真实实验

P6 运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.code_size_evaluator --p5-dir data\outputs\bounded_local_p5_p6_final --out data\outputs\code_size_p6_final --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

输出路径：

```text
data/outputs/code_size_p6_final/object_size.csv
data/outputs/code_size_p6_final/code_size_report.md
data/outputs/code_size_p6_final/object_outputs/
```

结果摘要：

```text
Programs: 8
Anchor object builds: 8
Single-swap object builds: 16
Object builds attempted: 24
ObjectBuildFailed: 0
SizeParseFailed: 0
Anchor sizes available: 8
Single-swap sizes available: 16
CodeSizeDeltaVsAnchor computed: 16

smaller_text: 1
equal_text: 15
larger_text: 0
average_text_delta_pct: -0.2751
median_text_delta_pct: 0.0000
min_text_delta_pct: -4.4017
max_text_delta_pct: 0.0000
```

按相邻 pair 汇总：

```text
early-cse,instcombine:
  candidates=4 smaller=0 equal=4 larger=0 avg_text_delta_pct=0.0000

instcombine,simplifycfg:
  candidates=4 smaller=1 equal=3 larger=0 avg_text_delta_pct=-1.1004

sroa,early-cse:
  candidates=8 smaller=0 equal=8 larger=0 avg_text_delta_pct=0.0000
```

唯一 text size 变小的例子：

```text
program: testsuite_stanford_queens
candidate_id: testsuite_stanford_queens__swap_2__instcombine__simplifycfg
pass_a,pass_b: instcombine,simplifycfg
anchor_text_size: 727
text_size: 695
text_delta: -32
text_delta_pct: -4.401651
```

这只表示该 candidate 的 object text size 小于 anchor，不表示整体 pipeline 更优，也不涉及 runtime。

### 本次代码快照：P5 invariant

```python
def validate_candidate_invariants(
    candidates: Sequence[CandidatePipeline],
) -> list[str]:
    errors: list[str] = []
    for candidate in candidates:
        base = _split_pipeline(candidate.base_pipeline)
        trial = _split_pipeline(candidate.candidate_pipeline)
        label = f"{candidate.program}/{candidate.candidate_id}"
        if Counter(base) != Counter(trial):
            errors.append(f"{label}: candidate pass multiset differs from anchor")
        if candidate.source == "anchor":
            if base != trial:
                errors.append(f"{label}: anchor candidate differs from base pipeline")
            if candidate.validation_label != "anchor":
                errors.append(f"{label}: anchor validation label is not anchor")
            continue
        if candidate.source != "single_swap":
            errors.append(f"{label}: unsupported candidate source {candidate.source}")
            continue
        if candidate.validation_label != "not_certified_independent":
            errors.append(
                f"{label}: single-swap candidate is not not_certified_independent"
            )
        if not _is_exact_adjacent_swap(base, trial, candidate.swap_index):
            errors.append(f"{label}: not exactly one adjacent swap")
    return errors
```

### 本次代码快照：`src/ecpor/object_size_runner.py`

```python
@dataclass(frozen=True)
class ObjectSizeRecord:
    program: str
    candidate_id: str
    ir_path: str
    object_path: str
    compile_exit_code: int
    compile_failure_kind: str | None
    size_exit_code: int
    text_size: int | None
    data_size: int | None
    bss_size: int | None
    total_size: int | None
    size_tool_output: str
    size_failure_kind: str | None = None


def parse_llvm_size_output(text: str) -> tuple[int, int, int, int] | None:
    for raw_line in text.splitlines():
        parts = raw_line.split()
        if len(parts) < 4:
            continue
        try:
            text_size = int(parts[0], 0)
            data_size = int(parts[1], 0)
            bss_size = int(parts[2], 0)
            total_size = int(parts[3], 0)
        except ValueError:
            continue
        return text_size, data_size, bss_size, total_size
    return None
```

### 本次代码快照：`src/ecpor/code_size_evaluator.py`

```python
def run_code_size_evaluation(
    *,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    pipeline_output_dir: str | Path,
    output_dir: str | Path,
    llc_path: ToolPath = "llc",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
) -> CodeSizeEvaluation:
    candidates = _load_csv(candidates_csv)
    pipeline_runs = _load_csv(pipeline_runs_csv)
    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    ...
    for run_row in pipeline_runs:
        candidate = candidate_by_id[run_row["candidate_id"]]
        ir_path = ir_root / f"{_safe_name(run_row['candidate_id'])}.ll"
        object_path = object_root / f"{_safe_name(run_row['candidate_id'])}.o"
        records.append(
            measure_object_size(
                program=run_row["program"],
                candidate_id=run_row["candidate_id"],
                ir_path=ir_path,
                object_path=object_path,
                llc_path=llc_path,
                llvm_size_path=llvm_size_path,
                timeout_sec=timeout_sec,
            )
        )
```

### 风险与备注

- P6 只比较 object code size，不比较 runtime。
- P6 没有引入完整 searcher，也没有多步 swap。
- 当前 object size 使用 `llc` 直接从 LLVM IR 生成 object；这条链路短，适合最小版，但后续如果要和真实编译流程对齐，可能需要增加 `clang -c` 路径作为对照。
- 当前报告主要使用 `text_size` 作为代码大小指标；`total_size` 被记录但暂不作为主判断。
- `smaller_text` 可以说明 text size 小于 anchor，但不能写成整体更优。

### 下一步

- P5 final 已在提交后复跑，并确认 `ecpor_git_dirty = False`。
- P6 final 已保持 `ObjectBuildFailed = 0`、`SizeParseFailed = 0`、`CodeSizeDeltaVsAnchor computed = 16`。
- 下一阶段可以考虑 P7 bounded two-swap exploration。
- P7 仍应保持 bounded，不直接进入完整 searcher。
