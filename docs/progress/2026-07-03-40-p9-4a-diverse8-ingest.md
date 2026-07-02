# P9-4a diverse8 depth1-only benchmark ingestion

## 当前目标

本阶段目标是进入 P9-4 optional benchmark 扩展，但只做 `diverse8` 的 ingestion，不进入 full search、不进入 two-swap、不运行 runtime、不新增 certificate。

本阶段刻意保持 depth1-only 边界：先确认新的 8 个输入能稳定通过 LLVM IR 生成、scalar pipeline、`llc` object build、`clang -c` object build 和 `llvm-size` 解析，再决定是否进入 P9-4b 的 `diverse8 x 28` matrix/static filter 评估。

## 完成内容

1. 从 `feature/phase-ordering-footprint` 新建分支 `p9-4-diverse8-depth1`。
2. 为 `benchmark_ingest.py` 增加 source-dir stratification，避免只从一个目录连续取样。
3. 增加 `max_programs_per_family`，用 family cap 避免 `flops_1` 到 `flops_5` 这类同族输入占满样本。
4. 增加 `program_prefix`，P9-4a 输出使用 `testsuite_diverse_*`，不复用 P8b-0 的 `testsuite_misc_*` 命名。
5. 为 benchmark-ingest result manifest 增加 `stage` / `description` 参数，并把 family cap 指标纳入 summary。
6. 真实运行 P9-4a ingestion，生成 8 个 diverse 输入和对应 manifest。
7. 更新 `docs/project_progress.md` 与 `docs/data_retention_manifest.md`。

## 真实运行命令

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.benchmark_ingest `
  --suite-root E:\llvm-test-suite `
  --source-dir SingleSource/Benchmarks/Misc `
  --source-dir SingleSource/Regression/C `
  --source-dir SingleSource/UnitTests `
  --input-dir data\inputs `
  --out data\outputs\benchmark_ingest_diverse8 `
  --config configs\benchmarks_diverse8.yaml `
  --clang E:\llvm\build\bin\clang.exe `
  --opt E:\llvm\build\bin\opt.exe `
  --llc E:\llvm\build\bin\llc.exe `
  --llvm-size E:\llvm\build\bin\llvm-size.exe `
  --accepted-limit 8 `
  --min-scanned 30 `
  --max-programs-per-family 2 `
  --stratify-source-dirs `
  --program-prefix testsuite_diverse `
  --stage-name P9-4a `
  --timeout-sec 30
```

生成 manifest：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest benchmark-ingest `
  --out-manifest docs\results\benchmark_ingest_diverse8_manifest.json `
  --source-root E:\llvm-test-suite `
  --config configs\benchmarks_diverse8.yaml `
  --output-dir data\outputs\benchmark_ingest_diverse8 `
  --clang E:\llvm\build\bin\clang.exe `
  --opt E:\llvm\build\bin\opt.exe `
  --llc E:\llvm\build\bin\llc.exe `
  --llvm-size E:\llvm\build\bin\llvm-size.exe `
  --repo-root . `
  --stage-name P9-4a `
  --description "P9-4a diverse8 benchmark ingestion with family cap and source-dir stratification."
```

## 结果

P9-4a ingestion report：

```text
CandidateSourceFilesScanned: 30
AcceptedPrograms: 8
RejectedPrograms: 22
MaxProgramsPerFamily: 2
MaxAcceptedFamilyCount: 1
FamilyLimitViolations: 0
IRGenerationOk: 29
ScalarPipelineOk: 8
LlcObjectOk: 8
ClangObjectOk: 8
SizeParseOk: 8
```

Accepted inputs：

```text
testsuite_diverse_aarch64_init_cpu_features
testsuite_diverse_2003_05_14_initialize_string
testsuite_diverse_2002_04_17_printfchar
testsuite_diverse_2003_05_21_bitfieldhandling
testsuite_diverse_2002_05_02_argumenttest
testsuite_diverse_evalloop
testsuite_diverse_2003_05_21_unionbitfields
testsuite_diverse_2002_05_02_casttest
```

保留文件：

```text
configs/benchmarks_diverse8.yaml
data/inputs/testsuite_diverse_*.ll
data/outputs/benchmark_ingest_diverse8/ingest_summary.csv
data/outputs/benchmark_ingest_diverse8/report.md
docs/results/benchmark_ingest_diverse8_manifest.json
```

## 验证结果

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
111 passed in 14.53s
```

P9-4a acceptance check：

```text
CandidateSourceFilesScanned>=30: True
AcceptedPrograms==8: True
EachFamily<=2: True
ScalarPipelineOk==8: True
LlcObjectOk==8: True
ClangObjectOk==8: True
SizeParseOk==8: True
MaxProgramsPerFamily==2: True
MaxAcceptedFamilyCount<=2: True
ManifestStageP9-4a: True
max_family_count: 1
```

## 代码快照

`benchmark_ingest.py` 的新参数与 selection 逻辑：

```python
def run_benchmark_ingest(
    *,
    source_roots: Sequence[str | Path],
    input_dir: str | Path = "data/inputs",
    output_dir: str | Path = "data/outputs/benchmark_ingest_p8b",
    config_path: str | Path = "configs/benchmarks_p8b.yaml",
    clang_path: ToolPath = "E:/llvm/build/bin/clang.exe",
    opt_path: OptPath = "E:/llvm/build/bin/opt.exe",
    llc_path: ToolPath = "E:/llvm/build/bin/llc.exe",
    llvm_size_path: ToolPath = "E:/llvm/build/bin/llvm-size.exe",
    scalar_pipeline: str = DEFAULT_SCALAR_PIPELINE,
    accepted_limit: int = 8,
    min_scanned: int = 20,
    max_programs_per_family: int | None = None,
    stratify_source_dirs: bool = False,
    program_prefix: str = "testsuite_misc",
    stage_name: str = "P8b-0",
    instruction_limit: int = 5000,
    timeout_sec: float = 30.0,
    config_input_prefix: str = "data/inputs",
    keep_scratch: bool = False,
) -> BenchmarkIngestResult:
    sources = discover_c_sources(
        source_roots,
        stratify_source_dirs=stratify_source_dirs,
    )
    ...
    for source in sources:
        if len(accepted_rows) >= accepted_limit and len(rows) >= min_scanned:
            break
        program = _program_id(source, used_ids, program_prefix=program_prefix)
        family = _program_family(program)
        if len(accepted_rows) >= accepted_limit:
            row = _row(
                program=program,
                family=family,
                source=source,
                status="rejected",
                failure_stage="selection",
                failure_kind="accepted_limit_reached",
            )
        elif (
            max_programs_per_family is not None
            and accepted_family_counts.get(family, 0) >= max_programs_per_family
        ):
            row = _row(
                program=program,
                family=family,
                source=source,
                status="rejected",
                failure_stage="selection",
                failure_kind="family_limit_reached",
            )
```

source-dir stratification 与 family 归并：

```python
def discover_c_sources(
    source_roots: Sequence[str | Path],
    *,
    stratify_source_dirs: bool = False,
) -> list[Path]:
    buckets: list[list[Path]] = []
    for root in source_roots:
        candidate = Path(root)
        if candidate.is_file() and candidate.suffix.lower() == ".c":
            buckets.append([candidate])
        elif candidate.exists():
            buckets.append(
                sorted(
                    (
                        path
                        for path in candidate.rglob("*.c")
                        if path.is_file() and not path.name.startswith(".")
                    ),
                    key=lambda path: path.as_posix().lower(),
                )
            )
    if stratify_source_dirs:
        return _round_robin_sources(buckets)
    return sorted(
        (path for bucket in buckets for path in bucket),
        key=lambda path: path.as_posix().lower(),
    )


def _program_family(program: str) -> str:
    return re.sub(r"(?:_\d+|\d+)$", "", program)
```

manifest builder 的 stage 与 diversity summary：

```python
P8B_INGEST_SUMMARY_KEYS = {
    "CandidateSourceFilesScanned",
    "AcceptedPrograms",
    "RejectedPrograms",
    "MaxProgramsPerFamily",
    "MaxAcceptedFamilyCount",
    "FamilyLimitViolations",
    "IRGenerationOk",
    "ScalarPipelineOk",
    "LlcObjectOk",
    "ClangObjectOk",
    "SizeParseOk",
}


def build_benchmark_ingest_manifest(
    *,
    source_root: str | Path,
    config_path: str | Path,
    output_dir: str | Path,
    clang_path: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
    stage: str = "P8b-0",
    description: str = "Benchmark ingestion for P8b expansion from llvm-test-suite.",
) -> dict[str, Any]:
    ...
    return build_result_manifest(
        stage=stage,
        description=description,
        ...
    )
```

关键回归测试：

```python
def test_family_cap_rejects_extra_accepted_programs_from_same_family(self):
    ...
    result = run_benchmark_ingest(
        ...
        max_programs_per_family=2,
        stage_name="P9-4a",
    )
    ...
    self.assertEqual(result.summary["AcceptedPrograms"], 3)
    self.assertEqual(result.summary["MaxProgramsPerFamily"], 2)
    self.assertEqual(result.summary["MaxAcceptedFamilyCount"], 2)
    self.assertEqual(result.summary["FamilyLimitViolations"], 1)
    self.assertEqual(rejected["failure_kind"], "family_limit_reached")


def test_discover_c_sources_can_stratify_source_dirs(self):
    ...
    sources = discover_c_sources([first, second], stratify_source_dirs=True)
    self.assertEqual(
        [path.name for path in sources],
        ["a1.c", "b1.c", "a2.c", "b2.c"],
    )
```

## 风险和备注

1. 本阶段只证明 diverse8 ingestion 稳定，不说明这些输入上的 pass pair 已经可剪枝。
2. `MaxAcceptedFamilyCount = 1` 说明本轮没有触发同族 accepted 上限，但 family cap 的回归测试已经覆盖 `family_limit_reached`。
3. `RejectedPrograms = 22` 中大部分是达到 accepted limit 后为了满足 `min_scanned = 30` 的选择性拒绝，不是 LLVM 失败。
4. 本阶段没有运行 P9-4b matrix，也没有运行 P4/P5/P6/P8a depth1 chain。

## 下一步

如果继续推进 P9-4，下一步建议进入 P9-4b：对 `configs/benchmarks_diverse8.yaml` 做 `diverse8 x 28` full matrix 和 static filter 评估。仍然不要进入 two-swap、beam search、runtime、loop/inline/O2/O3 或 Alive2。
