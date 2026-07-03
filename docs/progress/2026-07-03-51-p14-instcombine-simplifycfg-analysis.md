# P14 instcombine/simplifycfg pair-family analysis

> P14.5 后的边界更正：P14 是针对 corpus-level graph 中唯一 objective-sensitive hotspot `instcombine/simplifycfg` 的 pair-family analysis。它不替代 per-program reduced component analysis，也不能直接推出 program-local search-space reduction。

## 当前目标

P14 的目标是只读取已有 retained evidence，聚焦 P13 objective-sensitive graph 中唯一非 singleton 热点：

```text
instcombine,simplifycfg
```

本阶段回答的问题是：这个 pair 在 24 个程序中什么时候只是 order-sensitive，什么时候生成 one-swap candidate，什么时候 final IR 不同，什么时候传导到 `llc` / `clang -c` both-smaller，以及 Queens / ffbench 的 attribution 是否存在共同 opcode pattern。

本阶段仍然不是 search：

- 不新增 LLVM 实验。
- 不新增 certificate。
- 不新增 search。
- 不运行 runtime benchmark。
- 不改变 PassSpec 行为。
- 不改变 static filter 行为。

## 完成内容

新增代码：

```text
src/ecpor/pair_family_analysis.py
tests/test_pair_family_analysis.py
```

扩展 manifest 支持：

```text
src/ecpor/manifest_builders.py
src/ecpor/manifest_cli.py
tests/test_result_manifest.py
```

生成 P14 输出：

```text
data/outputs/pair_family_instcombine_simplifycfg/pair_family_events.csv
data/outputs/pair_family_instcombine_simplifycfg/pair_family_program_summary.csv
data/outputs/pair_family_instcombine_simplifycfg/pair_family_objective_summary.csv
data/outputs/pair_family_instcombine_simplifycfg/pair_family_attribution_compare.csv
data/outputs/pair_family_instcombine_simplifycfg/pair_family_analysis.json
data/outputs/pair_family_instcombine_simplifycfg/pair_family_analysis_report.md
docs/results/pair_family_instcombine_simplifycfg_manifest.json
```

`data/outputs/...` 是生成产物，按 data retention 规则保留但不纳入 Git；tracked evidence 入口是 manifest：

```text
docs/results/pair_family_instcombine_simplifycfg_manifest.json
```

## 输入证据

P14 读取这些既有结果：

```text
data/outputs/interaction_graph_v1/pass_interaction_edges.csv
data/outputs/reduced_components_v1/reduced_component_edges.csv
data/outputs/reduced_components_v1/search_space_estimate.csv
data/outputs/cert_summary.csv
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_p9_diverse8_pre.csv
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p8b_misc8/attempts.csv
data/outputs/lazy_validation_p9_diverse8/attempts.csv
data/outputs/bounded_local_p5_p6_final/candidates.csv
data/outputs/bounded_local_p8b_misc8/candidates.csv
data/outputs/bounded_local_p9_diverse8/candidates.csv
data/outputs/code_size_p6_final/object_size.csv
data/outputs/code_size_p8b_misc8/object_size.csv
data/outputs/code_size_p9_diverse8/object_size.csv
data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv
data/outputs/codegen_sensitivity_p8b_misc8/p8a_codegen_direction_compare.csv
data/outputs/codegen_sensitivity_p9_diverse8/p8a_codegen_direction_compare.csv
data/outputs/core_evidence_report/ecpor_attribution_summary.csv
data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv
```

## 真实结果

P14 真实输出：

```text
PairFamily: instcombine,simplifycfg
Programs: 24
FullMatrixCertified: 11
FullMatrixNotCertified: 13
PrefixCertified: 10
PrefixNotCertified: 10
OneSwapCandidates: 10
FinalIrDifferent: 10
BothSmallerPrograms: 2
AttributionCases: 2
SelectRelatedAttributionCases: 2
NewExperiments: False
NewCertificates: False
NewSearch: False
```

`pair_family_objective_summary.csv`：

```csv
benchmark_set,programs,one_swap_candidates,llc_smaller,llc_equal,llc_larger,clang_smaller,clang_equal,clang_larger,both_smaller,direction_disagreement
Stanford-8,8,4,1,3,0,1,1,2,1,2
Misc8,8,5,1,4,0,1,4,0,1,0
Diverse8,8,1,0,1,0,0,0,1,0,1
```

`pair_family_attribution_compare.csv`：

```csv
benchmark_set,program,pair,opcode_delta,removed_opcodes,added_opcodes,net_instruction_delta,llc_text_delta_pct,clang_text_delta_pct,evidence_level
Stanford-8,testsuite_stanford_queens,"instcombine,simplifycfg",num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1,icmp;select,add,-1,-4.401651,-1.673640,"observed attribution, not causal proof"
Misc8,testsuite_misc_ffbench,"instcombine,simplifycfg",num_select_delta=-1;num_or_delta=1,select,or,0,-1.005025,-0.127280,observed_attribution_not_causal_proof
```

解释：

- `instcombine/simplifycfg` 在 input-state full matrix 中有 `13/24` 个 not-certified event。
- 在 prefix-state adjacent validation 中有 `10/24` 个 not-certified event，并生成 `10` 个 one-swap candidate。
- 这 `10` 个 one-swap candidate 都造成 final IR different。
- 只有 `2` 个程序在 `llc` 与 `clang -c` 下同时 `.text` smaller：`testsuite_stanford_queens` 和 `testsuite_misc_ffbench`。
- 两个 attribution case 都出现了 `select` 相关 opcode delta：Queens 为 `icmp/select` 减少、`add` 增加；ffbench 为 `select` 减少、`or` 增加。
- 这只能写成 observed pattern，不能写成 causal theorem 或全局排序规则。

## 关键代码快照

### P14 入口聚合函数

```python
def build_pair_family_analysis(
    *,
    pair_a: str = DEFAULT_PAIR_A,
    pair_b: str = DEFAULT_PAIR_B,
    full_matrix_rows: Sequence[Mapping[str, str]],
    prefix_attempt_rows: Sequence[Mapping[str, str]],
    candidate_rows: Sequence[Mapping[str, str]],
    object_rows: Sequence[Mapping[str, str]],
    codegen_rows: Sequence[Mapping[str, str]],
    attribution_rows: Sequence[Mapping[str, str]],
    interaction_edge_rows: Sequence[Mapping[str, str]] = (),
    reduced_component_rows: Sequence[Mapping[str, str]] = (),
    search_space_rows: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    pair = _pair_set(pair_a, pair_b)
    pair_text = f"{pair_a},{pair_b}"

    target_full = [_with_set(row) for row in full_matrix_rows if _row_matches(row, pair)]
    target_prefix = [_with_set(row) for row in prefix_attempt_rows if _row_matches(row, pair)]
    target_candidates = [
        _with_set(row)
        for row in candidate_rows
        if str(row.get("source", "")) == "single_swap" and _row_matches(row, pair)
    ]
```

### direction-insensitive pair matching

```python
def _row_matches(row: Mapping[str, str], pair: frozenset[str]) -> bool:
    row_pair = _row_pair(row)
    return bool(row_pair) and row_pair == pair


def _row_pair(row: Mapping[str, str]) -> frozenset[str]:
    pair_text = str(row.get("pair", "")).strip()
    if pair_text and "," in pair_text:
        left, right = pair_text.split(",", 1)
        return _pair_set(left, right)
    left = row.get("pass_a") or row.get("pair_a")
    right = row.get("pass_b") or row.get("pair_b")
    if left and right:
        return _pair_set(left, right)
    return _pair_from_candidate_id(row.get("candidate_id", ""))
```

### attribution opcode compare

```python
def _build_attribution_compare(
    *,
    pair_text: str,
    attribution_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in attribution_rows:
        opcode_delta = _opcode_delta_text(row)
        deltas = _parse_named_deltas(opcode_delta)
        removed = [
            _opcode_name(name) for name, value in deltas.items() if value < 0
        ]
        added = [_opcode_name(name) for name, value in deltas.items() if value > 0]
```

### P14 manifest scope

```python
"scope_limits": {
    "stage": "P14",
    "summary_only": True,
    "pair_family_analysis_only": True,
    "target_pair": pair,
    "new_experiments": False,
    "new_certificates": False,
    "new_search": False,
    "runtime_benchmarks": False,
    "passspec_behavior_change": False,
    "static_filter_behavior_change": False,
}
```

### 测试覆盖

```python
def test_builds_direction_insensitive_pair_family_summary(self):
    analysis = build_pair_family_analysis(
        pair_a="instcombine",
        pair_b="simplifycfg",
        full_matrix_rows=[
            {
                "benchmark_set": "SetA",
                "program": "prog_a",
                "pair_a": "instcombine",
                "pair_b": "simplifycfg",
                "label": "not_certified_independent",
            },
            {
                "benchmark_set": "SetA",
                "program": "prog_b",
                "pair_a": "simplifycfg",
                "pair_b": "instcombine",
                "label": "certified_independent",
            },
        ],
        ...
    )

    self.assertEqual(analysis["summary"]["FullMatrixCertified"], 1)
    self.assertEqual(analysis["summary"]["FullMatrixNotCertified"], 1)
```

## 验证结果

先写测试后实现，目标测试曾按预期失败：

```text
ModuleNotFoundError: No module named 'ecpor.pair_family_analysis'
ImportError: cannot import name 'build_pair_family_analysis_manifest'
```

实现后目标测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_pair_family_analysis.py tests\test_result_manifest.py -q
```

结果：

```text
22 passed in 1.16s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
159 passed in 24.20s
```

生成 P14 结果：

```powershell
$env:PYTHONPATH = 'src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.pair_family_analysis
```

生成 P14 manifest：

```powershell
$env:PYTHONPATH = 'src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest pair-family-analysis `
  --out-manifest docs\results\pair_family_instcombine_simplifycfg_manifest.json `
  --interaction-graph-dir data\outputs\interaction_graph_v1 `
  --reduced-components-dir data\outputs\reduced_components_v1 `
  --output-dir data\outputs\pair_family_instcombine_simplifycfg `
  --repo-root . `
  --result-generated-from-commit 34e61c018214a2f72ab6df242497c2a76ff4ba5f
```

P14 manifest 记录：

```text
result_generated_from_commit = 34e61c018214a2f72ab6df242497c2a76ff4ba5f
ecpor_git_commit = 34e61c018214a2f72ab6df242497c2a76ff4ba5f
ecpor_git_dirty = false
summary_only = true
pair_family_analysis_only = true
target_pair = instcombine,simplifycfg
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
passspec_behavior_change = false
static_filter_behavior_change = false
```

## 风险和边界

1. P14 只说明当前 retained 24-program depth1 evidence；不能外推为所有程序、所有 state 或所有 pipeline。
2. Queens 和 ffbench 都有 select-related opcode delta，这是 observed pattern，不是因果证明。
3. Full matrix input-state 与 prefix-state adjacent validation 是两个不同 state scope，P14 在 program summary 中分开记录，不混用。
4. `BothSmallerPrograms = 2` 是 objective-layer observation，不是 hard-prune evidence。
5. 这个 pair 适合作为 targeted interaction family，不适合写成全局排序规则。

## 下一步

P14 后不建议进入 full search、two-swap、depth=3 或 runtime。更合适的下一步有两个方向：

```text
P15A：targeted witness-state collection for instcombine/simplifycfg
P15B：final research report / paper draft freeze
```

如果继续技术分析，应只围绕 `instcombine,simplifycfg` 收集更细 witness state；如果准备收束，则可以把 P12-P14 作为“为什么不继续搜索”的核心证据写进最终报告。
