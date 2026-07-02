# ECPOR 进度记录：P8b-1 Misc8 full matrix 与 static filter pre 评估

## 2026-07-02：8 个 llvm-test-suite Misc 输入 × 28 个 pass pair

### 当前目标

P8b-0 已经从 `E:\llvm-test-suite` ingest 出 8 个新输入。本轮进入 P8b-1，只验证“现有证书闭环和 static filter 在新输入上是否稳定”，不做 passspec 调参、不做搜索、不做 code size，也不运行 runtime benchmark。

目标：

```text
Programs = 8
PassPairs = 28
FullMatrixCertificates = 224
CertificateReproductionRate = 100%
HardFalseIndependent = 0
CertifiedFeatureMismatchCount = 0
RunFailed = 0
```

### 已完成内容

- [x] 新增 P8b Misc8 matrix preset：`p8b-misc8x28`。
- [x] 新增 static filter 程序 preset：`p8b-misc8`。
- [x] 新增 P8b-1 tracked manifest builder：`ecpor.result_manifest p8b-matrix`。
- [x] 先提交 tooling clean commit：`ed4cff79a13e0cb455a4c917fa10a3b9243fdf45`。
- [x] 在 clean commit 下重跑 Misc8 × 28 full matrix。
- [x] 生成：
  - `data/outputs/cert_summary_p8b_misc8_pre.csv`
  - `data/outputs/cert_summary_report_p8b_misc8_pre.txt`
  - `data/outputs/static_filter_decisions_p8b_misc8_pre.csv`
  - `data/outputs/static_filter_report_p8b_misc8_pre.md`
  - `data/certs/pair_tests_p8b_misc8/`
  - `docs/results/p8b_misc8_matrix_manifest.json`
- [x] 删除可再生成的 `data/outputs/pair_tests_p8b_misc8/repro/` 临时复现输出。

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_batch_certificates.py tests/test_static_filter.py tests/test_result_manifest.py -q
```

初始失败符合预期：

```text
ImportError: cannot import name 'P8B_MISC8_PROGRAMS'
AssertionError: 0 != 8
ImportError: cannot import name 'build_p8b_matrix_manifest'
```

实现后 targeted tests：

```text
22 passed in 1.54s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
96 passed in 12.80s
```

### 真实运行命令

环境：

```text
env_id = 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e
llvm_version = 23.0.0git
result_generated_from_commit = ed4cff79a13e0cb455a4c917fa10a3b9243fdf45
```

生成 P8b-1 full matrix：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates --preset p8b-misc8x28 --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests_p8b_misc8 --cert-dir data\certs\pair_tests_p8b_misc8 --summary data\outputs\cert_summary_p8b_misc8_pre.csv --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git --timeout-sec 30
```

生成 summary report：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.summary_report data\outputs\cert_summary_p8b_misc8_pre.csv --out data\outputs\cert_summary_report_p8b_misc8_pre.txt
```

生成 static filter pre 评估：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter --program-preset p8b-misc8 --mode per-program --observed-summary data\outputs\cert_summary_p8b_misc8_pre.csv --out-csv data\outputs\static_filter_decisions_p8b_misc8_pre.csv --out-report data\outputs\static_filter_report_p8b_misc8_pre.md --window-size 7
```

生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p8b-matrix --out-manifest docs\results\p8b_misc8_matrix_manifest.json --benchmark-config configs\benchmarks_p8b.yaml --pipeline-config configs\pipeline_scalar.yaml --passspec configs\passspec.yaml --output-dir data\outputs\pair_tests_p8b_misc8 --cert-dir data\certs\pair_tests_p8b_misc8 --summary-csv data\outputs\cert_summary_p8b_misc8_pre.csv --summary-report data\outputs\cert_summary_report_p8b_misc8_pre.txt --static-decisions data\outputs\static_filter_decisions_p8b_misc8_pre.csv --static-report data\outputs\static_filter_report_p8b_misc8_pre.md --opt E:\llvm\build\bin\opt.exe --repo-root . --result-generated-from-commit ed4cff79a13e0cb455a4c917fa10a3b9243fdf45
```

### 真实结果

Full matrix 输出：

```text
total = 224
reproduced = 224
hard_false_independent = 0
certified_feature_mismatch = 0
certified_independent = 148
not_certified_independent = 76
run_failed = 0
```

summary report 关键字段：

```text
Total certificates: 224
Reproduced: 224 / 224 = 100.00%
HardFalseIndependent: 0
CertifiedFeatureMismatchCount: 0
Certificates with any failure: 0 / 224
Failure directions: no_failure = 448 / 448
```

Per-program certified 数量：

```text
testsuite_misc_aarch64_init_cpu_features: 21/28 certified
testsuite_misc_evalloop: 21/28 certified
testsuite_misc_ffbench: 13/28 certified
testsuite_misc_flops_1: 17/28 certified
testsuite_misc_flops_2: 18/28 certified
testsuite_misc_flops_3: 19/28 certified
testsuite_misc_flops_4: 20/28 certified
testsuite_misc_flops_5: 19/28 certified
```

Static filter pre 评估：

```text
candidate = 184
low_priority = 40
frozen = 0
StaticCandidateRecall = 93.42%
MacroStaticCandidateRecall = 94.39%
StaticFalseNegativeObserved = 5
StaticCandidateReduction = 17.86%
```

Static false negatives：

```text
sroa,adce on testsuite_misc_ffbench
sroa,dce on testsuite_misc_flops_1
sroa,adce on testsuite_misc_flops_1
sroa,dce on testsuite_misc_flops_2
sroa,adce on testsuite_misc_flops_2
```

`docs/results/p8b_misc8_matrix_manifest.json` 关键字段：

```text
stage = P8b-1
ecpor_git_commit = ed4cff79a13e0cb455a4c917fa10a3b9243fdf45
ecpor_git_dirty = False
TotalCertificates = 224
ReproducedCertificates = 224
CertificateReproductionRate = 100.00%
CertifiedIndependent = 148
NotCertifiedIndependent = 76
RunFailed = 0
HardFalseIndependent = 0
CertifiedFeatureMismatchCount = 0
StaticFalseNegativeObserved = 5
```

scope limits：

```text
benchmark_set = P8b-Misc8
program_count = 8
pass_pair_count = 28
passspec_tuning = False
new_search = False
runtime_benchmarks = False
code_size_evaluation = False
pre_tuning_static_filter_eval = True
```

### 代码快照

`batch_certificates.py` 新增 P8b 输入集：

```python
P8B_MISC8_PROGRAMS: list[Program] = [
    (
        "testsuite_misc_aarch64_init_cpu_features",
        "data/inputs/testsuite_misc_aarch64_init_cpu_features.ll",
    ),
    ("testsuite_misc_evalloop", "data/inputs/testsuite_misc_evalloop.ll"),
    ("testsuite_misc_ffbench", "data/inputs/testsuite_misc_ffbench.ll"),
    ("testsuite_misc_flops_1", "data/inputs/testsuite_misc_flops_1.ll"),
    ("testsuite_misc_flops_2", "data/inputs/testsuite_misc_flops_2.ll"),
    ("testsuite_misc_flops_3", "data/inputs/testsuite_misc_flops_3.ll"),
    ("testsuite_misc_flops_4", "data/inputs/testsuite_misc_flops_4.ll"),
    ("testsuite_misc_flops_5", "data/inputs/testsuite_misc_flops_5.ll"),
]
```

`batch_certificates.py` 新增 preset：

```python
parser.add_argument(
    "--preset",
    choices=[
        "stanford-3x3",
        "stanford-3x8",
        "stanford-3x28",
        "stanford-8x28",
        "p8b-misc8x28",
    ],
    default="stanford-3x8",
    help="Program/pass-pair preset to run.",
)
```

```python
def _preset_pass_pairs(preset: str) -> list[PassPair]:
    if preset == "stanford-3x3":
        return STANFORD_3X3_PASS_PAIRS
    if preset in {"stanford-3x28", "stanford-8x28", "p8b-misc8x28"}:
        return FULL_SCALAR_PASS_PAIRS
    return DEFAULT_PASS_PAIRS


def _preset_programs(preset: str) -> list[Program]:
    if preset == "p8b-misc8x28":
        return P8B_MISC8_PROGRAMS
    if preset == "stanford-8x28":
        return STANFORD_8_PROGRAMS
    return DEFAULT_STANFORD_PROGRAMS
```

`static_filter.py` 新增 P8b preset：

```python
parser.add_argument(
    "--program-preset",
    choices=["stanford-3", "stanford-8", "p8b-misc8"],
    help="Scan a built-in program set to build program features.",
)
```

```python
if args.program_preset == "p8b-misc8":
    feature_map = scan_program_features(P8B_MISC8_PROGRAMS)
    return feature_map, len(feature_map)
```

`result_manifest.py` 新增 P8b-1 manifest builder：

```python
def build_p8b_matrix_manifest(
    *,
    benchmark_config_path: str | Path,
    pipeline_config_path: str | Path,
    passspec_path: str | Path,
    output_dir: str | Path,
    cert_dir: str | Path,
    summary_csv: str | Path,
    summary_report: str | Path,
    static_decisions_csv: str | Path,
    static_report: str | Path,
    opt_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    summary = _certificate_matrix_summary(summary_csv)
    summary.update(
        _filter_keys(
            _parse_key_value_report(static_report),
            P8B_MATRIX_STATIC_SUMMARY_KEYS,
        )
    )
    return build_result_manifest(
        stage="P8b-1",
        description="P8b Misc8 by 28 unordered pass-pair certificate matrix.",
        ...
    )
```

CSV 统计 helper：

```python
def _certificate_matrix_summary(path: str | Path) -> dict[str, Any]:
    rows = _load_csv(path)
    label_counts: dict[str, int] = {}
    for row in rows:
        label = row.get("label", "")
        label_counts[label] = label_counts.get(label, 0) + 1
    total = len(rows)
    reproduced = sum(1 for row in rows if _is_true(row.get("reproduced", "")))
    return {
        "TotalCertificates": total,
        "ReproducedCertificates": reproduced,
        "CertificateReproductionRate": (
            f"{(reproduced / total * 100.0):.2f}%" if total else "0.00%"
        ),
        "CertifiedIndependent": label_counts.get("certified_independent", 0),
        "NotCertifiedIndependent": label_counts.get("not_certified_independent", 0),
        "RunFailed": label_counts.get("run_failed", 0),
        "HardFalseIndependent": sum(...),
        "CertifiedFeatureMismatchCount": sum(...),
        "FailureDirections": sum(...),
    }
```

### 语义边界

1. 这批结果是 `pre`，因为 static filter 出现 5 个 false negative；后续如果调 `passspec.yaml`，必须和这批 pre 结果分开记录。
2. `StaticCandidateRecall = 93.42%` 说明当前 static filter 对新 benchmark 不再满足“零 false negative”的目标，不能直接作为硬剪枝。
3. `HardFalseIndependent = 0` 和 `CertificateReproductionRate = 100%` 说明证书系统本身在 Misc8 × 28 上稳定。
4. 本轮没有做 code size、runtime、P4/P5/P6/P8a，也没有调整 passspec。

### data 保留情况

保留：

```text
data/outputs/pair_tests_p8b_misc8/
data/certs/pair_tests_p8b_misc8/
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_report_p8b_misc8_pre.txt
data/outputs/static_filter_decisions_p8b_misc8_pre.csv
data/outputs/static_filter_report_p8b_misc8_pre.md
docs/results/p8b_misc8_matrix_manifest.json
```

已删除：

```text
data/outputs/pair_tests_p8b_misc8/repro/
```

原因：`repro/` 是复现过程输出，可由 certificate 再生成；当前阶段只需要保留原始 AB/BA 输出、证书、summary 和 static pre 评估。

### 下一步

建议进入 P8b-2：只针对这 5 个 static false negative 做保守 passspec 修正，并保留 pre/post 对照。

P8b-2 不需要重跑 224 个证书；可以先基于同一个 `cert_summary_p8b_misc8_pre.csv` 只重跑 static filter：

```text
目标：
  StaticFalseNegativeObserved 降到 0
  尽量少降低 StaticCandidateReduction
  明确记录 passspec 改动原因
```

如果 P8b-2 达到 static recall 100%，再决定是否进入 Misc8 的 P4/P5/P6/P8a 扩展验证。
