# ECPOR 进度记录：P7b.5 two-swap 结果解释与分布分析

## 2026-07-02：解释 P7b，而不是继续加深搜索

### 当前目标

本轮不做 depth=3，不做完整 searcher，不新增 LLVM 动态验证，只解释 P7b 已经产生的数据：

```text
1. 按 program 汇总 P7b seed、attempt、depth2 和 code-size 结果。
2. 按 second-swap pair 汇总 certified/not-certified 与 code-size 分布。
3. 列出 depth2 candidate 的 parent、swap_path、delta vs parent 和是否超过 program depth1 best。
4. 审计 P7b first-run 的 5 个 cache hit 来源。
5. 审计 42 raw depth2 到 22 unique depth2 的 20 个 duplicate sequence。
6. 生成 analysis manifest，继续保持 data/ 目录只保留必要结果。
```

### 已完成内容

- [x] 新增 `src/ecpor/two_swap_analysis.py`：
  - `run_two_swap_analysis()`
  - `build_analysis_report()`
  - CLI：`python -m ecpor.two_swap_analysis ...`
- [x] 新增 `tests/test_two_swap_analysis.py`：
  - program summary
  - pair summary
  - depth2 details
  - cache audit
  - duplicate audit
- [x] 扩展 `src/ecpor/result_manifest.py`：
  - `build_p7b_analysis_manifest()`
  - CLI：`python -m ecpor.result_manifest p7b-analysis ...`
  - 新增 `P7B_ANALYSIS_SUMMARY_KEYS`，避免把 per-program 文本行误收进 manifest summary。
- [x] 更新 `tests/test_result_manifest.py`：
  - 增加 P7b.5 manifest 测试。
  - 增加 manifest summary 白名单回归测试。
- [x] 生成真实 P7b.5 分析输出：
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_program_summary.csv`
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_pair_summary.csv`
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_depth2_details.csv`
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_cache_audit.csv`
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_duplicate_audit.csv`
  - `data/outputs/bounded_two_swap_p7b_analysis/p7b_analysis_report.md`
- [x] 生成 tracked manifest：
  - `docs/results/p7b_analysis_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_analysis.py
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.two_swap_analysis'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_analysis.py
```

结果：

```text
1 passed in 0.06s
```

Manifest RED test：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_result_manifest.py
```

初始失败符合预期：

```text
ImportError: cannot import name 'build_p7b_analysis_manifest'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_result_manifest.py tests/test_two_swap_analysis.py
```

结果：

```text
3 passed in 0.15s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
81 passed in 11.05s
```

源码提交：

```text
76e683d0d34a3950bc991c512ba529de1471ebe4
add P7b two-swap analysis reports

49a0a8fbe9b9755ec2519248b9531581eb7ed041
filter P7b analysis manifest summary
```

### 真实 P7b.5 分析命令

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.two_swap_analysis --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --out data\outputs\bounded_two_swap_p7b_analysis
```

输出报告摘要：

```text
Programs: 8
SelectedSeeds: 16
RawDepth2Candidates: 42
UniqueDepth2Candidates: 22
DuplicateSequences: 20
DuplicateSequenceRate: 47.62%
Depth2SmallerText: 3
Depth2EqualText: 16
Depth2LargerText: 3
Depth2SmallerPrograms: 1
Depth2ImprovesProgramDepth1Best: 0
Depth2ImprovesGlobalDepth1Best: 0
FirstRunCacheHits: 5
PipelineRuns: 30
PipelineRunFailed: 0
```

解释：

```text
P7b 的 two-swap 确实增加了 smaller-text candidate 数量：
depth1 smaller = 1
depth2 smaller = 3

但 P7b 没有扩大受益程序数量：
Depth2SmallerPrograms = 1

3 个 depth2 smaller 全部来自 testsuite_stanford_queens。
它们都没有超过 queens 已有的 depth1 best：
Depth2ImprovesProgramDepth1Best = 0
Depth2ImprovesGlobalDepth1Best = 0
```

### Program summary 关键表

路径：

```text
data/outputs/bounded_two_swap_p7b_analysis/p7b_program_summary.csv
```

关键行：

```text
testsuite_stanford_bubblesort: seeds=2 raw_depth2=4 unique_depth2=2 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_intmm: seeds=2 raw_depth2=4 unique_depth2=2 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_oscar: seeds=2 raw_depth2=6 unique_depth2=3 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_perm: seeds=2 raw_depth2=5 unique_depth2=3 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_puzzle: seeds=2 raw_depth2=6 unique_depth2=3 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_queens: seeds=2 raw_depth2=7 unique_depth2=4 smaller=3 best_depth1=-4.401651 best_depth2=-4.401651 improves=False
testsuite_stanford_quicksort: seeds=1 raw_depth2=2 unique_depth2=1 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
testsuite_stanford_towers: seeds=3 raw_depth2=8 unique_depth2=4 smaller=0 best_depth1=0.000000 best_depth2=0.000000 improves=False
```

### 3 个 smaller depth2 candidate

路径：

```text
data/outputs/bounded_two_swap_p7b_analysis/p7b_depth2_details.csv
```

结果：

| program | parent | second swap | parent Δtext | depth2 Δtext | vs parent | 超过 program depth1 best |
| --- | --- | --- | ---: | ---: | ---: | --- |
| testsuite_stanford_queens | `testsuite_stanford_queens__swap_2__instcombine__simplifycfg` | `sroa,early-cse` | `-4.401651` | `-4.401651` | `0.000000` | `False` |
| testsuite_stanford_queens | `testsuite_stanford_queens__swap_2__instcombine__simplifycfg` | `instcombine,reassociate` | `-4.401651` | `-4.401651` | `0.000000` | `False` |
| testsuite_stanford_queens | `testsuite_stanford_queens__swap_2__instcombine__simplifycfg` | `reassociate,gvn` | `-4.401651` | `-2.200825` | `2.200826` | `False` |

结论：

```text
3 个 smaller depth2 都围绕 queens 的同一个 depth1 smaller parent。
其中 2 个与 parent 持平，1 个比 parent 更差但仍小于 anchor。
P7b 没有发现新的 program-level best，也没有发现 global best。
```

### Cache audit

路径：

```text
data/outputs/bounded_two_swap_p7b_analysis/p7b_cache_audit.csv
```

first-run 的 5 个 cache hit 来源：

```text
testsuite_stanford_oscar:
  seed=testsuite_stanford_oscar__swap_2__instcombine__simplifycfg
  swap_index=0
  pair=sroa,early-cse
  matched_previous_seed=testsuite_stanford_oscar__swap_0__sroa__early-cse

testsuite_stanford_perm:
  seed=testsuite_stanford_perm__swap_1__early-cse__instcombine
  swap_index=6
  pair=dce,adce
  matched_previous_seed=testsuite_stanford_perm__swap_0__sroa__early-cse

testsuite_stanford_puzzle:
  seed=testsuite_stanford_puzzle__swap_2__instcombine__simplifycfg
  swap_index=0
  pair=sroa,early-cse
  matched_previous_seed=testsuite_stanford_puzzle__swap_0__sroa__early-cse

testsuite_stanford_queens:
  seed=testsuite_stanford_queens__swap_0__sroa__early-cse
  swap_index=0
  pair=early-cse,sroa
  matched_previous_seed=testsuite_stanford_queens__swap_2__instcombine__simplifycfg

testsuite_stanford_towers:
  seed=testsuite_stanford_towers__swap_2__instcombine__simplifycfg
  swap_index=0
  pair=sroa,early-cse
  matched_previous_seed=testsuite_stanford_towers__swap_0__sroa__early-cse
```

解释：

```text
这些 cache hit 都能追溯到同一个 prefix_state_hash 加同一 unordered pair 的前序 attempt。
这支持 P7b first-run 内部 cache reuse 是正常的 state-indexed certificate reuse，而不是 key 过宽。
```

### Duplicate audit

路径：

```text
data/outputs/bounded_two_swap_p7b_analysis/p7b_duplicate_audit.csv
```

结果：

```text
RawDepth2Candidates = 42
UniqueDepth2Candidates = 22
DuplicateSequences = 20
DuplicateSequenceRate = 47.62%
```

解释：

```text
P7b 的 two-swap raw candidate 中，接近一半在 pass-sequence 层面被去重。
这是 sequence-level 去重，不是 semantic equivalence，也不是 hard-hash equivalence。
但它已经说明 two-swap 路径空间里存在明显的路径重复，后续 searcher 必须把 dedup 放在核心路径上。
```

### Manifest

生成命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p7b-analysis --out-manifest docs\results\p7b_analysis_manifest.json --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --analysis-dir data\outputs\bounded_two_swap_p7b_analysis --repo-root . --result-generated-from-commit 49a0a8fbe9b9755ec2519248b9531581eb7ed041
```

关键字段：

```text
stage: P7b.5
result_generated_from_commit: 49a0a8fbe9b9755ec2519248b9531581eb7ed041
ecpor_git_commit: 49a0a8fbe9b9755ec2519248b9531581eb7ed041
ecpor_git_dirty: false
```

关键 hash：

```text
p7b_program_summary_csv: 8fa9822a33bbeb34469671fdd73593bd6f744dbffcf06ea5cc636906df621a81
p7b_pair_summary_csv: 15e3e713b680423b5cc9b8b5a2bd7df911b48c63af59a5f5991343d50f6c250d
p7b_depth2_details_csv: 0392305746b40feb5946a73e3428d06c04dba5a7bf861bc9424e8edd0619ae44
p7b_cache_audit_csv: a3c3d030a4bc3b04f7d08bd00caa4615ba0b6b8a260d350bfc1bd6efc7be2294
p7b_duplicate_audit_csv: 69b2474d48618ea71fa963d62514bf475a2e9b0201b5fbe4bfce691295cac0e9
p7b_analysis_report: 960c04c52b90860f58034a8ea1ea2196e419a7050b031d94cd149b9ddf4ed90f
```

### 本次代码快照：分析入口

```python
def run_two_swap_analysis(
    *,
    seeds_csv: str | Path,
    attempts_csv: str | Path,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    object_size_csv: str | Path,
    p6_object_size_csv: str | Path,
    output_dir: str | Path,
) -> TwoSwapAnalysis:
    seeds = _load_csv(seeds_csv)
    attempts = _load_csv(attempts_csv)
    candidates = _load_csv(candidates_csv)
    pipeline_runs = _load_csv(pipeline_runs_csv)
    object_rows = _load_csv(object_size_csv)
    p6_rows = _load_csv(p6_object_size_csv)

    raw_depth2_rows = _raw_depth2_rows(attempts, seeds=seeds, p6_rows=p6_rows)
    depth2_rows = [row for row in candidates if row.get("source") == "two_swap"]
    program_rows = _build_program_summary(...)
    pair_rows = _build_pair_summary(...)
    depth2_detail_rows = _build_depth2_details(...)
    cache_audit_rows = _build_cache_audit(attempts)
    duplicate_audit_rows = _build_duplicate_audit(...)
```

### 本次代码快照：cache audit key

```python
def _build_cache_audit(attempts: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    previous_by_key: dict[tuple[str, tuple[str, str]], dict[str, str]] = {}
    rows: list[dict[str, str]] = []
    for attempt in attempts:
        key = (
            attempt.get("state_hash", ""),
            _pair_key(attempt.get("pass_a", ""), attempt.get("pass_b", "")),
        )
        previous = previous_by_key.get(key, {})
        rows.append(
            {
                "program": attempt.get("program", ""),
                "seed_candidate_id": attempt.get("seed_candidate_id", ""),
                "swap_index": attempt.get("swap_index", ""),
                "pass_a": attempt.get("pass_a", ""),
                "pass_b": attempt.get("pass_b", ""),
                "prefix_state_hash": attempt.get("state_hash", ""),
                "cache_hit": attempt.get("cache_hit", ""),
                "cert_id": attempt.get("cert_id", ""),
                "matched_previous_seed_candidate_id": previous.get(
                    "seed_candidate_id", ""
                ),
                "matched_previous_swap_index": previous.get("swap_index", ""),
            }
        )
        if attempt.get("cert_id"):
            previous_by_key.setdefault(key, attempt)
    return rows
```

### 本次代码快照：manifest summary 白名单

```python
P7B_ANALYSIS_SUMMARY_KEYS = {
    "Programs",
    "SelectedSeeds",
    "RawDepth2Candidates",
    "UniqueDepth2Candidates",
    "DuplicateSequences",
    "DuplicateSequenceRate",
    "Depth2SmallerText",
    "Depth2EqualText",
    "Depth2LargerText",
    "Depth2SmallerPrograms",
    "Depth2ImprovesProgramDepth1Best",
    "Depth2ImprovesGlobalDepth1Best",
    "FirstRunCacheHits",
    "PipelineRuns",
    "PipelineRunFailed",
}
```

### 风险与备注

- P7b.5 是 analysis-only，不重新运行 LLVM，也不新增 certificate。
- `DuplicateSequenceRate = 47.62%` 是 pass sequence 层面的去重率，不等价于 IR semantic equivalence。
- 3 个 smaller depth2 都来自 queens，因此不能说 depth2 已经普遍提升 code size。
- 目前仍然只有 `llc -filetype=obj` 的 `.text` size 结果，不能推出 runtime 结论。
- `data/outputs/bounded_two_swap_p7b_analysis/` 暂时保留，因为 tracked manifest 和进度文档都引用它作为当前 P7b.5 证据。

### 下一步

不建议马上做 depth=3。更稳的选择是二选一：

```text
A. benchmark expansion：
   增加 8-12 个 LLVM test-suite SingleSource/Misc 小程序，
   保持同一个 8-pass scalar subset，
   看 depth2 smaller 是否仍只集中在少数程序。

B. clang-c codegen sensitivity：
   对 P6/P7b 关键 candidates 做 clang -c 路径对照，
   检查 llc -filetype=obj 的 .text 结论是否稳定。
```

如果坚持进入搜索，也应该只做很小的 beam：

```text
beam_width = 3
max_depth = 3
same 8-pass scalar subset
same state-indexed lazy validation
same code-size target
```
