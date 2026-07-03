# P13 reduced components / search-space reduction report

## 当前目标

P13 的目标是基于 P12 interaction graph v1，生成 reduced components 和搜索空间缩减估计。

本阶段仍然只做 graph analysis / report：

- 不新增实验。
- 不新增 certificate。
- 不新增 search。
- 不运行 runtime benchmark。
- 不改变 PassSpec 行为。
- 不改变 static filter 行为。

## 完成内容

新增代码：

```text
src/ecpor/reduced_components.py
tests/test_reduced_components.py
```

扩展 manifest 支持：

```text
src/ecpor/manifest_builders.py
src/ecpor/manifest_cli.py
tests/test_result_manifest.py
```

生成 P13 输出：

```text
data/outputs/reduced_components_v1/reduced_component_nodes.csv
data/outputs/reduced_components_v1/reduced_component_edges.csv
data/outputs/reduced_components_v1/reduced_components.json
data/outputs/reduced_components_v1/search_space_estimate.csv
data/outputs/reduced_components_v1/reduced_components_report.md
docs/results/reduced_components_v1_manifest.json
```

## 输入证据

P13 只读取 P12 graph 输出和 pipeline 配置：

```text
configs/pipeline_scalar.yaml
data/outputs/interaction_graph_v1/pass_interaction_nodes.csv
data/outputs/interaction_graph_v1/pass_interaction_edges.csv
data/outputs/interaction_graph_v1/pass_interaction_graph.json
data/outputs/interaction_graph_v1/pass_interaction_graph_report.md
```

## 图模式

P13 同时构建两张图。

### Conservative graph

保留：

```text
order_sensitive
objective_sensitive
attribution_hypothesis
insufficient_observed_evidence
```

它回答的是：在最保守解释下，哪些 pass 仍属于同一个 order-sensitive component。

### Objective-sensitive graph

保留：

```text
objective_sensitive
attribution_hypothesis
```

同时为了兼容 P12 的分类优先级，也会保留带有 `both_smaller_count > 0` 或 `attribution_cases > 0` 的边。它回答的是：当前哪些 pass pair 已经观察到目标层收益或 attribution evidence。

## 真实结果

P13 真实输出：

```text
OriginalPermutations: 40320
ConservativeGraphComponents: 1
ObjectiveSensitiveGraphComponents: 7
ConservativeWithinComponentPermutations: 40320
ObjectiveWithinComponentPermutations: 2
ConservativeReductionRatio: 0.0000%
ObjectiveReductionRatio: 99.9950%
```

解释：

- 原始 8-pass pass-type permutation 上界为 `8! = 40320`。
- conservative graph 形成一个 8-pass 大 component，说明 observed order-sensitivity graph 当前仍然很密，不能声称有保守搜索空间压缩。
- objective-sensitive graph 只有一个非 singleton component：`{instcombine, simplifycfg}`。
- objective-sensitive estimate 的 `2` 只是目标层热点的局部搜索上界，不是 hard-prune 证明。

`search_space_estimate.csv`：

```csv
graph_mode,pass_count,original_factorial,component_sizes,within_component_factorial_product,reduction_ratio,interpretation
conservative,8,40320,8,40320,0.0000%,coarse upper-bound estimate; component order anchored to current pipeline
objective_sensitive,8,40320,1;1;2;1;1;1;1,2,99.9950%,coarse upper-bound estimate; component order anchored to current pipeline
```

## 关键代码快照

### 两种 graph mode 的边选择

```python
def _edge_selected_for_mode(edge: Mapping[str, str], mode: str) -> bool:
    edge_kind = str(edge.get("edge_kind", ""))
    if mode == "conservative":
        return edge_kind in {
            "order_sensitive",
            "objective_sensitive",
            "attribution_hypothesis",
            "insufficient_observed_evidence",
        }
    if mode == "objective_sensitive":
        return (
            edge_kind in {"objective_sensitive", "attribution_hypothesis"}
            or _int(edge.get("both_smaller_count")) > 0
            or _int(edge.get("attribution_cases")) > 0
        )
    raise ValueError(f"unsupported graph mode: {mode}")
```

### 搜索空间粗略估计

```python
def _build_search_space(
    components: Sequence[Mapping[str, Any]],
    *,
    pass_count: int,
) -> list[dict[str, Any]]:
    original = math.factorial(pass_count)
    rows: list[dict[str, Any]] = []
    for mode in GRAPH_MODES:
        mode_components = [
            component
            for component in components
            if component["graph_mode"] == mode
        ]
        sizes = [int(component["component_size"]) for component in mode_components]
        product = 1
        for size in sizes:
            product *= math.factorial(size)
        reduction = 0.0 if original == 0 else (1.0 - (product / original)) * 100.0
```

### P13 manifest scope

```python
"scope_limits": {
    "stage": "P13",
    "summary_only": True,
    "graph_analysis_only": True,
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
def test_certified_dominant_edge_is_not_conservative_component_edge(self):
    graph = build_reduced_components(
        nodes=_nodes(["a", "b"]),
        edges=[_edge("a", "b", "certified_dominant")],
        pipeline_passes=["a", "b"],
    )

    conservative_edges = [
        row for row in graph["component_edges"] if row["graph_mode"] == "conservative"
    ]
    conservative_components = _components_by_mode(graph, "conservative")

    self.assertEqual(conservative_edges, [])
    self.assertEqual([component["passes"] for component in conservative_components], [["a"], ["b"]])
```

## 验证结果

目标测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_reduced_components.py tests\test_result_manifest.py -q
```

结果：

```text
24 passed in 1.10s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
154 passed in 22.85s
```

P13 manifest 记录：

```text
result_generated_from_commit = f5eaaf17ca68699ca97c91c09edac7e9007205e3
ecpor_git_commit = f5eaaf17ca68699ca97c91c09edac7e9007205e3
ecpor_git_dirty = false
summary_only = true
graph_analysis_only = true
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
passspec_behavior_change = false
static_filter_behavior_change = false
```

## 风险和边界

1. Conservative graph 不给出搜索空间压缩，目前是一个 8-pass 大 component。
2. Objective-sensitive graph 的 `99.9950%` reduction 是热点定位视角的粗略上界，不是全局搜索空间证明。
3. `certified_dominant` 不是 global independence；P13 没有把它作为全局 hard prune 使用。
4. `{instcombine, simplifycfg}` 是当前唯一目标层热点，但 attribution 仍然是 observed attribution，不是因果定理。

## 下一步

建议进入 P14：targeted pair-family analysis for `instcombine,simplifycfg`。

P14 不应该直接写完整 searcher，而应先回答：

```text
这个 pair 在 24 programs 中什么时候 not-certified？
什么时候 one-swap 影响 final IR？
什么时候传导到 llc/clang both-smaller？
Queens 和 ffbench 的 attribution 是否有共同模式？
```
