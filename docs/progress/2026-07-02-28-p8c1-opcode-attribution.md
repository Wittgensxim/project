# ECPOR 进度记录：P8c.1 opcode-level attribution

## 2026-07-02：把 Queens 的 feature 解释细化到 opcode multiset

### 当前目标

P8c 已经说明 Queens 的 `simplifycfg,instcombine` 顺序在局部 pair 后产生 IR 差异，并且 suffix 后差异保持。本轮做一个很小的解释增强：

```text
不新增搜索；
不新增 certificate；
不扩大 benchmark；
只给 P8c 的 AB/BA state 增加 opcode-level delta。
```

目标是把“BA 比 AB 少 1 条 instruction”细化成更可读的 opcode multiset 变化。

### 已完成内容

- [x] 更新 `src/ecpor/effect_attribution.py`：
  - 新增 opcode multiset 扫描。
  - 新增 `opcode_delta.csv`。
  - 报告新增 `Opcode Delta` 段落。
  - summary 新增 `FinalOpcodeDeltaNonZero`。
- [x] 更新 `src/ecpor/result_manifest.py`：
  - P8c manifest 新增 `opcode_delta_csv`。
  - P8c summary 记录 `FinalOpcodeDeltaNonZero`。
- [x] 更新测试：
  - `tests/test_effect_attribution.py`
  - `tests/test_result_manifest.py`
- [x] 重新生成真实输出：
  - `data/outputs/effect_attribution_queens/opcode_delta.csv`
  - `data/outputs/effect_attribution_queens/attribution_report.md`
- [x] 重新生成 tracked manifest：
  - `docs/results/queens_effect_attribution_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py::EffectAttributionTests::test_runs_queens_attribution_and_writes_required_outputs
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_p8c_queens_attribution_manifest
```

初始失败符合预期：

```text
FileNotFoundError: opcode_delta.csv
AssertionError: 'opcode_delta_csv' not found in manifest outputs
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py::EffectAttributionTests::test_runs_queens_attribution_and_writes_required_outputs
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_p8c_queens_attribution_manifest
```

结果：

```text
1 passed in 0.54s
1 passed in 0.07s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py tests\test_result_manifest.py tests\test_object_size_runner.py tests\test_feature_scan.py
```

结果：

```text
15 passed in 1.01s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
90 passed in 11.22s
```

源码提交：

```text
70fd929761117597d3adaf932e9baad8fccfb9bd
add P8c opcode attribution
```

### 真实运行命令

重新生成 P8c/P8c.1 输出：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.effect_attribution --input-ir data\inputs\testsuite_stanford_queens.ll --out data\outputs\effect_attribution_queens --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

重新生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p8c-attribution --out-manifest docs\results\queens_effect_attribution_manifest.json --input-ir data\inputs\testsuite_stanford_queens.ll --output-dir data\outputs\effect_attribution_queens --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --repo-root . --result-generated-from-commit 70fd929761117597d3adaf932e9baad8fccfb9bd
```

manifest provenance：

```text
stage: P8c
result_generated_from_commit: 70fd929761117597d3adaf932e9baad8fccfb9bd
ecpor_git_commit: 70fd929761117597d3adaf932e9baad8fccfb9bd
ecpor_git_dirty: False
```

### Opcode delta 结果

路径：

```text
data/outputs/effect_attribution_queens/opcode_delta.csv
```

核心表：

| comparison | icmp delta | select delta | add delta | and delta |
| --- | ---: | ---: | ---: | ---: |
| S_to_A | 0 | 0 | -2 | 0 |
| S_to_B | 0 | 1 | 0 | 1 |
| local_AB_vs_BA | -1 | -1 | 1 | 0 |
| final_AB_vs_BA | -1 | -1 | 1 | 0 |
| AB_local_to_final | 0 | 0 | 0 | 0 |
| BA_local_to_final | 0 | 0 | 0 | 0 |

关键解释：

```text
局部 BA 相对 AB：
  num_icmp_delta = -1
  num_select_delta = -1
  num_add_delta = 1

最终 BA 相对 AB：
  num_icmp_delta = -1
  num_select_delta = -1
  num_add_delta = 1
```

这说明“少 1 条 instruction”不是简单少一个 `add`，而是 opcode multiset 发生了组合变化：少了一个 `icmp` 和一个 `select`，多了一个 `add`，净 instruction delta 为 `-1`。

### 报告新增摘要

路径：

```text
data/outputs/effect_attribution_queens/attribution_report.md
```

新增 summary：

```text
FinalOpcodeDeltaNonZero: num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1
```

新增 `Opcode Delta` 段落后，P8c 的 observed attribution hypothesis 更精确：

```text
交换 simplifycfg 与 instcombine 后，局部和最终 IR 都表现为 icmp/select 减少、add 增加，净少 1 条 instruction；
该差异仍然对应 llc 与 clang-c 下更小的 .text。
```

### 关键代码快照

opcode 集合：

```python
OPCODE_NAMES = [
    "icmp",
    "select",
    "getelementptr",
    "bitcast",
    "zext",
    "sext",
    "trunc",
    "unreachable",
    "switch",
    "add",
    "sub",
    "mul",
    "shl",
    "or",
    "and",
]
```

opcode 扫描：

```python
def scan_opcode_multiset(path: str | Path) -> dict[str, int]:
    counts = {f"num_{opcode}": 0 for opcode in OPCODE_NAMES}
    for raw_line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        opcode = _opcode(raw_line)
        key = f"num_{opcode}"
        if key in counts:
            counts[key] += 1
    return counts
```

opcode delta 输出：

```python
def _opcode_delta_rows(
    state_opcodes: Mapping[str, Mapping[str, int]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for comparison, left_name, right_name in _comparison_pairs():
        left = state_opcodes.get(left_name, {})
        right = state_opcodes.get(right_name, {})
        row = {
            "comparison": comparison,
            "left_state": left_name,
            "right_state": right_name,
        }
        for opcode in OPCODE_NAMES:
            key = f"num_{opcode}"
            row[f"{key}_delta"] = str(int(right.get(key, 0)) - int(left.get(key, 0)))
        rows.append(row)
    return rows
```

manifest 输出键：

```python
outputs={
    "output_dir": out,
    "states_csv": out / "states.csv",
    "feature_deltas_csv": out / "feature_deltas.csv",
    "opcode_delta_csv": out / "opcode_delta.csv",
    "object_size_csv": out / "object_size.csv",
    "attribution_report": report,
}
```

### 风险与备注

```text
1. opcode-level attribution 仍然是文本级 IR 统计，不是完整 LLVM IR 语义分析。
2. 这一步解释的是当前 Queens state，不外推到其他程序。
3. `num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1` 是 observation，不是因果定理。
4. 当前仍然没有 runtime benchmark，也没有新增 formal equivalence proof。
5. P8c.1 不是进入更深搜索的理由；它只是让当前稳定 case 的解释更具体。
```

### 下一步

下一步仍然是 P8b benchmark expansion：

```text
1. P8b-0：benchmark_ingest.py，从 E:\llvm-test-suite 自动筛选 8 个小程序，并记录失败原因。
2. P8b-1：新 8 个程序 × 28 pair full matrix，验证 static filter recall。
3. P8b-2：新 8 个程序跑 P4/P5/P6/P8a，看 depth1 both-smaller programs 是否增加。
4. 只有出现更多稳定 smaller programs，再考虑 P8b-3 bounded two-swap。
```
