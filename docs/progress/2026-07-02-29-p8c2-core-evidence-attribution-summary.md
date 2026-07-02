# ECPOR 进度记录：P8c.2 attribution summary 纳入 core evidence

## 2026-07-02：把 Queens opcode attribution 放回总证据链

### 当前目标

本轮根据最新建议做一个小收尾：不扩大 benchmark、不加深搜索、不新增 certificate，而是把 P8c/P8c.1 的 Queens observed attribution 接入核心证据报告。

目标是让 `ecpor_core_evidence_report.md` 不只说明 pruning / candidate propagation / objective-layer 现象，还能在同一份主报告里记录一个稳定 case 的解释性证据：

```text
program = testsuite_stanford_queens
pair = simplifycfg,instcombine
scope = single-state observed attribution
opcode_delta = num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1
llc_text_delta_pct = -4.401651
clang_text_delta_pct = -1.673640
evidence_level = observed attribution, not causal proof
```

### 已完成内容

- [x] 更新 `src/ecpor/core_evidence_report.py`：
  - 新增可选 P8c 输入参数。
  - 新增 `ecpor_attribution_summary.csv`。
  - 在主报告中新增 `Observed Attribution Summary`。
  - summary 新增 `AttributionCases` 与 `AttributionObservedButNotCausalProof`。
- [x] 更新 `src/ecpor/result_manifest.py`：
  - core evidence manifest 的 stage 更新为 `P8c.2`。
  - 记录 P8c attribution 输入 hash。
  - 记录 `ecpor_attribution_summary_csv` 输出 hash。
- [x] 更新测试：
  - `tests/test_core_evidence_report.py`
  - `tests/test_result_manifest.py`
- [x] 重新生成真实 core evidence 输出：
  - `data/outputs/core_evidence_report/ecpor_attribution_summary.csv`
  - `data/outputs/core_evidence_report/ecpor_core_evidence_report.md`
- [x] 重新生成 tracked manifest：
  - `docs/results/core_evidence_manifest.json`
- [x] 更新：
  - `README.md`
  - `docs/project_progress.md`
  - `docs/data_retention_manifest.md`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_core_evidence_report.py::CoreEvidenceReportTests::test_builds_reduction_funnel_evidence_and_codegen_summary
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_core_evidence_manifest
```

初始失败符合预期：

```text
TypeError: run_core_evidence_report() got an unexpected keyword argument 'p8c_attribution_report'
AssertionError: 'ecpor_attribution_summary_csv' not found in loaded["outputs"]
```

补 manifest 输入记录时继续按 RED/GREEN：

```text
TypeError: build_core_evidence_manifest() got an unexpected keyword argument 'p8c_attribution_report'
```

补 stage 命名时继续按 RED/GREEN：

```text
AssertionError: 'P8a.6' != 'P8c.2'
```

最终相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_core_evidence_report.py tests\test_result_manifest.py tests\test_effect_attribution.py tests\test_codegen_sensitivity.py tests\test_object_size_runner.py
```

结果：

```text
15 passed in 1.26s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
90 passed
```

代码层提交：

```text
fc94e47 integrate attribution into core evidence
146ae56 record attribution inputs in core manifest
6225f27 label core evidence attribution manifest
```

### 真实运行命令

重新生成 P8c.2 core evidence report：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.core_evidence_report --p4-attempts data\outputs\lazy_validation_p4_e83c409_first.csv --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7b-attempts data\outputs\bounded_two_swap_p7b\two_swap_attempts.csv --p7b-candidates data\outputs\bounded_two_swap_p7b\two_swap_candidates.csv --p7b-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --p7b-analysis-report data\outputs\bounded_two_swap_p7b_analysis\p7b_analysis_report.md --p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --p8c-attribution-report data\outputs\effect_attribution_queens\attribution_report.md --p8c-feature-deltas data\outputs\effect_attribution_queens\feature_deltas.csv --p8c-opcode-delta data\outputs\effect_attribution_queens\opcode_delta.csv --p8c-object-size data\outputs\effect_attribution_queens\object_size.csv --out data\outputs\core_evidence_report
```

重新生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest core-evidence --out-manifest docs\results\core_evidence_manifest.json --p4-attempts data\outputs\lazy_validation_p4_e83c409_first.csv --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7b-attempts data\outputs\bounded_two_swap_p7b\two_swap_attempts.csv --p7b-candidates data\outputs\bounded_two_swap_p7b\two_swap_candidates.csv --p7b-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --p7b-analysis-report data\outputs\bounded_two_swap_p7b_analysis\p7b_analysis_report.md --p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --p8c-attribution-report data\outputs\effect_attribution_queens\attribution_report.md --p8c-feature-deltas data\outputs\effect_attribution_queens\feature_deltas.csv --p8c-opcode-delta data\outputs\effect_attribution_queens\opcode_delta.csv --p8c-object-size data\outputs\effect_attribution_queens\object_size.csv --output-dir data\outputs\core_evidence_report --repo-root . --result-generated-from-commit 6225f27918d8af0195601c2222c642496abae24d
```

### 真实输出

`data/outputs/core_evidence_report/ecpor_attribution_summary.csv`：

```csv
program,pair,scope,local_feature_delta,final_feature_delta,opcode_delta,llc_text_delta_pct,clang_text_delta_pct,evidence_level
testsuite_stanford_queens,"simplifycfg,instcombine",single-state observed attribution,num_instructions_delta=-1,num_instructions_delta=-1,num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1,-4.401651,-1.673640,"observed attribution, not causal proof"
```

`docs/results/core_evidence_manifest.json` 关键字段：

```text
stage = P8c.2
ecpor_git_commit = 6225f27918d8af0195601c2222c642496abae24d
ecpor_git_dirty = False
result_generated_from_commit = 6225f27918d8af0195601c2222c642496abae24d
AttributionCases = 1
AttributionObservedButNotCausalProof = True
```

manifest 已记录 P8c 输入：

```text
p8c_attribution_report
p8c_feature_deltas_csv
p8c_opcode_delta_csv
p8c_object_size_csv
```

### 代码快照

`core_evidence_report.py` 新增输出字段：

```python
ATTRIBUTION_SUMMARY_FIELDS = [
    "program",
    "pair",
    "scope",
    "local_feature_delta",
    "final_feature_delta",
    "opcode_delta",
    "llc_text_delta_pct",
    "clang_text_delta_pct",
    "evidence_level",
]
```

`run_core_evidence_report()` 新增可选 P8c 输入：

```python
def run_core_evidence_report(
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
    p8c_attribution_report: str | Path | None = None,
    p8c_feature_deltas_csv: str | Path | None = None,
    p8c_opcode_delta_csv: str | Path | None = None,
    p8c_object_size_csv: str | Path | None = None,
) -> CoreEvidenceReport:
```

attribution row 构造：

```python
def _build_attribution_rows(
    *,
    attribution_report: Mapping[str, Any],
    feature_deltas: Sequence[dict[str, str]],
    opcode_deltas: Sequence[dict[str, str]],
    object_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    if not attribution_report and not feature_deltas and not opcode_deltas:
        return []

    program = str(attribution_report.get("Program") or _first_value(object_rows, "program"))
    if not program:
        program = "testsuite_stanford_queens"
    local_features = _comparison_row(feature_deltas, "local_AB_vs_BA")
    final_features = _comparison_row(feature_deltas, "final_AB_vs_BA")
    final_opcodes = _comparison_row(opcode_deltas, "final_AB_vs_BA")
    return [
        {
            "program": program,
            "pair": "simplifycfg,instcombine",
            "scope": "single-state observed attribution",
            "local_feature_delta": _format_nonzero_deltas(local_features),
            "final_feature_delta": _format_nonzero_deltas(final_features),
            "opcode_delta": (
                str(attribution_report.get("FinalOpcodeDeltaNonZero") or "")
                or _format_nonzero_deltas(final_opcodes)
            ),
            "llc_text_delta_pct": _object_text_delta_pct(object_rows, "llc"),
            "clang_text_delta_pct": _object_text_delta_pct(object_rows, "clang"),
            "evidence_level": "observed attribution, not causal proof",
        }
    ]
```

core report 新增段落：

```python
lines.extend(
    [
        "",
        "## Observed Attribution Summary",
        "",
        "This is observed attribution evidence, not pruning evidence or causal proof.",
        "",
        f"AttributionCases: {len(attribution_rows)}",
        f"AttributionObservedButNotCausalProof: {bool(attribution_rows)}",
        "",
        "| program | pair | scope | local feature delta | final feature delta | opcode delta | llc text delta % | clang text delta % | evidence level |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
)
```

manifest 输入记录：

```python
inputs.update(
    _optional_paths(
        p8c_attribution_report=p8c_attribution_report,
        p8c_feature_deltas_csv=p8c_feature_deltas_csv,
        p8c_opcode_delta_csv=p8c_opcode_delta_csv,
        p8c_object_size_csv=p8c_object_size_csv,
    )
)
```

manifest stage 更新：

```python
return build_result_manifest(
    stage="P8c.2",
    description=(
        "Core evidence report with P8c Queens observed attribution summary."
    ),
```

### 语义边界

1. `ecpor_attribution_summary.csv` 是解释性 evidence，不是 hard pruning evidence。
2. `AttributionObservedButNotCausalProof = True` 只表示当前报告里包含 observed attribution case，不表示证明了因果定理。
3. 当前只有 Queens 单程序、单 state、单 pair，不能推广为 `simplifycfg` 总应在 `instcombine` 前。
4. 本轮没有新增搜索、没有新增 certificate、没有 runtime benchmark。

### data 保留情况

`data/outputs/core_evidence_report/` 当前保留 6 个必要文件：

```text
ecpor_attribution_summary.csv
ecpor_candidate_propagation_funnel.csv
ecpor_certified_pruning_summary.csv
ecpor_core_evidence_report.md
ecpor_objective_layer_summary.csv
ecpor_validation_funnel.csv
```

没有新增临时 work 目录。

### 下一步

下一步进入 P8b-0 benchmark ingestion：

```text
src/ecpor/benchmark_ingest.py
tests/test_benchmark_ingest.py
configs/benchmarks_p8b.yaml
```

目标是从 `E:\llvm-test-suite` 自动筛选 8 个小程序，记录成功和失败原因，再进入 P8b-1 的新 8 程序 full matrix / static filter recall 验证。
