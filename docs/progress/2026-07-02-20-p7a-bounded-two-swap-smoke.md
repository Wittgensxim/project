# ECPOR 进度记录：P7a bounded two-swap smoke test

## 2026-07-02：从唯一 smaller one-swap seed 做二次相邻交换冒烟测试

### 当前目标

本轮进入 P7a，但仍然不是完整 searcher。目标是验证 two-swap 基础设施：

```text
从 P6 中唯一 .text 变小的 one-swap candidate 出发；
尝试再做一次相邻交换；
每个 second swap 都必须重新 materialize seed pipeline 下的 prefix state；
在该 prefix state 上重新 static filter + lazy validation；
最后复用 P6 code size evaluator 生成 object size。
```

本轮不做：

```text
完整搜索
runtime benchmark
beam search
loop / inline / O2 / O3
Alive2
```

### 已完成内容

- [x] 新增 `src/ecpor/pipeline_dedup.py`：
  - `pipeline_sequence_hash()`
  - `deduplicate_pipeline_rows()`
  - 防止同一 pass sequence 重复跑完整 pipeline。
- [x] 新增 `src/ecpor/bounded_two_swap_driver.py`：
  - 读取 P5 `candidates.csv` / `pipeline_runs.csv`。
  - 读取 P6 `object_size.csv`。
  - P7a seed 只选择 `source == single_swap` 且 `text_delta_pct < 0`。
  - 对 seed pipeline 的每个 adjacent pair materialize prefix state。
  - 在新 prefix state 上做 static filter 和 lazy validation。
  - 只为 `not_certified_independent` 生成 depth=2 candidate。
  - 对重复 pipeline sequence 去重。
  - 跑完整 pipeline。
  - 复用 P6 code size evaluator。
- [x] `src/ecpor/code_size_evaluator.py` 支持 `source == two_swap`：
  - 新增 `candidate_object_builds`。
  - 新增 `candidate_sizes_available`。
  - `code_size_delta_computed` / `smaller_text` / `equal_text` / `larger_text` 可统计 `two_swap`。
- [x] 新增 tests：
  - `tests/test_pipeline_dedup.py`
  - `tests/test_bounded_two_swap_driver.py`
  - 扩展 `tests/test_code_size_evaluator.py`
- [x] 新增可提交 manifest：
  - `docs/results/p7a_bounded_two_swap_manifest.json`
- [x] 更新 `docs/results/p6_5_code_size_manifest.json`：
  - 补 `object_size_csv` SHA-256。
  - 补 `code_size_report` SHA-256。
  - 更新到 `079ab662158061a8690e321cb209cc656cd5d714` clean run。
- [x] 更新 `docs/data_retention_manifest.md`：
  - 保留 `data/outputs/bounded_two_swap_p7a/`。
  - 保留 `data/certs/bounded_two_swap_p7a/`。
- [x] 更新 README P7a 复跑命令。

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_pipeline_dedup.py tests\test_bounded_two_swap_driver.py tests\test_code_size_evaluator.py
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.pipeline_dedup'
ModuleNotFoundError: No module named 'ecpor.bounded_two_swap_driver'
KeyError: 'candidate_object_builds'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_pipeline_dedup.py tests\test_bounded_two_swap_driver.py tests\test_code_size_evaluator.py
```

结果：

```text
8 passed in 1.36s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
75 passed in 8.21s
```

### clean P5/P6 复跑

P7a 源码提交：

```text
079ab662158061a8690e321cb209cc656cd5d714
```

提交后复跑 P5：

```text
ecpor_git_commit: 079ab662158061a8690e321cb209cc656cd5d714
ecpor_git_dirty: False
anchor_candidates: 8
single_swap_candidates: 16
pipeline_runs: 24
pipeline_run_failed: 0
single_swap_same_as_anchor: 0
single_swap_different_from_anchor: 16
```

提交后复跑 P6：

```text
ecpor_git_commit: 079ab662158061a8690e321cb209cc656cd5d714
ecpor_git_dirty: False
ObjectBuildFailed: 0
SizeParseFailed: 0
CodeSizeDeltaVsAnchor computed: 16
SingleSwapP5SameAsAnchor: 0
SingleSwapP5DifferentFromAnchor: 16
IRDifferentButTextEqualCount: 15
IRDifferentButTextEqualRate: 93.75%
```

### P7a 真实运行

运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7a --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

输出：

```text
data/outputs/bounded_two_swap_p7a/two_swap_attempts.csv
data/outputs/bounded_two_swap_p7a/two_swap_candidates.csv
data/outputs/bounded_two_swap_p7a/two_swap_pipeline_runs.csv
data/outputs/bounded_two_swap_p7a/two_swap_object_size.csv
data/outputs/bounded_two_swap_p7a/two_swap_report.md
data/certs/bounded_two_swap_p7a/
```

P7a report：

```text
seed_candidates: 1
attempted_second_swaps: 7
candidate_second_swaps: 7
low_priority_skipped: 0
cache_hits: 0
dynamic_tests: 7
certified_independent: 3
not_certified_independent: 4
run_failed: 0
two_swap_candidates_generated: 3
duplicate_sequences: 1
pipeline_runs: 11
pipeline_run_failed: 0
object_build_failed: 0
size_parse_failed: 0
best_depth2_text_delta_pct: -4.4017
```

### P7a seed

P7a 只使用 P6 中唯一 `.text` 变小的 one-swap candidate：

```text
program: testsuite_stanford_queens
candidate_id: testsuite_stanford_queens__swap_2__instcombine__simplifycfg
candidate_pipeline: sroa,early-cse,simplifycfg,instcombine,reassociate,gvn,dce,adce
depth1_text_delta_pct: -4.4017
```

### second-swap validation 明细

P7a 对 seed pipeline 的 7 个相邻位置全部重新 materialize prefix state 并 lazy validate：

```text
swap 0: prefix=[]; sroa,early-cse -> not_certified_independent
swap 1: prefix=sroa; early-cse,simplifycfg -> certified_independent
swap 2: prefix=sroa,early-cse; simplifycfg,instcombine -> not_certified_independent
swap 3: prefix=sroa,early-cse,simplifycfg; instcombine,reassociate -> not_certified_independent
swap 4: prefix=sroa,early-cse,simplifycfg,instcombine; reassociate,gvn -> not_certified_independent
swap 5: prefix=sroa,early-cse,simplifycfg,instcombine,reassociate; gvn,dce -> certified_independent
swap 6: prefix=sroa,early-cse,simplifycfg,instcombine,reassociate,gvn; dce,adce -> certified_independent
```

其中 `swap 2` 会回到 P5 已存在的 one-swap sequence，因此被去重；最终生成 3 个新的 depth=2 candidate。

### depth=2 candidates

```text
1. swap_0__sroa__early-cse
   pipeline: early-cse,sroa,simplifycfg,instcombine,reassociate,gvn,dce,adce
   text_delta_pct: -4.4017

2. swap_3__instcombine__reassociate
   pipeline: sroa,early-cse,simplifycfg,reassociate,instcombine,gvn,dce,adce
   text_delta_pct: -4.4017

3. swap_4__reassociate__gvn
   pipeline: sroa,early-cse,simplifycfg,instcombine,gvn,reassociate,dce,adce
   text_delta_pct: -2.2008
```

结论：P7a smoke 没有发现超过 depth1 best `-4.4017%` 的 `.text` 改善；两个 depth2 candidate 与 depth1 best 持平，一个较弱。

### 本次代码快照：pipeline dedup

```python
def pipeline_sequence_hash(passes: Sequence[str]) -> str:
    joined = ",".join(part.strip() for part in passes if part.strip())
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def deduplicate_pipeline_rows(
    rows: Sequence[dict[str, str]],
    *,
    pipeline_field: str = "candidate_pipeline",
) -> PipelineDeduplicationResult:
    seen: set[str] = set()
    unique_rows: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []
    sequence_to_candidate_ids: dict[str, list[str]] = {}
    for row in rows:
        normalized = _split_pipeline(row.get(pipeline_field, ""))
        sequence_hash = row.get("pipeline_sequence_hash") or pipeline_sequence_hash(
            normalized
        )
        enriched = {**row, "pipeline_sequence_hash": sequence_hash}
        sequence_to_candidate_ids.setdefault(sequence_hash, []).append(
            row.get("candidate_id", "")
        )
        if sequence_hash in seen:
            duplicate_rows.append(enriched)
            continue
        seen.add(sequence_hash)
        unique_rows.append(enriched)
    return PipelineDeduplicationResult(
        unique_rows=unique_rows,
        duplicate_rows=duplicate_rows,
        sequence_to_candidate_ids=sequence_to_candidate_ids,
    )
```

### 本次代码快照：second swap prefix

```python
prefix = list(seed_passes[:swap_index])
pass_a = seed_passes[swap_index]
pass_b = seed_passes[swap_index + 1]
state = materialize_prefix_state(
    input_ir,
    prefix,
    opt_path=opt_path,
    output_dir=program_root / "prefix_states",
    env_id=env_id,
    nesting=nesting,
    normalizer_version=normalizer_version,
    extra_flags=extra_flags,
    timeout_sec=timeout_sec,
)
```

这段保证 P7 的第二个 swap 使用的是 seed pipeline 的 prefix，而不是 anchor pipeline 的 prefix。

### 风险与备注

- P7a 是 smoke test，不是正式 P7b 结论。
- P7a seed 只有一个，来自 `testsuite_stanford_queens`，不能泛化到所有程序。
- `best_depth2_text_delta_pct = -4.4017` 只说明 `.text` size 与 depth1 best 持平，不说明 runtime。
- 当前仍只用 `llc -filetype=obj`，没有 `clang -c` 对照。
- P7b 应扩大 seed：每个程序最多 top-3 one-swap candidate，而不是只沿 Queens 单点继续。

### 下一步

- 提交 P7a manifest、进度文档和索引更新。
- P7b 前可以先补一个小改动：把 P6 manifest 和 P7a manifest 的生成逻辑脚本化，减少手写 hash 的风险。
- 然后进入 P7b：per-program top-3 seed 的 bounded two-swap controlled experiment。
