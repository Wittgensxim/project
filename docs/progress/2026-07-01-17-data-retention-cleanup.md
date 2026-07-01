# ECPOR 进度记录：data 目录保守清理

## 2026-07-01：整理生成产物，保留可复现实验依据

### 当前目标

本轮不是推进新的 P 阶段，而是整理 `data/` 目录。目标是：

- 保留所有 Git 跟踪的输入。
- 保留 P4/P5/P6 当前 final 结果。
- 删除明确的 `*_work`、旧 commit P5 输出和重复的 P4 final 目录。
- 不删除 `pair_tests`，避免破坏历史证书和 diff report 的人工检查链路。
- 建立一份可复用的 data retention manifest。

### 已完成内容

- [x] 新增 `docs/data_retention_manifest.md`：
  - 定义 `keep / delete / regenerate` 规则。
  - 明确 `data/inputs/*.ll` 必须保留。
  - 明确 `data/outputs/` 和 `data/certs/` 是生成产物，默认不进 Git。
  - 明确 `*_work` 和旧 P5 commit 输出可以删除。
- [x] 删除临时/重复输出目录：
  - `data/outputs/lazy_validation_p4_work/`
  - `data/outputs/lazy_validation_p4_final/`
  - `data/outputs/bounded_local_p5_work/`
  - `data/outputs/bounded_local_p5_92bcc03/`
  - `data/outputs/bounded_local_p5_final/`
  - `data/outputs/bounded_local_p5_p6_work/`
  - `data/outputs/code_size_p6_work/`
  - `data/outputs/state_index_safety_work/`
  - `data/outputs/state_index_safety_final/`
  - `data/outputs/state_index_safety_e83c409/`
  - `data/outputs/negative/`
- [x] 删除临时/重复证书目录：
  - `data/certs/lazy_validation_p4_work/`
  - `data/certs/lazy_validation_p4_final/`
  - `data/certs/state_index_safety_work/`
  - `data/certs/state_index_safety_final/`
  - `data/certs/state_index_safety_e83c409/`
- [x] 保留关键目录：
  - `data/inputs/`
  - `data/outputs/pair_tests/`
  - `data/outputs/lazy_validation_p4_e83c409/`
  - `data/outputs/bounded_local_p5_p6_final/`
  - `data/outputs/code_size_p6_final/`
  - `data/certs/pair_tests/`
  - `data/certs/lazy_validation_p4_e83c409/`

### 清理前后对比

清理前：

```text
data/outputs: 6301 files, 30.41 MB
data/certs:    375 files,  0.88 MB
data/inputs:    11 files,  0.17 MB
```

清理后：

```text
data/outputs: 4532 files, 21.57 MB
data/certs:    276 files,  0.62 MB
data/inputs:    11 files,  0.17 MB
```

主要剩余体积：

```text
data/outputs/pair_tests:                3634 files, 16.84 MB
data/outputs/lazy_validation_p4_e83c409:  816 files,  3.68 MB
data/outputs/bounded_local_p5_p6_final:    27 files,  0.34 MB
data/outputs/code_size_p6_final:           26 files,  0.08 MB
data/certs/pair_tests:                    227 files,  0.49 MB
data/certs/lazy_validation_p4_e83c409:     48 files,  0.13 MB
```

### Git 状态检查

Git 跟踪的 `data/` 文件仍然只有输入：

```text
data/inputs/alloca.ll
data/inputs/branch.ll
data/inputs/dead_code.ll
data/inputs/testsuite_stanford_bubblesort.ll
data/inputs/testsuite_stanford_intmm.ll
data/inputs/testsuite_stanford_oscar.ll
data/inputs/testsuite_stanford_perm.ll
data/inputs/testsuite_stanford_puzzle.ll
data/inputs/testsuite_stanford_queens.ll
data/inputs/testsuite_stanford_quicksort.ll
data/inputs/testsuite_stanford_towers.ll
```

`data/outputs/` 和 `data/certs/` 仍是 ignored 生成产物。

### 验证结果

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
66 passed in 7.24s
```

P5 final 报告仍可读取：

```text
ecpor_git_commit: 715924286f5825d19346e0392670aa6e0b9c1abc
ecpor_git_dirty: False
single_swap_same_as_anchor: 0
single_swap_different_from_anchor: 16
```

P6 final 报告仍可读取：

```text
ObjectBuildFailed: 0
SizeParseFailed: 0
CodeSizeDeltaVsAnchor computed: 16
smaller_text: 1
equal_text: 15
larger_text: 0
```

`object_size.csv` 仍有：

```text
24 rows
```

### 本次清理命令快照

删除前先解析路径，并确认目标位于 `E:\project\data` 下：

```powershell
$root = (Resolve-Path -LiteralPath 'E:\project\data').Path
$targets = @(
  'E:\project\data\outputs\lazy_validation_p4_work',
  'E:\project\data\outputs\lazy_validation_p4_final',
  'E:\project\data\outputs\bounded_local_p5_work',
  'E:\project\data\outputs\bounded_local_p5_92bcc03',
  'E:\project\data\outputs\bounded_local_p5_final',
  'E:\project\data\outputs\bounded_local_p5_p6_work',
  'E:\project\data\outputs\code_size_p6_work',
  'E:\project\data\certs\lazy_validation_p4_work',
  'E:\project\data\certs\lazy_validation_p4_final'
)
foreach ($target in $targets) {
  if (-not (Test-Path -LiteralPath $target)) { continue }
  $resolved = (Resolve-Path -LiteralPath $target).Path
  if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to delete outside data root: $resolved"
  }
  Remove-Item -LiteralPath $resolved -Recurse -Force
}
```

### 风险与备注

- 本轮删除的都是 ignored 生成产物，没有删除 Git 跟踪文件。
- 本轮没有删除 `data/outputs/pair_tests/`，因为历史证书 JSON 中仍记录 AB/BA 输出路径。
- 后续如果 certificate reproduction 完全不依赖旧 `output_ab/output_ba` 路径，可以再考虑清理 `pair_tests` 输出目录。
- 生成产物目录未来仍可能膨胀；建议每个阶段只保留一个当前 final 目录和必要 CSV/report。

### 下一步

- 后续新实验默认输出到阶段命名 final 目录。
- 临时目录继续使用 `*_work` 后缀，阶段完成后按 manifest 清理。
- P7 开始前不需要再清理 `pair_tests`。
