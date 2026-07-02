# ECPOR 进度记录：P8b-0 benchmark ingestion

## 2026-07-02：从 llvm-test-suite 自动筛选 8 个新小程序

### 当前目标

P8c.2 已经把 Queens observed attribution 纳入 core evidence。本轮按最新建议进入 P8b-0，不继续围绕 Queens 或 depth 搜索，而是先扩大 benchmark 输入集合。

本轮只做 benchmark ingestion：

```text
不运行 pair matrix；
不新增 certificate；
不做 P4/P5/P6/P8a；
不做 runtime benchmark；
不做 searcher。
```

目标是从 `E:\llvm-test-suite` 自动扫描候选 C 文件，筛出 8 个能通过当前工具链的程序，并记录所有失败原因。

### 已完成内容

- [x] 新增 `src/ecpor/benchmark_ingest.py`：
  - 从多个 source root 自动扫描 `.c` 文件。
  - 使用 `clang -g0 -O0 -Xclang -disable-O0-optnone -S -emit-llvm` 生成 `.ll`。
  - 检查 `optnone`。
  - 扫描 IR feature，限制 `num_instructions < 5000`。
  - 跑当前 8-pass function scalar pipeline。
  - 分别用 `llc -filetype=obj` 和 `clang -c` 生成 object。
  - 用 `llvm-size` 验证 size 可解析。
  - 输出 `ingest_summary.csv`、`report.md` 和 `configs/benchmarks_p8b.yaml`。
- [x] 新增 `tests/test_benchmark_ingest.py`。
- [x] 更新 `src/ecpor/result_manifest.py`：
  - 新增 `build_benchmark_ingest_manifest()`。
  - 新增 CLI stage：`benchmark-ingest`。
- [x] 更新 `tests/test_result_manifest.py`。
- [x] 真实运行 P8b-0 ingestion。
- [x] 新增并跟踪 8 个 accepted `.ll`：
  - `data/inputs/testsuite_misc_aarch64_init_cpu_features.ll`
  - `data/inputs/testsuite_misc_evalloop.ll`
  - `data/inputs/testsuite_misc_ffbench.ll`
  - `data/inputs/testsuite_misc_flops_1.ll`
  - `data/inputs/testsuite_misc_flops_2.ll`
  - `data/inputs/testsuite_misc_flops_3.ll`
  - `data/inputs/testsuite_misc_flops_4.ll`
  - `data/inputs/testsuite_misc_flops_5.ll`
- [x] 新增 `configs/benchmarks_p8b.yaml`。
- [x] 新增 tracked manifest：
  - `docs/results/benchmark_ingest_p8b_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_benchmark_ingest.py::BenchmarkIngestTests::test_ingests_accepts_and_rejects_sources_with_failure_reasons
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_benchmark_ingest_manifest
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.benchmark_ingest'
ImportError: cannot import name 'build_benchmark_ingest_manifest'
```

真实 ingestion 第一次运行后发现 accepted hard cap bug：`accepted_limit = 8` 但为了满足 `min_scanned = 20`，继续接受到了 16 个程序。新增 RED test：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_benchmark_ingest.py::BenchmarkIngestTests::test_accepted_limit_is_hard_cap_while_min_scanned_continues
```

失败符合预期：

```text
AssertionError: 3 != 1
```

修复后 benchmark ingestion 测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_benchmark_ingest.py
```

结果：

```text
2 passed in 0.43s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_benchmark_ingest.py tests\test_result_manifest.py tests\test_object_size_runner.py tests\test_runner.py tests\test_feature_scan.py
```

结果：

```text
22 passed in 1.17s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
93 passed
```

代码层提交：

```text
fea409c add P8b benchmark ingestion
0589c48 cap accepted P8b ingest programs
```

输入集提交：

```text
e342c6dcd0f0ed84e83f30747e2b9df4c74cbe99
add P8b ingested benchmark inputs
```

### 真实运行命令

生成 benchmark ingestion 输出：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.benchmark_ingest --suite-root E:\llvm-test-suite --source-dir SingleSource\Benchmarks\Misc --source-dir SingleSource\Regression\C --source-dir SingleSource\UnitTests --input-dir data\inputs --out data\outputs\benchmark_ingest_p8b --config configs\benchmarks_p8b.yaml --clang E:\llvm\build\bin\clang.exe --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --accepted-limit 8 --min-scanned 20 --instruction-limit 5000 --timeout-sec 30
```

生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest benchmark-ingest --out-manifest docs\results\benchmark_ingest_p8b_manifest.json --source-root E:\llvm-test-suite --config configs\benchmarks_p8b.yaml --output-dir data\outputs\benchmark_ingest_p8b --clang E:\llvm\build\bin\clang.exe --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --repo-root . --result-generated-from-commit e342c6dcd0f0ed84e83f30747e2b9df4c74cbe99
```

### 真实输出

`data/outputs/benchmark_ingest_p8b/report.md`：

```text
CandidateSourceFilesScanned: 20
AcceptedPrograms: 8
RejectedPrograms: 12
IRGenerationOk: 18
ScalarPipelineOk: 8
LlcObjectOk: 8
ClangObjectOk: 8
SizeParseOk: 8

Failure Distribution:
  ir_generation:clang_failed = 2
  selection:accepted_limit_reached = 10
```

accepted programs：

```text
testsuite_misc_aarch64_init_cpu_features: instructions=38
testsuite_misc_evalloop: instructions=550
testsuite_misc_ffbench: instructions=762
testsuite_misc_flops_1: instructions=138
testsuite_misc_flops_2: instructions=148
testsuite_misc_flops_3: instructions=142
testsuite_misc_flops_4: instructions=169
testsuite_misc_flops_5: instructions=182
```

`docs/results/benchmark_ingest_p8b_manifest.json` 关键字段：

```text
stage = P8b-0
ecpor_git_commit = e342c6dcd0f0ed84e83f30747e2b9df4c74cbe99
ecpor_git_dirty = False
result_generated_from_commit = e342c6dcd0f0ed84e83f30747e2b9df4c74cbe99
AcceptedPrograms = 8
CandidateSourceFilesScanned = 20
RejectedPrograms = 12
```

scope limits：

```text
new_certificates = False
pair_matrix = False
new_search = False
runtime_benchmarks = False
ingestion_only = True
```

### 代码快照

`benchmark_ingest.py` 的字段定义：

```python
INGEST_SUMMARY_FIELDS = [
    "program",
    "source_path",
    "input_ir",
    "status",
    "failure_stage",
    "failure_kind",
    "num_functions",
    "num_instructions",
    "num_basic_blocks",
    "scalar_pipeline_ok",
    "llc_object_ok",
    "clang_object_ok",
    "size_parse_ok",
]
```

主入口参数：

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
    instruction_limit: int = 5000,
    timeout_sec: float = 30.0,
    config_input_prefix: str = "data/inputs",
    keep_scratch: bool = False,
) -> BenchmarkIngestResult:
```

accepted hard cap 修复：

```python
for source in sources:
    if len(accepted_rows) >= accepted_limit and len(rows) >= min_scanned:
        break
    program = _program_id(source, used_ids)
    if len(accepted_rows) >= accepted_limit:
        row = _row(
            program=program,
            source=source,
            status="rejected",
            failure_stage="selection",
            failure_kind="accepted_limit_reached",
        )
    else:
        row = _ingest_one_source(...)
```

单个源文件的核心检查链：

```python
ir_result = _run_clang_emit_llvm(source, candidate_ir, clang_path, timeout_sec)
if _compile_failure_kind(ir_result, candidate_ir):
    return _row(..., failure_stage="ir_generation", ...)

ir_text = candidate_ir.read_text(encoding="utf-8", errors="replace")
if "optnone" in ir_text:
    return _row(..., failure_stage="ir_validation", failure_kind="optnone_present")

features = scan_ir_file(candidate_ir)
if int(features.get("num_instructions", 0)) >= instruction_limit:
    return _row(..., failure_stage="ir_validation", failure_kind="ir_too_large")

scalar_result = run_opt(candidate_ir, scalar_pipeline, scalar_ir, opt_path=opt_path)
if scalar_result.failure_kind:
    return _row(..., failure_stage="scalar_pipeline", ...)

llc_record = measure_object_size(..., compile_mode="llc")
clang_record = measure_object_size(..., compile_mode="clang")
```

manifest builder：

```python
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
) -> dict[str, Any]:
    out = Path(output_dir)
    summary_csv = out / "ingest_summary.csv"
    report = out / "report.md"
    outputs: dict[str, str | Path] = {
        "config": config_path,
        "output_dir": out,
        "ingest_summary_csv": summary_csv,
        "report": report,
    }
    for row in _load_csv(summary_csv):
        if row.get("status") != "accepted" or not row.get("input_ir"):
            continue
        outputs[f"accepted_ir_{_manifest_key(row.get('program', ''))}"] = row[
            "input_ir"
        ]
```

### 语义边界

1. P8b-0 只证明“这 8 个新输入能通过当前 ingestion 条件”，不是 pair independence 结论。
2. `selection:accepted_limit_reached` 是为了同时满足 `AcceptedPrograms = 8` 和 `CandidateSourceFilesScanned >= 20` 的透明记录，不代表这些程序失败。
3. 本轮没有生成 certificate，没有做 full matrix，没有比较 code size。
4. 新 accepted 输入来自 `SingleSource/Benchmarks/Misc` 的前序可通过候选，下一步才验证 static filter / pair matrix。

### data 保留情况

本轮保留：

```text
configs/benchmarks_p8b.yaml
data/inputs/testsuite_misc_*.ll
data/outputs/benchmark_ingest_p8b/ingest_summary.csv
data/outputs/benchmark_ingest_p8b/report.md
docs/results/benchmark_ingest_p8b_manifest.json
```

默认不保留 scratch：

```text
data/outputs/benchmark_ingest_p8b/_scratch/
```

原因：accepted `.ll` 已复制到 `data/inputs/` 并跟踪；scratch IR、scalar IR、object 文件都能由 ingestion 命令再生成。

### 下一步

进入 P8b-1：

```text
新 8 个程序 × 28 pass pair full matrix
目标：
  FullMatrixCertificates = 224
  CertificateReproductionRate = 100%
  HardFalseIndependent = 0
  StaticCandidateRecall
  StaticFalseNegativeObserved
  StaticCandidateReduction
```

如果出现 static false negative，先保存 pre-tuning 报告，再保守调整 passspec，避免对新 benchmark 直接调参后只报告最终结果。
