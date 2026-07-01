# ECPOR 进度记录：P8a.5 core evidence report

## 2026-07-02：把项目拉回“搜索空间坍缩证据链”

### 当前目标

本轮不加深搜索、不做 beam search、不新增 benchmark。目标是把已有 P4-P8a 结果收束成一个面向最初研究问题的核心证据报告：

```text
哪些顺序被 hard evidence 折叠？
哪些顺序必须保留？
哪些只是 static hint 或 sequence-level duplicate？
哪些 IR 差异传导到了 llc/clang-c object .text？
```

同时修一个命名问题：

```text
object_size_runner.py 的 clang mode 不再只暴露 llc_path 这个名字；
新增 compiler_path，保留 llc_path 兼容旧调用。
```

### 已完成内容

- [x] 更新 `src/ecpor/object_size_runner.py`：
  - 新增 `compiler_path` 参数。
  - `llc_path` 保留为兼容参数。
  - `clang` mode 的调用现在可以写成 `compiler_path=clang_path`。
- [x] 更新 `src/ecpor/codegen_sensitivity.py`：
  - P8a 调用 `measure_object_size()` 时改用 `compiler_path=clang_path`。
- [x] 新增 `src/ecpor/core_evidence_report.py`：
  - 输出 reduction funnel。
  - 输出 hard/soft evidence summary。
  - 输出 codegen sensitivity summary。
  - 生成中文主报告 `ecpor_core_evidence_report.md`。
- [x] 扩展 `src/ecpor/result_manifest.py`：
  - 新增 `build_core_evidence_manifest()`。
  - 新增 CLI：`python -m ecpor.result_manifest core-evidence ...`
- [x] 新增测试：
  - `tests/test_core_evidence_report.py`
  - 更新 `tests/test_object_size_runner.py`
  - 更新 `tests/test_result_manifest.py`
- [x] 生成真实输出：
  - `data/outputs/core_evidence_report/ecpor_core_evidence_report.md`
  - `data/outputs/core_evidence_report/ecpor_reduction_funnel.csv`
  - `data/outputs/core_evidence_report/ecpor_certified_pruning_summary.csv`
  - `data/outputs/core_evidence_report/ecpor_codegen_sensitivity_summary.csv`
- [x] 生成 tracked manifest：
  - `docs/results/core_evidence_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_object_size_runner.py::ObjectSizeRunnerTests::test_compiler_path_alias_avoids_llc_name_for_clang_mode tests\test_core_evidence_report.py::CoreEvidenceReportTests::test_builds_reduction_funnel_evidence_and_codegen_summary
```

初始失败符合预期：

```text
TypeError: measure_object_size() got an unexpected keyword argument 'compiler_path'
ModuleNotFoundError: No module named 'ecpor.core_evidence_report'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_object_size_runner.py tests\test_core_evidence_report.py tests\test_result_manifest.py tests\test_codegen_sensitivity.py
```

结果：

```text
13 passed in 0.91s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
88 passed in 13.00s
```

源码提交：

```text
0310bd948dc972aecae88553dcb3a0a5eb4fc0e9
add P8a core evidence report
```

### 真实运行命令

生成 core evidence report：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.core_evidence_report --p4-attempts data\outputs\lazy_validation_p4_e83c409_first.csv --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7b-attempts data\outputs\bounded_two_swap_p7b\two_swap_attempts.csv --p7b-candidates data\outputs\bounded_two_swap_p7b\two_swap_candidates.csv --p7b-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --p7b-analysis-report data\outputs\bounded_two_swap_p7b_analysis\p7b_analysis_report.md --p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --out data\outputs\core_evidence_report
```

生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest core-evidence --out-manifest docs\results\core_evidence_manifest.json --p4-attempts data\outputs\lazy_validation_p4_e83c409_first.csv --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7b-attempts data\outputs\bounded_two_swap_p7b\two_swap_attempts.csv --p7b-candidates data\outputs\bounded_two_swap_p7b\two_swap_candidates.csv --p7b-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --p7b-analysis-report data\outputs\bounded_two_swap_p7b_analysis\p7b_analysis_report.md --p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --output-dir data\outputs\core_evidence_report --repo-root . --result-generated-from-commit 0310bd948dc972aecae88553dcb3a0a5eb4fc0e9
```

manifest provenance：

```text
ecpor_git_commit: 0310bd948dc972aecae88553dcb3a0a5eb4fc0e9
ecpor_git_dirty: False
```

### Reduction funnel

路径：

```text
data/outputs/core_evidence_report/ecpor_reduction_funnel.csv
```

核心表：

| stage | input | candidate | certified collapsed | not-certified kept | low-priority frozen | duplicates removed | unique |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P4 | 56 | 48 | 32 | 16 | 8 | 0 | 16 |
| P5 | 24 | 16 | 32 | 16 | 8 | 0 | 16 |
| P6 | 16 | 16 | 0 | 16 | 0 | 0 | 16 |
| P7b | 112 | 42 | 58 | 42 | 12 | 20 | 22 |
| P8a | 38 | 38 | 0 | 38 | 0 | 0 | 38 |

解释：

```text
P4 把 56 个 anchor-adjacent 尝试分成：
32 个 certified independent，可以 hard prune；
16 个 not-certified，需要保留；
8 个 low priority，只是 static hint，不是证明。

P7b 的 second-swap 空间中：
42 个 raw depth2 candidate 经 sequence-level dedup 后剩 22 个 unique。
```

### Hard evidence vs soft evidence

路径：

```text
data/outputs/core_evidence_report/ecpor_certified_pruning_summary.csv
```

核心表：

| evidence | count | hard prune | 含义 |
| --- | ---: | --- | --- |
| certified_independent | 90 | True | 同一 state 上 `A;B` 与 `B;A` hard hash 相同 |
| not_certified_independent | 58 | False | hard hash 不同，不能当 independent 剪枝 |
| low_priority | 20 | False | static filter 低优先级，不是证明 |
| sequence_duplicate | 20 | False | pass sequence 重复，可去重但不是语义等价证明 |
| llc_clang_both_smaller | 4 | False | 目标函数层更强 observation，不是 independence proof |

关键边界：

```text
只有 certified_independent 是 hard pruning evidence。
static filter、sequence duplicate、code-size smaller 都不能替代 certificate。
```

### Codegen sensitivity summary

路径：

```text
data/outputs/core_evidence_report/ecpor_codegen_sensitivity_summary.csv
```

核心指标：

```text
DirectionComparisonCandidates: 38
DirectionAgreementCount: 26
DirectionAgreementRate: 68.42%
SmallerUnderBothCount: 4
SmallerOnlyUnderLlcCount: 0
SmallerOnlyUnderClangCount: 5
DirectionDisagreementCount: 12
```

解释：

```text
llc 与 clang-c 的目标函数方向并不完全一致。
当前没有发现 llc-smaller 在 clang 下消失。
4 个 both-smaller candidate 仍然都集中在 Queens 相关 case。
```

### 关键代码快照

`object_size_runner.py` 的命名兼容：

```python
def measure_object_size(
    *,
    program: str,
    candidate_id: str,
    ir_path: str | Path,
    object_path: str | Path,
    compiler_path: ToolPath | None = None,
    llc_path: ToolPath = "llc",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
    compile_mode: CompileMode = "llc",
) -> ObjectSizeRecord:
    ir = Path(ir_path)
    obj = Path(object_path)
    obj.parent.mkdir(parents=True, exist_ok=True)
    compiler = compiler_path if compiler_path is not None else llc_path
    compile_result = _run_compile(ir, obj, compiler, timeout_sec, compile_mode)
```

`core_evidence_report.py` 的 funnel 核心逻辑：

```python
return [
    {
        "stage": "P4",
        "input_count": str(len(p4_attempts)),
        "candidate_count": str(_count_true(p4_attempts, "dynamic_test")),
        "certified_collapsed": str(_count_label(p4_attempts, "certified_independent")),
        "not_certified_kept": str(_count_label(p4_attempts, "not_certified_independent")),
        "low_priority_frozen": str(_count_action(p4_attempts, "skipped_low_priority")),
        "duplicates_removed": "0",
        "unique_candidates": str(_count_label(p4_attempts, "not_certified_independent")),
        "notes": "state-indexed adjacent lazy validation",
    },
    {
        "stage": "P7b",
        "input_count": str(len(p7b_attempts)),
        "candidate_count": str(_as_int(p7b_analysis.get("RawDepth2Candidates"), _count_label(p7b_attempts, "not_certified_independent"))),
        "certified_collapsed": str(_count_label(p7b_attempts, "certified_independent")),
        "not_certified_kept": str(_count_label(p7b_attempts, "not_certified_independent")),
        "low_priority_frozen": str(_count_action(p7b_attempts, "skipped_low_priority")),
        "duplicates_removed": str(_as_int(p7b_analysis.get("DuplicateSequences"), 0)),
        "unique_candidates": str(_as_int(p7b_analysis.get("UniqueDepth2Candidates"), len(p7b_depth2))),
        "notes": "bounded depth2 candidates after sequence-level dedup",
    },
]
```

`result_manifest.py` 的 P8a.5 manifest：

```python
def build_core_evidence_manifest(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    p7b_attempts_csv: str | Path,
    p7b_candidates_csv: str | Path,
    p7b_object_size_csv: str | Path,
    p7b_analysis_report: str | Path,
    p8a_compare_csv: str | Path,
    output_dir: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "ecpor_core_evidence_report.md"
    return build_result_manifest(
        stage="P8a.5",
        description="Core evidence report for ECPOR pruning and objective-layer sensitivity.",
        inputs={
            "p4_attempts_csv": p4_attempts_csv,
            "p5_candidates_csv": p5_candidates_csv,
            "p5_pipeline_runs_csv": p5_pipeline_runs_csv,
            "p6_object_size_csv": p6_object_size_csv,
            "p7b_attempts_csv": p7b_attempts_csv,
            "p7b_candidates_csv": p7b_candidates_csv,
            "p7b_object_size_csv": p7b_object_size_csv,
            "p7b_analysis_report": p7b_analysis_report,
            "p8a_compare_csv": p8a_compare_csv,
        },
        outputs={
            "output_dir": out,
            "ecpor_core_evidence_report": report,
            "ecpor_reduction_funnel_csv": out / "ecpor_reduction_funnel.csv",
            "ecpor_certified_pruning_summary_csv": out / "ecpor_certified_pruning_summary.csv",
            "ecpor_codegen_sensitivity_summary_csv": out / "ecpor_codegen_sensitivity_summary.csv",
        },
        tools={},
        summary=_filter_keys(
            _parse_key_value_report(report),
            CORE_EVIDENCE_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
    )
```

### 风险与备注

```text
1. 本轮是 report-only，没有新增搜索、certificate、runtime benchmark。
2. P8a.5 的 “certified_independent = 90” 是 P4 和 P7b 两阶段相加，不代表全局所有状态。
3. sequence duplicate 只说明 pass sequence 重复，不说明 IR 或语义等价。
4. llc_clang_both_smaller 是目标层 observation，不是 pruning proof。
5. Queens 归因实验尚未做；本轮先把主线证据链收束清楚。
```

### 下一步

建议下一步做 Queens effect attribution 小实验，而不是 P8b 或 depth=3：

```text
1. 只针对 testsuite_stanford_queens 的 instcombine/simplifycfg case。
2. 比较 prefix 后 A、B、AB、BA、本地特征和 suffix 后最终特征。
3. 同时记录 llc 与 clang-c text delta。
4. 输出 observed attribution hypothesis，不写成强因果证明。
```
