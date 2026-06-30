# ECPOR 进度记录：P1.5 failure kind 与 P2 3×3 最小证书表

## 2026-07-01：P1.5 failure kind 与 P2 3×3 最小证书表

### 当前目标

按 review 建议先完成 P1.5 收尾：拆分 `runner.py` 的失败原因字段，避免批量证书表把 timeout、非零退出、输出缺失等错误混在一起。随后进入 P2：生成 3 个 Stanford 输入 × 3 个 pass pair 的最小证书表和 `cert_summary.csv`。

### 已完成内容

- [x] 扩展 `RunResult`：
  - `opt_success`
  - `output_exists`
  - `verify_each_enabled`
  - `verifier_ok: bool | None`
  - `failure_kind: str | None`
- [x] 第一版 `failure_kind` 已覆盖：
  - `timeout`
  - `os_error`
  - `opt_failed`
  - `output_missing`
  - `opt_failed_output_exists`
- [x] 调整 `pair_test._classify()`：优先按 `failure_kind` 归类为 `run_failed`；只有 stderr 明确出现 verifier 相关信号时才标为 `verifier_failed`。
- [x] `PairCertificate` 新增：
  - `failure_kind_ab`
  - `failure_kind_ba`
  - `elapsed_ab_ms`
  - `elapsed_ba_ms`
- [x] 新增 `src/ecpor/batch_certificates.py`：
  - 默认 Stanford 3 输入
  - 默认 3 个 pass pair
  - 生成 9 个 JSON certificate
  - 对每个 certificate 做 reproduction
  - 写出 `cert_summary.csv`
- [x] 新增 `tests/test_batch_certificates.py`，用 fake opt 覆盖 summary 和 reproduction。
- [x] 更新 `README.md`，加入 3×3 certificate matrix 命令。
- [x] 已提交 P1.5：
  - `69f69da clarify runner failure kinds`
- [x] 已提交 P2 生成器：
  - `f3131d8 add certificate summary matrix runner`

### 验证结果

P1.5 RED 后补绿：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_runner.py tests/test_cert.py tests/test_pair_test.py -q
```

结果：

```text
14 passed in 1.72s
```

P2 batch 单测：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_batch_certificates.py -q
```

结果：

```text
1 passed in 1.22s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
24 passed in 2.85s
```

真实 LLVM 3×3 certificate matrix：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.batch_certificates import DEFAULT_PASS_PAIRS, DEFAULT_STANFORD_PROGRAMS, run_certificate_matrix, summarize_rows; rows=run_certificate_matrix(programs=DEFAULT_STANFORD_PROGRAMS, pass_pairs=DEFAULT_PASS_PAIRS, opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests', cert_dir='data/certs/pair_tests', summary_csv='data/outputs/cert_summary.csv', env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e', llvm_version='23.0.0git'); print(summarize_rows(rows)); [print(row) for row in rows]"
```

汇总：

```text
total = 9
reproduced = 9
CertificateReproductionRate = 100%
HardFalseIndependent = 0
certified_independent = 3
not_certified_independent = 6
run_failed = 0
```

`cert_summary.csv` 路径：

```text
data/outputs/cert_summary.csv
```

### 3×3 结果表

| program | pair | label | hard_equal | failure_kind_ab | failure_kind_ba | reproduced |
| --- | --- | --- | --- | --- | --- | --- |
| testsuite_stanford_bubblesort | instcombine,dce | certified_independent | True |  |  | True |
| testsuite_stanford_bubblesort | simplifycfg,instcombine | not_certified_independent | False |  |  | True |
| testsuite_stanford_bubblesort | sroa,early-cse | not_certified_independent | False |  |  | True |
| testsuite_stanford_intmm | instcombine,dce | certified_independent | True |  |  | True |
| testsuite_stanford_intmm | simplifycfg,instcombine | not_certified_independent | False |  |  | True |
| testsuite_stanford_intmm | sroa,early-cse | not_certified_independent | False |  |  | True |
| testsuite_stanford_perm | instcombine,dce | certified_independent | True |  |  | True |
| testsuite_stanford_perm | simplifycfg,instcombine | not_certified_independent | False |  |  | True |
| testsuite_stanford_perm | sroa,early-cse | not_certified_independent | False |  |  | True |

### 风险与备注

- 当前 3×3 表没有 run failure，说明这组输入和 function scalar pair 在本地 LLVM 23.0.0git 上均可运行。
- `verifier_failed` 仍然只在 stderr 明确包含 verifier 相关信号时使用；其他非零退出统一进入 `run_failed` 并由 `failure_kind` 细分。
- 生成产物位于 `data/outputs/` 和 `data/certs/`，按 `.gitignore` 规则不进入仓库。
- 这一步仍然没有做 `feature_scan.py`、静态过滤、搜索器、code size evaluator，也没有扩展到 loop / inline / O2/O3，范围保持在 P2 最小统计表。

### 下一步

1. 基于 `cert_summary.csv` 增加一个很小的汇总报告读取器，输出 label count、failure kind count 和 reproduction rate。
2. 如果 3×3 表继续稳定，再进入 `feature_scan.py`。
3. feature scan 只先作为解释性 soft evidence，不参与 hard certificate 判定。

### 本次代码快照：`src/ecpor/runner.py` 关键片段

```python
@dataclass(frozen=True)
class RunResult:
    command: list[str]
    input_path: Path
    output_path: Path
    pipeline: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float
    opt_success: bool
    output_exists: bool
    verify_each_enabled: bool
    verifier_ok: bool | None
    failure_kind: str | None
    timed_out: bool = False
    hard_hash: str | None = None
```

```python
def _failure_kind(opt_success: bool, output_exists: bool) -> str | None:
    if opt_success and output_exists:
        return None
    if opt_success and not output_exists:
        return "output_missing"
    if not opt_success and output_exists:
        return "opt_failed_output_exists"
    return "opt_failed"
```

### 本次代码快照：`src/ecpor/pair_test.py` 分类片段

```python
def _classify(result_ab, result_ba, hard_equal: bool) -> tuple[str, str]:
    if result_ab.failure_kind or result_ba.failure_kind:
        if _has_explicit_verifier_failure(result_ab.stderr + result_ba.stderr):
            return "verifier_failed", "opt reported verifier failure"
        failed = []
        if result_ab.failure_kind:
            failed.append(
                f"AB {result_ab.failure_kind} with exit code {result_ab.exit_code}"
            )
        if result_ba.failure_kind:
            failed.append(
                f"BA {result_ba.failure_kind} with exit code {result_ba.exit_code}"
            )
        stderr = " ".join(
            text.strip() for text in [result_ab.stderr, result_ba.stderr] if text.strip()
        )
        reason = "; ".join(failed)
        if stderr:
            reason = f"{reason}: {stderr}"
        return "run_failed", reason
    if hard_equal:
        return "certified_independent", "hard hash equal"
    return "not_certified_independent", "hard hash differs"
```

### 本次代码快照：`src/ecpor/batch_certificates.py` 关键片段

```python
DEFAULT_STANFORD_PROGRAMS: list[Program] = [
    ("testsuite_stanford_bubblesort", "data/inputs/testsuite_stanford_bubblesort.ll"),
    ("testsuite_stanford_intmm", "data/inputs/testsuite_stanford_intmm.ll"),
    ("testsuite_stanford_perm", "data/inputs/testsuite_stanford_perm.ll"),
]

DEFAULT_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("simplifycfg", "instcombine"),
    ("sroa", "early-cse"),
]

SUMMARY_FIELDS = [
    "program",
    "pair_a",
    "pair_b",
    "label",
    "hard_equal",
    "hash_ab",
    "hash_ba",
    "exit_ab",
    "exit_ba",
    "failure_kind_ab",
    "failure_kind_ba",
    "elapsed_ab_ms",
    "elapsed_ba_ms",
    "cert_id",
    "reproduced",
]
```

```python
def run_certificate_matrix(
    *,
    programs: Sequence[Program],
    pass_pairs: Sequence[PassPair],
    opt_path: OptPath,
    output_dir: str | Path,
    cert_dir: str | Path,
    summary_csv: str | Path,
    env_id: str,
    llvm_version: str,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] | None = None,
    timeout_sec: float = 30.0,
) -> list[dict[str, str]]:
    output_root = Path(output_dir)
    certificate_root = Path(cert_dir)
    certificate_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for program, input_ir in programs:
        for pass_a, pass_b in pass_pairs:
            cert = test_adjacent_swap(...)
            cert_path = certificate_root / (
                f"{_safe_name(program)}__{_safe_name(pass_a)}__{_safe_name(pass_b)}.json"
            )
            cert.save(cert_path)
            reproduction = reproduce_certificate(
                cert_path,
                opt_path=opt_path,
                output_dir=output_root / "repro",
                timeout_sec=timeout_sec,
            )
            rows.append(...)

    write_summary_csv(summary_csv, rows)
    return rows
```

### 本次代码快照：README 3×3 命令

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates --preset stanford-3x3 --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert-dir data\certs\pair_tests --summary data\outputs\cert_summary.csv --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```
