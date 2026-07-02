# P9-5 combined 24-program depth1 summary

## 当前目标

本阶段目标是把 Stanford-8、Misc8、Diverse8 三组已经完成的 depth1-only 证据合并成一个 post-MVP 总表。P9-5 只做 summary-only 汇总，不新增实验、不新增 certificate、不新增 search，不运行 runtime benchmark，也不把旧 P7b two-swap 结果混入 depth1 口径。

## 完成内容

1. 新增 `src/ecpor/combined_depth1_summary.py`，从已有 retained result files 读取三组结果。
2. 新增 `tests/test_combined_depth1_summary.py`，先写失败测试，再实现汇总器。
3. 在 `src/ecpor/manifest_builders.py` 中导出 `build_combined_depth1_summary_manifest`，保持 `ecpor.result_manifest` 兼容入口可见。
4. 生成 `data/outputs/combined_depth1_summary/`：
   - `benchmark_set_summary.csv`
   - `depth1_reduction_summary.csv`
   - `depth1_objective_summary.csv`
   - `depth1_codegen_summary.csv`
   - `combined_depth1_report.md`
5. 生成 tracked manifest：`docs/results/combined_depth1_summary_manifest.json`。
6. 更新 `README.md`、`docs/ecpor_mvp_report.md`、`docs/data_retention_manifest.md` 与 `docs/project_progress.md`，说明 P9-5 是 post-MVP 扩展，不改变 `v0.1.1` MVP 语义。

## 核心结果

```text
BenchmarkSets = 3
TotalPrograms = 24
TotalPairMatrixCertificates = 672
TotalReproducedCertificates = 672
TotalHardFalseIndependent = 0
TotalAdjacentAttempts = 168
CertifiedAdjacentEvents = 101
NotCertifiedAdjacentEvents = 39
TotalOneSwapCandidates = 39
TotalBothSmallerPrograms = 2
Diverse8BothSmallerPrograms = 0
AttributionCases = 2
Depth1Only = True
NoNewExperiments = True
```

解释：Diverse8 增加了覆盖面，但没有新增 depth1 both-smaller program。当前 both-smaller program 仍然只有 Stanford Queens 与 Misc ffbench，因此不建议继续搜索；下一步更适合进入总结合并、阶段报告或论文草稿。

## 汇总表含义

`benchmark_set_summary.csv` 是最高层总表。每一行是一组 benchmark set，记录程序数、pair certificate 数、复现数、hard false independent、静态 false negative、P4 adjacent validation 事件数、one-swap candidate 数和 depth1 both-smaller program 数。

`depth1_reduction_summary.csv` 聚焦 reduction/certificate 层。它区分完整 pair matrix 中的 `certified_independent` / `not_certified_independent`，以及 P4 prefix-state adjacent validation 中实际尝试的相邻 swap、low-priority skip、dynamic tests 和 run_failed。

`depth1_objective_summary.csv` 聚焦 objective layer。它只统计 depth1 single-swap candidate 的 object `.text` 方向：smaller、equal、larger，以及 IR 已经不同但 `.text` 相等的候选数。

`depth1_codegen_summary.csv` 聚焦 `llc` 与 `clang -c` 的方向一致性。这里显式过滤 `source == "single_swap"`，避免 Stanford 的旧 P7b two-swap rows 污染 P9-5 depth1-only 总结。

## 关键代码快照

新增输入描述：

```python
@dataclass(frozen=True)
class BenchmarkSetInputs:
    name: str
    pair_summary_csv: str | Path
    static_filter_report: str | Path
    lazy_validation_report: str | Path
    p5_candidates_csv: str | Path
    p5_pipeline_runs_csv: str | Path
    p6_object_size_csv: str | Path
    codegen_compare_csv: str | Path
    attribution_summary_csv: str | Path | None = None
```

depth1-only codegen 过滤：

```python
def _codegen_summary(
    name: str,
    compare_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    depth1 = [
        row
        for row in compare_rows
        if row.get("source") == "single_swap"
        and row.get("llc_direction")
        and row.get("clang_direction")
    ]
    agreement = [_direction_agrees(row) for row in depth1]
    both_smaller = [
        row
        for row in depth1
        if row.get("llc_direction") == "smaller"
        and row.get("clang_direction") == "smaller"
    ]
```

manifest scope limits：

```python
"scope_limits": {
    "stage": "P9-5",
    "new_experiments": False,
    "new_certificates": False,
    "new_search": False,
    "runtime_benchmarks": False,
    "two_swap_search": False,
    "summary_only": True,
    "depth": 1,
    "benchmark_sets": [item.name for item in benchmark_sets],
}
```

测试里专门加入一条 `two_swap` both-smaller 行，并断言 P9-5 不把它算入 depth1：

```python
_write_codegen_compare(
    folder / "compare.csv",
    prefix,
    both_smaller=both_smaller,
    include_depth2_both_smaller=include_depth2_both_smaller,
)

self.assertEqual(codegen_rows[0]["direction_comparison_candidates"], "2")
self.assertEqual(codegen_rows[0]["smaller_under_both_count"], "1")
```

## 运行命令

测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

生成 P9-5 汇总：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.combined_depth1_summary import main; raise SystemExit(main(['--out', 'data\\outputs\\combined_depth1_summary', '--manifest', 'docs\\results\\combined_depth1_summary_manifest.json']))"
```

## 验证结果

```text
117 passed
```

正式 manifest 记录：

```text
stage = P9-5
result_generated_from_commit = b3b6b28adf97380273abd7ffddbd956e96cd8f1c
ecpor_git_dirty = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
two_swap_search = false
summary_only = true
```

## 风险和边界

1. P9-5 不是新的实验阶段，只是读取已有结果并汇总。
2. P9-5 不修 PassSpec，不新增 pair matrix，不运行 LLVM pipeline。
3. P9-5 不做 Diverse8 attribution，因为 Diverse8 没有新增 both-smaller program。
4. P9-5 不改变 `v0.1.1` MVP 定义；`v0.1.1` 仍是 Stanford-8 + Misc8 的 16-program / 448-certificate 发布边界。

## 下一步

优先进入总结合并阶段：写阶段报告或论文草稿。若继续工程收尾，建议做 P10 PassSpec provenance v2；当前不建议继续 two-swap、depth=3、beam/searcher、runtime benchmark、Alive2 或 PassInstrumentation。
