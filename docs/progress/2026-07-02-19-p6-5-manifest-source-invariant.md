# ECPOR 进度记录：P6.5 manifest 与 candidate-source invariant

## 2026-07-02：补齐 P6.5 可提交结果边界

### 当前目标

本轮仍然不进入 P7，也不做完整 searcher。目标是处理 P6.5 后的两个收尾点：

```text
1. P6 的 object_size.csv 不只检查 size/delta，还检查 candidate source 语义。
2. P6.5 的关键实验 metadata 不能只存在于 ignored 的 data/outputs 里，
   需要新增一个可提交的 docs/results manifest。
```

### 已完成内容

- [x] 新增 P6 candidate-source invariant：
  - anchor row 的 `p5_same_as_anchor` 必须为 `True`。
  - single-swap row 必须有 `anchor_text_size`。
  - single-swap row 必须有 `text_delta`。
  - single-swap row 的 `p5_same_as_anchor` 必须来自 P5 `pipeline_runs.csv`，值为 `True` 或 `False`。
- [x] P6 report 新增：
  - `SingleSwapP5SameAsAnchor`
  - `SingleSwapP5DifferentFromAnchor`
- [x] 新增可提交 manifest：
  - `docs/results/p6_5_code_size_manifest.json`
- [x] manifest 记录：
  - clean run commit
  - P4/P5/P6 输入输出路径
  - P5 report / candidates / pipeline_runs hash
  - `llc` / `llvm-size` hash
  - P5 summary
  - P6 summary
  - best smaller candidate
  - 当前 scope limit

### TDD 验证

先写 RED 测试：

```text
test_validates_candidate_source_invariants
test_counts_ir_different_but_text_equal_candidates
```

第一次 RED 失败符合预期：

```text
KeyError: 'single_swap_p5_same_as_anchor'
AssertionError: anchor p5_same_as_anchor is not True not found
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_code_size_evaluator.py tests\test_object_size_runner.py
```

结果：

```text
9 passed in 0.48s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
71 passed in 7.65s
```

### clean run 结果

source invariant 提交后，在 clean commit 下复跑 P5：

```text
ecpor_git_commit: 4af57cd73687b9c274ac8e678c0cd1521e32f309
ecpor_git_dirty: False
anchor_candidates: 8
single_swap_candidates: 16
pipeline_runs: 24
pipeline_run_failed: 0
single_swap_same_as_anchor: 0
single_swap_different_from_anchor: 16
```

在同一 clean commit 下复跑 P6：

```text
ecpor_git_commit: 4af57cd73687b9c274ac8e678c0cd1521e32f309
ecpor_git_dirty: False
ObjectBuildFailed: 0
SizeParseFailed: 0
CodeSizeDeltaVsAnchor computed: 16
SingleSwapP5SameAsAnchor: 0
SingleSwapP5DifferentFromAnchor: 16
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

### manifest 说明

manifest 路径：

```text
docs/results/p6_5_code_size_manifest.json
```

manifest 中的 `ecpor_git_commit` 指的是生成 P5/P6 clean run 的代码提交：

```text
4af57cd73687b9c274ac8e678c0cd1521e32f309
```

这个文件本身会在后续提交中进入 Git，因此它不是在自引用自己的 commit hash。这样做的边界是：

```text
manifest commit 负责保存实验记录；
ecpor_git_commit 负责指向产生实验结果的 clean code commit。
```

### 本次代码快照：candidate-source invariant

```python
if source == "single_swap":
    anchor = anchor_by_program.get(program)
    if (
        anchor is None
        or not row.get("anchor_candidate_id")
        or row.get("anchor_candidate_id") != anchor.get("candidate_id")
    ):
        errors.append(f"{candidate_id}: missing program anchor")
    if _parse_optional_int(row.get("anchor_text_size")) is None:
        errors.append(f"{candidate_id}: single_swap anchor_text_size missing")
    if _parse_optional_int(row.get("text_delta")) is None:
        errors.append(f"{candidate_id}: single_swap text_delta missing")
    if row.get("p5_same_as_anchor") not in {"True", "False"}:
        errors.append(f"{candidate_id}: single_swap p5_same_as_anchor missing")

if source == "anchor":
    for field in ("text_delta", "total_delta"):
        delta = _parse_optional_int(row.get(field))
        if delta not in {None, 0}:
            errors.append(f"{candidate_id}: anchor delta is not zero")
    if row.get("p5_same_as_anchor") != "True":
        errors.append(f"{candidate_id}: anchor p5_same_as_anchor is not True")
```

### 本次代码快照：P6 summary 新字段

```python
single_swap_same_as_anchor = [
    row
    for row in single_swap_rows
    if row.get("p5_same_as_anchor", "").lower() == "true"
]

return {
    ...
    "single_swap_p5_same_as_anchor": len(single_swap_same_as_anchor),
    "single_swap_p5_different_from_anchor": len(ir_different_rows),
    "ir_different_but_text_equal_count": len(ir_different_but_text_equal),
}
```

### 本次 manifest 快照

```json
{
  "stage": "P6.5",
  "result_generated_from_commit": "4af57cd73687b9c274ac8e678c0cd1521e32f309",
  "ecpor_git_dirty": false,
  "p6_summary": {
    "object_build_failed": 0,
    "size_parse_failed": 0,
    "code_size_delta_vs_anchor_computed": 16,
    "smaller_text": 1,
    "equal_text": 15,
    "larger_text": 0,
    "single_swap_p5_same_as_anchor": 0,
    "single_swap_p5_different_from_anchor": 16,
    "ir_different_but_text_equal_count": 15,
    "ir_different_but_text_equal_rate": 0.9375
  }
}
```

### 风险与备注

- `docs/results/p6_5_code_size_manifest.json` 只保存小体量 metadata，不保存 `.ll`、`.o` 或大 CSV。
- manifest 记录的是产生实验结果的 clean commit，不试图记录包含 manifest 自身的 commit，避免 commit hash 自引用问题。
- 当前仍未做 `clang -c` 对照；这不是 P7a 的硬阻塞项，可以放到 P7.5。
- 当前仍不能把 `smaller_text=1` 写成“整体更优”，只能写成 bounded object text size observation。

### 下一步

- 提交 manifest 与文档索引。
- 最终验证后进入 P7a bounded two-swap smoke test。
- P7a 的第二个 swap 必须重新 materialize seed pipeline 下的新 prefix state，不能复用其他 state 的 certificate。
