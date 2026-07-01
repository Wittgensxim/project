# ECPOR 进度记录：P8a.6 core evidence 语义收尾

## 2026-07-02：把核心证据报告拆成两条不混淆的证据线

### 当前目标

本轮是 P8a.5 的小收尾，不新增搜索、不新增 certificate、不扩大 benchmark。目标是修正 core evidence report 的语义边界：

```text
validation funnel 只统计 state-indexed adjacent swap 的验证事件；
candidate propagation funnel 只统计候选从 P5/P6/P7b/P8a 怎样继续流动；
objective-layer evidence 单独呈现 codegen 方向比较；
certified_independent 这种容易误读的总数改成 certified_independent_events。
```

这样报告就不会把“证书剪枝”“候选传播”“目标函数观察”混成一个 reduction funnel。

### 已完成内容

- [x] 更新 `src/ecpor/core_evidence_report.py`：
  - 将旧的 `ecpor_reduction_funnel.csv` 拆成 `ecpor_validation_funnel.csv` 与 `ecpor_candidate_propagation_funnel.csv`。
  - 将旧的 `ecpor_codegen_sensitivity_summary.csv` 改为 `ecpor_objective_layer_summary.csv`。
  - 将 `certified_independent` 改写为 `certified_independent_events`。
  - 为 hard/soft evidence 增加 `scope` 与 `proof_level`。
  - 报告新增 `Relation to Original Research Question` 段落。
- [x] 更新 `src/ecpor/result_manifest.py`：
  - core-evidence manifest 不再引用旧 CSV。
  - manifest 输出改为 validation funnel、candidate propagation funnel、certified pruning summary、objective-layer summary。
- [x] 更新测试：
  - `tests/test_core_evidence_report.py`
  - `tests/test_result_manifest.py`
- [x] 重新生成真实结果：
  - `data/outputs/core_evidence_report/ecpor_core_evidence_report.md`
  - `data/outputs/core_evidence_report/ecpor_validation_funnel.csv`
  - `data/outputs/core_evidence_report/ecpor_candidate_propagation_funnel.csv`
  - `data/outputs/core_evidence_report/ecpor_certified_pruning_summary.csv`
  - `data/outputs/core_evidence_report/ecpor_objective_layer_summary.csv`
- [x] 删除旧语义输出：
  - `data/outputs/core_evidence_report/ecpor_reduction_funnel.csv`
  - `data/outputs/core_evidence_report/ecpor_codegen_sensitivity_summary.csv`
- [x] 重新生成 tracked manifest：
  - `docs/results/core_evidence_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_core_evidence_report.py::CoreEvidenceReportTests::test_builds_reduction_funnel_evidence_and_codegen_summary tests\test_result_manifest.py::ResultManifestTests::test_builds_core_evidence_manifest
```

初始失败符合预期：

```text
旧实现还没有生成 ecpor_validation_funnel.csv；
manifest 还在引用旧的 ecpor_reduction_funnel_csv / ecpor_codegen_sensitivity_summary_csv。
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_core_evidence_report.py::CoreEvidenceReportTests::test_builds_reduction_funnel_evidence_and_codegen_summary tests\test_result_manifest.py::ResultManifestTests::test_builds_core_evidence_manifest
```

结果：

```text
2 passed in 0.13s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_core_evidence_report.py tests\test_result_manifest.py tests\test_codegen_sensitivity.py tests\test_object_size_runner.py
```

结果：

```text
13 passed in 0.77s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
88 passed in 11.16s
```

源码提交：

```text
a5269597f2e75922a167925cdc0d1ef947fda9e7
refine core evidence report semantics
346dbedd1c4beabaa80268923ad0904cf4ec8aca
label core evidence manifest as P8a6
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
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest core-evidence --out-manifest docs\results\core_evidence_manifest.json --p4-attempts data\outputs\lazy_validation_p4_e83c409_first.csv --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7b-attempts data\outputs\bounded_two_swap_p7b\two_swap_attempts.csv --p7b-candidates data\outputs\bounded_two_swap_p7b\two_swap_candidates.csv --p7b-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --p7b-analysis-report data\outputs\bounded_two_swap_p7b_analysis\p7b_analysis_report.md --p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --output-dir data\outputs\core_evidence_report --repo-root . --result-generated-from-commit 346dbedd1c4beabaa80268923ad0904cf4ec8aca
```

manifest provenance：

```text
result_generated_from_commit: 346dbedd1c4beabaa80268923ad0904cf4ec8aca
ecpor_git_commit: 346dbedd1c4beabaa80268923ad0904cf4ec8aca
ecpor_git_dirty: False
```

### Validation funnel

路径：

```text
data/outputs/core_evidence_report/ecpor_validation_funnel.csv
```

核心表：

| stage | basis | attempts | static candidate | dynamic tests | cache hits | certified events | not-certified events | low-priority events | run failed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P4 | state_indexed_adjacent_swap_events | 56 | 48 | 48 | 0 | 32 | 16 | 8 | 0 |
| P7b | state_indexed_adjacent_swap_events | 112 | 100 | 95 | 5 | 58 | 42 | 12 | 0 |

解释：

```text
P4 与 P7b 的 validation funnel 只回答一个问题：
在当前 materialized state 上，某个 adjacent swap 是否已经被 hard certificate 验证。

这里的 90 个 certified_independent_events 是事件数，不是全局 pass-pair 规则。
```

### Candidate propagation funnel

路径：

```text
data/outputs/core_evidence_report/ecpor_candidate_propagation_funnel.csv
```

核心表：

| stage | basis | anchors | single-swap | raw depth2 | duplicates removed | unique depth2 | object-size evaluated | clang-c compared |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P5 | candidate_pipelines_from_P4_evidence | 8 | 16 | 0 | 0 | 0 | 0 | 0 |
| P6 | single_swap_candidate_object_eval | 8 | 16 | 0 | 0 | 0 | 16 | 0 |
| P7b | depth2_candidate_pipelines | 8 | 0 | 42 | 20 | 22 | 22 | 0 |
| P8a | objective_layer_codegen_comparison | 0 | 0 | 0 | 0 | 0 | 0 | 38 |

解释：

```text
candidate propagation funnel 只说明候选怎样继续进入后续阶段。
它不表达 hard pruning，也不把 P8a 的 codegen 方向比较写成 reduction proof。
```

### Hard evidence vs soft evidence

路径：

```text
data/outputs/core_evidence_report/ecpor_certified_pruning_summary.csv
```

核心表：

| evidence event | count | scope | hard prune | proof level |
| --- | ---: | --- | --- | --- |
| certified_independent_events | 90 | state-indexed adjacent swap events | True | hard |
| not_certified_events | 58 | state-indexed adjacent swap events | False | hard_negative_for_equality |
| low_priority_events | 20 | static filter classification events | False | soft |
| sequence_duplicates | 20 | identical pass sequence paths | False | syntactic_dedup |
| llc_clang_both_smaller_object | 4 | objective-layer object-size observations | False | target_layer |

关键边界：

```text
只有 certified_independent_events 是 hard pruning evidence。
not_certified_events 是 hard negative：说明不能剪。
low_priority_events、sequence_duplicates、llc_clang_both_smaller_object 都不是 independence proof。
```

### Objective-layer evidence

路径：

```text
data/outputs/core_evidence_report/ecpor_objective_layer_summary.csv
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
P8a 只说明目标函数层存在 codegen path sensitivity。
它可以提示哪些 IR 差异值得继续看，但不能替代 certificate，也不能证明 pass independence。
```

### 关键代码快照

新输出字段定义：

```python
VALIDATION_FUNNEL_FIELDS = [
    "stage",
    "count_basis",
    "attempted_swaps",
    "static_candidate_swaps",
    "dynamic_tests",
    "cache_hits",
    "certified_independent_events",
    "not_certified_events",
    "low_priority_events",
    "run_failed",
    "notes",
]

CANDIDATE_PROPAGATION_FIELDS = [
    "stage",
    "count_basis",
    "anchor_candidates",
    "single_swap_candidates",
    "raw_depth2_candidates",
    "duplicates_removed",
    "unique_depth2_candidates",
    "object_size_evaluated_candidates",
    "clang_c_compared_candidates",
    "notes",
]
```

输出文件写入逻辑：

```python
_write_csv(
    output_root / "ecpor_validation_funnel.csv",
    validation_rows,
    VALIDATION_FUNNEL_FIELDS,
)
_write_csv(
    output_root / "ecpor_candidate_propagation_funnel.csv",
    propagation_rows,
    CANDIDATE_PROPAGATION_FIELDS,
)
_write_csv(
    output_root / "ecpor_certified_pruning_summary.csv",
    pruning_rows,
    PRUNING_FIELDS,
)
_write_csv(
    output_root / "ecpor_objective_layer_summary.csv",
    objective_rows,
    OBJECTIVE_LAYER_FIELDS,
)
```

hard evidence 命名修正：

```python
{
    "stage": "P4/P7b",
    "evidence_event": "certified_independent_events",
    "count": str(certified),
    "scope": "state-indexed adjacent swap events",
    "hard_prune": "True",
    "proof_level": "hard",
    "evidence_source": "hard hash equality certificate",
    "meaning": "A;B and B;A are equal for the same materialized state",
}
```

manifest 输出键修正：

```python
outputs={
    "output_dir": out,
    "ecpor_core_evidence_report": report,
    "ecpor_validation_funnel_csv": out / "ecpor_validation_funnel.csv",
    "ecpor_candidate_propagation_funnel_csv": out
    / "ecpor_candidate_propagation_funnel.csv",
    "ecpor_certified_pruning_summary_csv": out
    / "ecpor_certified_pruning_summary.csv",
    "ecpor_objective_layer_summary_csv": out
    / "ecpor_objective_layer_summary.csv",
}
```

### data 保留状态

`data/outputs/core_evidence_report/` 当前只保留 5 个必要文件：

```text
ecpor_candidate_propagation_funnel.csv
ecpor_certified_pruning_summary.csv
ecpor_core_evidence_report.md
ecpor_objective_layer_summary.csv
ecpor_validation_funnel.csv
```

旧文件 `ecpor_reduction_funnel.csv` 和 `ecpor_codegen_sensitivity_summary.csv` 已删除，因为它们的语义会误导后续阅读。

### 风险与备注

```text
1. 本轮是语义收尾，不改变已有实验数据。
2. P8a.6 的 certified_independent_events = 90 仍然只覆盖 P4/P7b 已观测到的 state-indexed adjacent swap 事件。
3. P8a 的目标函数观察已经从 pruning summary 中拆出，避免被误读为 reduction proof。
4. 旧 P8a.5 文档仍作为历史记录保留；以后引用当前结论时应优先使用本 P8a.6 文档。
```

### 下一步

下一步进入 Queens effect attribution 小实验：

```text
1. 只分析当前 both-smaller 最稳定来源 testsuite_stanford_queens。
2. 比较 prefix 后 A、B、AB、BA 的 IR feature 和最终 suffix 后 feature。
3. 同时保留 llc 与 clang-c 的 object .text delta。
4. 输出 observed attribution hypothesis，不写成强因果证明。
```
