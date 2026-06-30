# ECPOR 进度记录：P2.5 summary report 与 feature scan soft evidence

## 2026-07-01：P2.5 summary report 与 feature scan soft evidence

### 当前目标

按最新 review 建议，先补 P2.5 报告与解释层，不直接进入搜索器。目标是让 3×3 certificate matrix 不只停留在“hash 相同/不同”，还可以输出可统计报告，并为 not-certified pair 提供文本级 IR feature delta 作为 soft evidence。

### 已完成内容

- [x] 新增 `src/ecpor/summary_report.py`：
  - 读取 `cert_summary.csv`
  - 输出 total certificates
  - 输出 label counts
  - 输出 failure kind counts
  - 输出 reproduction rate
  - 输出 HardFalseIndependent
  - 输出 AB/BA 平均耗时
  - 输出 per-pair certified rate
  - 输出 per-program certified rate
- [x] 新增 `src/ecpor/feature_scan.py`：
  - 文本扫描 LLVM IR
  - 统计 function、basic block、instruction 数量
  - 统计 alloca/load/store/call/branch/phi/ret
  - 输出 has_alloca、has_load_store、has_call、has_branch、has_phi
  - 提供 `diff_features()`，用于 AB/BA soft feature delta
- [x] 扩展 `src/ecpor/batch_certificates.py` 的 `cert_summary.csv` 字段：
  - `env_id`
  - `llvm_version`
  - `normalizer_version`
  - `execution_model`
  - `nesting`
  - `region_id`
  - `input_state_hash`
  - `ecpor_git_commit`
  - `input_ir_path`
  - `pipeline_ab`
  - `pipeline_ba`
  - `features_ab`
  - `features_ba`
  - `feature_delta`
- [x] 更新 `README.md`，加入 summary report 和 feature scan 命令。
- [x] 新增测试：
  - `tests/test_feature_scan.py`
  - `tests/test_summary_report.py`
  - 扩展 `tests/test_batch_certificates.py`

### 验证结果

RED 测试确认：

```text
feature_scan.py 和 summary_report.py 不存在时，新增测试按预期失败。
batch_certificates.py 尚未补全 metadata/feature 字段时，测试按预期出现 KeyError: 'env_id'。
```

相关测试补绿：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_feature_scan.py tests/test_summary_report.py tests/test_batch_certificates.py -q
```

结果：

```text
4 passed in 1.10s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
27 passed in 2.66s
```

真实 LLVM 3×3 matrix 复跑：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.batch_certificates import DEFAULT_PASS_PAIRS, DEFAULT_STANFORD_PROGRAMS, run_certificate_matrix, summarize_rows; rows=run_certificate_matrix(programs=DEFAULT_STANFORD_PROGRAMS, pass_pairs=DEFAULT_PASS_PAIRS, opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests', cert_dir='data/certs/pair_tests', summary_csv='data/outputs/cert_summary.csv', env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e', llvm_version='23.0.0git'); print(summarize_rows(rows)); print(rows[1]['ecpor_git_commit'], rows[1]['feature_delta'])"
```

结果：

```text
{'certified_independent': 3, 'not_certified_independent': 6, 'total': 9, 'reproduced': 9, 'hard_false_independent': 0}
902261f35a8ec668a3d48d8e1e3191c675feab1c {"has_alloca":"","has_branch":"","has_call":"","has_load_store":"","has_phi":"","num_alloca":0,"num_basic_blocks":0,"num_branch":-1,"num_call":0,"num_functions":0,"num_instructions":-1,"num_load":1,"num_phi":0,"num_ret":0,"num_store":0}
```

summary report：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.summary_report import main; raise SystemExit(main(['data/outputs/cert_summary.csv','--out','data/outputs/cert_summary_report.txt']))"
```

输出：

```text
Total certificates: 9
Reproduced: 9 / 9 = 100.00%
HardFalseIndependent: 0

Label counts:
  certified_independent: 3
  not_certified_independent: 6
  run_failed: 0

Failure kind counts:
  none: 0

Average elapsed_ab_ms: 33.950
Average elapsed_ba_ms: 32.870

Per pair:
  instcombine,dce: 3/3 certified
  simplifycfg,instcombine: 0/3 certified
  sroa,early-cse: 0/3 certified

Per program:
  testsuite_stanford_bubblesort: 1/3 certified
  testsuite_stanford_intmm: 1/3 certified
  testsuite_stanford_perm: 1/3 certified
```

真实 LLVM 负例验证：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.runner import run_opt; r=run_opt('data/inputs/testsuite_stanford_bubblesort.ll','function(no-such-pass)','data/outputs/negative/no_such_pass.ll',opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.failure_kind, r.opt_success, r.output_exists, r.verifier_ok); print((r.stderr or '')[:500].replace('\n',' '))"
```

结果：

```text
1 opt_failed False False False
E:/llvm/build/bin/opt.exe: unknown function pass 'no-such-pass'
```

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.runner import run_opt; r=run_opt('data/inputs/testsuite_stanford_bubblesort.ll','function(globalopt)','data/outputs/negative/bad_nesting.ll',opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.failure_kind, r.opt_success, r.output_exists, r.verifier_ok); print((r.stderr or '')[:500].replace('\n',' '))"
```

结果：

```text
1 opt_failed False False False
E:/llvm/build/bin/opt.exe: unknown function pass 'globalopt'
```

### 风险与备注

- `feature_scan.py` 是文本级 soft evidence，不参与 hard certificate 判定，也不能作为剪枝依据。
- `feature_delta` 只能解释 AB/BA 输出差异的表面结构变化，不能证明语义等价或不等价。
- 当前 IR feature 扫描没有引入 LLVM parser，后续如需更精确的 CFG/IR 结构统计，可以再替换实现。
- `function(loop-simplify)` 在当前 LLVM 中被接受，因此不适合作为 invalid nesting 负例；已改用 `function(globalopt)` 验证 opt failure。

### 下一步

1. 基于 `feature_delta` 生成 not-certified pair diff report。
2. 将 `features_ab/features_ba/feature_delta` 从 JSON 字符串升级为更适合报告展示的表格视图。
3. 再进入 `feature_scan.py` 的扩展或静态过滤；仍然不要直接进入搜索器。

### 本次代码快照：`src/ecpor/feature_scan.py` 关键片段

```python
FEATURE_FIELDS = [
    "num_functions",
    "num_basic_blocks",
    "num_instructions",
    "num_alloca",
    "num_load",
    "num_store",
    "num_call",
    "num_branch",
    "num_phi",
    "num_ret",
    "has_alloca",
    "has_load_store",
    "has_call",
    "has_branch",
    "has_phi",
]


def scan_ir_file(path: str | Path) -> dict[str, int | bool]:
    return scan_ir_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def diff_features(
    features_ab: dict[str, Any], features_ba: dict[str, Any]
) -> dict[str, int | str]:
    diff: dict[str, int | str] = {}
    for key in sorted(set(features_ab) | set(features_ba)):
        left = features_ab.get(key)
        right = features_ba.get(key)
        if isinstance(left, bool) or isinstance(right, bool):
            diff[key] = "" if left == right else f"{left} -> {right}"
        elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
            diff[key] = right - left
        elif left == right:
            diff[key] = ""
        else:
            diff[key] = f"{left} -> {right}"
    return diff
```

### 本次代码快照：`src/ecpor/summary_report.py` 关键片段

```python
KNOWN_LABELS = [
    "certified_independent",
    "not_certified_independent",
    "run_failed",
]


def build_summary_report(rows: Sequence[dict[str, str]]) -> str:
    total = len(rows)
    reproduced = sum(1 for row in rows if _is_true(row.get("reproduced", "")))
    reproduction_rate = (reproduced / total * 100.0) if total else 0.0
    hard_false = sum(
        1
        for row in rows
        if row.get("label") == "certified_independent"
        and not _is_true(row.get("hard_equal", ""))
    )
    label_counts = Counter(row.get("label", "") for row in rows)
    failure_counts = Counter()
```

### 本次代码快照：`src/ecpor/batch_certificates.py` summary 字段片段

```python
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
    "env_id",
    "llvm_version",
    "normalizer_version",
    "execution_model",
    "nesting",
    "region_id",
    "input_state_hash",
    "ecpor_git_commit",
    "input_ir_path",
    "pipeline_ab",
    "pipeline_ba",
    "features_ab",
    "features_ba",
    "feature_delta",
]
```
