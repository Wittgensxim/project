# P12 interaction graph v1

## 当前目标

P12 的目标是把已有的 24-program depth1 证据整理成第一版 8-pass interaction graph。

本阶段只做 summary / graph construction：

- 不新增实验。
- 不新增 certificate。
- 不新增 search。
- 不运行 runtime benchmark。
- 不改变 PassSpec 行为。
- 不改变 static filter 行为。

## 完成内容

新增代码：

```text
src/ecpor/interaction_graph.py
tests/test_interaction_graph.py
```

扩展 manifest 支持：

```text
src/ecpor/manifest_builders.py
src/ecpor/manifest_cli.py
tests/test_result_manifest.py
```

生成 P12 输出：

```text
data/outputs/interaction_graph_v1/pass_interaction_nodes.csv
data/outputs/interaction_graph_v1/pass_interaction_edges.csv
data/outputs/interaction_graph_v1/pass_interaction_graph.json
data/outputs/interaction_graph_v1/pass_interaction_graph_report.md
docs/results/interaction_graph_v1_manifest.json
```

## 输入证据

P12 读取的是已有结果，不重新运行 LLVM：

```text
configs/passspec.yaml
configs/pipeline_scalar.yaml
data/outputs/passspec_registry_check/passspec_registry_check.csv
data/outputs/combined_depth1_summary/*.csv
data/outputs/cert_summary.csv
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_p9_diverse8_pre.csv
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p8b_misc8/attempts.csv
data/outputs/lazy_validation_p9_diverse8/attempts.csv
data/outputs/bounded_local_p5_p6_final/candidates.csv
data/outputs/bounded_local_p8b_misc8/candidates.csv
data/outputs/bounded_local_p9_diverse8/candidates.csv
data/outputs/depth1_analysis_p8b_misc8/depth1_both_smaller_cases.csv
data/outputs/depth1_analysis_p9_diverse8/depth1_both_smaller_cases.csv
data/outputs/core_evidence_report/ecpor_attribution_summary.csv
data/outputs/core_evidence_report_misc8/misc8_attribution_summary.csv
```

## 结果摘要

真实 P12 graph 结果：

```text
Nodes: 8
Edges: 28
ObservedPairEdges: 28
CertifiedDominantPairs: 10
OrderSensitivePairs: 17
ObjectiveSensitivePairs: 1
AttributionHypothesisPairs: 1
InsufficientObservedEvidencePairs: 0
FullMatrixCertifiedEvents: 488
FullMatrixNotCertifiedEvents: 184
PrefixCertifiedEvents: 101
PrefixNotCertifiedEvents: 39
LowPriorityEvents: 28
OneSwapCandidates: 39
BothSmallerCases: 2
AttributionCases: 2
```

最重要的边是：

```text
instcombine,simplifycfg
```

这条边同时具有：

- `both_smaller_count = 2`
- `attribution_cases = 2`
- edge kind 为 `attribution_hypothesis`

它对应两个 observed attribution case：

```text
testsuite_stanford_queens: simplifycfg,instcombine
testsuite_misc_ffbench: instcombine,simplifycfg
```

注意：因为分类优先级是 `attribution > objective > not-certified > certified`，所以该 pair 的主分类是 `attribution_hypothesis`，但报告中的 objective-sensitive 区块仍然列出它携带 both-smaller 目标层证据。

## 关键代码快照

### interaction graph 分类优先级

```python
def _classify_edge(edge: Mapping[str, Any]) -> dict[str, str]:
    if int(edge["attribution_cases"]) > 0:
        return {
            "edge_kind": "attribution_hypothesis",
            "evidence_level": "observed attribution; not causal proof",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
    if int(edge["both_smaller_count"]) > 0:
        return {
            "edge_kind": "objective_sensitive",
            "evidence_level": "objective-layer observation; not independence proof",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
    if int(edge["prefix_not_certified_events"]) > 0 or int(
        edge["full_matrix_not_certified"]
    ) > 0:
        return {
            "edge_kind": "order_sensitive",
            "evidence_level": "not-certified event observed",
            "hard_prune_scope": "none",
            "notes": _edge_notes(edge),
        }
```

### graph JSON 证据边界

```python
"evidence_boundary": {
    "certified_independent_events_are_state_indexed": True,
    "certified_dominant_is_not_global_independence": True,
    "objective_sensitive_is_not_independence_proof": True,
    "objective_sensitive_is_not_hard_prune_evidence": True,
    "attribution_is_not_causal_proof": True,
    "static_filter_behavior_change": False,
    "passspec_behavior_change": False,
}
```

### P12 manifest scope

```python
"scope_limits": {
    "stage": "P12",
    "summary_only": True,
    "graph_construction_only": True,
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
def test_attribution_pair_has_highest_priority(self):
    edges = build_edges(
        pipeline_passes=["a", "b"],
        full_matrix_rows=[],
        prefix_attempt_rows=[
            {"pass_a": "a", "pass_b": "b", "label": "not_certified_independent"}
        ],
        candidate_rows=[],
        both_smaller_rows=[{"pair": "a,b"}],
        attribution_rows=[{"pair": "b,a"}],
    )

    self.assertEqual(edges[0]["edge_kind"], "attribution_hypothesis")
    self.assertEqual(edges[0]["attribution_cases"], 1)
```

## 验证结果

目标测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_interaction_graph.py tests\test_result_manifest.py -q
```

结果：

```text
24 passed in 1.03s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
146 passed in 23.49s
```

P12 manifest 记录：

```text
result_generated_from_commit = 2fb14ce5186a0f0826ebdcc4770af46fe8bccb61
ecpor_git_commit = 2fb14ce5186a0f0826ebdcc4770af46fe8bccb61
ecpor_git_dirty = false
summary_only = true
graph_construction_only = true
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
passspec_behavior_change = false
static_filter_behavior_change = false
```

## 风险和边界

1. `certified_dominant` 只表示 observed state-indexed events 中 certified 占主导，不表示全局 independence。
2. `order_sensitive` 来自 observed not-certified event，说明该 pair 不能直接折叠为可交换。
3. `objective_sensitive` 不是 hard-prune 证据，也不是 independence proof。
4. `attribution_hypothesis` 是 observed attribution，不是 causal theorem。
5. P12 没有估算 search-space reduction；它只生成 graph。

## 下一步

进入 P13：reduced components / search-space reduction estimate。

P13 才开始回答：

```text
根据 interaction graph，哪些 pass pair 需要留在同一 order-sensitive component？
哪些 pair 可以用 state-indexed certificate evidence 折叠？
8-pass MVP 的搜索空间从完整排列估计压到多大？
```
