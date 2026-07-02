# P9-4c diverse8 depth1 chain 与分析

## 当前目标

本阶段目标是在 P9-4b 已经通过的 `P9-Diverse8` full pair matrix 基础上，继续跑 depth1 链路：

```text
P4 prefix-state adjacent lazy validation
  -> P5 one-swap candidate propagation
  -> P6 llc object-size
  -> P8a-style clang-c sensitivity
  -> depth1 analysis
```

本阶段仍然保持边界：

```text
depth1-only
no two-swap
no runtime benchmark
no full searcher
no passspec repair
no attribution
```

## 完成内容

1. 从 `p9-4b-diverse8-matrix` 切出 `p9-4c-diverse8-depth1`。
2. 给 `adjacent_swap_driver.py` 增加 `--benchmark-config`，使 P4 能读取 `configs/benchmarks_diverse8.yaml`。
3. 给 `bounded_local_driver.py` 增加 `--benchmark-config`，使 P5 不需要硬编码 diverse8 preset。
4. 给 P8b depth1 manifest builders 增加 `stage`、`description`、`benchmark_set`、`program_count` 等 override，避免 P9-4c 被误标为 P8b/Misc8。
5. 给 `depth1_analysis.py` 增加 `--benchmark-label`，使报告标题和正文能正确显示 `Diverse8`。
6. 真实运行 P4/P5/P6/P8a/depth1 analysis。
7. 生成 5 个 tracked result manifests，并确认 `ecpor_git_dirty = false`。
8. 更新 `docs/project_progress.md` 和 `docs/data_retention_manifest.md`。

## 真实运行命令

P4 prefix-state adjacent lazy validation：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.adjacent_swap_driver `
  --benchmark-config configs\benchmarks_diverse8.yaml `
  --pipeline configs\pipeline_scalar.yaml `
  --passspec configs\passspec.yaml `
  --cert-dir data\certs\lazy_validation_p9_diverse8 `
  --out data\outputs\lazy_validation_p9_diverse8 `
  --attempts-csv data\outputs\lazy_validation_p9_diverse8\attempts.csv `
  --report data\outputs\lazy_validation_p9_diverse8\report.md `
  --opt E:\llvm\build\bin\opt.exe `
  --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e `
  --llvm-version 23.0.0git `
  --timeout-sec 30
```

P5 one-swap candidate propagation：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver `
  --benchmark-config configs\benchmarks_diverse8.yaml `
  --pipeline configs\pipeline_scalar.yaml `
  --attempts-csv data\outputs\lazy_validation_p9_diverse8\attempts.csv `
  --out data\outputs\bounded_local_p9_diverse8 `
  --opt E:\llvm\build\bin\opt.exe `
  --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e `
  --llvm-version 23.0.0git `
  --timeout-sec 30
```

P6 `llc` object-size：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.code_size_evaluator `
  --p5-dir data\outputs\bounded_local_p9_diverse8 `
  --out data\outputs\code_size_p9_diverse8 `
  --llc E:\llvm\build\bin\llc.exe `
  --llvm-size E:\llvm\build\bin\llvm-size.exe `
  --timeout-sec 30
```

P8a-style `clang -c` sensitivity：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.codegen_sensitivity `
  --p6-object-size data\outputs\code_size_p9_diverse8\object_size.csv `
  --p6-only `
  --out data\outputs\codegen_sensitivity_p9_diverse8 `
  --clang E:\llvm\build\bin\clang.exe `
  --llvm-size E:\llvm\build\bin\llvm-size.exe `
  --timeout-sec 30
```

depth1 analysis：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.depth1_analysis `
  --p4-attempts data\outputs\lazy_validation_p9_diverse8\attempts.csv `
  --p5-candidates data\outputs\bounded_local_p9_diverse8\candidates.csv `
  --p5-pipeline-runs data\outputs\bounded_local_p9_diverse8\pipeline_runs.csv `
  --p6-object-size data\outputs\code_size_p9_diverse8\object_size.csv `
  --p8a-compare data\outputs\codegen_sensitivity_p9_diverse8\p8a_codegen_direction_compare.csv `
  --reference-p6-object-size data\outputs\code_size_p8b_misc8\object_size.csv `
  --reference-p8a-compare data\outputs\codegen_sensitivity_p8b_misc8\p8a_codegen_direction_compare.csv `
  --benchmark-label Diverse8 `
  --out data\outputs\depth1_analysis_p9_diverse8
```

## 结果

P4 lazy validation：

```text
attempted_adjacent_swaps: 56
candidate_swaps: 44
low_priority_skipped: 12
cache_hits: 0
dynamic_tests: 44
certified_independent: 37
not_certified_independent: 7
run_failed: 0
HardFalseIndependent: 0
CertificateReproductionRate: 100.00%
CertifiedPruningRatioAttempted: 66.07%
CertifiedPruningRatioDynamic: 84.09%
```

P5 bounded local：

```text
anchor_candidates: 8
single_swap_candidates: 7
collapsed_certified_independent: 37
frozen_by_static_filter: 12
pipeline_runs: 15
pipeline_run_failed: 0
single_swap_same_as_anchor: 1
single_swap_different_from_anchor: 6
```

P6 object-size：

```text
Programs: 8
ObjectBuildFailed: 0
SizeParseFailed: 0
CodeSizeDeltaVsAnchor: 7
SmallerText: 0
EqualText: 5
LargerText: 2
IRDifferentButTextEqualCount: 4
IRDifferentButTextEqualRate: 66.67%
```

P8a-style clang-c sensitivity：

```text
IRInputs: 15
AnchorInputs: 8
SingleSwapInputs: 7
Depth2Inputs: 0
ClangObjectBuildFailed: 0
ClangSizeParseFailed: 0
DirectionComparisonCandidates: 7
DirectionAgreementRate: 71.43%
SmallerUnderBothCount: 0
SmallerOnlyUnderLlcCount: 0
SmallerOnlyUnderClangCount: 0
DirectionDisagreementCount: 2
```

Depth1 analysis：

```text
SingleSwapCandidates: 7
ObjectEvaluated: 7
BothSmallerCases: 0
Depth1BothSmallerPrograms: 0
ReferenceDepth1BothSmallerPrograms: 1
```

P9-4c 的判断属于：

```text
Depth1BothSmallerPrograms = 0
```

所以本阶段不进入 two-swap，也不做 targeted attribution。

## Manifests

本阶段新增：

```text
docs/results/p9_diverse8_lazy_validation_manifest.json
docs/results/p9_diverse8_bounded_local_manifest.json
docs/results/p9_diverse8_code_size_manifest.json
docs/results/p9_diverse8_codegen_sensitivity_manifest.json
docs/results/p9_diverse8_depth1_analysis_manifest.json
```

全部满足：

```text
result_generated_from_commit = 3ad70629745dd4d4ccc4b57a8097902c31a77a61
ecpor_git_dirty = false
benchmark_set = P9-Diverse8
two_swap_search = false
runtime_benchmarks = false
```

## 验证结果

TDD RED：

```text
4 failed, 15 passed
```

失败点符合预期：

```text
adjacent_swap_driver.py: unrecognized arguments: --benchmark-config
bounded_local_driver.py: unrecognized arguments: --benchmark-config
manifest builders: unexpected keyword argument 'stage'
```

TDD GREEN：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q `
  tests\test_adjacent_swap_driver.py `
  tests\test_bounded_local_driver.py `
  tests\test_result_manifest.py
```

结果：

```text
19 passed
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q `
  tests\test_adjacent_swap_driver.py `
  tests\test_bounded_local_driver.py `
  tests\test_code_size_evaluator.py `
  tests\test_codegen_sensitivity.py `
  tests\test_depth1_analysis.py `
  tests\test_result_manifest.py
```

结果：

```text
27 passed
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
116 passed
```

## 代码快照

`adjacent_swap_driver.py` 的 benchmark config 入口：

```python
parser.add_argument(
    "--benchmark-config",
    help="Load programs from a benchmark YAML config instead of a built-in preset.",
)

run = run_adjacent_swap_validation(
    programs=_programs_for_args(args),
    passes=list(pipeline["passes"]),
    passspec=load_passspec(args.passspec),
    cert_db=CertificateDB(args.cert_dir),
    opt_path=args.opt,
    output_dir=args.out,
    env_id=args.env_id,
    llvm_version=args.llvm_version,
    timeout_sec=args.timeout_sec,
)

def _programs_for_args(args: argparse.Namespace) -> list[Program]:
    if args.benchmark_config:
        return load_benchmark_config_programs(args.benchmark_config)
    return _programs_for_preset(args.program_preset)
```

`bounded_local_driver.py` 的 benchmark config 入口：

```python
parser.add_argument(
    "--benchmark-config",
    help="Load programs from a benchmark YAML config instead of a built-in preset.",
)

run = run_bounded_local_exploration(
    programs=_programs_for_args(args),
    anchor_passes=list(pipeline["passes"]),
    attempts_csv=args.attempts_csv,
    opt_path=opt_path,
    output_dir=args.out,
    env_id=env_id,
    llvm_version=llvm_version,
    normalizer_version=args.normalizer_version,
    pipeline_config_path=args.pipeline,
    timeout_sec=args.timeout_sec,
)
```

P8b depth1 manifest builder 的 P9 override：

```python
def build_p8b_lazy_validation_manifest(
    *,
    pipeline_config_path: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    attempts_csv: str | Path,
    report_path: str | Path,
    opt_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    stage: str = "P8b-3a",
    description: str = "P8b Misc8 prefix-state adjacent lazy validation.",
    benchmark_set: str = "P8b-Misc8",
    program_count: int = 8,
    anchor_adjacent_swaps_per_program: int = 7,
) -> dict[str, Any]:
    return build_result_manifest(
        stage=stage,
        description=description,
        ...
        extra={
            "scope_limits": {
                "benchmark_set": benchmark_set,
                "program_count": program_count,
                "anchor_adjacent_swaps_per_program": anchor_adjacent_swaps_per_program,
                "two_swap_search": False,
                "full_searcher": False,
                "runtime_benchmarks": False,
                "code_size_evaluation": False,
            }
        },
    )
```

`depth1_analysis.py` 的 benchmark label：

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
    benchmark_label: str = "Misc8",
) -> Depth1AnalysisResult:
    ...
    (output_root / "depth1_analysis_report.md").write_text(
        build_depth1_analysis_report(
            summary,
            program_rows,
            pair_rows,
            both_smaller_rows,
            benchmark_label=benchmark_label,
        ),
        encoding="utf-8",
    )
```

## 风险与备注

1. P9-4b 是 input-state full matrix；P9-4c 是 prefix-state lazy validation，两者不能互相替代。
2. Diverse8 的 P4 prefix-state 层仍然稳定：没有 run failure，没有 hard false independent。
3. Diverse8 depth1 没有产生 llc/clang-c both-smaller case；这说明当前没有足够理由进入 two-swap。
4. `DirectionAgreementRate = 71.43%` 说明 codegen path 仍然有差异，但本阶段没有 smaller under either path；因此不应基于 llc-only 继续搜索。
5. 本阶段新增的 `data/outputs/*_p9_diverse8/` 与 `data/certs/lazy_validation_p9_diverse8/` 已登记到 `docs/data_retention_manifest.md`，作为 P9-4c final evidence 保留。

## 下一步

下一步建议进入：

```text
P9-5 combined 24-program summary
```

把下面三个 benchmark set 合并为 MVP+ 总表：

```text
Stanford-8
Misc8
Diverse8
```

至少更新：

```text
BenchmarkSets = 3
TotalPrograms = 24
TotalPairMatrixCertificates = 672
TotalReproducedCertificates = 672
TotalHardFalseIndependent = 0
StaticFalseNegativeObserved = 0 after repair/pre for all retained sets
Depth1BothSmallerPrograms = 2
```

当前不要做：

```text
two-swap
depth=3
beam search
runtime benchmark
loop / inline / module pass
Alive2 / PassInstrumentation
targeted attribution
```
