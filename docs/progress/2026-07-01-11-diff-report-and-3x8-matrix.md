# ECPOR 进度记录：P2.6 diff report 与 3×8 matrix

## 2026-07-01：P2.6 diff report 与 3×8 matrix

### 当前目标

按最新 review 要求，本轮仍不进入 searcher，而是继续收紧报告层：

- 修正 `summary_report.py` 的 failure 统计表达，不再输出容易误读的 `none: 0`。
- 明确 `feature_delta = features_ba - features_ab`，并在报告中标注 feature delta 只是 soft evidence。
- 新增 not-certified 专用 diff report，把 JSON feature delta 展开成人类可读表格。
- 加入 `CertifiedFeatureMismatchCount` sanity check。
- 将 Stanford matrix 从 `3×3` 扩展到 `3×8`，先固定程序集合，只扩大 pass pair。

### 已完成内容

- [x] `summary_report.py` 改为按 AB/BA direction 统计 failure：
  - `total_directions`
  - `no_failure`
  - `opt_failed`
  - `timeout`
  - `output_missing`
  - `opt_failed_output_exists`
  - `os_error`
- [x] `summary_report.py` 新增 certificate-level failure 统计：
  - `Certificates with any failure`
- [x] `summary_report.py` 新增：
  - `CertifiedFeatureMismatchCount`
  - `Feature delta is soft evidence only.`
  - `Delta convention: feature_delta = features_ba - features_ab`
- [x] 新增 `src/ecpor/diff_report.py`：
  - 只读取 `label == not_certified_independent` 的 row。
  - 生成 `data/outputs/not_certified_diff_report.md`。
  - 生成 `data/outputs/not_certified_diff_summary.csv`。
  - 把 `features_ab/features_ba/feature_delta` JSON 展开为 Markdown 表格。
- [x] 扩展默认 pass pair 到 8 个：
  - `instcombine,dce`
  - `instcombine,adce`
  - `dce,adce`
  - `simplifycfg,instcombine`
  - `simplifycfg,dce`
  - `sroa,early-cse`
  - `sroa,instcombine`
  - `early-cse,gvn`
- [x] `README.md` 更新为 3×8 matrix 命令，并加入 diff report 命令。
- [x] `docs/project_progress.md` 更新第 11 个进度索引。

### 验证结果

RED 测试确认：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_summary_report.py tests/test_diff_report.py tests/test_batch_certificates.py -q
```

初始失败符合预期：

```text
5 failed, 1 passed
```

失败点对应：

- `summary_report.py` 尚未输出 `CertifiedFeatureMismatchCount`。
- `summary_report.py` 尚未输出 failure direction 统计。
- `src/ecpor/diff_report.py` 尚不存在。
- 默认 pass pair 仍是 3 个而不是 8 个。

GREEN 后局部测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_summary_report.py tests/test_diff_report.py tests/test_batch_certificates.py -q
```

结果：

```text
6 passed in 1.12s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
31 passed in 2.57s
```

### 真实 LLVM 3×8 matrix

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.batch_certificates import DEFAULT_PASS_PAIRS, DEFAULT_STANFORD_PROGRAMS, run_certificate_matrix, summarize_rows; rows=run_certificate_matrix(programs=DEFAULT_STANFORD_PROGRAMS, pass_pairs=DEFAULT_PASS_PAIRS, opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests', cert_dir='data/certs/pair_tests', summary_csv='data/outputs/cert_summary.csv', env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e', llvm_version='23.0.0git'); print(summarize_rows(rows))"
```

结果：

```text
{'certified_independent': 15, 'not_certified_independent': 9, 'total': 24, 'reproduced': 24, 'hard_false_independent': 0, 'certified_feature_mismatch': 0}
```

### summary report 输出

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.summary_report import main; raise SystemExit(main(['data/outputs/cert_summary.csv','--out','data/outputs/cert_summary_report.txt']))"
```

关键输出：

```text
Total certificates: 24
Reproduced: 24 / 24 = 100.00%
HardFalseIndependent: 0
CertifiedFeatureMismatchCount: 0
Feature delta is soft evidence only.
Delta convention: feature_delta = features_ba - features_ab

Label counts:
  certified_independent: 15
  not_certified_independent: 9
  run_failed: 0

Certificates with any failure: 0 / 24
Failure directions:
  total_directions: 48
  no_failure: 48 / 48
  opt_failed: 0
  timeout: 0
  output_missing: 0
  opt_failed_output_exists: 0
  os_error: 0
```

per-pair 结果：

```text
dce,adce: 3/3 certified
early-cse,gvn: 3/3 certified
instcombine,adce: 3/3 certified
instcombine,dce: 3/3 certified
simplifycfg,dce: 3/3 certified
simplifycfg,instcombine: 0/3 certified
sroa,early-cse: 0/3 certified
sroa,instcombine: 0/3 certified
```

### not-certified diff report

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.diff_report import main; raise SystemExit(main(['data/outputs/cert_summary.csv','--out-md','data/outputs/not_certified_diff_report.md','--out-csv','data/outputs/not_certified_diff_summary.csv']))"
```

生成文件：

```text
data/outputs/not_certified_diff_report.md
data/outputs/not_certified_diff_summary.csv
```

not-certified 数量：

```text
Not-certified certificates: 9
```

示例条目：

```markdown
## testsuite_stanford_bubblesort :: simplifycfg -> instcombine

Label: not_certified_independent
Reason: hard hash differs
Delta convention: BA - AB

| feature | AB | BA | delta |
|---|---:|---:|---:|
| num_branch | 21 | 20 | -1 |
| num_instructions | 154 | 153 | -1 |
| num_load | 30 | 31 | +1 |
```

### 风险与备注

- `feature_delta` 仍然只是 soft evidence，不参与 hard certificate 判定，也不能证明语义等价或不等价。
- 当前 certificate 仍然是 input-state certificate，只能说明在当前 observed input state 上的 AB/BA 结果；不能推广为全局 pass 交换律。
- 有些 not-certified pair 的 `feature_delta` 为空，但 hard hash 不同。这说明文本级 feature scan 的分辨率有限，不能代替 canonical hard hash。
- 24-case matrix 只扩大了 pass pair，没有扩大 program 集合；这是刻意控制变量，便于定位后续静态过滤问题。

### 下一步

- 做第一版 high-recall `passspec.yaml`。
- 做 `static_filter.py`，只输出候选优先级，不输出 hard proof。
- 继续保留规则：hard pruning 只依赖 certificate/hard hash equality，不用 feature scan 直接证明 independence。
- 暂不进入 `search.py`、code size evaluator、Alive2、loop pass、inline 或完整 O2/O3。

### 本次代码快照：`src/ecpor/diff_report.py`

```python
DIFF_SUMMARY_FIELDS = [
    "program",
    "pair_a",
    "pair_b",
    "input_state_hash",
    "pipeline_ab",
    "pipeline_ba",
    "hash_ab",
    "hash_ba",
    "nonzero_feature_delta",
    "elapsed_ab_ms",
    "elapsed_ba_ms",
    "cert_id",
]


def build_not_certified_diff_report(rows: Sequence[dict[str, str]]) -> str:
    report_rows = _not_certified_rows(rows)
    lines = [
        "# Not-Certified Feature Delta Report",
        "",
        "Feature delta is soft evidence only.",
        "It is not used for hard pruning.",
        "Delta convention: feature_delta = features_ba - features_ab",
        "",
        f"Not-certified certificates: {len(report_rows)}",
    ]

    if not report_rows:
        lines.append("")
        lines.append("No not-certified certificates found.")
        return "\n".join(lines) + "\n"

    for row in report_rows:
        features_ab = _parse_json_object(row.get("features_ab", ""))
        features_ba = _parse_json_object(row.get("features_ba", ""))
        feature_delta = _parse_json_object(row.get("feature_delta", ""))
        nonzero = _nonzero_delta_items(feature_delta)

        lines.extend(
            [
                "",
                f"## {row.get('program', '')} :: {row.get('pair_a', '')} -> {row.get('pair_b', '')}",
                "",
                f"Label: {row.get('label', '')}",
                "Reason: hard hash differs",
                "Delta convention: BA - AB",
                "",
                f"- input_state_hash: `{row.get('input_state_hash', '')}`",
                f"- pipeline_ab: `{row.get('pipeline_ab', '')}`",
                f"- pipeline_ba: `{row.get('pipeline_ba', '')}`",
                f"- hash_ab: `{row.get('hash_ab', '')}`",
                f"- hash_ba: `{row.get('hash_ba', '')}`",
                f"- elapsed_ab_ms: {row.get('elapsed_ab_ms', '')}",
                f"- elapsed_ba_ms: {row.get('elapsed_ba_ms', '')}",
                f"- cert_id: `{row.get('cert_id', '')}`",
                "",
            ]
        )
        if nonzero:
            lines.extend(
                [
                    "| feature | AB | BA | delta |",
                    "|---|---:|---:|---:|",
                ]
            )
            for key, delta_value in nonzero:
                lines.append(
                    "| {feature} | {ab} | {ba} | {delta} |".format(
                        feature=key,
                        ab=_format_value(features_ab.get(key, "")),
                        ba=_format_value(features_ba.get(key, "")),
                        delta=_format_delta(delta_value),
                    )
                )
        else:
            lines.append("No nonzero feature delta.")

    return "\n".join(lines) + "\n"
```

### 本次代码快照：`src/ecpor/summary_report.py` 关键片段

```python
KNOWN_FAILURE_KINDS = [
    "opt_failed",
    "timeout",
    "output_missing",
    "opt_failed_output_exists",
    "os_error",
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
    certified_feature_mismatch = sum(
        1
        for row in rows
        if row.get("label") == "certified_independent"
        and _has_nonzero_feature_delta(row.get("feature_delta", ""))
    )
    label_counts = Counter(row.get("label", "") for row in rows)
    failure_counts = Counter[str]()
    no_failure_directions = 0
    certificates_with_any_failure = 0
    for row in rows:
        row_has_failure = False
        for key in ("failure_kind_ab", "failure_kind_ba"):
            value = row.get(key, "").strip()
            if value and value != "none":
                failure_counts[value] += 1
                row_has_failure = True
            else:
                no_failure_directions += 1
        if row_has_failure:
            certificates_with_any_failure += 1
    total_directions = total * 2

    lines = [
        f"Total certificates: {total}",
        f"Reproduced: {reproduced} / {total} = {reproduction_rate:.2f}%",
        f"HardFalseIndependent: {hard_false}",
        f"CertifiedFeatureMismatchCount: {certified_feature_mismatch}",
        "Feature delta is soft evidence only.",
        "Delta convention: feature_delta = features_ba - features_ab",
        "",
        "Label counts:",
    ]
```

### 本次代码快照：`src/ecpor/batch_certificates.py` pass pair 与 sanity 片段

```python
STANFORD_3X3_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("simplifycfg", "instcombine"),
    ("sroa", "early-cse"),
]

DEFAULT_PASS_PAIRS: list[PassPair] = [
    ("instcombine", "dce"),
    ("instcombine", "adce"),
    ("dce", "adce"),
    ("simplifycfg", "instcombine"),
    ("simplifycfg", "dce"),
    ("sroa", "early-cse"),
    ("sroa", "instcombine"),
    ("early-cse", "gvn"),
]


def summarize_rows(rows: Sequence[dict[str, str]]) -> dict[str, int]:
    label_counts = Counter(row["label"] for row in rows)
    reproduced_count = sum(1 for row in rows if row["reproduced"] == "True")
    hard_false_independent = sum(
        1
        for row in rows
        if row["label"] == "certified_independent" and row["hard_equal"] != "True"
    )
    certified_feature_mismatch = sum(
        1
        for row in rows
        if row["label"] == "certified_independent"
        and _has_nonzero_feature_delta(row.get("feature_delta", ""))
    )
    summary = dict(label_counts)
    summary["total"] = len(rows)
    summary["reproduced"] = reproduced_count
    summary["hard_false_independent"] = hard_false_independent
    summary["certified_feature_mismatch"] = certified_feature_mismatch
    return summary
```
