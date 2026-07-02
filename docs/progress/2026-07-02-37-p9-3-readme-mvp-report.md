# ECPOR 进度记录：P9-3 README 与 MVP 主报告

## 2026-07-02：把 P9-1 汇总变成项目主入口

### 当前目标

P9-2 已经完成 `result_manifest.py` 的工程拆分，本轮进入 P9-3：不新增实验，只整理 README 与项目主报告，让读者可以快速理解当前 MVP 的研究问题、证据边界和复现路径。

明确不做：

```text
不新增实验
不新增 certificate
不运行新的 LLVM pipeline
不做 depth=3 / beam search / RL / MCTS
不做 runtime benchmark
不引入 Alive2 / PassInstrumentation
不宣称击败 O2/O3
```

### 已完成内容

- [x] 重写 `README.md` 顶部入口，把 ECPOR 定义为 evidence-carrying LLVM phase-ordering reduction prototype，而不是完整 searcher。
- [x] 将 P9-1 四个核心结论放入 README 前半部分：
  - `448` 个 pair certificate，`448/448` 可复现。
  - Stanford-8 与 Misc8 修复后 `StaticFalseNegativeObserved = 0`。
  - 两组各 `16` 个 one-swap candidate，其中各 `1` 个 `.text` smaller、各 `15` 个 IR-different text-equal。
  - Queens 与 ffbench 两个 both-smaller program 均有 case-level attribution。
- [x] 在 README 加入 evidence level 表，明确只有 `certified_independent_event` 可以作为 hard prune。
- [x] 在 README 加入 Mermaid 主流程图。
- [x] 在 README 加入最小复现命令与期望 P9-1 核心值。
- [x] 新增 `docs/ecpor_mvp_report.md`，作为比 README 更完整的 MVP 主报告。
- [x] 保留 unsupported scope，避免把当前 MVP 误读为完整 phase-ordering searcher。

### README 核心片段

```markdown
ECPOR 是一个 evidence-carrying LLVM phase-ordering reduction 原型，不是完整 pass-order searcher。它用 state-indexed 的 AB/BA 相邻 pass 证书证明哪些顺序可以折叠，用静态过滤降低候选量，并把 order-sensitive 的候选保留下来继续做 bounded local validation 与 `.text` 目标层检查。
```

P9-1 核心结果入口：

```markdown
| 结论 | 当前结果 |
| --- | ---: |
| benchmark sets | 2 |
| programs | 16 |
| pair certificates | 448 |
| reproduced certificates | 448 / 448 |
| HardFalseIndependent | 0 |
| StaticFalseNegativeObserved after repair | 0 on Stanford-8 and Misc8 |
| one-swap candidates | 32 |
| `.text` smaller one-swap candidates | 2 programs, 1 per set |
| IR-different but `.text` equal one-swap candidates | 30 |
| attribution cases | 2: Queens and ffbench |
```

Evidence level 边界：

```markdown
| evidence level | 含义 | 可作为 hard prune |
| --- | --- | --- |
| `certified_independent_event` | 当前 state 下 AB/BA hard hash 相同，且 certificate 可复现 | yes |
| `not_certified_event` | 当前 state 下 AB/BA hard hash 不同 | no |
| `low_priority` | 静态过滤认为优先级低，但未动态证明 | no |
| `sequence_duplicate` | 不同 swap 路径生成同一 sequence，可去重 | no |
| `llc/clang both-smaller` | `.text` 在两条 codegen path 下都变小 | no |
| `attribution` | 对单个 observed case 的 feature/opcode/object 归因 | no |
```

### MVP 主报告片段

`docs/ecpor_mvp_report.md` 明确当前 MVP 只回答：

```text
在给定 LLVM IR state、给定 scalar pass 集合和给定相邻 pass pair 下，
哪些顺序可以用 hard hash certificate 证明等价，从而不用继续搜索？
哪些顺序不能证明等价，需要保留为候选？
少数候选在 object .text 上是否真的产生目标层差异？
```

### 复现命令

单元测试：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

重新生成 P9-1 MVP summary：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.mvp_summary `
  --out data\outputs\final_mvp_summary `
  --manifest docs\results\mvp_summary_manifest.json
```

期望核心值：

```text
BenchmarkSets=2
TotalPrograms=16
TotalPairMatrixCertificates=448
TotalReproducedCertificates=448
TotalHardFalseIndependent=0
TotalBothSmallerPrograms=2
AttributionCases=2
```

### 验证结果

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
107 passed in 13.83s
```

P9-1 summary 核心值复跑验证：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.mvp_summary import run_mvp_summary; r = run_mvp_summary(output_dir='data/outputs/final_mvp_summary', manifest_path=None); keys = ['BenchmarkSets','TotalPrograms','TotalPairMatrixCertificates','TotalReproducedCertificates','TotalHardFalseIndependent','TotalBothSmallerPrograms','AttributionCases']; print('\n'.join(f'{k}={r.summary[k]}' for k in keys))"
```

结果：

```text
BenchmarkSets=2
TotalPrograms=16
TotalPairMatrixCertificates=448
TotalReproducedCertificates=448
TotalHardFalseIndependent=0
TotalBothSmallerPrograms=2
AttributionCases=2
```

本次验证没有写 `docs/results/mvp_summary_manifest.json`，原因是 P9-3 文档改动尚未提交；直接写正式 manifest 会把当前工作区 dirty 状态写入 manifest。README 中仍保留正式用户复现命令。

### 风险与备注

- README 与主报告只引用已有 P9-1/P8 系列输出，没有改变代码路径和实验数据。
- `llc/clang both-smaller` 与 attribution 仍然只是目标层 observation，不能当作 pass independence 证明。
- `low_priority` 仍然只是静态提示，不能当作 hard prune。
- 当前不支持完整 searcher、runtime、Alive2、PassInstrumentation、loop/module/inline pass 和 O2/O3 对比宣称。

### 下一步

先审阅 README 与 `docs/ecpor_mvp_report.md` 是否足够清楚。若后续继续扩展 benchmark，建议进入 P9-4 optional diverse8，且仍保持 depth1-only。
