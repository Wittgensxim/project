# ECPOR 进度记录：P8b-3-lite Misc8 depth1 chain

## 2026-07-02：在 Misc8 上只跑 P4/P5/P6/P8a，不进入 two-swap

### 当前目标

上一阶段 P8b-2 已经把 Misc8 full matrix 暴露的 static filter false negative 修到 0。本轮目标不是扩大搜索，而是把 Misc8 benchmark set 走通一条 depth1 证据链：

```text
P8b-3a：Misc8 P4 prefix-state adjacent lazy validation
P8b-3b：Misc8 P5 bounded local one-swap
P8b-3c：Misc8 P6 llc object-size
P8b-3d：Misc8 P8a-style clang-c codegen sensitivity
```

明确不做：

```text
two-swap / beam search / depth=3 / runtime benchmark / loop pass / inline / O2/O3 / Alive2
```

### 已完成内容

- [x] `adjacent_swap_driver.py` 支持 `--program-preset p8b-misc8`。
- [x] `bounded_local_driver.py` 支持 `--program-preset p8b-misc8`。
- [x] `codegen_sensitivity.py` 支持 `--p6-only`，只比较 P6 anchor + single-swap，不读取 P7/P7b depth2 rows。
- [x] `result_manifest.py` 新增四个 P8b-3-lite manifest builder 和 CLI：
  - `p8b-lazy-validation`
  - `p8b-bounded-local`
  - `p8b-code-size`
  - `p8b-codegen`
- [x] 修正 P8b code-size manifest：`CodeSizeDeltaVsAnchor` 从 `object_size.csv` 派生，不依赖报告里的自然语言行。
- [x] 跑通 Misc8 P4/P5/P6/P8a depth1 链路。
- [x] 生成 tracked manifests：
  - `docs/results/p8b_misc8_lazy_validation_manifest.json`
  - `docs/results/p8b_misc8_bounded_local_manifest.json`
  - `docs/results/p8b_misc8_code_size_manifest.json`
  - `docs/results/p8b_misc8_codegen_sensitivity_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_adjacent_swap_driver.py::AdjacentSwapDriverTests::test_program_preset_supports_p8b_misc8 tests\test_bounded_local_driver.py::BoundedLocalDriverTests::test_program_preset_supports_p8b_misc8 tests\test_codegen_sensitivity.py::CodegenSensitivityTests::test_can_compare_p6_depth1_candidates_without_p7_rows tests\test_result_manifest.py::ResultManifestTests::test_builds_p8b_lite_manifests_for_depth1_chain
```

初始失败符合预期：

```text
ImportError: cannot import name '_programs_for_preset'
TypeError: expected str, bytes or os.PathLike object, not NoneType
ImportError: cannot import name 'build_p8b_bounded_local_manifest'
```

实现后 targeted tests：

```text
4 passed in 0.48s
```

受影响测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_adjacent_swap_driver.py tests\test_bounded_local_driver.py tests\test_codegen_sensitivity.py tests\test_result_manifest.py
```

结果：

```text
17 passed in 2.13s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
101 passed in 12.82s
```

工具层提交：

```text
9a449ee4e2b59a4a3b153ee06d136278d7b5373a
add P8b lite depth1 drivers
```

### 真实运行命令

P8b-3a：Misc8 P4 lazy validation：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.adjacent_swap_driver --program-preset p8b-misc8 --pipeline configs\pipeline_scalar.yaml --passspec configs\passspec.yaml --opt E:\llvm\build\bin\opt.exe --cert-dir data\certs\lazy_validation_p8b_misc8 --out data\outputs\lazy_validation_p8b_misc8 --attempts-csv data\outputs\lazy_validation_p8b_misc8\attempts.csv --report data\outputs\lazy_validation_p8b_misc8\report.md --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git --timeout-sec 30
```

P8b-3b：Misc8 P5 one-swap：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver --program-preset p8b-misc8 --pipeline configs\pipeline_scalar.yaml --attempts-csv data\outputs\lazy_validation_p8b_misc8\attempts.csv --out data\outputs\bounded_local_p8b_misc8 --opt E:\llvm\build\bin\opt.exe --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git --timeout-sec 30
```

P8b-3c：Misc8 P6 llc object-size：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.code_size_evaluator --p5-dir data\outputs\bounded_local_p8b_misc8 --out data\outputs\code_size_p8b_misc8 --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

P8b-3d：Misc8 P8a-style clang-c sensitivity，depth1 only：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.codegen_sensitivity --p6-object-size data\outputs\code_size_p8b_misc8\object_size.csv --p6-only --out data\outputs\codegen_sensitivity_p8b_misc8 --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

### 真实结果

P8b-3a lazy validation：

```text
attempted_adjacent_swaps = 56
candidate_swaps = 48
low_priority_skipped = 8
cache_hits = 0
dynamic_tests = 48
certified_independent = 32
not_certified_independent = 16
run_failed = 0
HardFalseIndependent = 0
CertificateReproductionRate = 100.00%
CertifiedPruningRatioAttempted = 57.14%
CertifiedPruningRatioDynamic = 66.67%
```

P8b-3b bounded local one-swap：

```text
anchor_candidates = 8
single_swap_candidates = 16
collapsed_certified_independent = 32
frozen_by_static_filter = 8
pipeline_runs = 24
pipeline_run_failed = 0
same_as_anchor = 8
different_from_anchor = 16
single_swap_same_as_anchor = 0
single_swap_different_from_anchor = 16
```

P8b-3c llc object-size：

```text
Programs = 8
Anchor object builds = 8
Single-swap object builds = 16
ObjectBuildFailed = 0
SizeParseFailed = 0
CodeSizeDeltaVsAnchor = 16
smaller_text = 1
equal_text = 15
larger_text = 0
IRDifferentButTextEqualCount = 15
IRDifferentButTextEqualRate = 93.75%
```

Best smaller candidate：

```text
program = testsuite_misc_ffbench
pair = instcombine,simplifycfg
candidate_id = testsuite_misc_ffbench__swap_2__instcombine__simplifycfg
text_delta = -16
text_delta_pct = -1.0050
```

P8b-3d clang-c codegen sensitivity：

```text
IRInputs = 24
AnchorInputs = 8
SingleSwapInputs = 16
Depth2Inputs = 0
ClangObjectBuildFailed = 0
ClangSizeParseFailed = 0
DirectionComparisonCandidates = 16
DirectionAgreementCount = 15
DirectionAgreementRate = 93.75%
SmallerUnderBothCount = 1
SmallerOnlyUnderLlcCount = 0
SmallerOnlyUnderClangCount = 0
DirectionDisagreementCount = 1
```

唯一方向分歧：

```text
testsuite_misc_ffbench__swap_0__sroa__early-cse
llc = equal, 0.000000%
clang = larger, 0.212134%
```

同时在 `llc` 与 `clang -c` 下变小的 depth1 case：

```text
testsuite_misc_ffbench__swap_2__instcombine__simplifycfg
llc_delta_pct = -1.005025
clang_delta_pct = -0.127280
```

### Manifest 关键字段

四个 manifest 都记录：

```text
result_generated_from_commit = 9a449ee4e2b59a4a3b153ee06d136278d7b5373a
ecpor_git_dirty = false
benchmark_set = P8b-Misc8
program_count = 8
runtime_benchmarks = false
two_swap_search = false
```

P8b-3d manifest 额外确认：

```text
Depth2Inputs = 0
new_certificates = false
llvm_opt_rerun = false
codegen_path_compared = clang -c
```

### 代码快照

P4/P5 driver 的 Misc8 preset：

```python
def _programs_for_preset(preset: str) -> list[Program]:
    if preset == "p8b-misc8":
        return P8B_MISC8_PROGRAMS
    return STANFORD_8_PROGRAMS
```

P8a-style codegen 支持 P6-only：

```python
def run_codegen_sensitivity(
    *,
    p6_object_size_csv: str | Path,
    p7_object_size_csv: str | Path | None,
    output_dir: str | Path,
    clang_path: ToolPath = "clang",
    llvm_size_path: ToolPath = "llvm-size",
    timeout_sec: float = 30.0,
) -> CodegenSensitivityResult:
    p6_rows = _load_csv(p6_object_size_csv)
    p7_rows = _load_csv(p7_object_size_csv) if p7_object_size_csv else []
    selected_rows = _select_input_rows(p6_rows, p7_rows)
```

P8b code-size manifest 不依赖报告自然语言：

```python
def _p8b_code_size_summary(
    report: str | Path,
    object_size_csv: str | Path,
) -> dict[str, Any]:
    summary = _filter_keys(
        _parse_key_value_report(report),
        P8B_CODE_SIZE_SUMMARY_KEYS,
    )
    rows = _load_csv(object_size_csv)
    single_swap_rows = [row for row in rows if row.get("source") == "single_swap"]
    computed_rows = [
        row
        for row in single_swap_rows
        if row.get("text_delta", "") != ""
        and not row.get("compile_failure_kind", "")
        and not row.get("size_failure_kind", "")
    ]
    summary.setdefault("CodeSizeDeltaVsAnchor", len(computed_rows))
    return summary
```

### 结论

P8b-3-lite 达成目标：Misc8 上的 P4/P5/P6/P8a depth1 链路稳定，失败数为 0，证书复现率 100%，code-size 与 clang-c sensitivity 都能生成可追踪 manifest。

但当前 Misc8 depth1 只有 `1` 个 `llc + clang` both-smaller case，且仍集中在 `testsuite_misc_ffbench` 的 `instcombine,simplifycfg`。因此下一步不应直接进入 P7b two-swap；更合适的是做 P8b-3.5 结果解释和单 case attribution，回答这个 ffbench case 是否类似 Queens：局部 AB/BA 差异是否在后缀后保留、opcode/feature delta 是什么、是否只是 codegen path 偶然性。
