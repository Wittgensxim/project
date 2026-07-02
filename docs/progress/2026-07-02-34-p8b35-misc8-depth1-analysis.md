# ECPOR 进度记录：P8b-3.5 Misc8 depth1 结果解释与 ffbench 归因

## 2026-07-02：先解释 Misc8 depth1，不进入 two-swap

### 当前目标

上一阶段 P8b-3-lite 已经在 Misc8 上跑通 P4/P5/P6/P8a-style depth1 链路，并发现只有 1 个 `llc + clang` both-smaller case。根据当前研究主线，本轮不扩大搜索，而是把已有结果解释清楚：

```text
P8b-3.5a：Misc8 depth1 result analysis
P8b-3.5b：ffbench instcombine/simplifycfg single-case effect attribution
P8b-3.5c：Misc8 core evidence supplement
```

明确不做：

```text
two-swap / beam search / depth=3 / runtime benchmark / O2/O3 / Alive2
```

### 已完成内容

- [x] 新增 `src/ecpor/depth1_analysis.py`，从 Misc8 P4/P5/P6/P8a 输出生成 depth1 分析表。
- [x] 将 `src/ecpor/effect_attribution.py` 从 Queens 专用归因工具参数化为通用单 case 归因工具，同时保留 Queens 默认入口。
- [x] 新增 `src/ecpor/core_evidence_misc8.py`，把 Misc8 depth1 validation / candidate propagation / objective layer / attribution 汇总为证据补充报告。
- [x] 扩展 `src/ecpor/result_manifest.py`，新增：
  - `build_depth1_analysis_manifest`
  - `build_effect_attribution_manifest`
  - `build_core_evidence_misc8_manifest`
  - CLI：`depth1-analysis`、`effect-attribution`、`core-evidence-misc8`
- [x] 生成 tracked manifests：
  - `docs/results/p8b_misc8_depth1_analysis_manifest.json`
  - `docs/results/ffbench_effect_attribution_manifest.json`
  - `docs/results/core_evidence_misc8_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_depth1_analysis.py tests\test_effect_attribution.py::EffectAttributionTests::test_runs_parameterized_ffbench_attribution tests\test_core_evidence_misc8.py tests\test_result_manifest.py::ResultManifestTests::test_builds_p8b35_analysis_attribution_and_misc8_manifests
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.depth1_analysis'
AssertionError: 'testsuite_stanford_queens' != 'testsuite_misc_ffbench'
ModuleNotFoundError: No module named 'ecpor.core_evidence_misc8'
ImportError: cannot import name 'build_core_evidence_misc8_manifest'
```

实现后 targeted tests：

```text
4 passed in 0.72s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
105 passed in 13.60s
```

工具层提交：

```text
c1899f8433e7ac8f2fe1a59b3423fd4bcb0ce66f
add P8b depth1 analysis tooling

fc662c18b7d0bf8c78f1e8609ecb5a94e12bd3e3
record Misc8 attribution evidence boundary
```

### 真实运行命令

P8b-3.5a：Misc8 depth1 分析：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.depth1_analysis --p4-attempts data\outputs\lazy_validation_p8b_misc8\attempts.csv --p5-candidates data\outputs\bounded_local_p8b_misc8\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p8b_misc8\pipeline_runs.csv --p6-object-size data\outputs\code_size_p8b_misc8\object_size.csv --p8a-compare data\outputs\codegen_sensitivity_p8b_misc8\p8a_codegen_direction_compare.csv --reference-p6-object-size data\outputs\code_size_p6_final\object_size.csv --reference-p8a-compare data\outputs\codegen_sensitivity_p8a\p8a_codegen_direction_compare.csv --out data\outputs\depth1_analysis_p8b_misc8
```

P8b-3.5b：ffbench case attribution：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.effect_attribution --program testsuite_misc_ffbench --input-ir data\inputs\testsuite_misc_ffbench.ll --prefix sroa,early-cse --pass-a instcombine --pass-b simplifycfg --suffix reassociate,gvn,dce,adce --out data\outputs\effect_attribution_ffbench --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

P8b-3.5c：Misc8 core evidence supplement：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.core_evidence_misc8 --p4-attempts data\outputs\lazy_validation_p8b_misc8\attempts.csv --p5-candidates data\outputs\bounded_local_p8b_misc8\candidates.csv --p6-object-size data\outputs\code_size_p8b_misc8\object_size.csv --p8a-compare data\outputs\codegen_sensitivity_p8b_misc8\p8a_codegen_direction_compare.csv --depth1-analysis-report data\outputs\depth1_analysis_p8b_misc8\depth1_analysis_report.md --attribution-report data\outputs\effect_attribution_ffbench\attribution_report.md --attribution-feature-deltas data\outputs\effect_attribution_ffbench\feature_deltas.csv --attribution-opcode-delta data\outputs\effect_attribution_ffbench\opcode_delta.csv --attribution-object-size data\outputs\effect_attribution_ffbench\object_size.csv --out data\outputs\core_evidence_report_misc8
```

### 真实结果

Misc8 depth1 分析：

```text
Programs = 8
SingleSwapCandidates = 16
ObjectEvaluated = 16
SmallerText = 1
EqualText = 15
LargerText = 0
IRDifferentButTextEqualCount = 15
IRDifferentButTextEqualRate = 93.75%
DirectionComparisonCandidates = 16
DirectionAgreementRate = 93.75%
BothSmallerCases = 1
Depth1BothSmallerPrograms = 1
DirectionDisagreementCount = 1
ReferenceIRDifferentButTextEqualRate = 93.75%
ReferenceDepth1BothSmallerPrograms = 1
```

唯一 both-smaller case：

```text
program = testsuite_misc_ffbench
candidate_id = testsuite_misc_ffbench__swap_2__instcombine__simplifycfg
pair = instcombine,simplifycfg
llc text_delta_pct = -1.005025
clang text_delta_pct = -0.127280
```

ffbench attribution：

```text
Program = testsuite_misc_ffbench
Pair = instcombine,simplifycfg
StateCount = 7
LocalABBAHardHashEqual = False
FinalABBAHardHashEqual = False
LocalInstructionDelta = 0
FinalInstructionDelta = 0
FeatureDeltaPropagation = kept
LlcTextDelta = -16
ClangTextDelta = -3
BothCodegenSmaller = True
FinalOpcodeDeltaNonZero = num_select_delta=-1;num_or_delta=1
```

Misc8 evidence supplement：

```text
AttemptedSwaps = 56
CertifiedIndependentEvents = 32
SingleSwapCandidates = 16
ObjectSizeEvaluatedCandidates = 16
DirectionComparisonCandidates = 16
DirectionAgreementRate = 93.75%
BothSmaller = 1
BothSmallerPrograms = 1
AttributionCases = 1
AttributionObservedButNotCausalProof = True
```

### 代码快照

`depth1_analysis.py` 的主入口把 P4/P5/P6/P8a 的结果收束成 3 个 CSV 和 1 个 Markdown 报告：

```python
def run_depth1_analysis(
    *,
    p4_attempts_csv: str | Path,
    p5_candidates_csv: str | Path,
    p5_pipeline_runs_csv: str | Path,
    p6_object_size_csv: str | Path,
    p8a_compare_csv: str | Path,
    output_dir: str | Path,
    reference_p6_object_size_csv: str | Path | None = None,
    reference_p8a_compare_csv: str | Path | None = None,
) -> Depth1AnalysisResult:
    attempts = _load_csv(p4_attempts_csv)
    candidates = _load_csv(p5_candidates_csv)
    pipeline_runs = _load_csv(p5_pipeline_runs_csv)
    object_rows = _load_csv(p6_object_size_csv)
    compare_rows = _load_csv(p8a_compare_csv)
```

`effect_attribution.py` 已经不再把 program 写死为 Queens：

```python
summary = _summary(
    program=program,
    pass_a=pass_a,
    pass_b=pass_b,
    state_rows=state_rows,
    delta_rows=delta_rows,
    opcode_delta_rows=opcode_delta_rows,
    object_rows=object_rows,
)
```

`core_evidence_misc8.py` 明确记录这只是 observed attribution，不是因果证明：

```python
return {
    "AttemptedSwaps": _parse_int(validation_rows[0].get("attempted_swaps"), 0),
    "CertifiedIndependentEvents": _parse_int(
        validation_rows[0].get("certified_independent_events"), 0
    ),
    "BothSmallerPrograms": _parse_int(
        depth1_summary.get("Depth1BothSmallerPrograms"),
        _parse_int(objective.get("depth1_both_smaller_programs"), 0),
    ),
    "AttributionCases": len(attribution_rows),
    "AttributionObservedButNotCausalProof": bool(attribution_rows),
}
```

`result_manifest.py` 为 P8b-3.5 增加了带边界的 manifest builder：

```python
"scope_limits": {
    "benchmark_set": "P8b-Misc8",
    "depth": 1,
    "supplement_only": True,
    "two_swap_search": False,
    "new_search": False,
    "new_certificates": False,
    "runtime_benchmarks": False,
}
```

### 产物与 manifest

本轮生成但不直接跟踪的大型结果目录：

```text
data/outputs/depth1_analysis_p8b_misc8/
data/outputs/effect_attribution_ffbench/
data/outputs/core_evidence_report_misc8/
```

本轮跟踪的小型 manifest：

```text
docs/results/p8b_misc8_depth1_analysis_manifest.json
docs/results/ffbench_effect_attribution_manifest.json
docs/results/core_evidence_misc8_manifest.json
```

三个 manifest 均记录：

```text
result_generated_from_commit = fc662c18b7d0bf8c78f1e8609ecb5a94e12bd3e3
ecpor_git_dirty = false
```

### 解释与结论

Misc8 没有偏离最开始的研究问题，反而强化了当前主线：大量 pass 顺序会改变 IR，但不会改变 `.text`；真正需要继续解释的是极少数 objective-layer 有变化的 case。

当前唯一 both-smaller case 是 `testsuite_misc_ffbench` 的 `instcombine,simplifycfg` 交换。它和 Stanford Queens 的模式相似：AB/BA 的 hard hash 不同，目标层也都变小。但 ffbench 更微妙：`num_instructions_delta = 0`，收益不是来自指令数量减少，而是 opcode 形态变化：

```text
num_select_delta = -1
num_or_delta = 1
```

因此当前 evidence claim 应该保持保守：

```text
ECPOR 能在 state-indexed 邻接 pass 交换上证明大量顺序无需搜索；
对少数未被证书剪掉且目标层变好的 case，可以给出可复查的单状态归因；
当前 ffbench 归因是 observed attribution，不是跨程序因果定理。
```

### 风险备注

- `Depth1BothSmallerPrograms = 1`，所以现在仍不应该进入 Misc8 two-swap。
- `DirectionDisagreementCount = 1`，说明 llc 与 clang 路径仍有轻微 codegen sensitivity，后续扩 benchmark 时必须继续保留 objective-layer 双路径比较。
- ffbench 的 `LocalInstructionDelta = 0`，说明只看 instruction count 不够，opcode-level delta 需要继续保留。

### 下一步

建议进入 P8b-4：扩展 benchmark ingestion 到更稳定的小集合，但仍先保持 depth1-only。

优先顺序：

```text
1. 扩到 16 或 24 个可稳定编译的 C benchmark；
2. 继续跑 P4/P5/P6/P8a depth1 chain；
3. 统计是否仍然是 “many IR-different text-equal, few both-smaller”；
4. 只对新增 both-smaller case 做 attribution；
5. 若 both-smaller programs 明显增加，再讨论是否进入 bounded two-swap。
```
