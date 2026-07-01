# ECPOR 进度记录：P7b per-program top-3 seed bounded two-swap controlled experiment

## 2026-07-02：从 P7a smoke 扩展到 P7b 受控实验

### 当前目标

本轮进入 P7b，但仍不做完整 searcher。目标是把 P7a 的单 seed smoke test 扩展为受控的 per-program top-k seed 二次相邻交换实验：

```text
1. 每个 Stanford 程序最多选择 3 个 one-swap seed。
2. seed 只允许 text size 不变或变小，不选择 larger seed。
3. 对每个 seed 的第二次相邻交换重新做 prefix-state lazy validation。
4. 每个程序最多保留 5 个 unique depth2 candidate，总数最多 40。
5. 跑 first-run 和同 cert-dir second-run cache reuse。
6. 生成 tracked manifest，而不是把大量 data 产物纳入 Git。
```

### 已完成内容

- [x] 新增 `src/ecpor/two_swap_seed.py`：
  - `smaller-only` 保持 P7a 默认行为。
  - `top-k-per-program` 支持 P7b seed 选择。
  - 输出 `two_swap_seeds.csv`，记录 seed pipeline、rank、reason 和 `.text` delta。
- [x] 扩展 `src/ecpor/bounded_two_swap_driver.py`：
  - 新增 `--seed-mode top-k-per-program`。
  - 新增 `--max-seeds-per-program`。
  - 新增 `--max-unique-depth2-per-program`。
  - 新增 `--max-total-depth2`。
  - 新增 `--stage-name`。
  - 新增 depth2 budget 裁剪和不变量检查。
- [x] 扩展 `src/ecpor/result_manifest.py`：
  - manifest 记录 `two_swap_seeds.csv`。
  - summary 过滤新增 P7b 字段。
  - manifest 记录 P7b 多 seed 列表。
- [x] 新增/更新测试：
  - `tests/test_two_swap_seed.py`
  - `tests/test_bounded_two_swap_driver.py`
  - `tests/test_result_manifest.py`
- [x] 跑真实 P7b first-run：
  - `data/outputs/bounded_two_swap_p7b/`
  - `data/certs/bounded_two_swap_p7b/`
- [x] 跑真实 P7b second-run cache reuse：
  - `data/outputs/bounded_two_swap_p7b_second/`
  - cert dir 复用 `data/certs/bounded_two_swap_p7b/`
- [x] 生成 tracked manifests：
  - `docs/results/p7b_bounded_two_swap_manifest.json`
  - `docs/results/p7b_cache_reuse_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_seed.py tests/test_bounded_two_swap_driver.py tests/test_result_manifest.py
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.two_swap_seed'
TypeError: run_bounded_two_swap_smoke() got an unexpected keyword argument 'seed_mode'
KeyError: 'selected_seed_candidates'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_seed.py tests/test_bounded_two_swap_driver.py tests/test_result_manifest.py
```

结果：

```text
5 passed in 3.62s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
79 passed in 10.54s
```

源码提交：

```text
3f9047942fe7b43e9e41f65e97e78af1ab6e8559
add P7b top-k two-swap seed mode
```

### P7b first-run

运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --seed-mode top-k-per-program --max-seeds-per-program 3 --max-unique-depth2-per-program 5 --max-total-depth2 40 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7b --cert-dir data\certs\bounded_two_swap_p7b --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30 --stage-name P7b
```

关键结果：

```text
ecpor_git_commit: 3f9047942fe7b43e9e41f65e97e78af1ab6e8559
ecpor_git_dirty: False
selected_seed_candidates: 16
selected_smaller_seeds: 1
selected_equal_seeds: 15
selected_seed_programs: 8
seed_mode: top-k-per-program
max_seeds_per_program: 3
attempted_second_swaps: 112
static_candidate_second_swaps: 100
low_priority_skipped: 12
validated_second_swaps: 100
cache_hits: 5
dynamic_tests: 95
certified_independent: 58
not_certified_independent: 42
run_failed: 0
raw_depth2_candidates: 42
duplicate_sequences: 20
unique_depth2_candidates_before_budget: 22
budget_skipped_depth2_candidates: 0
unique_depth2_candidates: 22
max_unique_depth2_per_program: 5
max_total_unique_depth2: 40
max_observed_depth2_per_program: 4
anchor_runs: 8
depth1_seed_runs: 0
depth2_candidate_runs: 22
total_pipeline_runs: 30
pipeline_run_failed: 0
object_build_failed: 0
size_parse_failed: 0
depth1_smaller_text: 1
depth1_equal_text: 15
depth1_larger_text: 0
depth2_smaller_text: 3
depth2_equal_text: 16
depth2_larger_text: 3
best_depth1_text_delta_pct_vs_anchor: -4.4017
best_depth2_text_delta_pct_vs_anchor: -4.4017
best_depth2_delta_pct_vs_parent: 0.0000
depth2_improves_over_depth1_best: False
best_candidate_depth: 1
```

解释：

```text
P7b 已经从 P7a 的单 seed 扩展到 8 个程序的 per-program seed 选择。
16 个 seed 中只有 queens 的一个 seed 让 .text 变小，其余 15 个为 equal-text seed。
112 次二次交换尝试中，100 次进入 lazy validation，12 次 static filter 判为 low_priority 后跳过。
first-run 中 95 次动态验证、5 次 cache 命中；这 5 次是同一轮运行中重复 state/certificate 的自然复用，不是 second-run 证据。
22 个 depth2 candidate 全部通过 pipeline/code-size 路径，没有触发预算裁剪。
depth2 中有 3 个 smaller-text candidate，但 best depth2 仍未超过已有 best depth1。
```

### P7b second-run cache reuse

运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --seed-mode top-k-per-program --max-seeds-per-program 3 --max-unique-depth2-per-program 5 --max-total-depth2 40 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7b_second --cert-dir data\certs\bounded_two_swap_p7b --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30 --stage-name P7b-cache
```

关键结果：

```text
validated_second_swaps: 100
cache_hits: 100
dynamic_tests: 0
certified_independent: 58
not_certified_independent: 42
run_failed: 0
unique_depth2_candidates: 22
pipeline_run_failed: 0
object_build_failed: 0
size_parse_failed: 0
```

说明：

```text
同一 cert-dir 的 second-run 达到 100/100 cache hit。
这证明 P7b 的 state-indexed certificate key 对本轮二次交换验证可复用，且复跑不需要新增动态证书测试。
```

### Manifest

本轮 manifest 路径：

```text
docs/results/p7b_bounded_two_swap_manifest.json
docs/results/p7b_cache_reuse_manifest.json
```

两个 manifest 均记录：

```text
result_generated_from_commit: 3f9047942fe7b43e9e41f65e97e78af1ab6e8559
ecpor_git_commit: 3f9047942fe7b43e9e41f65e97e78af1ab6e8559
ecpor_git_dirty: false
```

关键 hash 示例：

```text
p7b two_swap_seeds_csv: 2636749a77cce76f5ef05a7469a221c59fda055c13b9758fca9df03145f7a3ac
p7b two_swap_candidates_csv: 0a922ab3ab617e777a0c546db0dae32e3c24d47a3162986bbedf4aa641f32d7e
p7b two_swap_attempts_csv: 53c4e4c5fb797187feff8c88d59b89ae9d55ebade7d5ef415072a3201a3efcd6
p7b-cache two_swap_attempts_csv: 8592f378c4dbffb27296b67fbe296541a2bd4dc40f5952c43fa91a0e99e35cba
opt: f4a10cdc53c8f1288bb4051318af63ca8b07aae0f0b8ffb13b788fc98ace2543
llc: 1520eba7e1ee09cc6f38ce1d7ca6eb9fb5187f6ded3a9f70a37f264acebf384c
llvm_size: f425ef87d64380ff5f8fd055ddb52e1f0d38f3031bb2a5bbddd557d71c5bc589
```

### 本次代码快照：seed 选择

```python
def select_seed_rows(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
    *,
    seed_mode: str = "smaller-only",
    max_seeds_per_program: int = 3,
) -> list[dict[str, str]]:
    if seed_mode not in SEED_MODES:
        raise ValueError(
            f"unknown seed_mode {seed_mode!r}; expected one of {sorted(SEED_MODES)}"
        )
    if max_seeds_per_program < 1:
        raise ValueError("max_seeds_per_program must be >= 1")
    if seed_mode == "smaller-only":
        return _select_smaller_only(p6_rows, p5_candidate_by_id)
    return _select_top_k_per_program(
        p6_rows,
        p5_candidate_by_id,
        max_seeds_per_program=max_seeds_per_program,
    )
```

### 本次代码快照：P7b seed 规则

```python
def _select_top_k_per_program(
    p6_rows: Sequence[dict[str, str]],
    p5_candidate_by_id: dict[str, dict[str, str]],
    *,
    max_seeds_per_program: int,
) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in p6_rows:
        text_delta_pct = _parse_optional_float(row.get("text_delta_pct"))
        if (
            row.get("source") != "single_swap"
            or text_delta_pct is None
            or text_delta_pct > 0.0
            or row.get("candidate_id", "") not in p5_candidate_by_id
        ):
            continue
        grouped.setdefault(row.get("program", ""), []).append(row)

    selected: list[dict[str, str]] = []
    for program in sorted(grouped):
        rows = sorted(
            grouped[program],
            key=lambda row: (
                _parse_optional_float(row.get("text_delta_pct")) or 0.0,
                row.get("candidate_id", ""),
            ),
        )
        best = rows[0]
        best_pct = _parse_optional_float(best.get("text_delta_pct")) or 0.0
        best_reason = (
            "best_text_delta" if best_pct < 0.0 else "best_equal_text_delta"
        )
        chosen = [(best, best_reason)]
        chosen_ids = {best.get("candidate_id", "")}
        equal_rows = [
            row
            for row in rows
            if row.get("candidate_id", "") not in chosen_ids
            and (_parse_optional_float(row.get("text_delta_pct")) or 0.0) == 0.0
        ]
        ...
```

### 本次代码快照：depth2 budget 与不变量

```python
def _apply_depth2_budgets(
    rows: Sequence[dict[str, str]],
    *,
    max_unique_depth2_per_program: int | None,
    max_total_depth2: int | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    kept: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    per_program: Counter[str] = Counter()
    for row in rows:
        program = row.get("program", "")
        if max_total_depth2 is not None and len(kept) >= max_total_depth2:
            skipped.append({**row, "budget_skip_reason": "max_total_depth2"})
            continue
        if (
            max_unique_depth2_per_program is not None
            and per_program[program] >= max_unique_depth2_per_program
        ):
            skipped.append(
                {**row, "budget_skip_reason": "max_unique_depth2_per_program"}
            )
            continue
        kept.append(row)
        per_program[program] += 1
    return kept, skipped
```

### 本次代码快照：P7b summary 字段

```python
return {
    "seed_candidates": len(seed_rows),
    "selected_seed_candidates": len(seed_rows),
    "selected_smaller_seeds": _count_delta_kind(seed_rows, "smaller"),
    "selected_equal_seeds": _count_delta_kind(seed_rows, "equal"),
    "selected_seed_programs": len({row.get("program", "") for row in seed_rows}),
    "seed_mode": seed_mode,
    "max_seeds_per_program": max_seeds_per_program,
    "attempted_second_swaps": len(attempt_rows),
    "validated_second_swaps": sum(
        1
        for row in attempt_rows
        if row.get("cache_hit") == "True" or row.get("dynamic_test") == "True"
    ),
    "cache_hits": sum(1 for row in attempt_rows if row.get("cache_hit") == "True"),
    "dynamic_tests": sum(
        1 for row in attempt_rows if row.get("dynamic_test") == "True"
    ),
    "budget_skipped_depth2_candidates": len(budget_skipped_rows),
    "unique_depth2_candidates": len(depth2_rows),
    "max_observed_depth2_per_program": _max_depth2_per_program(depth2_rows),
    "depth2_smaller_text": _count_delta_kind(
        [row for row in object_size_rows if row.get("source") == "two_swap"],
        "smaller",
    ),
    "best_candidate_depth": _best_candidate_depth(best_depth1, best_depth2),
}
```

### 风险与备注

- P7b 仍然是 bounded controlled experiment，不是完整 searcher。
- `depth1_seed_runs = 0` 是刻意设计：P7b 复用 P5/P6 的 seed metadata，不重新运行 depth1 pipeline。
- P7b first-run 中出现 `cache_hits = 5`，不是异常；这是同一次运行内重复 state/certificate 的自然复用。
- 当前 code size 仍然只是 `llc -filetype=obj` 后的 `.text` size，不代表 runtime。
- depth2 里虽然出现 3 个 smaller-text candidate，但没有超过 P6/P7a 已观察到的 best depth1。
- `data/outputs/bounded_two_swap_p7b/`、`data/outputs/bounded_two_swap_p7b_second/` 与 `data/certs/bounded_two_swap_p7b/` 暂时保留，用于支撑 P7b manifest 和人工检查。

### 下一步

建议先做 P7b 结果解释和分布分析：

```text
1. 按 program 汇总 selected seed、not-certified second swap、depth2 text delta。
2. 找出 3 个 smaller depth2 candidate 的 parent、swap_path 和 pass pair。
3. 判断是否需要进入更大的 bounded search，或者先改 seed ranking。
4. 仍不要直接跳到完整 searcher、Alive2、loop pass、inline 或 O2/O3。
```
