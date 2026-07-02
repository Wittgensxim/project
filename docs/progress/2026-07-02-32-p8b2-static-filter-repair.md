# ECPOR 进度记录：P8b-2 static filter false-negative repair

## 2026-07-02：修复 Misc8 上的 5 个 static false negative

### 当前目标

P8b-1 证明证书层在 Misc8 × 28 上稳定，但 static filter pre 评估暴露了 5 个 false negative。本轮只修 static filter 的召回缺口，不重跑 224 个 certificate，不做搜索、不做 code size、不跑 runtime。

目标：

```text
StaticFalseNegativeObserved = 0
StaticCandidateRecall = 100%
保留 P8b-1 pre 与 P8b-2 post 对照
```

### Root Cause

P8b-1 的 5 个 false negative：

```text
sroa,adce on testsuite_misc_ffbench
sroa,dce on testsuite_misc_flops_1
sroa,adce on testsuite_misc_flops_1
sroa,dce on testsuite_misc_flops_2
sroa,adce on testsuite_misc_flops_2
```

pre static decisions 显示这些 case 的共同原因是：

```text
decision = low_priority
reason = no_static_hint
program_feature_gate = satisfied;sroa:has_alloca;dce/adce:instruction
producer_consumer = empty
```

`configs/passspec.yaml` 中 `dce/adce` 已经消费 `dce_opportunity`，但 `sroa.may_produce` 没有声明它可能产生 cleanup/DCE 机会。因此最小修复是：

```text
sroa.may_produce += dce_opportunity
```

### 已完成内容

- [x] 在 `tests/test_static_filter.py` 增加回归断言：
  - `sroa,dce -> candidate`
  - `sroa,adce -> candidate`
- [x] 在 `tests/test_result_manifest.py` 增加 P8b-2 repair manifest 测试。
- [x] 保守修改 `configs/passspec.yaml`。
- [x] 新增 `ecpor.result_manifest p8b-static-repair`。
- [x] 不重跑证书，只基于既有 `data/outputs/cert_summary_p8b_misc8_pre.csv` 重跑 static filter post。
- [x] 生成：
  - `data/outputs/static_filter_decisions_p8b_misc8_post.csv`
  - `data/outputs/static_filter_report_p8b_misc8_post.md`
  - `data/outputs/static_filter_repair_report_p8b_misc8.md`
  - `docs/results/p8b_misc8_static_filter_repair_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_static_filter.py::StaticFilterTests::test_real_passspec_marks_observed_false_negative_pairs_candidate tests/test_result_manifest.py::ResultManifestTests::test_builds_p8b_static_filter_repair_manifest -q
```

初始失败符合预期：

```text
AssertionError: 'low_priority' != 'candidate'
ImportError: cannot import name 'build_p8b_static_filter_repair_manifest'
```

实现后 targeted tests：

```text
2 passed in 0.12s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_static_filter.py tests/test_result_manifest.py -q
```

结果：

```text
18 passed in 0.46s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
97 passed in 13.01s
```

代码层提交：

```text
ca4cc094eeaf60f115a32863a45e0ea43bbaf512
repair P8b static filter recall
```

### 真实运行命令

只重跑 static filter post：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter --program-preset p8b-misc8 --mode per-program --observed-summary data\outputs\cert_summary_p8b_misc8_pre.csv --out-csv data\outputs\static_filter_decisions_p8b_misc8_post.csv --out-report data\outputs\static_filter_report_p8b_misc8_post.md --window-size 7
```

生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p8b-static-repair --out-manifest docs\results\p8b_misc8_static_filter_repair_manifest.json --observed-summary data\outputs\cert_summary_p8b_misc8_pre.csv --passspec configs\passspec.yaml --pre-static-decisions data\outputs\static_filter_decisions_p8b_misc8_pre.csv --pre-static-report data\outputs\static_filter_report_p8b_misc8_pre.md --post-static-decisions data\outputs\static_filter_decisions_p8b_misc8_post.csv --post-static-report data\outputs\static_filter_report_p8b_misc8_post.md --repair-report data\outputs\static_filter_repair_report_p8b_misc8.md --repo-root . --result-generated-from-commit ca4cc094eeaf60f115a32863a45e0ea43bbaf512
```

### 真实结果

Before：

```text
candidate = 184
low_priority = 40
frozen = 0
StaticCandidateRecall = 93.42%
MacroStaticCandidateRecall = 94.39%
StaticFalseNegativeObserved = 5
StaticCandidateReduction = 17.86%
```

After：

```text
candidate = 200
low_priority = 24
frozen = 0
StaticCandidateRecall = 100.00%
MacroStaticCandidateRecall = 100.00%
StaticFalseNegativeObserved = 0
StaticCandidateReduction = 10.71%
```

原 5 个 false negative 在 post 中全部变为：

```text
sroa->dce:dce_opportunity
sroa->adce:dce_opportunity
```

`docs/results/p8b_misc8_static_filter_repair_manifest.json` 关键字段：

```text
stage = P8b-2
ecpor_git_commit = ca4cc094eeaf60f115a32863a45e0ea43bbaf512
ecpor_git_dirty = False
PreStaticFalseNegativeObserved = 5
PostStaticFalseNegativeObserved = 0
StaticFalseNegativeDelta = 5
PreStaticCandidateReduction = 17.86%
PostStaticCandidateReduction = 10.71%
PassSpecRepair = sroa.may_produce += dce_opportunity
```

scope limits：

```text
new_certificates = False
certificate_matrix_rerun = False
new_search = False
runtime_benchmarks = False
code_size_evaluation = False
passspec_tuning = True
repair_source = empirical_false_negative_repair_p8b1
```

### 代码快照

`configs/passspec.yaml` 修复：

```yaml
  sroa:
    may_produce:
      - scalar_value
      - simplified_load_store
      - load_store
      - scalar_cfg_opportunity
      - instcombine_opportunity
      - early_cse_opportunity
      # P8b-1 empirical false-negative repair:
      # sroa can expose cleanup opportunities consumed by dce/adce.
      - dce_opportunity
```

回归测试：

```python
sroa_dce = classify_pair(
    "sroa",
    "dce",
    passspec,
    program_features=features,
    distance=6,
    window_size=7,
)
sroa_adce = classify_pair(
    "sroa",
    "adce",
    passspec,
    program_features=features,
    distance=7,
    window_size=7,
)

self.assertEqual(sroa_dce["decision"], "candidate")
self.assertEqual(sroa_dce["reason"], "producer_consumer")
self.assertEqual(sroa_adce["decision"], "candidate")
self.assertEqual(sroa_adce["reason"], "producer_consumer")
```

P8b-2 manifest builder：

```python
def build_p8b_static_filter_repair_manifest(
    *,
    observed_summary_csv: str | Path,
    passspec_path: str | Path,
    pre_static_decisions_csv: str | Path,
    pre_static_report: str | Path,
    post_static_decisions_csv: str | Path,
    post_static_report: str | Path,
    repair_report: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    pre_summary = _prefixed_report_summary(
        pre_static_report,
        prefix="Pre",
        keys=P8B_STATIC_REPAIR_KEYS,
    )
    post_summary = _prefixed_report_summary(
        post_static_report,
        prefix="Post",
        keys=P8B_STATIC_REPAIR_KEYS,
    )
    summary: dict[str, Any] = {
        **pre_summary,
        **post_summary,
        "StaticFalseNegativeDelta": _static_false_negative_delta(
            pre_summary,
            post_summary,
        ),
        "PassSpecRepair": "sroa.may_produce += dce_opportunity",
    }
```

### 语义边界

1. 这次修复只是 high-recall static hint 修复，不是 hard pruning 规则。
2. `StaticCandidateRecall = 100%` 只对当前 Misc8 full matrix 的 observed not-certified pair 成立。
3. Candidate reduction 从 `17.86%` 降到 `10.71%`，这是为了消除 false negative 的保守代价。
4. 本轮没有重跑 224 个 certificate；证书层结论仍来自 P8b-1。
5. 本轮没有做 P4/P5/P6/P8a，也没有进入 depth=3、beam search 或 runtime benchmark。

### data 保留情况

新增保留：

```text
data/outputs/static_filter_decisions_p8b_misc8_post.csv
data/outputs/static_filter_report_p8b_misc8_post.md
data/outputs/static_filter_repair_report_p8b_misc8.md
docs/results/p8b_misc8_static_filter_repair_manifest.json
```

原因：P8b-2 是基于 P8b-1 pre 的 passspec 修复，必须保留 pre/post 对照，避免只报告调参后的 post 结果。

### 下一步

进入 P8b-3-lite：

```text
Misc8 P4 prefix-state adjacent lazy validation
Misc8 P5 bounded one-swap
Misc8 P6 llc object size
Misc8 P8a clang-c sensitivity
暂不跑 P7b two-swap
```

判断标准：

```text
Depth1BothSmallerPrograms
DirectionAgreementRate
IRDifferentButTextEqualRate
SmallerOnlyUnderLlcCount
SmallerOnlyUnderClangCount
```

如果 `Depth1BothSmallerPrograms >= 2`，再考虑进入 Misc8 bounded two-swap。
