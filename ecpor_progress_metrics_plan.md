# ECPOR 项目进度与评价指标一体化计划

> 项目名称建议：**ECPOR: Evidence-Carrying Phase-Ordering Reduction**  
> 中文名称：**基于证据的 LLVM IR Phase Ordering 搜索空间坍缩系统**

---

## 0. 项目当前定位

本项目不以“找到所有 LLVM pass 任意排列下的绝对全局最优顺序”为目标。当前阶段的正确目标是：

> 在固定 LLVM 版本、固定输入程序、固定 target、固定 pass instance 集合和固定目标函数下，只对当前状态上有证书证明的相邻 pass 交换做 hard pruning；其他无法证明的情况保守标为 `unknown` 或 `not_certified`，并通过局部搜索寻找优于 controlled anchor pipeline 的候选顺序。

核心思想是：

```text
不要先找最优顺序
而是先证明哪些顺序不用搜
```

第一版项目要证明三件事：

```text
1. 能对相邻 pass A,B 在状态 S 上生成可复现 certificate；
2. 能安全地区分 certified_independent / not_certified / unknown；
3. 能减少实际需要动态验证和搜索的顺序选择，并在 code size 目标上得到不差于 anchor 的结果。
```

---

## 1. 总体路线图

项目从 0 开始分成三层：

```text
第 1 层：证书闭环
    输入 .ll
    运行 A;B 和 B;A
    比较 hard canonical hash
    输出 certificate

第 2 层：候选过滤 + lazy validation
    静态筛选只生成候选，不产生证明
    搜索器需要交换时才触发动态验证
    certificate key 必须包含 state_hash

第 3 层：局部搜索 + code size 评估 + 报告
    在受控 pass 子集里搜索
    输出 best candidate pipeline
    输出指标表、证书和解释报告
```

**关键约束：**

```text
hard pruning 只能来自：
    N(B(A(S))) == N(A(B(S)))

不能来自：
    静态 footprint
    feature 相似
    code size 相近
    runtime 相近
    observed-enable / observed-suppress 边
```

---

## 2. 推荐项目目录

```text
ecpor/
  README.md
  configs/
    env.yaml
    pipeline_scalar.yaml
    passspec.yaml
  data/
    inputs/
    states/
    outputs/
    objects/
    certs/
  ecpor/
    __init__.py
    config.py
    runner.py
    normalizer.py
    feature_scan.py
    cert.py
    pair_test.py
    static_filter.py
    lazy_validator.py
    search.py
    evaluator.py
    report.py
    metrics.py
    main.py
  experiments/
    run_microbenchmarks.py
  reports/
  tests/
```

---

## 3. 阶段总览

| 阶段 | 时间 | 核心目标 | 主要产物 | 核心评价指标 |
|---|---:|---|---|---|
| P0 | 第 1 周 | 固定环境，跑通 `opt` runner | `runner.py`, `env.yaml` | `RunnerSuccessRate`, `OptFailureCount` |
| P1 | 第 2 周 | 实现保守 normalizer 和 IR hash | `normalizer.py`, `feature_scan.py` | `HashReproductionRate`, `VerifierPassRate` |
| P2 | 第 3 周 | 实现 pair test + certificate | `pair_test.py`, `cert.py` | `CertificateCoverage`, `HardFalseIndependent` |
| P3 | 第 4 周 | 准备 benchmark 与受控 pass 子集 | microbenchmarks, pipeline config | `BenchmarkBuildRate`, `PipelineRunRate` |
| P4 | 第 5 周 | 实现 PassSpec 与静态候选筛选 | `passspec.yaml`, `static_filter.py` | `CandidatePairReduction` |
| P5 | 第 6 周 | 实现 lazy validation | `lazy_validator.py` | `DynamicTestReduction`, `CacheHitRate` |
| P6 | 第 7 周 | 实现最小局部搜索器 | `search.py` | `CertifiedPruningRatio`, `CandidatePipelineCount` |
| P7 | 第 8 周 | 实现 code size evaluator | `evaluator.py` | `CodeSizeDeltaVsAnchor`, `VerifierPassRate` |
| P8 | 第 9 周 | 生成解释报告和证书汇总 | `report.py` | `ReportCompleteness`, `ExplanationCoverage` |
| P9 | 第 10 周 | 做消融实验和汇总表 | 实验表格 | `DynamicTestReduction`, `CostPerCertifiedPrune` |
| P10 | 第 11 周 | 整理理论和边界 | 理论章节 | `HardFalseIndependent = 0` |
| P11 | 第 12 周 | 最终 demo 与文档整理 | 完整报告 | 全部 MVP 指标 |

---

# 4. 详细进度安排与阶段评价指标

---

## 第 1 周：环境固定与最小 Runner

### 目标

先不要做搜索、图、Alive2、PassInstrumentation。第一周只解决：

```text
能否稳定地对一个 .ll 文件运行指定 LLVM pass pipeline。
```

### 任务

1. 固定 LLVM 环境：

```text
clang
opt
llc 可选
llvm-size
target triple
LLVM version / commit
Python version
```

2. 创建 `configs/env.yaml`：

```yaml
llvm_version: "填入实际版本"
clang: "clang"
opt: "opt"
llc: "llc"
llvm_size: "llvm-size"
target_triple: "填入实际 triple"
execution_model: "materialized_ir_fresh_opt"
debug_policy: "input_strip_or_no_debug"
```

3. 实现 `ecpor/runner.py`：

```python
def run_opt(input_ll, passes, output_ll, extra_flags=None) -> RunResult:
    ...
```

运行形式：

```bash
opt input.ll -S -o output.ll -passes="instcombine,dce" -verify-each
```

### 验收标准

```text
1. 能对 input.ll 运行单个 pass；
2. 能对 input.ll 运行 pass 序列；
3. 能捕获 return code、stdout、stderr、运行时间；
4. opt 失败时不会崩溃，而是返回 structured error。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `RunnerSuccessRate` | 成功运行的 opt 命令数 / 总 opt 命令数 | ≥ 95% |
| `OptFailureCount` | opt 非 0 返回次数 | 越低越好 |
| `CommandRecordRate` | 每次 run 是否记录完整命令 | 100% |

### 本周不要做

```text
不要做完整 -O2/-O3 pipeline
不要碰所有 LLVM pass
不要写 C++ plugin
不要接 Alive2
不要做 runtime benchmark
```

---

## 第 2 周：Hard Normalizer 与 Feature Scanner

### 目标

实现最保守的 hard equality 判断：

```text
hard_equal(IR1, IR2) := hard_hash(IR1) == hard_hash(IR2)
```

第一版 normalizer 必须保守。它的目的不是尽可能多地判相等，而是避免错判。

### 任务

1. 实现 `ecpor/normalizer.py`：

```python
def hard_canonicalize(ir_text: str) -> str:
    ...

def hard_hash(ir_path: Path) -> str:
    ...
```

2. hard normalizer 允许做：

```text
统一换行
去掉工具运行产生的非 IR banner
确保同一 LLVM 版本输出格式一致
可选：输入阶段统一 strip debug，但必须写入 debug_policy
```

3. hard normalizer 暂时不要做：

```text
不要重排 function/global/basic block
不要删除 TBAA / alias.scope / range / prof / nonnull / align 等 metadata
不要用 instruction multiset hash 当 hard proof
不要把 feature 相似当作 independent
```

4. 实现 `ecpor/feature_scan.py`：

```text
num_functions
num_basic_blocks
num_instructions
num_alloca
num_load
num_store
num_call
num_branch
num_phi
has_alloca
has_load
has_store
has_call
has_phi
```

### 验收标准

```text
1. 同一个 IR 多次 hash 结果一致；
2. 两个文本完全一致的 IR hard_equal = true；
3. 不同 IR hard_equal = false；
4. feature scan 能输出 JSON。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `HashReproductionRate` | 同一 IR 重复 hash 一致比例 | 100% |
| `FeatureScanSuccessRate` | 成功扫描 IR 的比例 | ≥ 95% |
| `HardFalseEqualByUnitTest` | 单元测试中不同 IR 被误判相等次数 | 0 |

---

## 第 3 周：Pair Tester 与 Certificate 闭环

### 目标

实现项目的第一个关键闭环：

```text
输入状态 S 和 pass A,B
运行 A;B
运行 B;A
比较 hard hash
输出 certificate
```

### 任务

1. 实现 `ecpor/pair_test.py`：

```python
def test_adjacent_swap(state_ll, pass_a, pass_b, env) -> PairCertificate:
    ...
```

2. 实现 `ecpor/cert.py`：

```python
@dataclass
class PairCertificate:
    claim: str
    pass_a: str
    pass_b: str
    input_state_hash: str
    execution_model: str
    llvm_version: str
    command_ab: str
    command_ba: str
    output_ab: str
    output_ba: str
    hash_ab: str
    hash_ba: str
    hard_equal: bool
    normalizer_version: str
    feature_delta: dict
```

3. certificate 标签：

```text
certified_independent:
    hard_equal = true

not_certified_independent:
    hard_equal = false，但 AB 和 BA 都成功运行

run_failed:
    至少一个方向 opt 失败

verifier_failed:
    至少一个方向 verifier 失败

unknown:
    超时、unsupported nesting、normalizer 无法处理等
```

### 验收标准

命令：

```bash
python -m ecpor.pair_test \
  --state data/inputs/foo.ll \
  --A instcombine \
  --B dce
```

输出：

```text
certificates/*.json
outputs/foo_instcombine_dce.ll
outputs/foo_dce_instcombine.ll
hard_equal true/false
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `CertificateCoverage` | hard pruning 决策中有证书的比例 | 100% |
| `HardFalseIndependent` | 标为 independent 但复现 hash 不等的数量 | 0 |
| `CertificateReproductionRate` | 证书复现成功比例 | 100% |
| `PairTestSuccessRate` | AB/BA 都成功运行的 pair test 比例 | ≥ 90% |

---

## 第 4 周：Benchmark 与受控 Pass 子集

### 目标

建立第一版实验空间。不要使用所有 LLVM pass，也不要直接挑战完整 `-O3`。

### 推荐第一版 pass 子集

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

### 第二版可加入

```text
loop-simplify
licm
loop-rotate
```

### 第一版暂缓

```text
inline
globalopt
ipsccp
deadargelim
loop-vectorize
loop-unroll
slp-vectorizer
```

### Benchmark 准备

先自造 10 个 C 程序：

```text
01_arithmetic.c
02_dead_code.c
03_branch_simplify.c
04_alloca_sroa.c
05_reassociate.c
06_load_store.c
07_loop_simple.c
08_loop_invariant.c
09_call_no_inline.c
10_mixed.c
```

生成 IR：

```bash
clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm foo.c -o foo.ll
```

### 验收标准

```text
1. 至少 10 个 .ll 输入；
2. 每个输入能运行 controlled anchor pipeline；
3. 每个输入能进行至少 3 组 pair_test；
4. 每个输入有 feature scan JSON。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `BenchmarkBuildRate` | 成功生成 .ll 的 benchmark 比例 | 100% |
| `PipelineRunRate` | anchor pipeline 成功运行比例 | ≥ 95% |
| `VerifierPassRate` | 输出 IR 通过 verifier 的比例 | 100% |

---

## 第 5 周：PassSpec 与静态候选筛选

### 目标

实现低成本候选生成，但必须保持原则：

```text
静态筛选不产生 independent 证明。
静态筛选只决定测不测、优先级高不高、是否冻结在 anchor 位置。
```

### 任务

1. 实现 `configs/passspec.yaml`：

```yaml
instcombine:
  level: function
  requires_any:
    - instruction
  may_produce:
    - simplified_expr
    - dead_instruction
  may_consume:
    - algebraic_expr
    - constant_operand
  tags:
    - scalar

dce:
  level: function
  requires_any:
    - instruction
    - dead_instruction
  may_consume:
    - dead_instruction
  tags:
    - cleanup

sroa:
  level: function
  requires_any:
    - alloca
  may_produce:
    - scalar_value
    - simplified_load_store
  tags:
    - memory
    - scalar
```

2. 实现 `ecpor/static_filter.py`。

输入：

```text
ProgramFeatures
PassSpec
anchor pipeline
window size
```

输出：

```text
candidate_pairs
low_priority_pairs
frozen_passes
unsupported_pairs
```

3. 候选规则：

```text
同一 reorderable region
pipeline 距离在 window 内
may_produce/may_consume 有交集
coarse tags 相关
程序特征满足 pass 粗前置条件
```

### 验收标准

给定：

```text
pipeline = sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce
```

输出类似：

```json
{
  "candidate_pairs": [
    ["sroa", "early-cse", "producer_consumer"],
    ["instcombine", "dce", "may_produce_dead_instruction"],
    ["simplifycfg", "instcombine", "cfg_to_scalar_cleanup"]
  ],
  "low_priority_pairs": [...],
  "frozen_passes": [...]
}
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `CandidatePairReduction` | 1 - candidate_pairs / all_pairs | ≥ 40% 初步目标 |
| `StaticFilterTime` | 静态筛选耗时 | 越低越好 |
| `UnsupportedPairCount` | 因 nesting/level 不支持的 pair 数量 | 记录即可 |

---

## 第 6 周：Lazy Validation

### 目标

搜索器需要交换时才做动态验证，不预先构造全局 pair matrix。

### 任务

实现 `ecpor/lazy_validator.py`：

```python
def can_hard_swap(state, A, B, env):
    key = (A, B, state.hash, env.id, execution_model)
    cert = cert_db.lookup(key)
    if cert is not None:
        return cert.hard_equal, cert

    cert = test_adjacent_swap(state.ll, A, B, env)
    cert_db.save(cert)
    return cert.hard_equal, cert
```

**关键要求：**

```text
certificate key 不能只是 (A, B)
必须至少包含：
    A
    B
    input_state_hash
    LLVM env id
    execution_model
    normalizer version
```

因为：

```text
A,B 在 S1 上可交换，不代表在 S2 上可交换。
```

### 验收标准

```text
1. 第一次查询某 pair 会触发 pair_test；
2. 第二次同状态同 pair 查询命中 cache；
3. 不同 state_hash 不复用旧证书；
4. 没有证书时不会 hard prune。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `DynamicTestReduction` | 1 - actual_dynamic_tests / full_dynamic_tests | ≥ 30% 初步目标 |
| `CacheHitRate` | cache_hits / certificate_queries | 随搜索增加而上升 |
| `CertifiedPruningRatio` | certified_pruned_swaps / attempted_swaps | 记录即可 |

---

## 第 7 周：最小局部搜索器

### 目标

先做简单的相邻交换局部搜索，不做复杂 graph decomposition、BO、RL、MCTS。

### 任务

实现 `ecpor/search.py`：

```text
输入：anchor pipeline、candidate pairs、input IR、budget
输出：candidate pipelines、certified swaps、not-certified swaps
```

搜索策略第一版：

```text
1. 从 anchor pipeline 开始；
2. 只考虑 static_filter 给出的相邻或近邻 pair；
3. 交换前调用 lazy_validator；
4. hard_equal = true：记录 certified swap，可折叠；
5. hard_equal = false：生成 candidate pipeline，但不 hard prune；
6. 最多生成 K 个 candidate pipelines。
```

### 验收标准

```text
1. 输入一个 pipeline，能生成候选 pipeline 列表；
2. 每次 hard pruning 都能追溯到 certificate；
3. not-certified pair 不被删除，只记录为 soft evidence 或 unknown；
4. 搜索过程可复现。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `CandidatePipelineCount` | 生成候选 pipeline 数量 | 受 budget 控制 |
| `CertifiedPruningRatio` | certified_pruned_swaps / attempted_swaps | 越高越好 |
| `HardPruneWithoutCert` | 没有证书却 hard prune 的次数 | 必须为 0 |

---

## 第 8 周：Code Size Evaluator

### 目标

第一版主目标使用 code size，不使用 runtime 作为主指标。

### 任务

实现 `ecpor/evaluator.py`：

```text
1. 对 candidate pipeline 完整运行 opt；
2. 编译成 object；
3. 用 llvm-size 或 size 获取 .text / total size；
4. 记录 verifier 结果；
5. 输出 evaluation JSON。
```

指标记录：

```json
{
  "pipeline_id": "...",
  "pipeline": "sroa,instcombine,dce,...",
  "ir_hash": "...",
  "object_text_size": 1234,
  "object_total_size": 1456,
  "compile_success": true,
  "verify_success": true
}
```

### 验收标准

```text
1. 每个 benchmark 有 anchor code size；
2. 每个 candidate 有 code size；
3. invalid pipeline 不进入 best selection；
4. 能输出 best candidate pipeline。
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `CodeSizeDeltaVsAnchor` | (Size(best)-Size(anchor))/Size(anchor) | ≤ 0 为理想 |
| `ImprovementRate` | best 优于 anchor 的 benchmark 比例 | 记录即可 |
| `VerifierPassRate` | candidate 输出通过 verifier 比例 | 100% 有效候选 |
| `InvalidCandidateCount` | 编译或 verifier 失败候选数 | 记录并解释 |

---

## 第 9 周：报告生成器

### 目标

输出 human-readable report，不只输出 best pipeline。

### 任务

实现 `ecpor/report.py`。

报告必须包含：

```text
Program
LLVM environment
Execution model
Anchor pipeline
Pass subset
Goal
All pairs
Candidate pairs
Dynamic tests
Certified independent swaps
Unknown / not-certified pairs
Best candidate pipeline
Code size delta
Certificate list
Unknown reason distribution
```

每个 pair 的解释至少包含：

```text
A, B
input_state_hash
pipeline_ab
pipeline_ba
hash_ab
hash_ba
hard_equal
label
reason
commands
feature_delta
```

### 验收标准

```text
reports/foo/report.md
reports/foo/certificates.json
reports/foo/candidates.json
reports/foo/best_pipeline.txt
```

### 本周评价指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| `ReportCompleteness` | report 中必需字段完整比例 | 100% |
| `ExplanationCoverage` | not-certified pair 有解释原因的比例 | ≥ 95% |
| `CertificateCoverage` | hard prune 有证书比例 | 100% |

---

## 第 10 周：消融实验与汇总指标

### 目标

证明系统组件确实有用。

### 必做消融

```text
Ablation 1: 不用 static filter，直接测所有窗口内 pair
Ablation 2: 使用 static filter，只测 candidate pair
Ablation 3: 不使用 certificate cache
Ablation 4: 使用 certificate cache
Ablation 5: 只用 anchor pipeline，不做局部搜索
Ablation 6: 使用 ECPOR candidate search
```

### 核心问题

```text
RQ1: 静态筛选减少了多少 pair？
RQ2: lazy validation 减少了多少 dynamic tests？
RQ3: 有多少 pair 被证明 certified independent？
RQ4: hard false independent 是否为 0？
RQ5: 搜索后的 best pipeline 是否不差于 anchor？
RQ6: 每个 hard pruning 是否都有 certificate？
```

### 本周评价指标

| 指标 | 解释 |
|---|---|
| `CandidatePairReduction` | 静态筛选是否有效 |
| `DynamicTestReduction` | lazy validation 是否有效 |
| `CertifiedIndependentRate` | 是否真的发现可交换 pair |
| `TotalOptRuns` | 总成本 |
| `AnalysisWallTime` | 分析耗时 |
| `CostPerCertifiedPrune` | 平均每个 certified prune 的成本 |
| `CodeSizeDeltaVsAnchor` | 最终收益 |

---

## 第 11 周：理论章节与 Soundness 边界

### 目标

整理理论保证，只证明当前系统真正能保证的内容。

### 必写定理

#### 定理 1：状态索引相邻交换安全性

给定状态 `S` 和 pass `A,B`，如果 certificate 证明：

```text
N(B(A(S))) == N(A(B(S)))
```

则在当前 `execution_model` 下，`A;B` 与 `B;A` 属于同一 hard equivalence class。

#### 定理 2：有限次 certified swap 保持规范化结果

如果 pipeline `π1` 可以通过有限次 certified adjacent swaps 变成 `π2`，且每次 swap 都有当前实际状态上的 certificate，则：

```text
N(π1(P0)) == N(π2(P0))
```

#### 定理 3：Unknown 保守性

如果没有证书的 pair 不被 hard pruning，则系统不会因为 unknown pair 错删顺序选择。

#### 定理 4：静态筛选不影响 soundness

如果 static filter 只影响候选生成和优先级，不直接产生 `certified_independent`，则 static filter 的误判最多降低压缩率，不破坏 hard pruning soundness。

### 理论边界必须明确

```text
1. 不保证所有程序上的全局 pass 规律；
2. 不保证任意长度 pass 序列的全局最优；
3. 不把 code size/runtime 相近当 independent 证明；
4. 不把 static filter 当 proof；
5. 不把 observed-enable edge 当 hard precedence constraint。
```

### 本周评价指标

| 指标 | 目标 |
|---|---:|
| `HardFalseIndependent` | 0 |
| `HardPruneWithoutCert` | 0 |
| `UnknownPrunedCount` | 0 |

---

## 第 12 周：最终 Demo 与项目交付

### 目标

形成一个完整可运行研究原型。

### 最终命令

```bash
python -m ecpor.main \
  --input data/inputs/foo.ll \
  --pipeline configs/pipeline_scalar.yaml \
  --goal code_size \
  --out reports/foo/
```

### 最终产物

```text
reports/foo/report.md
reports/foo/certificates.json
reports/foo/candidates.json
reports/foo/best_pipeline.txt
reports/summary.csv
```

### 最终评价指标

```text
Safety:
  HardFalseIndependent
  CertificateReproductionRate
  VerifierPassRate

Reduction:
  CandidatePairReduction
  DynamicTestReduction
  CertifiedIndependentRate
  CertifiedPruningRatio

Cost:
  TotalOptRuns
  AnalysisWallTime
  CacheHitRate
  CostPerCertifiedPrune

Optimization:
  CodeSizeDeltaVsAnchor
  ImprovementRate
  OracleGap on small regions

Explainability / Verifiability:
  CertificateCoverage
  ReportCompleteness
  ExplanationCoverage
  UnknownReasonDistribution
```

---

# 5. 评价指标字典

---

## 5.1 安全性指标

### `HardFalseIndependent`

定义：

```text
系统标为 certified_independent，
但复现时发现 hash(A;B(S)) != hash(B;A(S)) 的数量。
```

公式：

```text
HardFalseIndependent =
|{(A,B,S) | label=certified_independent and hash_ab != hash_ba}|
```

目标：

```text
必须为 0
```

---

### `CertificateReproductionRate`

定义：

```text
同一 LLVM 环境、同一输入、同一命令下，certificate 能复现相同结论的比例。
```

公式：

```text
CertificateReproductionRate = reproduced_certificates / checked_certificates
```

目标：

```text
MVP 阶段 100%
```

---

### `VerifierPassRate`

定义：

```text
生成的 IR / candidate pipeline 通过 verifier 的比例。
```

公式：

```text
VerifierPassRate = verified_outputs / all_generated_outputs
```

目标：

```text
有效候选必须 100%
```

---

### `HardPruneWithoutCert`

定义：

```text
没有 certificate 却执行 hard pruning 的次数。
```

目标：

```text
必须为 0
```

---

## 5.2 搜索空间压缩指标

### `CandidatePairReduction`

定义：

```text
静态筛选把 pair 数量减少了多少。
```

公式：

```text
CandidatePairReduction = 1 - candidate_pairs / all_pairs
```

解释：

```text
衡量 PassSpec + ProgramFeatures 是否减少了需要进入 dynamic test 的 pair。
```

---

### `DynamicTestReduction`

定义：

```text
lazy validation 相比 full pairwise dynamic test 少跑了多少动态测试。
```

公式：

```text
DynamicTestReduction = 1 - actual_dynamic_tests / full_dynamic_tests
```

---

### `CertifiedIndependentRate`

定义：

```text
动态验证过的 pair 中，有多少被证明可 hard fold。
```

公式：

```text
CertifiedIndependentRate = certified_independent / dynamic_tests
```

---

### `UnknownRate`

定义：

```text
动态验证中无法证明 independent 或无法可靠分类的比例。
```

公式：

```text
UnknownRate = unknown / dynamic_tests
```

说明：

```text
Unknown 高不代表系统不安全；只代表压缩率不足或工具覆盖不足。
```

---

### `CertifiedPruningRatio`

定义：

```text
实际搜索中，有多少 attempted swaps 因为有证书而被 hard prune。
```

公式：

```text
CertifiedPruningRatio = certified_pruned_swaps / attempted_swaps
```

---

## 5.3 成本指标

### `TotalOptRuns`

定义：

```text
整个实验调用 opt 的总次数。
```

拆分记录：

```text
baseline_opt_runs
pair_test_opt_runs
candidate_pipeline_opt_runs
reproduction_opt_runs
```

---

### `AnalysisWallTime`

定义：

```text
从项目开始分析某 benchmark 到输出报告的总耗时。
```

拆分：

```text
feature_scan_time
static_filter_time
dynamic_test_time
search_time
evaluation_time
report_time
```

---

### `CacheHitRate`

定义：

```text
certificate cache 查询命中比例。
```

公式：

```text
CacheHitRate = certificate_cache_hits / certificate_queries
```

---

### `CostPerCertifiedPrune`

定义：

```text
平均花多少 dynamic test 时间换来一个 certified prune。
```

公式：

```text
CostPerCertifiedPrune = dynamic_test_time / certified_pruned_swaps
```

---

## 5.4 优化效果指标

### `CodeSizeDeltaVsAnchor`

定义：

```text
best candidate 相对 controlled anchor pipeline 的 code size 变化。
```

公式：

```text
CodeSizeDeltaVsAnchor = (Size(best) - Size(anchor)) / Size(anchor)
```

解释：

```text
负数代表代码变小。
```

---

### `ImprovementRate`

定义：

```text
best candidate 优于 anchor 的 benchmark 比例。
```

公式：

```text
ImprovementRate = improved_benchmarks / total_benchmarks
```

---

### `AverageCodeSizeDelta`

定义：

```text
所有 benchmark 上 CodeSizeDeltaVsAnchor 的平均值。
```

公式：

```text
AverageCodeSizeDelta = mean(CodeSizeDeltaVsAnchor_i)
```

---

### `OracleGap`

小规模局部穷举时使用。

定义：

```text
ECPOR best 与 exhaustive local optimum 的差距。
```

公式：

```text
OracleGap = (M(best_ecpor) - M(best_exhaustive)) / M(anchor)
```

说明：

```text
只在 pass 数量 <= 7 的局部 region 上做。
```

---

## 5.5 可解释与可验证指标

### `CertificateCoverage`

定义：

```text
hard pruning 决策中，有完整 certificate 的比例。
```

公式：

```text
CertificateCoverage = hard_pruning_with_certificate / hard_pruning_decisions
```

目标：

```text
必须 100%
```

---

### `ReportCompleteness`

定义：

```text
报告记录中必需字段完整的比例。
```

必需字段：

```text
program
input_state_hash
pass A
pass B
execution_model
pipeline_ab
pipeline_ba
hash_ab
hash_ba
hard_equal
label
reason
commands
LLVM version
```

公式：

```text
ReportCompleteness = complete_records / all_records
```

---

### `ExplanationCoverage`

定义：

```text
not-certified / unknown pair 有解释原因的比例。
```

原因类型：

```text
hash differs
feature delta
instruction count delta
basic block delta
opt failed
verifier failed
unsupported nesting
timeout
metadata difference
```

公式：

```text
ExplanationCoverage = explained_not_certified_pairs / not_certified_pairs
```

---

### `UnknownReasonDistribution`

定义：

```text
unknown 的原因分布。
```

示例：

| reason | count | percentage |
|---|---:|---:|
| hash differs | 15 | 50% |
| unsupported nesting | 5 | 16.7% |
| opt failed | 2 | 6.7% |
| timeout | 1 | 3.3% |
| metadata uncertain | 7 | 23.3% |

---

# 6. MVP 阶段必须报告的 10 个核心指标

第一版不要贪多，必须报告下面 10 个：

```text
1. HardFalseIndependent
2. CertificateReproductionRate
3. VerifierPassRate
4. CandidatePairReduction
5. DynamicTestReduction
6. CertifiedIndependentRate
7. UnknownRate
8. TotalOptRuns
9. CodeSizeDeltaVsAnchor
10. CertificateCoverage
```

如果只能展示 5 个，优先展示：

```text
1. HardFalseIndependent
2. CandidatePairReduction
3. DynamicTestReduction
4. CertifiedIndependentRate
5. CodeSizeDeltaVsAnchor
```

---

# 7. 实验表格模板

## 7.1 Benchmark 汇总表

| Benchmark | Passes | All pairs | Candidate pairs | Dynamic tests | Certified independent | Unknown/not-certified | Opt runs | Code size delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dead_code | 8 | 28 | 9 | 6 | 3 | 3 | 18 | -2.1% |
| branch | 8 | 28 | 8 | 5 | 2 | 3 | 15 | -1.4% |
| alloca | 8 | 28 | 10 | 7 | 4 | 3 | 21 | -3.8% |
| mixed | 8 | 28 | 12 | 8 | 3 | 5 | 24 | -0.9% |

---

## 7.2 Certificate 汇总表

| Program | State hash | A | B | Label | hash_ab | hash_ba | Reason |
|---|---|---|---|---|---|---|---|
| dead_code | `7f3a...` | instcombine | dce | certified_independent | `abc...` | `abc...` | hard hash equal |
| branch | `93bc...` | simplifycfg | instcombine | not_certified | `def...` | `102...` | hash differs |

---

## 7.3 消融实验表

| Setting | Static filter | Lazy validation | Cache | Dynamic tests | Opt runs | Certified swaps | Best code size delta |
|---|---|---|---|---:|---:|---:|---:|
| Full pairwise | no | no | no | 28 | 56 | 8 | -2.0% |
| Static only | yes | no | no | 12 | 24 | 5 | -1.8% |
| Static + lazy | yes | yes | no | 7 | 14 | 4 | -1.8% |
| Static + lazy + cache | yes | yes | yes | 7 | 10 | 4 | -1.8% |

---

# 8. 六周压缩版计划

如果时间不足，只做 6 周 MVP：

| 周 | 必做内容 | 必须指标 |
|---:|---|---|
| 1 | runner + 环境固定 | `RunnerSuccessRate` |
| 2 | normalizer + feature scan | `HashReproductionRate` |
| 3 | pair test + certificate | `HardFalseIndependent`, `CertificateCoverage` |
| 4 | benchmark + pass subset | `VerifierPassRate` |
| 5 | static filter + lazy validation | `CandidatePairReduction`, `DynamicTestReduction` |
| 6 | code size evaluator + report | `CodeSizeDeltaVsAnchor`, `ReportCompleteness` |

六周版成功标准：

```text
1. 至少 5 个 benchmark；
2. 至少 8 个 pass 的 controlled pipeline；
3. 至少 20 个 pair certificate；
4. HardFalseIndependent = 0；
5. CertificateCoverage = 100%；
6. 能输出 report.md 和 certificates.json；
7. 至少部分 benchmark 上 code size 不差于 anchor。
```

---

# 9. 现在不应该做的事情

为了避免项目失控，0 进度到 MVP 期间不要做：

```text
不要研究所有 LLVM pass
不要直接用完整 -O2/-O3 做主实验
不要把静态 filter 当证明
不要把 observed-enable 当 hard edge
不要写 PassInstrumentation C++ 插件
不要上来接 Alive2
不要做 runtime 作为主指标
不要做 RL / BO / MCTS
不要声称全局最优
```

这些可以作为后续增强，但不是 MVP 必需。

---

# 10. 最小成功标准

第一版项目成立，不需要超过 `-O3`。第一版成功标准是：

```text
Safety:
  HardFalseIndependent = 0
  HardPruneWithoutCert = 0
  CertificateCoverage = 100%

Reduction:
  CandidatePairReduction > 0
  DynamicTestReduction > 0
  CertifiedIndependentRate > 0

Cost:
  TotalOptRuns 明确记录
  AnalysisWallTime 明确记录

Optimization:
  CodeSizeDeltaVsAnchor 不显著变差
  至少部分 benchmark 有改善

Explainability:
  ReportCompleteness = 100%
  ExplanationCoverage >= 95%
```

一句话版本：

> 如果系统能在 10 个小程序上做到没有错剪、每个 hard pruning 都有证书、确实减少了 pair 和 dynamic tests、发现了一批 certified independent swaps，并且最终 code size 不差于 controlled anchor pipeline，那么 MVP 就成立。

---

# 11. 推荐第一周立即执行清单

## Day 1

```text
固定 LLVM 环境
创建项目目录
写 configs/env.yaml
写 README 草稿
```

## Day 2

```text
准备 3 个 C 程序：dead_code.c, branch.c, alloca.c
用 clang 生成 .ll
```

## Day 3

```text
实现 runner.py
跑通 opt -passes="instcombine,dce"
```

## Day 4

```text
实现 normalizer.py
实现 hard_hash
实现 feature_scan.py 初版
```

## Day 5

```text
实现 pair_test.py
测试 instcombine,dce 和 dce,instcombine
```

## Day 6

```text
实现 cert.py
输出 structured certificate JSON
```

## Day 7

```text
手动跑 3 个程序 × 3 个 pair
生成第一张小表
```

Day 7 最小表格：

| Program | Pair | hard_equal | hash_ab | hash_ba | label |
|---|---|---:|---|---|---|
| dead_code | instcombine,dce | true | ... | ... | certified_independent |
| branch | simplifycfg,instcombine | false | ... | ... | not_certified |
| alloca | sroa,early-cse | false | ... | ... | not_certified |

---

# 12. 最终交付物清单

```text
代码：
  ecpor/*.py

配置：
  configs/env.yaml
  configs/passspec.yaml
  configs/pipeline_scalar.yaml

数据：
  data/inputs/*.ll
  data/certs/*.json
  data/outputs/*.ll

报告：
  reports/*/report.md
  reports/*/certificates.json
  reports/summary.csv

文档：
  README.md
  理论保证说明.md
  实验结果.md
```

---

# 13. 评价指标 CSV 字段建议

`reports/summary.csv` 建议字段：

```csv
benchmark,passes,all_pairs,candidate_pairs,dynamic_tests,certified_independent,unknown,not_certified,opt_runs,analysis_time_sec,cache_hit_rate,anchor_text_size,best_text_size,code_size_delta,hard_false_independent,certificate_coverage,verifier_pass_rate,report_completeness
```

每个 pair 的 `certificates.jsonl` 建议一行一个 certificate：

```json
{
  "benchmark": "dead_code",
  "state_hash": "7f3a...",
  "A": "instcombine",
  "B": "dce",
  "execution_model": "materialized_ir_fresh_opt",
  "llvm_version": "...",
  "command_ab": "opt ... -passes=instcombine,dce",
  "command_ba": "opt ... -passes=dce,instcombine",
  "hash_ab": "abc...",
  "hash_ba": "abc...",
  "hard_equal": true,
  "label": "certified_independent",
  "reason": "hard hash equal",
  "feature_delta": {},
  "verify_ab": true,
  "verify_ba": true
}
```

---

# 14. 总结

当前从 0 进度开始，最正确的推进方式是：

```text
先做可复现的 pair certificate
再做静态候选过滤
再做 lazy validation
再做局部搜索
最后用 code size 和证书报告评价
```

当前阶段最重要的评价逻辑是：

```text
安全性优先于优化收益；
压缩能力优先于超过 -O3；
可复现证书优先于复杂模型；
code size 优先于 runtime；
unknown 保守处理优先于冒险剪枝。
```
