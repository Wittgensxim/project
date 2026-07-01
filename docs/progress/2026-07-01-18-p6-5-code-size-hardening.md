# ECPOR 进度记录：P6.5 code size provenance 与 invariant 加固

## 2026-07-01：先加固 P6，再进入 P7

### 当前目标

本轮不进入完整 searcher，也不做 P7 two-swap。目标是把 P6 code size evaluator 从“能跑出 object size 表”加固成“能审计、能复跑、能发现数据错位”的版本。

重点补齐三类能力：

```text
1. 报告 provenance：
   记录 ecpor git commit/dirty、P5 report hash、candidates.csv hash、
   pipeline_runs.csv hash、llc hash、llvm-size hash。

2. object_size.csv invariant：
   写表前检查行数、anchor、delta、total size、object path 与 candidate_id 是否一致。

3. P6 解释指标：
   记录 IRDifferentButTextEqualCount / Rate，并列出 best smaller candidate。
```

### 已完成内容

- [x] `src/ecpor/code_size_evaluator.py` 增加 `CodeSizeEvaluation.metadata`。
- [x] `object_size.csv` 新增：
  - `ir_path`
  - `object_path`
  - `data_size`
  - `bss_size`
  - `anchor_data_size`
  - `anchor_bss_size`
  - `data_delta`
  - `bss_delta`
  - `p5_same_as_anchor`
- [x] `code_size_report.md` 新增 `Run metadata`。
- [x] `code_size_report.md` 新增：
  - `IRDifferentButTextEqualCount`
  - `IRDifferentButTextEqualRate`
  - `Best smaller candidate`
- [x] 新增 `validate_object_size_invariants()`，在写 CSV 前检查 P6 数据一致性。
- [x] `llvm-size` parser 增加鲁棒性测试：
  - CRLF
  - warning line
  - empty output
  - header-only output
  - hex 数字
- [x] 修复测试夹具：`pipeline` 字段包含逗号，测试 CSV 改用 `csv.DictWriter` 生成，避免手写 CSV 字段错位。
- [x] README 中 P5 命令改为当前保留输出目录 `data/outputs/bounded_local_p5_p6_final/`。
- [x] 修复 P6 进度文档中的占位提交号。

### TDD 验证

本轮先补 RED 测试，最初预期失败点是：

```text
missing ir_different_but_text_equal_count
missing validate_object_size_invariants
missing metadata / pipeline_runs_sha256
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_object_size_runner.py tests\test_code_size_evaluator.py
```

结果：

```text
8 passed in 0.46s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
70 passed in 7.56s
```

### 真实 P5/P6 复跑

P5 复跑命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver --program-preset stanford-8 --pipeline configs\pipeline_scalar.yaml --attempts-csv data\outputs\lazy_validation_p4_e83c409_first.csv --out data\outputs\bounded_local_p5_p6_final --opt E:\llvm\build\bin\opt.exe --timeout-sec 30
```

P5 关键结果：

```text
anchor_candidates: 8
single_swap_candidates: 16
pipeline_runs: 24
pipeline_run_failed: 0
same_as_anchor: 8
different_from_anchor: 16
single_swap_same_as_anchor: 0
single_swap_different_from_anchor: 16
```

P6 复跑命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.code_size_evaluator --p5-dir data\outputs\bounded_local_p5_p6_final --out data\outputs\code_size_p6_final --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

P6 关键结果：

```text
Programs: 8
Anchor object builds: 8
Single-swap object builds: 16
Object builds attempted: 24
ObjectBuildFailed: 0
SizeParseFailed: 0
CodeSizeDeltaVsAnchor computed: 16

smaller_text: 1
equal_text: 15
larger_text: 0
IRDifferentButTextEqualCount: 15
IRDifferentButTextEqualRate: 93.75%
```

唯一 `.text` 变小的 candidate 仍然是：

```text
program: testsuite_stanford_queens
pair: instcombine,simplifycfg
candidate_id: testsuite_stanford_queens__swap_2__instcombine__simplifycfg
text_delta: -32
text_delta_pct: -4.4017
```

工具 hash：

```text
llc_sha256: 1520eba7e1ee09cc6f38ce1d7ca6eb9fb5187f6ded3a9f70a37f264acebf384c
llvm_size_sha256: f425ef87d64380ff5f8fd055ddb52e1f0d38f3031bb2a5bbddd557d71c5bc589
```

说明：最终 clean commit 的准确 `ecpor_git_commit`、`ecpor_git_dirty`、P5 report hash 和 pipeline CSV hash 以 `data/outputs/code_size_p6_final/code_size_report.md` 的 `Run metadata` 为准；该目录是生成产物，按 data retention 规则不纳入 Git。

### 本次代码快照：P6 metadata

```python
def build_code_size_metadata(
    *,
    candidates_csv: str | Path,
    pipeline_runs_csv: str | Path,
    p5_report_path: str | Path,
    llc_path: ToolPath,
    llvm_size_path: ToolPath,
) -> dict[str, str]:
    git = git_info(Path.cwd())
    return {
        "ecpor_git_commit": git.commit,
        "ecpor_git_dirty": str(git.dirty),
        "p5_report": _path_text(p5_report_path),
        "p5_report_sha256": _file_hash_or_empty(p5_report_path),
        "candidates_csv": _path_text(candidates_csv),
        "candidates_csv_sha256": _file_hash_or_empty(candidates_csv),
        "pipeline_runs_csv": _path_text(pipeline_runs_csv),
        "pipeline_runs_sha256": _file_hash_or_empty(pipeline_runs_csv),
        "llc_path": _tool_path_text(llc_path),
        "llc_sha256": _tool_sha256(llc_path),
        "llvm_size_path": _tool_path_text(llvm_size_path),
        "llvm_size_sha256": _tool_sha256(llvm_size_path),
    }
```

### 本次代码快照：P6 invariant

```python
def validate_object_size_invariants(
    rows: Sequence[dict[str, str]],
    *,
    pipeline_run_count: int | None = None,
) -> list[str]:
    errors: list[str] = []
    if pipeline_run_count is not None and len(rows) != pipeline_run_count:
        errors.append(
            f"row count mismatch: object_size rows={len(rows)} "
            f"pipeline_runs rows={pipeline_run_count}"
        )

    programs = sorted({row.get("program", "") for row in rows})
    anchor_by_program: dict[str, dict[str, str]] = {}
    for program in programs:
        anchor_rows = [
            row
            for row in rows
            if row.get("program") == program and row.get("source") == "anchor"
        ]
        if len(anchor_rows) != 1:
            errors.append(
                f"program {program} has {len(anchor_rows)} anchor rows; expected 1"
            )
            continue
        anchor_by_program[program] = anchor_rows[0]

    for row in rows:
        candidate_id = row.get("candidate_id", "")
        text_size = _parse_optional_int(row.get("text_size"))
        data_size = _parse_optional_int(row.get("data_size"))
        bss_size = _parse_optional_int(row.get("bss_size"))
        total_size = _parse_optional_int(row.get("total_size"))
        if None not in {text_size, data_size, bss_size, total_size}:
            expected_total = text_size + data_size + bss_size
            if total_size != expected_total:
                errors.append(
                    f"{candidate_id}: total_size != text+data+bss "
                    f"({total_size} != {expected_total})"
                )

        _validate_delta(
            errors,
            row,
            candidate_id,
            value_field="text_size",
            anchor_field="anchor_text_size",
            delta_field="text_delta",
            pct_field="text_delta_pct",
        )
```

### 本次代码快照：P6 report 指标

```python
ir_different_rows = [
    row
    for row in single_swap_rows
    if row.get("p5_same_as_anchor", "").lower() == "false"
    and row.get("text_delta", "") != ""
]
ir_different_but_text_equal = [
    row for row in ir_different_rows if int(row["text_delta"]) == 0
]

return {
    ...
    "ir_different_but_text_equal_count": len(ir_different_but_text_equal),
    "ir_different_but_text_equal_rate": (
        len(ir_different_but_text_equal) / len(ir_different_rows)
        if ir_different_rows
        else 0.0
    ),
}
```

### 风险与备注

- `IRDifferentButTextEqualRate = 93.75%` 只说明 P5 中 15 个 IR-different single-swap candidate 最终 `.text` size 与 anchor 相同，不说明它们语义相同，也不说明 runtime 相同。
- `smaller_text = 1` 只说明一个 candidate 的 `.text` 小于 anchor；不能写成“整体更优”。
- 本轮仍然只比较 `llc -filetype=obj` 后的 object size；还没有加入 `clang -c` 对照。
- 本轮没有扩大搜索空间；P7 如果做，也应继续保持 bounded two-swap，而不是直接上完整 searcher。
- 本轮没有新增长期 `data/*_work` 目录；真实输出仍写入当前保留 final 目录。

### 下一步

- 提交本轮 P6.5 加固。
- 提交后复跑全量测试、P5 final、P6 final，确认最终报告中 `ecpor_git_dirty = False`。
- 然后再进入 P7 bounded two-swap exploration 的设计与最小实现。
