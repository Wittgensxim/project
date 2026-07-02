# ECPOR 进度记录：P9-3.6 MVP 发布与外部复现检查

## 2026-07-03：发布前 smoke check，修复 fresh clone 的 summary 边界

### 当前目标

P9-3.5 已经冻结 MVP 版本，本轮进入 P9-3.6：做发布前外部读者 smoke check，确认 tag、README、manifest、测试和 release notes 的边界。仍然不进入 P9-4 diverse8，不新增实验。

明确不做：

```text
不新增 benchmark
不新增 certificate
不新增 search
不运行 LLVM pipeline
不运行 runtime benchmark
不做 two-swap / depth=3 / beam search
不拆 manifest_builders.py
```

### 外部 clone smoke check

执行 fresh clone 到临时目录：

```powershell
git clone --depth 1 --branch v0.1-ecpor-mvp https://github.com/Wittgensxim/project.git <temp-dir>
cd <temp-dir>
git rev-parse --short HEAD
git describe --tags --exact-match
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

观察结果：

```text
b01f447
v0.1-ecpor-mvp
107 passed in 12.36s
docs/results/mvp_summary_manifest.json exists = True
data/outputs/final_mvp_summary/mvp_summary_report.md exists = False
```

这说明外部 clone 可以读 README、MVP 主报告和 manifest，也可以跑单元测试；但由于 `data/outputs/` 按 data retention 规则不进 Git，fresh clone 不具备直接重生成 P9-1 summary 的 retained result inputs。

### 发现的问题

在 fresh clone 中运行 README 的 summary 命令时，旧实现不会失败，而是生成全 0 summary：

```text
BenchmarkSets: 2
TotalPrograms: 0
TotalPairMatrixCertificates: 0
TotalReproducedCertificates: 0
TotalBothSmallerPrograms: 0
AttributionCases: 0
exit_code=0
```

这是 P9-3.6 发布前必须修复的问题。缺少输入时应该显式失败，不能生成看似成功的全 0 报告。

### TDD 修复

先加入 RED test：

```python
def test_missing_required_inputs_fail_instead_of_zero_summary(self):
    from ecpor.mvp_summary import BenchmarkSetInputs, run_mvp_summary

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        missing = root / "missing"

        with self.assertRaises(FileNotFoundError) as raised:
            run_mvp_summary(
                output_dir=root / "final_mvp_summary",
                benchmark_sets=[
                    BenchmarkSetInputs(
                        name="MissingSet",
                        pair_summary_csv=missing / "cert_summary.csv",
                        static_filter_report=missing / "static_report.md",
                        lazy_validation_report=missing / "lazy_report.md",
                        p5_candidates_csv=missing / "candidates.csv",
                        p6_object_size_csv=missing / "object_size.csv",
                        codegen_compare_csv=missing / "compare.csv",
                        attribution_summary_csv=missing / "attribution.csv",
                    )
                ],
            )

    message = str(raised.exception)
    self.assertIn("missing MVP summary input files", message)
    self.assertIn("MissingSet_pair_summary_csv", message)
```

RED 结果：

```text
FAILED tests/test_mvp_summary.py::MvpSummaryTests::test_missing_required_inputs_fail_instead_of_zero_summary
AssertionError: FileNotFoundError not raised
```

实现修复：

```python
def _require_input_files(benchmark_sets: Sequence[BenchmarkSetInputs]) -> None:
    missing = [
        f"{key}={Path(path).as_posix()}"
        for key, path in _input_paths(benchmark_sets).items()
        if not Path(path).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "missing MVP summary input files: " + "; ".join(missing)
        )
```

CLI 现在会返回非零并打印清楚错误：

```python
try:
    result = run_mvp_summary(...)
except FileNotFoundError as error:
    print(f"error: {error}", file=sys.stderr)
    return 2
```

### 文档补充

README 与 `docs/ecpor_mvp_report.md` 已补充：

```text
外部 fresh clone 可以直接检查 README、docs/ecpor_mvp_report.md 和 docs/results/mvp_summary_manifest.json。
完整 ecpor.mvp_summary 重生成需要当前工作区保留已有 P4/P5/P6/P8/P9 输出。
若输入文件缺失，ecpor.mvp_summary 会返回非零并列出缺失文件，避免生成误导性的全 0 summary。
```

新增 release notes：

```text
docs/releases/v0.1.1-ecpor-mvp.md
```

由于 `v0.1-ecpor-mvp` 已经推送过，本轮不强行重写旧 tag；修复后使用补丁标签：

```text
v0.1.1-ecpor-mvp
```

### 验证结果

targeted test：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_mvp_summary.py
```

结果：

```text
2 passed in 0.09s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
108 passed in 13.85s
```

最终提交后复跑：

```text
108 passed in 14.12s
```

缺少 retained `data/outputs` 的负路径验证：

```text
exit_code=2
error: missing MVP summary input files: Stanford_8_pair_summary_csv=...
```

正式 `mvp_summary` 在 retained-result workspace 中重跑，核心值保持：

```text
BenchmarkSets: 2
TotalPrograms: 16
TotalPairMatrixCertificates: 448
TotalReproducedCertificates: 448
TotalHardFalseIndependent: 0
TotalBothSmallerPrograms: 2
AttributionCases: 2
NoNewExperiments: True
```

刷新后的 manifest 记录：

```text
result_generated_from_commit = 010f4444f83b09f572282d41ed645adb448d5b6d
ecpor_git_dirty = false
new_experiments = false
new_certificates = false
new_search = false
runtime_benchmarks = false
llvm_pipeline_rerun = false
```

### 风险与备注

- `v0.1-ecpor-mvp` 是已推送 tag，不建议 force-move。
- `v0.1.1-ecpor-mvp` 用于发布带 missing-input guard 的 MVP 冻结版本。
- fresh clone 仍不能直接重生成 P9-1 summary，因为 retained result inputs 不在 Git 中；这现在已经在 README / 主报告中明确。
- 本轮修复只改变缺失输入时的失败行为，不改变已有 retained-result workspace 的 P9-1 核心结果。

### 下一步

推送分支与 `v0.1.1-ecpor-mvp` tag，并尝试用 `docs/releases/v0.1.1-ecpor-mvp.md` 创建 GitHub Release。之后再考虑 P9-4 diverse8 depth1-only。
