# ECPOR 阶段报告：state-indexed certificate 驱动的 phase-ordering reduction

## 摘要

ECPOR 当前不是完整 pass-order searcher，也不宣称找到全局最优 pass 顺序。它的目标更窄：在给定 LLVM IR state、给定 scalar pass 集合和给定相邻 pass pair 的条件下，用可复现的 AB/BA certificate 证明哪些相邻顺序可以折叠，哪些顺序必须保留为候选，再把剩余的小空间交给 bounded local validation 与 objective-layer 检查。

截至 P9-5，项目已经完成 Stanford-8、Misc8、Diverse8 三组 depth1-only 汇总：

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

这说明证书层和 reduction 链路已经稳定；但 objective-layer benefit 很稀疏，24 个程序里仍然只有 Stanford Queens 与 Misc ffbench 两个 depth1 both-smaller program。Diverse8 扩展了覆盖面，但没有新增 both-smaller program。因此当前阶段不应继续加深搜索，而应先完成阶段报告、论文草稿或 PassSpec provenance 升级。

## 研究问题

传统 phase ordering 的搜索空间很大。直接搜索 pass 全排列很容易把时间花在大量无关顺序上，也很难解释“为什么这个顺序值得搜”。ECPOR 选择先回答一个更可复查的问题：

```text
在当前 LLVM IR state 上，哪些相邻 pass 顺序可以被证书证明等价，从而不用继续搜索？
哪些顺序不能被证明等价，必须保留为后续候选？
这些候选在 object .text 上是否真的产生目标层差异？
```

因此本项目的核心不是输出一个唯一 pipeline，而是输出一条 evidence-carrying reduction 链：证书、候选、目标层结果和 attribution 都要能被单独复查。

## 核心思想

不要先搜索 pass 全排列，而是先证明哪些相邻 pass 顺序在当前 state 上可以折叠。

具体来说，对一个当前 state `S` 和相邻 pass pair `(A, B)`，ECPOR materialize 两条 pipeline：

```text
S -> A -> B
S -> B -> A
```

然后用 hard-normalized IR hash 判断 AB/BA 是否相同。若 hash 相同，则生成 `certified_independent_event`，它可以作为当前 state 下的 hard prune evidence。若 hash 不同，则生成 `not_certified_event`，该 pair 不能被折叠，必须保留为 one-swap candidate 或后续分析对象。

## 方法链路

当前 MVP 与 post-MVP depth1 扩展包含以下模块：

| 模块 | 作用 | 是否产生 hard prune |
| --- | --- | --- |
| Runner / Normalizer | 调用 LLVM `opt` 并生成 hard-normalized IR hash | no |
| PairCertificate | 记录当前 state 的 AB/BA 证书、环境指纹和复现字段 | yes, only when certified |
| StaticFilter | 用 `passspec.yaml` 生成 candidate / low_priority hint | no |
| Prefix-state lazy validation | 在 pipeline prefix state 上按需生成或复用 certificate | yes, only when certified |
| Bounded local one-swap | 把 not-certified adjacent event 转成 one-swap candidate | no |
| Object-size evaluator | 用 `llc` 编译 object 并比较 `.text` | no |
| Clang-c sensitivity | 用 `clang -c` 检查 codegen path sensitivity | no |
| Attribution | 对 observed both-smaller case 做 feature/opcode/object 解释 | no |
| Combined summary | 汇总 24-program depth1-only 结果 | no |

关键边界是：只有当前 state 上的 `certified_independent_event` 可以 hard prune。Static hint、low priority、sequence duplicate、objective improvement 和 attribution 都不能作为 hard prune。

## 证据等级

| evidence | 含义 | 是否 hard prune |
| --- | --- | --- |
| `certified_independent_event` | 当前 state 中 AB/BA hard hash 相同，且 certificate 可复现 | yes |
| `not_certified_event` | 当前 state 中 AB/BA hard hash 不同 | no |
| `low_priority` | static filter 认为优先级较低，但未动态证明 | no |
| `sequence_duplicate` | 不同 swap 路径生成同一 pass sequence，可去重 | no |
| `one_swap_objective_result` | one-swap candidate 的 `.text` 观察结果 | no |
| `llc/clang both-smaller` | 两条 codegen path 下 `.text` 都变小 | no |
| `attribution` | 单个 observed case 的 feature/opcode/object 解释 | no |

这个分层能避免把 static filter 或 objective observation 误写成安全剪枝依据。

## 结果总览

P9-5 只汇总已有结果，不新增实验、不新增 certificate、不新增 search、不运行 runtime benchmark，也不混入旧 P7b two-swap rows。

| benchmark set | programs | pair certificates | reproduced | hard false | adjacent attempts | certified adjacent | not-certified adjacent | one-swap | both-smaller programs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stanford-8 | 8 | 224 | 224 | 0 | 56 | 32 | 16 | 16 | 1 |
| Misc8 | 8 | 224 | 224 | 0 | 56 | 32 | 16 | 16 | 1 |
| Diverse8 | 8 | 224 | 224 | 0 | 56 | 37 | 7 | 7 | 0 |
| total | 24 | 672 | 672 | 0 | 168 | 101 | 39 | 39 | 2 |

主要结论：

1. `672/672` pair certificates 可复现，`HardFalseIndependent = 0`。
2. 三组 depth1 adjacent validation 共 `168` 次，其中 `101` 次 certified，可作为当前 state 的 hard prune evidence。
3. `39` 个 not-certified adjacent event 进入 one-swap 候选层。
4. 只有 `2` 个程序在 depth1 层出现 both-smaller objective observation。
5. Diverse8 没有新增 both-smaller program，说明当前不适合继续加深搜索。

## Objective Layer

| benchmark set | one-swap candidates | object evaluated | smaller | equal | larger | IR-different text-equal | direction agreement | both-smaller |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stanford-8 | 16 | 16 | 1 | 15 | 0 | 15 | 75.00% | 1 |
| Misc8 | 16 | 16 | 1 | 15 | 0 | 15 | 93.75% | 1 |
| Diverse8 | 7 | 7 | 0 | 5 | 2 | 4 | 71.43% | 0 |

IR hard hash 不同并不等于 objective-layer 一定变好。Stanford-8 与 Misc8 各有 `15/16` 个 one-swap candidate 是 IR-different 但 `.text` equal；Diverse8 的 `7` 个 one-swap candidate 中没有 both-smaller case。

## Attribution Cases

当前只有两个 observed attribution case，它们都是解释性证据，不是因果证明：

| benchmark | program | pair | observed opcode delta | llc text delta | clang text delta |
| --- | --- | --- | --- | ---: | ---: |
| Stanford-8 | `testsuite_stanford_queens` | `simplifycfg,instcombine` | `num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1` | -4.401651% | -1.673640% |
| Misc8 | `testsuite_misc_ffbench` | `instcombine,simplifycfg` | `num_select_delta=-1;num_or_delta=1` | -1.005025% | -0.127280% |

它们的价值在于把 “search result” 压缩成可复查的单状态案例：局部顺序差异、opcode delta 和 object-size delta 可以放在同一条证据链中审阅。

## 解释

P9-5 的结果支持三个谨慎结论。

第一，证书层目前稳定。完整 pair matrix 与 prefix-state lazy validation 都没有观察到 hard false independent，且 retained certificates 均可复现。

第二，static filter 当前只能作为 candidate generation 与 low-priority hint。它不能代替 certificate；真正可 hard prune 的证据必须来自当前 state 的 AB/BA hard hash 相同。

第三，objective-layer benefit 很稀疏。24 个程序和 39 个 one-swap candidate 中，只有 2 个程序在 `llc` 与 `clang -c` 下同时 `.text` 变小。Diverse8 没有新增 both-smaller program，说明继续 two-swap、depth=3 或 beam search 的收益依据不足。

## 限制

当前阶段仍不支持：

```text
完整 phase-ordering searcher
depth=3 / beam search / RL / MCTS
loop pass / module pass / inline pipeline
runtime benchmark
Alive2 / formal equivalence proof
LLVM PassInstrumentation tracing
自动完整 PassSpecDB
击败 O2/O3 这类大范围性能宣称
```

此外，当前 PassSpec 仍有手工知识成分。P8b-2 的 `sroa -> dce_opportunity` repair 已经说明 PassSpec 需要 provenance：每条 hint 应该记录来源、置信度和 empirical support，而不是被误读成 LLVM 官方事实。

## 下一步

推荐路线：

```text
P9-6: 阶段报告 / 论文草稿
  -> P10: PassSpec provenance v2
  -> P10.5: passspec audit report
  -> 再决定是否进入 larger benchmark 或 interaction graph
```

当前不建议继续做 two-swap、depth=3、beam/searcher、runtime benchmark、Alive2 或 PassInstrumentation。更合适的下一步是把现有证据链整理成可展示、可答辩、可引用的研究报告，并把 PassSpec 从手工 hint 表升级为带来源与置信度的 metadata 表。

## P12-P14.5 补充：corpus-union 与 program-local 的边界

P12 之后新增的 interaction graph / reduced component 分析不改变本文的核心结论：ECPOR 仍然不是完整 searcher，也不把 objective observation 当成 hard prune。新增结果只把“哪些顺序不用搜、哪些必须保留为候选”这条证据链解释得更清楚。

需要区分三层图：

```text
P13  corpus-union graph:
  把 24 个程序的 retained evidence 合并成一张保守图。
  ConservativeReductionRatio = 0.0000% 表示 corpus-union conservative graph 是 8-pass 大 component。
  这不是每个程序本地都不可拆的结论。

P14  objective hotspot pair-family:
  聚焦 corpus-level graph 里唯一 objective-sensitive hotspot：instcombine/simplifycfg。
  它解释 Queens 和 ffbench 的 both-smaller attribution case。
  它不替代 per-program reduced component analysis。

P14.5 program-local graph:
  对每个程序分别构建 input_full_matrix、prefix_adjacent、objective_sensitive 三种 scoped graph。
  input_full_matrix 下 22/24 个程序有多个 component。
  prefix_adjacent 下 24/24 个程序有多个 component，但只覆盖 7 个 adjacent pair。
  objective_sensitive 下只有 Queens 和 ffbench 的 instcombine/simplifycfg 是非 singleton component。
```

因此，P13 的 0% conservative reduction 应写成“corpus-union conservative graph 没有搜索空间压缩”，不能写成“所有 program-local graph 都没有搜索空间压缩”。P14.5 的价值是把这个边界补清楚，但它仍然不新增实验、不新增 certificate、不启动 search。

## P15 补充：受控 scalar12 expansion protocol

P15 在 P14.5 之后只做 pass expansion protocol，不改变本文的 hard-prune 语义，也不把项目升级为完整 searcher。它从 P11 registry snapshot 中挑选 function-level scalar / cleanup 候选，对 24 个 retained program 运行 single-pass `function(candidate)` smoke。

真实结果为：

```text
CandidatePasses = 8
RegistryPresentCandidates = 8
Programs = 24
ProgramsAttempted = 192
RunFailedCandidates = 0
TimeoutCandidates = 0
VerifierFailedCandidates = 0
ChangedIrCandidates = 8
SelectedNewPasses = 4
Scalar12PassCount = 12
```

进入 scalar12 的新增 pass 是：

```text
instsimplify
bdce
sccp
correlated-propagation
```

P15 的边界是：

```text
new_experiments = true
new_certificates = false
new_search = false
runtime_benchmarks = false
loop_passes = false
module_passes = false
inline_passes = false
baseline_scalar8_configs_unchanged = true
```

因此，P15 的意义是证明当前工具链可以受控地从 scalar8 扩展到 scalar12 配置。它不证明 scalar12 的 pair matrix 结果，也不证明 code-size benefit。后续若继续实验，应进入 P16：scalar12 full matrix、per-program reduced components 与 depth1-only chain；仍不应进入 two-swap、depth=3、beam search、runtime benchmark、Alive2 或 loop/module/inline pass。
