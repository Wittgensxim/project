# ECPOR 进度记录：P7a report 字段、manifest 自动化与 cache 复跑

## 2026-07-02：P7a 收尾后再进入 P7b

### 当前目标

本轮不扩大搜索，不进入 P7b 正式实验，只做 P7a 收尾：

```text
1. 把 P7a report 中容易误读的字段拆清楚。
2. 新增 result_manifest.py，避免手工填写 manifest hash。
3. 用同一个 P7a cert-dir 做 second-run cache reuse 验证。
4. 记录 second-run manifest 和 data retention 边界。
```

### 已完成内容

- [x] `src/ecpor/bounded_two_swap_driver.py` 更新 P7a summary/report 字段：
  - `candidate_second_swaps` 改为 `static_candidate_second_swaps`。
  - `two_swap_candidates_generated` 改为 `unique_depth2_candidates`。
  - 新增 `validated_second_swaps`、`raw_depth2_candidates`。
  - 新增 `anchor_runs`、`depth1_seed_runs`、`depth2_candidate_runs`、`total_pipeline_runs`。
  - 新增 `best_depth1_text_delta_pct_vs_anchor`、`best_depth2_text_delta_pct_vs_anchor`、`best_depth2_delta_pct_vs_parent`。
- [x] 新增 `src/ecpor/result_manifest.py`：
  - `build_result_manifest()`
  - `build_p7a_manifest()`
  - `build_p6_5_manifest()`
  - `write_manifest()`
  - CLI：`python -m ecpor.result_manifest p7a ...`
- [x] 新增/更新 tests：
  - `tests/test_bounded_two_swap_driver.py`
  - `tests/test_result_manifest.py`
- [x] 生成 P7a second-run cache manifest：
  - `docs/results/p7a_cache_reuse_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_bounded_two_swap_driver.py tests\test_result_manifest.py
```

初始失败符合预期：

```text
KeyError: 'static_candidate_second_swaps'
ModuleNotFoundError: No module named 'ecpor.result_manifest'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_bounded_two_swap_driver.py tests\test_result_manifest.py
```

结果：

```text
2 passed in 1.12s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_bounded_two_swap_driver.py tests\test_result_manifest.py tests\test_code_size_evaluator.py tests\test_pipeline_dedup.py
```

结果：

```text
9 passed in 1.33s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
76 passed in 8.36s
```

### P7a second-run cache reuse

源码 clean commit：

```text
083ab55e639f289d65cd035f4b3c98e4c0c31ed7
```

运行命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7a_second --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

结果：

```text
ecpor_git_commit: 083ab55e639f289d65cd035f4b3c98e4c0c31ed7
ecpor_git_dirty: False
seed_candidates: 1
attempted_second_swaps: 7
static_candidate_second_swaps: 7
validated_second_swaps: 7
cache_hits: 7
dynamic_tests: 0
certified_independent: 3
not_certified_independent: 4
run_failed: 0
raw_depth2_candidates: 4
duplicate_sequences: 1
unique_depth2_candidates: 3
anchor_runs: 8
depth1_seed_runs: 0
depth2_candidate_runs: 3
total_pipeline_runs: 11
pipeline_run_failed: 0
object_build_failed: 0
size_parse_failed: 0
best_depth1_text_delta_pct_vs_anchor: -4.4017
best_depth2_text_delta_pct_vs_anchor: -4.4017
best_depth2_delta_pct_vs_parent: 0.0000
depth2_improves_over_depth1_best: False
```

说明：

```text
P7a second-run 在同一个 cert-dir 下 7/7 命中 cache；
没有触发新的 dynamic test；
depth2 仍未超过 depth1 best；
两个 depth2 candidate 与 parent depth1 持平，一个比 parent 弱。
```

### Manifest 自动生成

生成命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p7a --out-manifest docs\results\p7a_cache_reuse_manifest.json --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --output-dir data\outputs\bounded_two_swap_p7a_second --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --stage-name P7a-cache --description "P7a second-run cache reuse check with the first P7a certificate directory."
```

manifest 路径：

```text
docs/results/p7a_cache_reuse_manifest.json
```

关键 hash：

```text
two_swap_candidates_csv: ec4a0b10ac9a619201015608a8bf1b5152f80b01e870fddb446440ea701d0542
two_swap_attempts_csv: 2ea4a2848d6f37220250ed9eeab77e499052ffc5315931776d89d8233375cf92
two_swap_pipeline_runs_csv: d53ff792abec81c234a6725ed96de69e6d45bffec97c0447365073d39ad29f9c
two_swap_object_size_csv: c566c1fbb78a0b127f9d4c1ea7db9d1b7b65779e41195a5f97b76a3a64df42a2
two_swap_report: 6390dde603804a7a9853e8f2e9ce605f8b9741c6b09587f05e74e2ccfeead661
```

### 本次代码快照：P7a summary 字段

```python
return {
    "seed_candidates": len(seed_rows),
    "attempted_second_swaps": len(attempt_rows),
    "static_candidate_second_swaps": sum(
        1 for row in attempt_rows if row.get("static_decision") == "candidate"
    ),
    "validated_second_swaps": sum(
        1
        for row in attempt_rows
        if row.get("cache_hit") == "True" or row.get("dynamic_test") == "True"
    ),
    "raw_depth2_candidates": raw_depth2_candidates,
    "duplicate_sequences": len(duplicate_rows),
    "unique_depth2_candidates": len(depth2_rows),
    "anchor_runs": sum(1 for source in run_sources if source == "anchor"),
    "depth1_seed_runs": sum(1 for source in run_sources if source == "single_swap"),
    "depth2_candidate_runs": sum(1 for source in run_sources if source == "two_swap"),
    "total_pipeline_runs": len(pipeline_runs),
    "best_depth1_text_delta_pct_vs_anchor": best_depth1,
    "best_depth2_text_delta_pct_vs_anchor": best_depth2,
    "best_depth2_delta_pct_vs_parent": best_depth2_vs_parent,
    "depth2_improves_over_depth1_best": best_depth2 < best_depth1,
}
```

### 本次代码快照：manifest 生成入口

```python
def build_p7a_manifest(
    *,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    stage: str = "P7a",
    description: str = (
        "Bounded two-swap smoke test seeded from P6 one-swap candidates."
    ),
) -> dict[str, Any]:
    out = Path(output_dir)
    candidates_csv = out / "two_swap_candidates.csv"
    attempts_csv = out / "two_swap_attempts.csv"
    pipeline_runs_csv = out / "two_swap_pipeline_runs.csv"
    object_size_csv = out / "two_swap_object_size.csv"
    report_md = out / "two_swap_report.md"
    ...
```

### 风险与备注

- `data/outputs/bounded_two_swap_p7a_second/` 保留为 P7a cache reuse 证据；如果未来 P7b 生成更完整 cache 报告，可以再清理。
- `docs/results/p7a_bounded_two_swap_manifest.json` 仍记录第一次 P7a smoke；`docs/results/p7a_cache_reuse_manifest.json` 记录第二次 cache reuse。
- P7a 仍然只有一个 seed，不能泛化为 two-swap 无收益。
- 当前 code size 仍是 `llc -filetype=obj` 下的 `.text` size，不代表 runtime。

### 下一步

进入 P7b：per-program top-3 seed 的 bounded two-swap controlled experiment。

P7b 必须继续保持：

```text
每一个第二次交换，都重新在对应 seed pipeline 的 prefix state 上做 lazy validation。
```
