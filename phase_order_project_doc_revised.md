# ECPOR 修订版项目文档：基于状态索引证书的 LLVM Phase Ordering 搜索空间坍缩系统

**项目中文名**：基于证据的 LLVM Phase Ordering 搜索空间坍缩系统  
**建议简称**：ECPOR, Evidence-Carrying Phase-Ordering Reduction  
**文档版本**：v1.1 修订版  
**修订日期**：2026-06-30  
**修订原则**：将 v1.0 中过强的“全局图压缩”表述，修正为“状态索引、证书驱动、lazy validation 的局部相邻交换压缩”。

---

## 0. 修订版可行性结论

本项目仍然可行，而且具有明确研究价值，但项目目标必须从“全局优化顺序求解”调整为：

> 在固定程序、固定 LLVM 版本、固定目标平台、固定 pass instance 搜索空间、固定执行模型和固定目标函数下，构建一个 state-indexed、certificate-driven 的 LLVM IR pass ordering reduction 原型。系统只对当前中间状态上有证书的相邻 pass 交换做 hard pruning；其他交互作为 soft evidence 引导局部搜索。最终候选 pipeline 必须完整复跑、验证和评估。

这个定义比 v1.0 更保守，但更可落地，也更容易给出严谨理论保证。

### 0.1 可行性分级

| 目标版本 | 可行性 | 说明 |
|---|---:|---|
| 受控 LLVM IR middle-end pass 子集上的研究原型 | 高 | 推荐作为 MVP。只处理 Function/Loop 层级的受控 pipeline，输出证书和解释报告。 |
| 完整 `-O2` / `-O3` pipeline 的全局安全压缩 | 中低 | 需要处理复杂 nesting、analysis cache、target hooks、required pass、unknown 爆炸。 |
| 所有 LLVM pass 任意重排并证明全局最优 | 不作为目标 | 范围过大，且会混入 pass selection、codegen、target-specific pipeline 等问题。 |
| 状态索引证书 + lazy validation + 局部搜索 | 高 | 本文档采用的正式项目定义。 |

### 0.2 项目主贡献

本项目不是再做一个黑盒 pass-ordering 搜索器，而是做一个可复用的**顺序空间坍缩层**：

```text
原始候选 pipeline 空间
  ↓
静态高召回候选生成
  ↓
当前状态上的相邻交换证书
  ↓
hard pruning 仅删除已证实重复的规范化 IR 结果
  ↓
soft interaction evidence 引导局部搜索
  ↓
完整 pipeline 复跑验证与评估
```

项目输出不只是一个 pipeline，而是一套可复现证据：哪些相邻交换被证明安全、哪些交互被观察到、哪些 pair 无法判断、哪些候选最终通过验证。

---

## 1. 问题定义与项目边界

### 1.1 背景问题

LLVM 等现代编译器通常通过一系列 pass 对 IR 进行优化。pass 的先后顺序会影响最终 IR、机器码、runtime、code size 和 compile time。若有 `n` 个可重排 pass instance，全部排列数量最高可达 `n!`，直接穷举不可行。

本项目利用一个结构性事实：在具体程序的具体中间状态上，很多相邻 pass 交换可能得到同一个规范化 IR 结果。这些“顺序差异”不需要重复搜索。真正需要保留的是那些没有证书、或者已经观察到会改变结果的交互。

### 1.2 正式目标

给定：

```text
P0      输入 LLVM IR
C       编译器环境：LLVM commit/version、target triple、data layout、flags
Omega   固定的候选 pass instance 搜索空间
M       目标函数：code size / runtime / compile time / energy
E       执行模型：例如 materialized_ir_fresh_opt
N       保守 normalizer
```

ECPOR 的目标是：

1. 在搜索过程中，对当前 prefix 产生的状态 `S`，按需验证相邻 pass `A, B` 是否满足：

   ```text
   N(B(A(S))) == N(A(B(S)))
   ```

2. 只有当上述等式有可复现证书时，才把 `A;B` 与 `B;A` 视为同一个 hard equivalence class。
3. 对无法证明的 pair，标为 `unknown` 或 `dependent`，不做 hard pruning。
4. 对 IR 不同的 pair，收集 soft interaction evidence，例如 observed-enable、observed-suppress、observed-conflict。
5. 用证书化 hard pruning 缩小搜索空间，用 soft evidence 引导局部搜索。
6. 对最终候选 pipeline 进行完整复跑、verifier、语义/测试兜底和目标函数评估。
7. 输出可解释、可复现的 certificate bundle 与报告。

### 1.3 明确不承诺的内容

本项目第一版不承诺：

1. 不承诺在所有 LLVM pass 序列中找到绝对全局最优。
2. 不承诺某两个 pass 在所有程序或所有状态上全局可交换。
3. 不把静态预筛当作 independence 证明。
4. 不把 runtime/code size 近似相等当作 hard independence 证明。
5. 不把 observed-enable / observed-suppress 当作严格因果证明或 hard precedence 约束。
6. 不默认支持 backend MIR/codegen pass。
7. 不默认支持 interprocedural pass 的 hard proof；inline、globalopt、ipsccp 等应在第一版冻结或排除。
8. 不把 PassSpec 里的 may-read/may-write 当作精确读写集。
9. 不假设 `A,B` 在若干 witness states 上可交换，就可以推广到所有未来状态。
10. 不在静态阶段删除 pass，除非实验一开始就把 pass selection 纳入问题定义。

正确承诺是：

> Hard pruning 只来自当前状态上的 certified adjacent swap。所有没有证书的关系都保守保留。因此系统失败模式是“压缩不够多”，不是“错误删除重要顺序”。

---

## 2. 核心修订点

本节列出相对于 v1.0 必须修正的关键设计。

### 2.1 从全局 interaction graph 改为 state-indexed evidence database

v1.0 容易让人误解为：

```text
A 和 B 被观察到可交换 => A 和 B 全局可交换
```

修订版改为：

```text
independent(A, B, S_hash, execution_model, env_id)
```

即：`A` 和 `B` 只在某个具体状态 `S`、某个执行模型 `E`、某个 LLVM 环境 `C` 下被证明可交换。

证书 key 必须至少包含：

```text
A_id
B_id
input_state_hash
execution_model
llvm_env_id
pipeline_nesting
normalizer_version
debug_policy
metadata_policy
```

### 2.2 从“静态删除 pass”改为“静态冻结 pass”

静态 filter 不能直接删除 pass。删除 pass 会把 phase ordering 变成 pass selection，理论边界复杂很多。

修订版处理方式：

| 静态判断 | 处理方式 |
|---|---|
| relevant | 参与 pair generation 与局部搜索 |
| low_priority | 冻结在 anchor pipeline 默认位置，不主动生成重排候选 |
| structural_required | 固定位置，不重排 |
| unsupported | 固定位置，或在实验定义阶段排除 |
| excluded_by_experiment | 只有在实验空间一开始就不包含该 pass 时才允许 |

### 2.3 从 hard interaction graph 改为 hard/soft 双层图

修订版区分：

```text
Hard constraints:
  pass manager nesting
  legality constraints
  required/structural pass constraints
  certified adjacent independence equivalence classes

Soft evidence:
  observed-enable
  observed-suppress
  observed-conflict
  metric delta
  remarks/statistics differences
```

`A observed-enables B` 不意味着搜索器必须固定 `A before B`。它只是一个排序启发或解释证据。最终是否采用该顺序，仍由完整候选 pipeline 的目标函数评估决定。

### 2.4 从强 normalizer 改为保守 hard normalizer + soft fingerprints

Hard normalizer 不得做可能影响后续 pass、codegen、profile、layout 或启发式遍历顺序的变换。

第一版 hard normalizer 建议：

```text
可以：
  统一输入 debug policy，例如实验开始前统一 strip debug
  统一换行、文件头、工具产生的非语义 banner
  使用同一 LLVM 版本的 deterministic printer 输出
  计算完整 IR 文本或 bitcode hash

不可以用于 hard proof：
  重排 function/global/basic block
  删除 TBAA、alias.scope、range、prof、nonnull、align、dereferenceable 等优化相关 metadata
  改写 metadata graph
  只用 instruction multiset hash 代替结构等价
  只用 CFG hash 代替完整 IR 等价
```

可以额外计算 soft fingerprints：

```text
cfg_hash
callgraph_hash
loop_structure_hash
instruction_multiset_hash
feature_vector_hash
```

但这些只能辅助解释和排序，不能单独产生 `definitely_independent`。

### 2.5 从 eager pairwise matrix 改为 lazy validation

修订版不预先构建所有 `A,B` 的可交换矩阵。搜索器每次想交换相邻 `A,B` 时才触发：

```text
search wants swap A,B under prefix u
  ↓
materialize current state S = u(P0)
  ↓
lookup certificate(A,B,S)
  ↓
if exists and valid: hard collapse
  ↓
else run dynamic pair test under budget
  ↓
if pass: create certificate
  ↓
else: record soft/unknown evidence, do not hard prune
```

这样可以避免 `O(n^2 * states)` 的全量验证。

---

## 3. 理论模型

### 3.1 编译环境

定义固定编译环境：

```text
C = (
  LLVM version or commit,
  opt binary path,
  clang binary path if needed,
  target triple,
  data layout,
  CPU/features,
  optimization flags,
  pass plugin set,
  environment variables
)
```

所有证书必须绑定 `C`。不同 LLVM commit 下 pass 行为、pass name、pipeline nesting、IR printer 输出都可能变化，因此证书不能跨版本无条件复用。

### 3.2 执行模型

第一版建议使用：

```text
execution_model = materialized_ir_fresh_opt
```

含义：每个 witness state 都被保存成 `.ll` 或 `.bc`，pair test 从该 materialized IR 文件重新启动一个 fresh `opt` 进程：

```text
S.ll -> opt -passes="A,B" -> out_ab.ll
S.ll -> opt -passes="B,A" -> out_ba.ll
```

该模型优点是实现简单、证书易复现、analysis cache 状态干净。缺点是它不完全等价于一个长 pipeline 内部复用 analysis cache 的语境。

因此文档必须明确：

> 第一版证书适用于 materialized-state execution model。最终候选 pipeline 必须作为完整 pipeline 重新运行和验证，不能只依赖局部证书。

第二阶段可以实现：

```text
execution_model = in_driver_prefix_pair
```

即自定义 LLVM driver 在同一个 pass manager 中执行：

```text
prefix -> A -> B
prefix -> B -> A
```

它更接近真实 pipeline，但工程复杂度更高。

### 3.3 程序状态

程序状态定义为：

```text
S = (
  LLVM IR module,
  compiler environment C,
  pass manager nesting context,
  debug policy,
  metadata policy,
  execution model E,
  optional analysis-cache policy
)
```

工程中的状态 ID：

```text
StateID = SHA256(
  hard_normalized_ir,
  llvm_env_id,
  target_triple,
  data_layout,
  execution_model,
  pipeline_nesting,
  normalizer_version,
  debug_policy,
  metadata_policy
)
```

### 3.4 Pass instance

必须区分 pass type 和 pass instance：

```text
instcombine#1 != instcombine#2
```

一个 pass instance 至少包含：

```text
pass_instance_id
pass_name
position_in_anchor_pipeline
pipeline_region_id
ir_level: module / cgscc / function / loop
nesting_string
is_required_or_structural
```

同一个 pass type 在不同位置、不同 prefix state 下效果可能完全不同。

### 3.5 Reorderable region

不能把 LLVM pipeline 扁平化。必须先解析 pipeline nesting，并划分可重排区域：

```text
Region = 同一 IR level、同一 pass manager context、满足合法交换约束的一段 pass instance 序列
```

例如：

```text
module(function(sroa,early-cse,instcombine,simplifycfg))
```

只允许在 `function(...)` 内部受控重排。不同 region 间默认冻结，不跨层级交换。

### 3.6 Normalizer

定义：

```text
N : S -> S_hat
```

v1 hard proof 采用保守 normalizer。严格地说，若要从 `N(S1)=N(S2)` 推出后续 suffix 不区分二者，需要一个条件：

```text
N 对所允许的后续 pass 观察是完备的。
```

这个条件工程上很难证明。因此 v1 采用更保守做法：

```text
hard equality 尽量接近 exact IR equality，保留所有可能影响优化和 codegen 的信息。
```

若 normalizer 进行了任何可能改变 pass 可观察输入的归一化，则该结果只能作为 soft evidence。

---

## 4. 理论保证与定理

本节给出修订版理论保证。所有保证都是条件性的，必须满足证书、状态索引、执行模型和 normalizer 条件。

### 4.1 定义：状态索引的证书化独立性

对两个相邻 pass instance `A, B` 和状态 `S`，定义：

```text
CertifiedIndependent(A, B, S, E, C)
```

当且仅当：

1. `A` 和 `B` 在 `S` 所在 reorderable region 内合法交换；
2. 在固定执行模型 `E` 和编译环境 `C` 下，以下两条命令都成功：

   ```text
   S -> A;B
   S -> B;A
   ```

3. 两个输出均通过 LLVM verifier；
4. hard normalizer 输出相等：

   ```text
   N(B(A(S))) == N(A(B(S)))
   ```

5. 证书记录了输入 hash、命令、输出 hash、normalizer 版本、pipeline nesting、debug policy、metadata policy 和环境 ID。

### 4.2 定理 1：局部相邻交换安全性

**定理**：设 pipeline 片段为：

```text
u ; A ; B ; v
```

其中 `u` 是 prefix，`v` 是 suffix。令：

```text
S = u(P0)
```

如果存在证书：

```text
CertifiedIndependent(A, B, S, E, C)
```

并且满足以下条件之一：

1. `A;B` 与 `B;A` 的 hard output 是 exact materialized IR equality；或
2. hard normalizer `N` 对 suffix `v` 的所有 pass 是观察完备的；

则在同一执行模型和编译环境下，交换 `A,B` 不会产生新的规范化 IR 结果：

```text
N(v(B(A(S)))) == N(v(A(B(S))))
```

**证明**：

由证书定义可得：

```text
N(B(A(S))) == N(A(B(S)))
```

若 hard equality 是 exact materialized IR equality，则后续 suffix `v` 从相同 IR、相同环境、相同 nesting 和相同 debug/metadata policy 开始，确定性执行得到相同结果。若使用 normalizer，则需要 `N` 对 suffix 可观察输入完备，即后续 pass 无法区分两个 `N` 相同的状态，因此执行 `v` 后仍得到相同规范化结果。

证毕。

**工程含义**：

该定理不是说 `A,B` 全局可交换，而是说：

```text
A,B 在当前 prefix 产生的状态 S 上、在证书记载的执行模型中可以安全交换。
```

### 4.3 定理 2：多次证书化相邻交换保持结果

**定理**：若 pipeline `pi1` 可以通过有限次相邻交换变为 `pi2`，且每一次交换都有对应当前状态上的 `CertifiedIndependent` 证书，则：

```text
N(pi1(P0)) == N(pi2(P0))
```

**证明**：

对交换次数做归纳。

- 0 次交换时，结论显然成立。
- 假设前 `k` 次交换保持最终规范化结果不变。
- 第 `k+1` 次交换发生在某个实际 prefix state `S_k` 上，并有证书。由定理 1，该次交换不改变后续规范化结果。

因此有限次证书化相邻交换整体不改变最终规范化 IR。

证毕。

### 4.4 定理 3：Hard pruning 不丢失规范化 IR 结果

**定理**：设原搜索空间为 `Omega`，reduced space `R` 通过以下规则得到：

```text
只合并由证书化相邻交换连接的 pipeline。
每个等价类保留一个 representative。
```

如果每一次合并都满足定理 2 的条件，则：

```text
{ N(pi(P0)) | pi in Omega }
= 
{ N(r(P0)) | r in R }
```

**证明**：

任取 `pi in Omega`。根据 representative 定义，存在 `r in R`，使 `pi` 可通过有限次证书化相邻交换变成 `r`。由定理 2：

```text
N(pi(P0)) == N(r(P0))
```

所以原空间中的每个规范化结果都被 reduced space 覆盖。反过来，`R` 是 `Omega` 的子集或代表集合，因此 reduced space 不会产生原空间之外的结果。

证毕。

### 4.5 定理 4：静态预筛不影响 soundness

**定理**：如果静态预筛只用于候选生成、优先级排序或冻结 pass，而不直接产生 `definitely_independent`，则静态预筛误判不会造成错误 hard pruning。

**证明**：

Hard pruning 的唯一来源是 `CertifiedIndependent` 证书。静态预筛不产生证书，因此无论它是否漏掉某些可交换 pair，最多造成系统少发现 independent 关系、压缩率下降，不会把真正 dependent 的 pair 错误折叠。

证毕。

### 4.6 定理 5：Unknown 保守性

**定理**：如果系统对所有未证实 independent 的 pair 都标为 `unknown` 或 `dependent`，并且不对它们做 hard pruning，则 unknown 判断不会破坏 soundness。

**证明**：

系统只对 `definitely_independent` 做 hard pruning。`unknown` pair 不被折叠，仍保留在搜索空间或被冻结在 anchor 顺序中。因此 unknown 的后果只是搜索空间更大，而不是删除可能重要的顺序。

证毕。

### 4.7 定理 6：Reduced space 内最优的条件

若系统在 reduced space `R` 中穷举所有候选，并且目标函数 `M` 是确定性的，或通过统计协议控制噪声，则选择：

```text
pi* = argmin_{pi in R} M(pi(P0))
```

可以声称：

```text
pi* 是证书等价类商空间内的最优。
```

但如果使用 beam search、Bayesian optimization、MCTS、遗传算法或 RL 等非穷举搜索，则只能声称：

```text
pi* 是当前搜索预算下找到的最好候选。
```

该限制不影响 hard pruning 的 soundness，只影响“最优性”声明强度。

---

## 5. 系统整体流程

修订版 ECPOR 的完整流程如下：

```text
Step 0. 固定 LLVM 环境、target、flags、debug policy、metadata policy、controlled pipeline。
Step 1. 用 opt --print-passes 与 -debug-pass-manager 记录 pass 名称、可用性和 nesting。
Step 2. 解析 anchor pipeline，生成 pass instances 与 reorderable regions。
Step 3. 对输入 IR 做 cheap feature scan。
Step 4. 用 PassSpec 做高召回候选 pass/pair 生成；低相关 pass 冻结，不删除。
Step 5. 搜索器只在同一 reorderable region 内提出相邻交换。
Step 6. 每次想交换 A,B 时，计算当前 prefix state S。
Step 7. 查找 certificate(A,B,S,E,C)。
Step 8. 如果无证书且预算允许，运行 dynamic pair test。
Step 9. 如果 hard hash 相等，创建 CertifiedIndependent 证书并允许 hard collapse。
Step 10. 如果不同，记录 observed interaction 或 unknown，不 hard prune。
Step 11. 生成候选 pipeline。
Step 12. 每个候选 pipeline 完整运行 opt pipeline。
Step 13. 通过 verifier、可选 Alive2/test、code size/runtime evaluator。
Step 14. 输出推荐 pipeline、证据数据库、解释报告。
```

### 5.1 高层架构图

```text
+---------------------+
| LLVM Environment    |
| Version/Target/Flags|
+----------+----------+
           |
           v
+---------------------+       +------------------+
| Pipeline Parser     |<----->| PassSpec DB       |
| Region Resolver     |       | Static Hints      |
+----------+----------+       +------------------+
           |
           v
+---------------------+       +------------------+
| Feature Scanner     |-----> | Static Candidate  |
| Program Features    |       | Generator         |
+----------+----------+       +---------+--------+
                                      |
                                      v
+---------------------+       +------------------+
| Search Engine       |-----> | Lazy Pair Tester  |
| Adjacent Swaps      |       | A;B vs B;A        |
+----------+----------+       +---------+--------+
           |                            |
           v                            v
+---------------------+       +------------------+
| Evidence DB         |<----- | Certificate Mgr   |
| State-indexed       |       | Hash/Diff/Logs    |
+----------+----------+       +---------+--------+
           |
           v
+---------------------+       +------------------+
| Final Validator     |-----> | Report Generator  |
| Full Pipeline Rerun |       | Explanation       |
+---------------------+       +------------------+
```

---

## 6. 模块设计与实现细节

### 6.1 Environment Manager

职责：固定所有影响 pass 行为和证书有效性的环境信息。

#### 输入

```yaml
llvm:
  opt_path: /path/to/opt
  clang_path: /path/to/clang
  llvm_config_path: /path/to/llvm-config
  expected_version: "LLVM 18.x or fixed commit"

target:
  triple: "x86_64-unknown-linux-gnu"
  cpu: "native or fixed-cpu"
  features: ""
  data_layout: "auto-detected or fixed"

policies:
  execution_model: "materialized_ir_fresh_opt"
  debug_policy: "strip_at_input"
  metadata_policy: "preserve_optimization_metadata"
  normalizer_version: "hard-normalizer-v1"
```

#### 输出

```json
{
  "env_id": "sha256(...)" ,
  "llvm_version": "...",
  "opt_path": "...",
  "target_triple": "...",
  "flags": [...],
  "debug_policy": "strip_at_input",
  "metadata_policy": "preserve_optimization_metadata"
}
```

#### 实现细节

1. 运行 `opt --version`、`llvm-config --version` 记录版本。
2. 运行 `opt --print-passes` 保存 pass registry snapshot。
3. 所有实验输出目录中保存 `env.json`。
4. 证书中必须包含 `env_id`。

---

### 6.2 Pipeline Parser 与 Reorderable Region Resolver

该模块是 soundness-critical 模块。不能把 pipeline 当成扁平列表。

#### 输入

```text
anchor pipeline string
opt --print-passes output
-debug-pass-manager output
PassSpec DB
```

#### 输出

```json
{
  "pipeline_id": "...",
  "instances": [
    {
      "pass_instance_id": "instcombine#3",
      "pass_name": "instcombine",
      "position": 12,
      "ir_level": "function",
      "region_id": "function_region_2",
      "nesting": "module(function(...))",
      "reorderable": true
    }
  ],
  "regions": [
    {
      "region_id": "function_region_2",
      "ir_level": "function",
      "start": 9,
      "end": 16,
      "allowed_swaps": "adjacent_only"
    }
  ]
}
```

#### 实现原则

1. 只在同一 IR level、同一 nesting context 内交换。
2. `ModulePass`、`CGSCCPass`、`FunctionPass`、`LoopPass` 不跨层级交换。
3. required/structural pass 默认冻结。
4. 不能确定 legality 的 pass 标为 unsupported 或 frozen。
5. 所有实际运行的 pipeline 必须先通过 `opt -passes="..." -disable-output` 或等效 dry-run 验证语法。

#### MVP 建议

MVP-1 只使用受控 function scalar pipeline，例如：

```text
function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)
```

实际 pass 名称必须以当前 LLVM 版本的 `opt --print-passes` 为准。

---

### 6.3 PassSpec DB

PassSpec 是高召回、低精度的 candidate generator，不是静态证明器。

#### 数据结构

```yaml
instcombine:
  level: function
  required_features:
    - has_instructions
  coarse_effect_tags:
    may_read:
      - opcode
      - operands
      - constants
      - attributes
    may_write:
      - instructions
      - use_def
    may_produce:
      - simplified_expression
      - dead_instruction
    may_consume:
      - algebraic_pattern
      - constant_operand
  invalidation_hints:
    - instruction_analyses
  known_soft_followers:
    - dce
    - simplifycfg
  first_version_scope: "manual-mvp"

sroa:
  level: function
  required_features:
    - has_alloca
  coarse_effect_tags:
    may_read:
      - alloca
      - aggregate_type
    may_write:
      - allocas
      - loads
      - stores
      - scalar_values
    may_produce:
      - scalarized_memory
      - instcombine_opportunity
  known_soft_followers:
    - early-cse
    - instcombine
```

#### 重要限制

1. `may_read/may_write` 是 coarse effect tags，不是精确读写集。
2. `PreservedAnalyses` 只能作为 invalidation hint，不等价于 IR write set。
3. `known_soft_followers` 只是候选生成提示，不是 hard precedence。
4. PassSpec 误判只会影响候选生成，不影响 hard pruning soundness。

#### 构建方式

MVP 推荐手工维护 8-12 个 pass 的 PassSpec。后续可以半自动从 LLVM 源码提取：

```text
AM.getResult<...Analysis>()
PreservedAnalyses::none()
PA.preserve<...>()
PA.preserveSet<CFGAnalyses>()
```

但提取结果只能作为 hint。

---

### 6.4 Program Feature Scanner

职责：对输入 IR 做便宜扫描，生成程序特征。

#### 输出特征

```json
{
  "num_functions": 12,
  "num_basic_blocks": 240,
  "num_instructions": 1840,
  "has_loops": true,
  "has_calls": true,
  "has_alloca": true,
  "has_load_store": true,
  "has_globals": false,
  "has_switch": false,
  "has_phi": true,
  "has_vector_ops": false,
  "has_floating_point": true,
  "has_exception_handling": false,
  "opcode_histogram": {
    "load": 233,
    "store": 122,
    "br": 260,
    "phi": 88
  }
}
```

#### 实现方式

MVP 可用 Python 解析 `.ll` 文本，或调用 LLVM 工具生成粗略统计。更稳的版本是写 LLVM analysis pass 输出 JSON。

#### 注意

Program features 不用于证明 pass 无关，只用于候选生成和冻结决策。

---

### 6.5 Static Candidate Generator

职责：从所有 pass instances 中生成少量候选 pair。

#### 输入

```text
pass instances
reorderable regions
PassSpec DB
ProgramFeatures
search budget
window_size
```

#### 输出

```json
{
  "candidate_pairs": [
    {
      "A": "instcombine#2",
      "B": "dce#1",
      "reason": ["A may_produce dead_instruction", "B may_consume dead_instruction"],
      "priority": "high"
    }
  ],
  "frozen_passes": [
    {
      "pass": "unsupported_inline#1",
      "reason": "interprocedural unsupported in MVP"
    }
  ]
}
```

#### 规则

1. 不跨 reorderable region 生成 pair。
2. 默认只生成距离不超过 `window_size` 的 pair。
3. 如果 `A.may_write ∩ B.may_read` 或 `B.may_write ∩ A.may_read` 非空，则生成候选。
4. 如果 `A.may_produce ∩ B.may_consume` 非空，则生成候选。
5. 如果 PassSpec 有 known soft follower 关系，则生成候选。
6. 对低优先级 pass：冻结默认位置，不删除。
7. 对 unsupported pass：冻结或在实验定义阶段排除。

#### 伪代码

```python
def generate_candidate_pairs(instances, regions, specs, features, window):
    pairs = []
    frozen = []

    for region in regions:
        local = region.instances
        for p in local:
            if is_structural_or_unsupported(p, specs):
                frozen.append(p)

        active = [p for p in local if p not in frozen]

        for i, A in enumerate(active):
            for B in active[i+1 : min(i+1+window, len(active))]:
                if not same_reorderable_region(A, B):
                    continue
                reason = []
                if coarse_rw_may_interact(specs[A.name], specs[B.name]):
                    reason.append("coarse read/write overlap")
                if producer_consumer_may_exist(specs[A.name], specs[B.name]):
                    reason.append("producer-consumer hint")
                if known_soft_relation(specs[A.name], specs[B.name]):
                    reason.append("known soft relation")
                if reason:
                    pairs.append((A, B, reason))

    return pairs, frozen
```

---

### 6.6 Pipeline Runner

职责：运行 `opt` pipeline，保存输出 IR、verifier 结果、stats、remarks、timing。

#### 基本命令形态

```bash
opt input.ll \
  -S \
  -passes="function(instcombine,dce)" \
  -verify-each \
  -stats \
  -time-passes \
  -o output.ll
```

Remarks 可选：

```bash
opt input.ll \
  -S \
  -passes="..." \
  -pass-remarks=.* \
  -pass-remarks-missed=.* \
  -pass-remarks-analysis=.* \
  -o output.ll
```

具体 flags 以固定 LLVM 版本实际支持为准。若某个 flag 不可用，Environment Manager 必须记录替代方案。

#### 输出

```json
{
  "run_id": "...",
  "input_state_hash": "...",
  "pipeline": "...",
  "command": "...",
  "exit_code": 0,
  "verifier_ok": true,
  "output_ir_path": "...",
  "raw_ir_hash": "...",
  "hard_hash": "...",
  "soft_fingerprints": {},
  "stats_path": "...",
  "remarks_path": "...",
  "stderr_path": "...",
  "time_ms": 123
}
```

#### 实现细节

1. 每次运行必须记录完整命令和 stdout/stderr。
2. 所有输出文件 content-addressed 存储。
3. 若 verifier fail，则该 run 不能产生 independent 证书。
4. 若 pass name 或 pipeline nesting 无法运行，pair 标为 unsupported/unknown。
5. MVP 可以先用外部 `opt` 命令；后续再开发 C++ driver/plugin。

---

### 6.7 IR Normalizer

职责：生成 hard hash 和 soft fingerprints。

#### Hard normalizer v1

推荐做法：

1. 实验输入阶段统一 debug policy。如果目标不包含 debug size，可以先统一 strip debug；否则保留 debug。
2. 不删除优化相关 metadata。
3. 不重排 function/global/basic block。
4. 不改写 value name、basic block name，除非能证明 LLVM printer 非确定性导致假差异；MVP 可以先避免 alpha-renaming。
5. 使用同一 LLVM 版本输出的 `.ll` 或 `.bc` 直接 hash。
6. 对 hard proof，优先使用 `hard_hash == hard_hash`。

#### Soft fingerprints

可计算：

```text
instruction_count
opcode_histogram
cfg_hash
callgraph_hash
loop_structure_hash
instruction_multiset_hash
metadata_summary_hash
remarks_hash
stats_hash
```

这些用于解释、方向归因、候选排序，不能单独产生 hard independent。

#### 输出

```json
{
  "raw_hash": "sha256(raw output.ll)",
  "hard_hash": "sha256(hard_normalized_ir)",
  "soft": {
    "cfg_hash": "...",
    "opcode_histogram_hash": "...",
    "feature_vector_hash": "..."
  },
  "normalizer_version": "hard-normalizer-v1",
  "debug_policy": "strip_at_input",
  "metadata_policy": "preserve_optimization_metadata"
}
```

---

### 6.8 Lazy Dynamic Pair Tester

职责：对搜索器当前想交换的相邻 pair 进行按需验证。

#### 输入

```text
A, B
current prefix u
current state S = u(P0)
execution model E
compiler env C
budget
```

#### 证书查询 key

```json
{
  "A_id": "instcombine#2",
  "B_id": "dce#1",
  "input_state_hash": "...",
  "execution_model": "materialized_ir_fresh_opt",
  "env_id": "...",
  "pipeline_nesting": "function(...)" ,
  "normalizer_version": "hard-normalizer-v1"
}
```

#### 测试过程

```text
1. materialize S -> S.ll
2. run S.ll with pipeline A;B -> out_ab.ll
3. run S.ll with pipeline B;A -> out_ba.ll
4. verify both outputs
5. compute hard_hash(out_ab), hard_hash(out_ba)
6. if equal: emit CertifiedIndependent
7. else: send to Direction Attribution / unknown
```

#### 伪代码

```python
def certify_adjacent_swap(A, B, state, env, nesting, budget):
    key = cert_key(A, B, state, env, nesting)
    if EvidenceDB.has_valid_cert(key):
        return EvidenceDB.get(key)

    if budget.exhausted():
        return Unknown(reason="budget exhausted")

    ab = runner.run(state.ir_path, pipeline=nesting.with_sequence([A, B]))
    ba = runner.run(state.ir_path, pipeline=nesting.with_sequence([B, A]))

    if not ab.verifier_ok or not ba.verifier_ok:
        return Unknown(reason="verifier failure")

    if ab.hard_hash == ba.hard_hash:
        cert = make_independence_certificate(A, B, state, ab, ba)
        EvidenceDB.put(cert)
        return cert

    return analyze_difference(A, B, state, ab, ba)
```

#### 注意

1. 该测试只证明当前 `state_hash` 上的可交换性。
2. 不能把证书复用于不同 prefix state。
3. 不能因为 `A,B` 在若干 observed states 上都 independent，就宣布全局 independent。

---

### 6.9 Direction Attribution

职责：当 `A;B` 与 `B;A` 的 hard hash 不同，生成解释性 soft evidence。

#### 输入

```text
S
A(S)
B(S)
B(A(S))
A(B(S))
features / remarks / stats / diff
```

#### Effect vector

```text
Effect_p(S) = Δ(
  hard_hash,
  soft_features,
  opcode histogram,
  instruction count,
  CFG summary,
  remarks,
  stats,
  optional metric
)
```

#### 输出标签

| 标签 | 含义 | 是否 hard constraint |
|---|---|---|
| observed_enable_candidate | `B(S)` 几乎无变化，但 `B(A(S))` 有明显变化 | 否 |
| observed_suppress_candidate | `B(S)` 有变化，但 `B(A(S))` 变化消失或变差 | 否 |
| observed_conflict_candidate | 两种顺序产生不同 IR 且难以归因 | 否 |
| metric_sensitive | 两种顺序目标函数差异显著 | 否，需最终完整评估 |
| unknown | 无法解释或证据不足 | 否 |

#### 示例解释

```text
Pair: instcombine#2, dce#1
Witness state: S_hash
Observation:
  dce(S) removed 0 instructions
  dce(instcombine(S)) removed 5 instructions
Soft explanation:
  instcombine produced dead_instruction-like patterns consumed by dce
Evidence:
  instruction count delta
  stats delta
  IR diff in function @foo
```

#### 重要边界

`observed_enable_candidate` 不是严格因果证明，也不是 hard ordering constraint。它只说明在该 witness state 上观察到某种 counterfactual 差异。搜索器可用它调整优先级，但最终顺序仍由完整候选 pipeline 评估决定。

---

### 6.10 Evidence DB 与 Interaction Graph

修订版不把 graph 当作全局证明对象，而是把证据分层存储。

#### Evidence DB

```json
{
  "independence_certificates": [
    {
      "cert_id": "...",
      "A_id": "...",
      "B_id": "...",
      "input_state_hash": "...",
      "execution_model": "...",
      "env_id": "...",
      "hard_hash_ab": "...",
      "hard_hash_ba": "...",
      "claim": "definitely_independent_on_state"
    }
  ],
  "soft_interactions": [
    {
      "edge_id": "...",
      "A_id": "...",
      "B_id": "...",
      "state_hash": "...",
      "label": "observed_enable_candidate",
      "evidence": {...}
    }
  ],
  "unknowns": [
    {
      "A_id": "...",
      "B_id": "...",
      "state_hash": "...",
      "reason": "timeout or unsupported"
    }
  ]
}
```

#### Graph 视图

从 Evidence DB 可生成三种 graph 视图：

1. **Hard legality graph**：pass manager nesting、required pass、结构性约束。
2. **State-indexed independence graph**：仅显示某个 state 上已经证实的 adjacent commutation。
3. **Soft interaction graph**：observed-enable、observed-suppress、observed-conflict，用于解释和搜索启发。

#### 注意

跨分量无边不代表 independent，可能只是没测。只有当跨分量相关相邻交换都有证书时，component decomposition 才是 sound reduction。否则 component decomposition 只是 heuristic。

---

### 6.11 Reduced Search Engine

职责：在 anchor pipeline 附近做局部搜索，并通过 lazy validation 进行 hard pruning。

#### 搜索原则

1. 以 controlled anchor pipeline 为起点。
2. 只在 reorderable region 内进行 adjacent swap。
3. 每次 swap 前必须查证书或触发 lazy validation。
4. 只有 `CertifiedIndependent` 可以折叠重复状态。
5. Soft interaction edge 只影响候选排序，不直接排除候选。
6. Frozen pass 保持默认相对位置。
7. 最终候选必须完整复跑。

#### 搜索策略

MVP 推荐：

```text
region size <= 7: exhaustive search with certified quotient
region size 8-15: beam search
larger: budgeted local search / MCTS / BO optional
```

#### 伪代码

```python
def search_region(anchor_region, P0, env, budget):
    frontier = [anchor_region.sequence]
    visited = set()
    candidates = []

    while frontier and not budget.exhausted():
        seq = frontier.pop()
        full_pipeline = assemble_pipeline(seq)
        state_key = pipeline_prefix_signature(seq)

        if state_key in visited:
            continue
        visited.add(state_key)

        candidates.append(seq)

        for i in range(len(seq) - 1):
            A, B = seq[i], seq[i+1]
            if not legal_adjacent_swap(A, B):
                continue

            S = materialize_prefix_state(P0, seq[:i])
            result = certify_adjacent_swap(A, B, S, env, nesting=seq.region)

            if result.kind == "certified_independent":
                # AB and BA are equivalent at this state; avoid adding duplicate if desired.
                continue
            elif result.kind in ["soft_interaction", "unknown"]:
                new_seq = swap(seq, i, i+1)
                if heuristic_allows(new_seq, result):
                    frontier.append(new_seq)

    return candidates
```

#### 关于最优性声明

- 若 exhaustive search 覆盖 reduced space：可以声明 reduced space 内最优。
- 若 beam/local search：只能声明搜索预算内最好。

---

### 6.12 Final Pipeline Validator

局部证书不能替代完整 pipeline 验证。所有最终候选必须完整复跑。

#### 验证步骤

```text
1. 用完整 candidate pipeline 运行 opt。
2. 加 -verify-each 或至少最终 verifier。
3. 检查输出 IR 是否有效。
4. 可选：对支持范围内的 transformation 使用 Alive2 / translation validation。
5. codegen 成 object/binary。
6. 运行测试或 differential testing。
7. 评估 code size / runtime / compile time。
8. 与 anchor pipeline 比较。
```

#### code size 目标

MVP 建议优先做 code size，因为 runtime 噪声更大。

可记录：

```text
IR instruction count
object file size
.text section size
binary size
```

最终以 `.text` 或目标平台定义的 size metric 为准。

#### runtime 目标

若做 runtime：

```text
固定 CPU governor
固定输入数据
warmup
多次重复
记录 median / mean / stddev
使用统计检验或置信区间
```

runtime 只用于最终排序，不作为 independence 证明。

---

### 6.13 Certificate Manager

每个 hard claim 必须有 certificate bundle。

#### Independence certificate schema

```json
{
  "cert_type": "state_indexed_adjacent_independence",
  "cert_id": "sha256(...)" ,
  "created_at": "2026-06-30T00:00:00Z",

  "environment": {
    "env_id": "...",
    "llvm_version": "...",
    "opt_path": "...",
    "target_triple": "...",
    "flags": [...]
  },

  "execution": {
    "execution_model": "materialized_ir_fresh_opt",
    "analysis_cache_policy": "fresh",
    "pipeline_nesting": "function(...)" ,
    "prefix_pipeline": "...",
    "state_materialization_command": "..."
  },

  "input": {
    "program_id": "...",
    "input_state_hash": "...",
    "input_ir_path": "...",
    "debug_policy": "strip_at_input",
    "metadata_policy": "preserve_optimization_metadata"
  },

  "passes": {
    "A_id": "instcombine#2",
    "B_id": "dce#1",
    "A_name": "instcombine",
    "B_name": "dce"
  },

  "commands": {
    "AB": "opt S.ll -S -passes=\"function(instcombine,dce)\" -verify-each -o ab.ll",
    "BA": "opt S.ll -S -passes=\"function(dce,instcombine)\" -verify-each -o ba.ll"
  },

  "outputs": {
    "ab_exit_code": 0,
    "ba_exit_code": 0,
    "ab_verifier_ok": true,
    "ba_verifier_ok": true,
    "ab_hard_hash": "...",
    "ba_hard_hash": "...",
    "hard_equal": true
  },

  "normalizer": {
    "normalizer_version": "hard-normalizer-v1",
    "hard_policy": "no entity reordering; preserve optimization metadata"
  },

  "claim": {
    "label": "definitely_independent_on_state",
    "scope": "only this state_hash under this execution_model and env_id"
  }
}
```

#### Soft interaction certificate schema

```json
{
  "cert_type": "soft_interaction_observation",
  "label": "observed_enable_candidate",
  "A_id": "instcombine#2",
  "B_id": "dce#1",
  "state_hash": "...",
  "evidence": {
    "B_on_S_effect": {...},
    "B_on_A_S_effect": {...},
    "feature_delta": {...},
    "remarks_delta": {...},
    "stats_delta": {...},
    "diff_summary": "..."
  },
  "claim_strength": "soft; not hard precedence"
}
```

---

### 6.14 Report Generator

最终报告应同时面向研究者和工程使用者。

#### 报告结构

```text
Program: foo.ll
LLVM env: env_id
Goal: code size
Execution model: materialized_ir_fresh_opt
Anchor pipeline: ...

1. Search Space Summary
   original region sizes
   frozen passes
   dynamic tests attempted
   certificates created
   unknown count
   certified compression
   heuristic reduction

2. Certified Independent Adjacent Swaps
   A,B,state_hash,hard_hash,evidence path

3. Soft Interactions
   observed-enable
   observed-suppress
   observed-conflict
   metric-sensitive

4. Unknowns
   timeout
   unsupported pass
   verifier failure
   normalizer ambiguity

5. Candidate Pipelines
   pipeline string
   verifier result
   code size / runtime
   comparison against anchor

6. Reproducibility
   exact commands
   environment
   certificate bundle paths
```

#### 关键原则

报告必须把 `certified_compression` 和 `heuristic_search_reduction` 分开：

```text
certified_compression:
  只统计 hard certificates 带来的等价类合并。

heuristic_search_reduction:
  统计 static filter、window、beam search、component heuristic 减少的候选数量。
```

---

## 7. 实现路线与里程碑

### 7.1 MVP-0：环境与最小 runner

目标：跑通固定 pipeline，并生成可复现 run record。

任务：

```text
1. 固定 LLVM 版本和 opt 路径。
2. 保存 opt --print-passes 输出。
3. 实现 runner.py。
4. 实现 hard hash 计算。
5. 实现 run record JSON。
```

验收：

```text
给定 input.ll 和 pipeline string，生成 output.ll、hash、stderr、stats、remarks、run.json。
```

### 7.2 MVP-1：Function scalar pass 子集

建议 pass 范围：

```text
sroa
early-cse
instcombine
simplifycfg
reassociate
gvn
dce
adce
```

暂缓：

```text
inline
ipsccp
globalopt
loop-vectorize
loop-unroll
backend/codegen pass
```

目标：

```text
1. 解析受控 function pipeline。
2. 生成 pass instances。
3. 对相邻 pair 做 lazy dynamic test。
4. 生成 independence certificates。
5. 输出简单报告。
```

验收指标：

```text
certificate reproducibility = 100% for hard claims
hard_false_independent = 0
unknown reason 全部可解释
```

### 7.3 MVP-2：Static Candidate Generator 与冻结机制

目标：降低 dynamic test 数量。

任务：

```text
1. 手写 PassSpec DB。
2. 实现 Program Feature Scanner。
3. 实现 windowed candidate generation。
4. 实现 frozen pass 标记。
5. 报告 static filter 对候选数量的影响。
```

验收：

```text
动态 pair test 数量显著低于全量 pair。
但 hard pruning 仍只来自证书。
```

### 7.4 MVP-3：Soft Interaction Attribution

目标：解释 dependent / non-equal pair。

任务：

```text
1. 计算 feature delta。
2. 解析 stats / remarks。
3. 生成 observed-enable / suppress / conflict 标签。
4. 输出 per-edge explanation。
```

验收：

```text
至少在 microbenchmarks 中能解释典型 producer-consumer：
  instcombine -> dce
  sroa -> instcombine
  simplifycfg -> instcombine
```

### 7.5 MVP-4：Reduced Search Engine

目标：用 lazy validation 支持局部搜索。

任务：

```text
1. 实现 adjacent-swap local search。
2. 实现 evidence-aware visited set。
3. 实现 hard/soft 分离的 candidate ranking。
4. 对最终 candidates 完整复跑。
```

验收：

```text
在 controlled anchor pipeline 上，reduced search 能找到与 exhaustive search 相同或接近的 code size 最优候选。
```

### 7.6 MVP-5：Loop pass 扩展

加入：

```text
loop-simplify
licm
loop-rotate
```

目标：展示更明显的结构性 interaction。

注意：loop pass nesting 必须由当前 LLVM 版本验证，不可硬写。

### 7.7 MVP-6：Interprocedural pass 作为 unknown-handling 展示

可选加入：

```text
inline
ipsccp
globalopt
```

但第一阶段不对这些 pass 做 hard proof，只展示：

```text
unsupported / unknown / frozen
soft evidence only
```

---

## 8. 实验设计

### 8.1 实验目标

MVP 的第一目标不是超过完整 `-O3`，而是验证 ECPOR 是否能：

```text
1. 生成可复现的 state-indexed independence certificates。
2. 区分 hard evidence 与 soft evidence。
3. 降低局部搜索候选数量。
4. 在 controlled anchor pipeline 上找到更优或等价候选。
5. 对 unknown 给出可解释原因。
```

### 8.2 Benchmark 选择

推荐顺序：

```text
1. 自造 microbenchmarks
2. LLVM test-suite SingleSource 小程序
3. cBench 子集
4. SPEC 中可快速运行的函数级/文件级样本，可作为后续扩展
```

### 8.3 对照组

```text
anchor pipeline:
  受控默认顺序

full exhaustive within region:
  小 region 上穷举，用作 ground truth

ECPOR reduced search:
  使用 hard certificates + soft heuristics

random / beam baseline:
  可选
```

### 8.4 指标

#### Soundness 与证书指标

```text
hard certificates count
hard certificate reproduction rate
hard_false_independent count
unknown count by reason
state_generalization_failure count
```

定义：

```text
hard_false_independent:
  系统标 definitely_independent，但同环境复现时 hard hash 不相等。
  这是严重 bug，目标为 0。

state_generalization_failure:
  A,B 在 S 上 independent，但在 S' 上不 independent。
  这不是 bug，只说明不能全局推广。

soft_prediction_error:
  soft interaction 对最终目标函数排序预测失败。
  不影响 soundness。
```

#### 搜索效率指标

```text
original candidates
static candidate pairs
dynamic tests performed
certified_compression ratio
heuristic_search_reduction ratio
cache hit rate
analysis time
```

#### 优化质量指标

```text
IR instruction count
object size
.text size
binary size
compile time
runtime median / variance, optional
```

### 8.5 成功标准

MVP-1 / MVP-2：

```text
1. 所有 hard certificates 可复现。
2. hard_false_independent = 0。
3. 对小 region exhaustive search，ECPOR 不丢失证书等价类下的结果。
4. 相比全量 pair，dynamic tests 明显减少。
```

MVP-4：

```text
1. 在 controlled region 内，reduced search 找到与 exhaustive 相同或接近的 best candidate。
2. 所有最终 candidate 完整复跑并通过 verifier。
3. 报告能解释 hard/soft/unknown。
```

---

## 9. 风险与修正策略

### 9.1 Normalizer 过强

风险：normalizer 删除了后续 pass 可观察的信息，导致错误 hard pruning。

策略：

```text
1. hard normalizer 极保守。
2. 不删除优化相关 metadata。
3. 不重排实体。
4. soft fingerprints 与 hard hash 分离。
5. hard_false_independent 通过复现测试监控。
```

### 9.2 状态特定证书被错误全局复用

风险：在 `S1` 上证明的 `A,B` 被用于 `S2`。

策略：

```text
certificate key 必须包含 input_state_hash。
没有当前 state 证书时必须 lazy validate 或 unknown。
```

### 9.3 Analysis cache 语境不一致

风险：fresh opt pair test 与完整 pipeline 内部 cache 行为不一致。

策略：

```text
1. 明确 v1 execution_model = materialized_ir_fresh_opt。
2. 最终 candidate 必须完整复跑。
3. v2 可实现 in-driver prefix-pair execution model。
```

### 9.4 静态 filter 误删 pass

风险：把 pass 删除后改变问题定义。

策略：

```text
静态 filter 只冻结 pass，不删除 pass。
除非实验一开始就定义搜索空间不包含该 pass。
```

### 9.5 Soft edge 被误当 hard constraint

风险：`A observed-enables B` 被固定为 `A before B`，漏掉目标函数更优顺序。

策略：

```text
soft edge 只用于 ranking，不用于 legality pruning。
hard edge 只来自结构约束或证书等价。
```

### 9.6 Unknown 爆炸

风险：大量 pair unknown，压缩率低。

策略：

```text
1. 缩小 MVP pass 集合。
2. 使用 controlled pipeline。
3. 提高 PassSpec 召回质量。
4. 增加 budgeted lazy validation。
5. 报告 unknown 原因，逐步扩展支持范围。
```

### 9.7 Benchmark 噪声

风险：runtime 噪声误导搜索。

策略：

```text
MVP 优先 code size。
runtime 只做最终评价。
不用 runtime 证明 independence。
```

### 9.8 LLVM pass name / nesting 变化

风险：不同 LLVM 版本 pass name 与 pipeline grammar 不一致。

策略：

```text
1. 固定 LLVM commit。
2. 保存 opt --print-passes。
3. 所有 pipeline 先 dry-run。
4. PassSpec 绑定 LLVM 版本。
```

---

## 10. 推荐项目目录结构

```text
ecpor/
  README.md
  pyproject.toml
  configs/
    env.yaml
    mvp_function_pipeline.yaml
  pass_specs/
    llvm_version_x/
      scalar_passes.yaml
      loop_passes.yaml
  src/
    ecpor/
      environment.py
      pipeline_parser.py
      region_resolver.py
      feature_scanner.py
      passspec.py
      candidate_generator.py
      runner.py
      normalizer.py
      evidence_db.py
      pair_tester.py
      attribution.py
      search.py
      validator.py
      report.py
  llvm_plugins/
    optional_pass_instrumentation/
  benchmarks/
    micro/
    llvm_test_suite_subset/
  experiments/
    exp_001/
      env.json
      input/
      states/
      runs/
      certificates/
      reports/
  docs/
    theory.md
    implementation.md
    certificate_schema.md
```

---

## 11. 关键数据结构

### 11.1 PassInstance

```python
@dataclass(frozen=True)
class PassInstance:
    id: str
    name: str
    position: int
    region_id: str
    ir_level: str
    nesting: str
    is_required: bool = False
    is_structural: bool = False
    supported: bool = True
```

### 11.2 State

```python
@dataclass(frozen=True)
class State:
    state_hash: str
    ir_path: Path
    env_id: str
    execution_model: str
    nesting_context: str
    normalizer_version: str
    debug_policy: str
    metadata_policy: str
    prefix_pipeline: str
```

### 11.3 RunRecord

```python
@dataclass
class RunRecord:
    run_id: str
    input_state_hash: str
    pipeline: str
    command: list[str]
    exit_code: int
    verifier_ok: bool
    output_ir_path: Path
    raw_hash: str
    hard_hash: str
    soft_fingerprints: dict
    stats_path: Path | None
    remarks_path: Path | None
    stderr_path: Path
    elapsed_ms: float
```

### 11.4 Certificate

```python
@dataclass
class IndependenceCertificate:
    cert_id: str
    A_id: str
    B_id: str
    input_state_hash: str
    env_id: str
    execution_model: str
    pipeline_nesting: str
    normalizer_version: str
    hard_hash_ab: str
    hard_hash_ba: str
    command_ab: list[str]
    command_ba: list[str]
    verifier_ok: bool
    scope: str = "state-specific"
```

---

## 12. 与 LLVM 基础设施的关系

### 12.1 `opt`

第一版主要依赖 `opt` 完成 pipeline 运行。需要使用的能力包括：

```text
-passes="..."       指定 New PM pipeline
-verify-each        每个 pass 后插入 verifier，或至少进行验证
-stats              输出统计信息
--save-stats        若当前版本支持，保存统计信息
-time-passes        记录 pass 时间
--print-passes      打印可用 pass
-pass-remarks       输出 successful optimization remarks
-pass-remarks-missed
-pass-remarks-analysis
```

具体选项以固定 LLVM 版本官方文档和本地 `opt --help` 为准。

### 12.2 New Pass Manager

New PM 的层级结构决定了 ECPOR 必须处理 nesting：

```text
Module
CGSCC
Function
Loop
```

不同层级不能随便混排。pass manager 还维护 analysis manager 与 `PreservedAnalyses`，这也是为什么 v1 采用 fresh materialized execution model，并要求最终完整复跑。

### 12.3 PassInstrumentation

PassInstrumentation 可在后续版本用于更细粒度 before/after pass 数据采集，也可能控制 optional pass 是否执行。但它不是 MVP 的必要条件。

MVP 先用：

```text
opt runner
output IR
hard hash
stats
remarks
stderr/time
```

等基础闭环跑通后，再实现 C++ driver 或 plugin。

### 12.4 Alive2

Alive2 可作为 correctness guard，用于支持范围内的 LLVM IR transformation validation。它不应作为 hard independence 的必要条件，也不能覆盖 interprocedural transformations。

处理规则：

```text
Alive2 success:
  可作为语义安全证据。

Alive2 fail / timeout / unsupported:
  不直接说明 transformation 错；标 unknown 或使用其他验证方式。

interprocedural pass:
  MVP 冻结或排除，不用 Alive2 生成 hard proof。
```

---

## 13. 文档中的关键术语

| 术语 | 含义 |
|---|---|
| hard pruning | 由证书支持的严格剪枝，只合并规范化 IR 相同的相邻交换结果。 |
| soft evidence | IR diff、remarks、stats、metric delta 等解释性证据，不直接剪枝。 |
| state-indexed | 所有结论绑定具体 `state_hash`，不全局推广。 |
| materialized_ir_fresh_opt | 每次 pair test 从保存的 IR 文件启动 fresh `opt`。 |
| frozen pass | 保留在 anchor pipeline 默认位置，不参与重排；不是删除。 |
| PassSpec | 粗粒度 pass 能力提示表，用于候选生成，不用于证明。 |
| certified_compression | 由 hard certificates 带来的等价类压缩。 |
| heuristic_reduction | 由静态 filter、window、beam search 等带来的搜索减少。 |
| unknown | 工具无法判断或预算不足，保守不剪枝。 |

---

## 14. 最小实验样例

### 14.1 Microbenchmark：instcombine 与 dce

输入构造：

```llvm
; 伪示例：制造可被 instcombine 化简并被 dce 清理的冗余表达式
```

期望观察：

```text
B = dce
A = instcombine

Effect_B(S): small or zero
Effect_B(A(S)): removes newly dead instructions
Label: observed_enable_candidate(A, B)
```

是否 hard independent 由 `A;B` 与 `B;A` hard hash 决定。即使 observed-enable 成立，也不能自动作为 hard precedence。

### 14.2 Microbenchmark：sroa 与 instcombine

期望观察：

```text
sroa scalarizes aggregate allocas
instcombine consumes scalar simplification opportunities
```

输出 soft evidence：

```text
sroa observed-enables instcombine on state S
```

### 14.3 Loop pass 第二阶段样例

加入：

```text
loop-simplify
licm
loop-rotate
```

期望观察：

```text
loop-simplify changes loop form
licm behavior changes after loop-simplify
```

注意：loop pass nesting 必须先用当前 LLVM 版本验证。

---

## 15. 最终报告示例

```text
ECPOR Report
============

Program: foo.ll
Goal: code size
LLVM env: env_3f2a...
Execution model: materialized_ir_fresh_opt
Anchor pipeline: function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)

Search Summary
--------------
Pass instances: 8
Reorderable regions: 1
Static candidate pairs: 14 / 28
Dynamic pair tests: 9
Certified independent swaps: 4
Soft interactions: 3
Unknowns: 2
Frozen passes: 0
Certified compression: 1.8x
Heuristic reduction: 3.1x

Certified Independent Swaps
---------------------------
1. early-cse#1 <-> simplifycfg#1 on state S_abc
   hard_hash_ab == hard_hash_ba
   certificate: certs/cert_001.json

Soft Interactions
-----------------
1. instcombine#1 observed-enables dce#1 on state S_def
   dce(S): removed 0 instructions
   dce(instcombine(S)): removed 5 instructions
   evidence: reports/diff_003.md

Unknowns
--------
1. gvn#1 ? adce#1 on state S_xyz
   reason: dynamic test timeout
   search action: no hard pruning

Final Candidates
----------------
Candidate 1:
  pipeline: function(sroa,early-cse,instcombine,dce,simplifycfg,reassociate,gvn,adce)
  verifier: ok
  .text size: 12345 bytes
  improvement vs anchor: -1.7%

Reproducibility
---------------
Environment: env.json
Commands: commands.sh
Certificates: certs/
```

---

## 16. 推荐写法：项目摘要

可以在论文/开题报告中这样描述：

> ECPOR is a state-indexed, certificate-driven phase-ordering reduction framework for LLVM IR pipelines. For a fixed program, compiler environment, execution model, and pass-instance search space, ECPOR performs hard pruning only when an adjacent pass swap is certified to produce identical hard-normalized IR on the actual intermediate state. All unverified interactions are conservatively kept as dependent or unknown. Static pass specifications and program features are used only for high-recall candidate generation and freezing, not for hard independence proofs. Non-equal pass interactions are recorded as soft evidence such as observed-enable or observed-suppress relations and used to guide local search. Final candidate pipelines are always rerun and validated as complete pipelines. Therefore, ECPOR's hard reduction is sound under its stated execution model, while its explanatory report remains reproducible and auditable.

中文版本：

> ECPOR 是一个状态索引、证书驱动的 LLVM IR phase-ordering 搜索空间坍缩框架。在固定程序、固定编译器环境、固定执行模型和固定 pass instance 搜索空间下，系统只有在当前中间状态上证明相邻 pass 交换产生相同 hard-normalized IR 时，才进行严格剪枝；所有未验证的交互都保守保留为 dependent 或 unknown。静态 PassSpec 与程序特征只用于高召回候选生成和冻结机制，不用于硬证明。IR 不同的交互被记录为 observed-enable、observed-suppress 等 soft evidence，用于解释和引导局部搜索。最终候选 pipeline 必须完整复跑和验证。因此，ECPOR 的 hard reduction 在其声明的执行模型下是 sound 的，同时其报告具有可解释性和可复现性。

---

## 17. 参考资料

1. LLVM `opt` Command Guide: https://llvm.org/docs/CommandGuide/opt.html
2. LLVM New Pass Manager: https://llvm.org/docs/NewPassManager.html
3. LLVM Optimization Remarks: https://llvm.org/docs/Remarks.html
4. LLVM PassInstrumentation Doxygen: https://llvm.org/doxygen/classllvm_1_1PassInstrumentation.html
5. Alive2 GitHub README: https://github.com/AliveToolkit/alive2
6. DPOR / Partial-order reduction background: https://users.soe.ucsc.edu/~cormac/papers/popl05.pdf
7. AutoPhase: https://proceedings.mlsys.org/paper_files/paper/2020/file/5b47430e24a5a1f9fe21f0e8eb814131-Paper.pdf

---

## 18. 结论

修订版项目的核心判断是：

```text
项目可行，但必须保守定义理论保证。
```

最关键的落地原则是：

```text
1. 只证明当前状态上的相邻交换，不证明全局 pass pair 可交换。
2. hard pruning 只来自证书，不来自静态预筛或 runtime 近似。
3. 静态方法只生成候选和冻结 pass，不删除 pass。
4. observed-enable / suppress 是 soft evidence，不是 hard constraint。
5. graph 是 evidence view，不是全局可交换性证明。
6. final pipeline 必须完整复跑验证。
```

因此，本项目应被定位为：

> 一个能安全删除已证实重复顺序、保守保留未知交互、并用可解释证据引导局部搜索的 LLVM IR phase-ordering reduction 原型。

这个定位既保留了原始项目的研究价值，也避免了 v1.0 中“normalizer 过强、全局图过强、静态 filter 过强、soft edge 过强”的落地风险。
