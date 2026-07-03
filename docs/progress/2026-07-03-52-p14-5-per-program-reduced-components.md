# P14.5 per-program reduced components

## 当前目标

P14.5 的目标是补上 P13 和 P14 之间的一个解释缺口：

```text
P13  = corpus-union graph / corpus-level search-space diagnostic
P14  = instcombine/simplifycfg objective hotspot pair-family analysis
P14.5 = per-program reduced component analysis
```

这一步只读取已有 retained evidence，不运行 LLVM、不新增 certificate、不启动 search。它回答的问题是：P13 的 corpus-union conservative graph 是一个 8-pass 大 component，这是否只是把 24 个程序的边合并以后造成的全局现象；如果按每个程序单独建图，component 是否会拆开。

## 完成内容

新增代码：

```text
src/ecpor/reduced_components_per_program.py
tests/test_reduced_components_per_program.py
```

扩展 manifest 支持：

```text
src/ecpor/manifest_builders.py
src/ecpor/manifest_cli.py
tests/test_result_manifest.py
```

生成 P14.5 输出：

```text
data/outputs/reduced_components_per_program/per_program_components.csv
data/outputs/reduced_components_per_program/per_program_search_space_estimate.csv
data/outputs/reduced_components_per_program/per_benchmark_search_space_summary.csv
data/outputs/reduced_components_per_program/reduced_components_per_program_report.md
docs/results/reduced_components_per_program_manifest.json
```

`data/outputs/...` 是生成产物，按 data retention 规则保留但不纳入 Git；tracked evidence 入口是：

```text
docs/results/reduced_components_per_program_manifest.json
```

## 输入证据

P14.5 读取这些已有结果：

```text
configs/pipeline_scalar.yaml
data/outputs/cert_summary.csv
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_p9_diverse8_pre.csv
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p8b_misc8/attempts.csv
data/outputs/lazy_validation_p9_diverse8/attempts.csv
data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv
data/outputs/codegen_sensitivity_p8b_misc8/p8a_codegen_direction_compare.csv
data/outputs/codegen_sensitivity_p9_diverse8/p8a_codegen_direction_compare.csv
data/outputs/core_evidence_report/ecpor_attribution_summary.csv
data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv
```

## 三种图模式

`input_full_matrix`：

每个程序读取 28 个 unordered pair 的 full matrix，取 `label = not_certified_independent` 的 pair 作为边。它覆盖完整 pair matrix，但只代表 input-state，不是 prefix-safe 结论。

scope warning：

```text
input_full_matrix_only_not_prefix_safe
```

`prefix_adjacent`：

每个程序读取 P4/P8b/P9 lazy validation 的 adjacent prefix-state attempts，取 `label = not_certified_independent` 的 adjacent pair 作为边。它是真实 prefix state，但只覆盖当前 pipeline 的 7 个 adjacent pair，不覆盖完整 28 pair。

scope warning：

```text
prefix_adjacent_only_not_full_pair_coverage
```

`objective_sensitive`：

读取 llc/clang 都变小的 depth1 single-swap codegen case，以及 attribution case。它只表示目标层热点，不是 hard prune 证明。

scope warning：

```text
objective_layer_only_not_hard_prune
```

## 真实结果

P14.5 报告摘要：

```text
Programs: 24
GraphModes: 3
InputFullMatrixProgramsWithSingleComponent8: 2
InputFullMatrixProgramsWithMultipleComponents: 22
PrefixAdjacentProgramsWithSingleComponent8: 0
PrefixAdjacentProgramsWithMultipleComponents: 24
ObjectiveSensitiveProgramsWithNonSingletonComponent: 2
NewExperiments: False
NewCertificates: False
NewSearch: False
```

解释：

1. P13 的 `ConservativeReductionRatio = 0.0000%` 是 corpus-union conservative graph 的诊断结果，不能直接读成“每个程序本地都没有 component split”。
2. 在 `input_full_matrix` 模式下，`22/24` 个程序出现多个 component，说明 program-local 视角确实比 corpus-union 更可分。
3. 但 `input_full_matrix` 只代表 input state，因此不能拿来做 prefix-state hard prune。
4. 在 `prefix_adjacent` 模式下，`24/24` 个程序都有多个 component，但这是因为只观察 7 个 adjacent pair，不能当成完整 28 pair 覆盖。
5. `objective_sensitive` 只有 `2` 个程序出现非 singleton component，仍然是 Queens 和 ffbench 的 `{instcombine, simplifycfg}` 热点。

## 汇总表解释

`per_benchmark_search_space_summary.csv`：

```csv
benchmark_set,graph_mode,programs,median_reduction_ratio,mean_reduction_ratio,programs_with_single_component_8,programs_with_multiple_components,median_component_count,max_component_size_median
Stanford-8,input_full_matrix,8,98.2143%,86.3095%,1,7,3.0000,6.0000
Stanford-8,prefix_adjacent,8,99.9876%,99.9826%,0,8,6.0000,2.5000
Stanford-8,objective_sensitive,8,99.9975%,99.9972%,0,8,8.0000,1.0000
Misc8,input_full_matrix,8,99.7024%,95.1265%,0,8,4.0000,5.0000
Misc8,prefix_adjacent,8,99.9901%,99.9833%,0,8,6.0000,2.0000
Misc8,objective_sensitive,8,99.9975%,99.9972%,0,8,8.0000,1.0000
Diverse8,input_full_matrix,8,99.9690%,87.4169%,1,7,6.5000,2.5000
Diverse8,prefix_adjacent,8,99.9963%,99.9882%,0,8,7.5000,1.5000
Diverse8,objective_sensitive,8,99.9975%,99.9975%,0,8,8.0000,1.0000
```

字段含义：

- `programs`：该 benchmark set 中参与统计的程序数。
- `median_reduction_ratio` / `mean_reduction_ratio`：把每个程序的 component 内部 factorial product 与原始 `8!` 比较得到的粗略 reduction。它是诊断指标，不是新的搜索结果。
- `programs_with_single_component_8`：该模式下仍形成一个 8-pass 大 component 的程序数。
- `programs_with_multiple_components`：该模式下拆成多个 component 的程序数。
- `median_component_count`：每个程序 component 数量的中位数。
- `max_component_size_median`：每个程序最大 component size 的中位数。

## 运行过的例子

`testsuite_stanford_bubblesort` 的 input-state full matrix：

```csv
benchmark_set,program,graph_mode,pass_count,edge_count,component_sizes,original_factorial,within_component_factorial_product,reduction_ratio,scope_warning
Stanford-8,testsuite_stanford_bubblesort,input_full_matrix,8,9,6;1;1,40320,720,98.2143%,input_full_matrix_only_not_prefix_safe
```

含义：在 bubblesort 的 input-state full matrix 中，not-certified 边把 6 个 pass 连成一个大 component，另外 2 个 pass 是 singleton。粗略上界从 `8! = 40320` 降到 `6! = 720`。但是这个结论只属于 input state，不保证 prefix state 可用。

`testsuite_stanford_oscar` 的 input-state full matrix：

```csv
Stanford-8,testsuite_stanford_oscar,input_full_matrix,8,15,8,40320,40320,0.0000%,input_full_matrix_only_not_prefix_safe
```

含义：oscar 的 program-local input-state full matrix 自身就是 8-pass 大 component，因此在这个 scope 下没有 reduction。

objective-sensitive 非 singleton component：

```text
Stanford-8    testsuite_stanford_queens  objective_sensitive_c3  instcombine  2
Stanford-8    testsuite_stanford_queens  objective_sensitive_c3  simplifycfg  2
Misc8         testsuite_misc_ffbench     objective_sensitive_c3  instcombine  2
Misc8         testsuite_misc_ffbench     objective_sensitive_c3  simplifycfg  2
```

含义：P14 的 hotspot 没有被推翻，反而被 P14.5 放回 program-local 视角中：目标层的非 singleton component 仍集中在 `instcombine/simplifycfg`，对应 Queens 和 ffbench 两个 both-smaller attribution case。

## 关键代码快照

### P14.5 入口

```python
def build_reduced_components_per_program(
    *,
    pipeline_passes: Sequence[str],
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    pass_names = [str(pass_name) for pass_name in pipeline_passes]
    if not pass_names:
        raise ValueError("pipeline_passes must not be empty")

    program_sets = _collect_program_sets(
        full_matrix_rows,
        prefix_attempt_rows,
        codegen_rows,
        attribution_rows,
    )
    edge_sets = {
        "input_full_matrix": _build_not_certified_edges(full_matrix_rows, pass_names),
        "prefix_adjacent": _build_not_certified_edges(prefix_attempt_rows, pass_names),
        "objective_sensitive": _build_objective_edges(
            codegen_rows=codegen_rows,
            attribution_rows=attribution_rows,
            pass_names=pass_names,
        ),
    }
```

### objective-sensitive 边选择

```python
def _build_objective_edges(
    *,
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    pass_names: Sequence[str],
) -> dict[str, set[tuple[str, str]]]:
    by_program: dict[str, set[tuple[str, str]]] = defaultdict(set)
    pass_set = set(pass_names)
    pass_order = {name: index for index, name in enumerate(pass_names)}
    for row in codegen_rows:
        if not _is_depth1_single_swap(row) or not _row_has_both_smaller(row):
            continue
        program = str(row.get("program", "")).strip()
        pair = _row_pair(row, pass_set=pass_set, pass_order=pass_order)
        if program and pair:
            by_program[program].add(pair)
    for row in attribution_rows:
        program = str(row.get("program", "")).strip()
        pair = _row_pair(row, pass_set=pass_set, pass_order=pass_order)
        if program and pair:
            by_program[program].add(pair)
    return by_program
```

### search-space 粗略估计

```python
def _search_space_row(
    *,
    benchmark_set: str,
    program: str,
    mode: str,
    pass_count: int,
    edge_count: int,
    components: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    sizes = [int(component["component_size"]) for component in components]
    original = math.factorial(pass_count)
    product = 1
    for size in sizes:
        product *= math.factorial(size)
    reduction = 0.0 if original == 0 else (1.0 - (product / original)) * 100.0
```

### manifest scope

```python
"scope_limits": {
    "stage": "P14.5",
    "summary_only": True,
    "per_program_graph_analysis_only": True,
    "new_experiments": False,
    "new_certificates": False,
    "new_search": False,
    "runtime_benchmarks": False,
    "passspec_behavior_change": False,
    "static_filter_behavior_change": False,
}
```

## 验证结果

先写测试后实现，目标测试曾按预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.reduced_components_per_program'
AttributeError: module 'ecpor.result_manifest' has no attribute 'build_reduced_components_per_program_manifest'
```

实现后目标测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_reduced_components_per_program.py tests/test_result_manifest.py::ResultManifestTests::test_result_manifest_split_modules_keep_compatibility_exports tests/test_result_manifest.py::ResultManifestTests::test_builds_reduced_components_per_program_manifest -q
```

结果：

```text
5 passed in 0.11s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
163 passed in 24.38s
```

生成 P14.5 结果：

```powershell
$env:PYTHONPATH = 'src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.reduced_components_per_program
```

生成 P14.5 manifest：

```powershell
$env:PYTHONPATH = 'src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest reduced-components-per-program `
  --out-manifest docs\results\reduced_components_per_program_manifest.json `
  --pipeline-config configs\pipeline_scalar.yaml `
  --output-dir data\outputs\reduced_components_per_program `
  --repo-root . `
  --result-generated-from-commit 343266dc86963dc3052703793eeac2220662aa3f
```

manifest 记录：

```text
result_generated_from_commit = 343266dc86963dc3052703793eeac2220662aa3f
ecpor_git_commit = 343266dc86963dc3052703793eeac2220662aa3f
ecpor_git_dirty = false
summary_only = true
per_program_graph_analysis_only = true
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
passspec_behavior_change = false
static_filter_behavior_change = false
```

## 风险和边界

1. `input_full_matrix` 的 component split 只说明 input-state full matrix 的局部结构，不能复用到 prefix state。
2. `prefix_adjacent` 的 component split 只覆盖当前 pipeline 的 7 个 adjacent pair，不能声称覆盖全部 28 pair。
3. `objective_sensitive` 只说明目标层热点，不是 hard prune 规则。
4. `reduction_ratio` 是粗略上界估计，默认 component 之间按当前 pipeline 顺序锚定，只允许 component 内部排列。
5. P13、P14、P14.5 的关系需要在后续报告中保持清楚：P13 是 corpus-union，P14 是 hotspot pair family，P14.5 是 program-local diagnostic。

## 下一步

可以进入 P15。建议先做一个很小的决策文档，而不是继续搜索：

```text
P15A: targeted witness-state collection for instcombine/simplifycfg
P15B: final research report / paper draft freeze
```

如果继续技术分析，只围绕 `instcombine/simplifycfg` 做 witness-state collection；如果准备收束，则把 P12-P14.5 作为“为什么不继续扩展搜索”的核心证据写进最终报告。
