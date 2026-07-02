# P9-4b diverse8 full matrix 与 static filter pre 评估

## 当前目标

本阶段目标是在 P9-4a 已准备好的 `diverse8` 输入集上验证证书层和 static filter 是否仍然稳定。

本阶段只做：

```text
8 个 diverse8 programs x 28 个 unordered scalar pass pairs = 224 个 certificates
static filter pre evaluation
```

本阶段不做 P4/P5/P6/P8a depth1 链路，不做 two-swap，不做 runtime，不做 passspec repair。

## 完成内容

1. 从 `p9-4-diverse8-depth1` 切出 `p9-4b-diverse8-matrix`。
2. 给 `batch_certificates.py` 增加 `--benchmark-config` 与 `--pass-preset full-scalar-28`，支持从 `configs/benchmarks_diverse8.yaml` 读取 programs。
3. 给 `static_filter.py` 增加 `--benchmark-config`，使 static filter 和 batch certificate 使用同一份 benchmark config。
4. 给 matrix manifest builder 增加 `stage`、`description`、`benchmark_set` 等 override，避免 P9-4b 被误标成 P8b-1。
5. 真实运行 diverse8 x 28 full matrix。
6. 生成 certificate summary report。
7. 运行 static filter pre evaluation。
8. 更新 `docs/project_progress.md` 与 `docs/data_retention_manifest.md`。

## 真实运行命令

检测 LLVM 环境：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -c "from ecpor.environment import detect_environment; env=detect_environment('E:/llvm/build/bin', llvm_source_root='E:/llvm'); print(env.env_id); print(env.llvm_version)"
```

结果：

```text
3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e
23.0.0git
```

运行 full matrix：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates `
  --benchmark-config configs\benchmarks_diverse8.yaml `
  --pass-preset full-scalar-28 `
  --opt E:\llvm\build\bin\opt.exe `
  --out data\outputs\pair_tests_p9_diverse8 `
  --cert-dir data\certs\pair_tests_p9_diverse8 `
  --summary data\outputs\cert_summary_p9_diverse8_pre.csv `
  --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e `
  --llvm-version 23.0.0git `
  --timeout-sec 30
```

生成 summary report：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.summary_report `
  data\outputs\cert_summary_p9_diverse8_pre.csv `
  --out data\outputs\cert_summary_report_p9_diverse8_pre.txt
```

运行 static filter pre：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter `
  --benchmark-config configs\benchmarks_diverse8.yaml `
  --mode per-program `
  --observed-summary data\outputs\cert_summary_p9_diverse8_pre.csv `
  --out-csv data\outputs\static_filter_decisions_p9_diverse8_pre.csv `
  --out-report data\outputs\static_filter_report_p9_diverse8_pre.md `
  --window-size 7
```

## 结果

证书矩阵：

```text
total=224
reproduced=224
hard_false_independent=0
certified_feature_mismatch=0
certified_independent=196
not_certified_independent=28
run_failed=0
```

summary report：

```text
Total certificates: 224
Reproduced: 224 / 224 = 100.00%
HardFalseIndependent: 0
CertifiedFeatureMismatchCount: 0
Certificates with any failure: 0 / 224
```

static filter pre：

```text
Static decisions:
  candidate: 176
  low_priority: 48
  frozen: 0

Observed matrix:
  certified_independent: 196
  not_certified_independent: 28
  run_failed: 0
  reproduced: 224 / 224
  HardFalseIndependent: 0
  CertifiedFeatureMismatchCount: 0

Static filter quality:
  StaticCandidateRecall: 100.00%
  MacroStaticCandidateRecall: 100.00%
  StaticFalseNegativeObserved: 0
  StaticCandidateReduction: 21.43%
```

P9-4b 验收脚本：

```text
TotalCertificates==224: True
ReproducedCertificates==224: True
CertificateReproductionRate==100.00%: True
HardFalseIndependent==0: True
CertifiedFeatureMismatchCount==0: True
RunFailed==0: True
StaticCandidateRecall==100.00%: True
MacroStaticCandidateRecall==100.00%: True
StaticFalseNegativeObserved==0: True
ManifestStageP9-4b: True
BenchmarkSetP9Diverse8: True
CSVRows==224: True
CertifiedIndependent: 196
NotCertifiedIndependent: 28
StaticCandidateReduction: 21.43%
```

## 验证结果

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_batch_certificates.py tests\test_static_filter.py tests\test_result_manifest.py
```

结果：

```text
29 passed in 10.25s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
114 passed in 22.64s
```

## 代码快照

`batch_certificates.py` 的 benchmark config loader：

```python
def load_benchmark_config_programs(path: str | Path) -> list[Program]:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"benchmark config must contain a mapping: {path}")
    programs = data.get("programs", [])
    if not isinstance(programs, list):
        raise ValueError(f"benchmark config must contain a list 'programs': {path}")

    loaded: list[Program] = []
    for entry in programs:
        if not isinstance(entry, dict):
            raise ValueError(f"benchmark program entry must be a mapping: {path}")
        program_id = entry.get("id")
        ir_path = entry.get("ir")
        if not isinstance(program_id, str) or not isinstance(ir_path, str):
            raise ValueError(f"benchmark program entry needs string id and ir: {path}")
        loaded.append((program_id, Path(ir_path)))
    return loaded
```

`batch_certificates.py` 的 CLI 选择逻辑：

```python
parser.add_argument(
    "--benchmark-config",
    help="Benchmark YAML with a programs list. Overrides --preset programs.",
)
parser.add_argument(
    "--pass-preset",
    choices=["default-8", "full-scalar-28"],
    help="Pass-pair preset used with --benchmark-config.",
)
...
pass_pairs = (
    _pass_preset_pass_pairs(args.pass_preset)
    if args.pass_preset
    else _preset_pass_pairs(args.preset)
)
programs = (
    load_benchmark_config_programs(args.benchmark_config)
    if args.benchmark_config
    else _preset_programs(args.preset)
)
```

`static_filter.py` 的 benchmark config feature scan：

```python
if getattr(args, "benchmark_config", None):
    programs = load_benchmark_config_programs(args.benchmark_config)
    feature_map = scan_program_features(programs)
    return feature_map, len(feature_map)
```

matrix manifest 的 P9-4b override：

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
    stage: str = "P8b-1",
    description: str = "P8b Misc8 by 28 unordered pass-pair certificate matrix.",
    benchmark_set: str = "P8b-Misc8",
    program_count: int = 8,
    pass_pair_count: int = 28,
) -> dict[str, Any]:
    ...
```

新增测试示例：

```python
def test_main_uses_benchmark_config_with_full_scalar_pass_preset(self):
    ...
    exit_code = main(
        [
            "--benchmark-config",
            str(config),
            "--pass-preset",
            "full-scalar-28",
            "--opt",
            sys.executable,
            "--opt-arg",
            str(fake_opt),
            ...
        ]
    )

    rows = _read_csv(summary_csv)

    self.assertEqual(exit_code, 0)
    self.assertEqual(len(rows), 28)
    self.assertTrue(all(row["program"] == "configured_program" for row in rows))
```

## 风险和备注

1. P9-4b 证明 diverse8 上证书层和 static filter pre 评估稳定，但仍没有证明 one-swap candidate 或 `.text` smaller。
2. `StaticFalseNegativeObserved = 0`，因此本阶段不需要 passspec repair。
3. P9-4b 的 `not_certified_independent = 28` 只是需要保留的 hard negative，不是失败。
4. 本阶段删除了 `data/outputs/pair_tests_p9_diverse8/repro/`，因为它只是 certificate reproduction 临时输出，可由证书再生成。

## 下一步

下一步建议进入 P9-4c：基于 `configs/benchmarks_diverse8.yaml` 跑 depth1-only 链路：

```text
P4 adjacent lazy validation
P5 one-swap candidate generation
P6 llc object-size
P8a clang-c sensitivity
```

仍然不要进入 two-swap、depth=3、beam search、runtime、loop/inline/O2/O3 或 Alive2。
