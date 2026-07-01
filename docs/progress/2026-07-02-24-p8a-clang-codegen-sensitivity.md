# ECPOR 进度记录：P8a clang-c codegen sensitivity

## 2026-07-02：先验证 codegen 路径敏感性

### 当前目标

本轮不进入 depth=3，也不做完整 searcher。目标是先回答一个更基础的问题：

```text
P6/P7b 中基于 llc -filetype=obj 得到的 .text size 方向，
在 clang -c 路径下是否仍然一致？
```

同时做一个 P7b.5 收尾：

```text
1. 把 P7b.5 cache audit key 扩展到 env / execution_model / normalizer / nesting / region / extra_flags。
2. 在 P7b.5 报告中明确 Depth2SmallerFromSameParent。
3. 对 P6 的 8 anchor + 16 single-swap，以及 P7b 的 22 depth2 candidate 做 clang -c object-size 对照。
4. 生成 P8a tracked manifest。
```

### 已完成内容

- [x] 扩展 `src/ecpor/object_size_runner.py`：
  - `measure_object_size(..., compile_mode="llc" | "clang")`
  - `clang` 模式使用 `clang -x ir -c input.ll -o output.o`
- [x] 扩展 `src/ecpor/two_swap_analysis.py`：
  - cache audit key 从 `(state_hash, unordered_pair)` 扩展为：
    `state_hash + unordered_pair + env_id + execution_model + normalizer_version + nesting + region_id + extra_flags`
  - `p7b_cache_audit.csv` 新增上述 scope 字段。
  - 报告新增 `Depth2SmallerFromSameParent`。
- [x] 新增 `src/ecpor/codegen_sensitivity.py`：
  - 读取 P6/P7b 已保存 object-size CSV 和 IR 路径。
  - 对 46 个 IR 运行 `clang -c` + `llvm-size`。
  - 输出 clang object-size 表和 llc/clang 方向对照表。
- [x] 扩展 `src/ecpor/result_manifest.py`：
  - 新增 `build_p8a_codegen_sensitivity_manifest()`。
  - 新增 CLI：`python -m ecpor.result_manifest p8a-codegen ...`
  - P7b.5 manifest 白名单新增 `Depth2SmallerFromSameParent`。
- [x] 新增/更新测试：
  - `tests/test_object_size_runner.py`
  - `tests/test_two_swap_analysis.py`
  - `tests/test_codegen_sensitivity.py`
  - `tests/test_result_manifest.py`
- [x] 生成真实 P8a 输出：
  - `data/outputs/codegen_sensitivity_p8a/p8a_clang_object_size.csv`
  - `data/outputs/codegen_sensitivity_p8a/p8a_codegen_direction_compare.csv`
  - `data/outputs/codegen_sensitivity_p8a/p8a_codegen_sensitivity_report.md`
- [x] 生成 tracked manifest：
  - `docs/results/p8a_codegen_sensitivity_manifest.json`
- [x] 刷新 P7b.5 manifest：
  - `docs/results/p7b_analysis_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_object_size_runner.py::ObjectSizeRunnerTests::test_compile_mode_clang_uses_clang_ir_compile_command tests\test_two_swap_analysis.py::TwoSwapAnalysisTests::test_cache_audit_key_includes_environment_scope_when_available tests\test_codegen_sensitivity.py::CodegenSensitivityTests::test_compares_llc_and_clang_directions_for_p6_and_p7b_candidates
```

初始失败符合预期：

```text
TypeError: measure_object_size() got an unexpected keyword argument 'compile_mode'
KeyError: 'env_id'
ModuleNotFoundError: No module named 'ecpor.codegen_sensitivity'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_object_size_runner.py tests\test_two_swap_analysis.py tests\test_codegen_sensitivity.py tests\test_result_manifest.py
```

结果：

```text
12 passed in 0.85s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
85 passed in 13.81s
```

源码提交：

```text
3fa87e171ec9f14e622a052e1c0e75bacb6e9488
add P8a clang codegen sensitivity

73f3d19600dd8df0cda6481c7b0aca32d60560d7
refresh P7b analysis manifest
```

### P7b.5 收尾命令

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.two_swap_analysis --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --out data\outputs\bounded_two_swap_p7b_analysis
```

新增报告指标：

```text
Depth2SmallerText: 3
Depth2SmallerPrograms: 1
Depth2SmallerFromSameParent: 3
Depth2ImprovesProgramDepth1Best: 0
Depth2ImprovesGlobalDepth1Best: 0
```

解释：

```text
3 个 smaller depth2 全部来自同一个 queens depth1 parent。
这进一步降低了误读风险：two-swap 增加了 smaller variant 数量，
但没有扩大受益 program 数量，也没有超过 depth1 best。
```

### P8a 真实运行命令

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.codegen_sensitivity --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --out data\outputs\codegen_sensitivity_p8a --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

运行范围：

```text
Programs: 8
IRInputs: 46
AnchorInputs: 8
SingleSwapInputs: 16
Depth2Inputs: 22
ClangObjectBuildsAttempted: 46
ClangObjectBuildFailed: 0
ClangSizeParseFailed: 0
```

manifest 命令：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p8a-codegen --out-manifest docs\results\p8a_codegen_sensitivity_manifest.json --p6-object-size data\outputs\code_size_p6_final\object_size.csv --p7-object-size data\outputs\bounded_two_swap_p7b\two_swap_object_size.csv --output-dir data\outputs\codegen_sensitivity_p8a --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --repo-root . --result-generated-from-commit 73f3d19600dd8df0cda6481c7b0aca32d60560d7
```

manifest 关键 provenance：

```text
ecpor_git_commit: 73f3d19600dd8df0cda6481c7b0aca32d60560d7
ecpor_git_dirty: False
clang_sha256: 7813948a1b853beb1806fd1bb28b09917bcbd9e35d67b43345af02c100b93551
llvm_size_sha256: f425ef87d64380ff5f8fd055ddb52e1f0d38f3031bb2a5bbddd557d71c5bc589
```

### P8a 输出表含义

`p8a_clang_object_size.csv`：

| 字段 | 含义 |
| --- | --- |
| `program` | benchmark 程序名 |
| `candidate_id` | anchor / single-swap / depth2 candidate 标识 |
| `depth` | `0` anchor，`1` single-swap，`2` two-swap |
| `source` | `anchor` / `single_swap` / `two_swap` |
| `compile_mode` | 本表固定为 `clang` |
| `text_size` | clang -c object 的 `.text` size |
| `anchor_text_size` | 同 program anchor 在 clang -c 下的 `.text` size |
| `text_delta_pct` | clang -c 下相对 anchor 的 `.text` 百分比变化 |
| `direction` | clang -c 下的 `smaller` / `equal` / `larger` |
| `llc_*` | 原 P6/P7b llc 路径下的对应 size/delta/direction |

`p8a_codegen_direction_compare.csv`：

| 字段 | 含义 |
| --- | --- |
| `llc_direction` | `llc -filetype=obj` 下相对 anchor 的方向 |
| `clang_direction` | `clang -c` 下相对 anchor 的方向 |
| `direction_agree` | 两条 codegen 路径方向是否一致 |

### P8a 关键结果

方向对照结果：

```text
DirectionComparisonCandidates: 38
DirectionAgreementCount: 26
DirectionAgreementRate: 68.42%
SmallerUnderBothCount: 4
SmallerOnlyUnderLlcCount: 0
SmallerOnlyUnderClangCount: 5
DirectionDisagreementCount: 12
```

按方向分布：

```text
equal -> equal: 19
equal -> larger: 7
equal -> smaller: 5
smaller -> smaller: 4
larger -> larger: 3
```

解释：

```text
P8a 说明 code-size 方向存在 codegen-path sensitivity：
llc 下 equal 的 candidate，在 clang -c 下可能变 smaller 或 larger。

但当前最关键的 queens smaller 结论没有消失：
llc 下 smaller 的 4 个 candidate，在 clang -c 下仍然全部 smaller。
```

### Queens 关键 candidate

| source | candidate | llc direction | clang direction | llc Δtext pct | clang Δtext pct |
| --- | --- | --- | --- | ---: | ---: |
| single_swap | `testsuite_stanford_queens__swap_2__instcombine__simplifycfg` | smaller | smaller | `-4.401651` | `-1.673640` |
| two_swap | `...__swap_0__sroa__early-cse` | smaller | smaller | `-4.401651` | `-1.673640` |
| two_swap | `...__swap_3__instcombine__reassociate` | smaller | smaller | `-4.401651` | `-1.673640` |
| two_swap | `...__swap_4__reassociate__gvn` | smaller | smaller | `-2.200825` | `-1.673640` |

这意味着：

```text
Queens 的 smaller-text observation 不是 llc-only 假象。
但是 broader candidate distribution 对 codegen 路径敏感，
所以后续论文/报告不能只写 “code size improved”，要限定 codegen path。
```

### 关键代码快照

`object_size_runner.py` 中的 compile mode：

```python
def _run_compile(
    ir_path: Path,
    object_path: Path,
    llc_path: ToolPath,
    timeout_sec: float,
    compile_mode: CompileMode,
) -> _CommandResult:
    if compile_mode == "clang":
        command = [
            *_normalize_tool_path(llc_path),
            "-x",
            "ir",
            "-c",
            str(ir_path),
            "-o",
            str(object_path),
        ]
    else:
        command = [
            *_normalize_tool_path(llc_path),
            str(ir_path),
            "-filetype=obj",
            "-o",
            str(object_path),
        ]
    return _run_command(command, timeout_sec)
```

`two_swap_analysis.py` 中的 cache audit key：

```python
key = (
    attempt.get("state_hash", ""),
    _pair_key(attempt.get("pass_a", ""), attempt.get("pass_b", "")),
    attempt.get("env_id", ""),
    attempt.get("execution_model", ""),
    attempt.get("normalizer_version", ""),
    attempt.get("nesting", ""),
    attempt.get("region_id", ""),
    attempt.get("extra_flags", ""),
)
```

`codegen_sensitivity.py` 中的输入选择：

```python
def _select_input_rows(
    p6_rows: Sequence[dict[str, str]],
    p7_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in p6_rows:
        if row.get("source") not in {"anchor", "single_swap"}:
            continue
        if row.get("candidate_id", "") in seen:
            continue
        selected.append(row)
        seen.add(row.get("candidate_id", ""))
    anchor_programs = {row.get("program", "") for row in selected if row.get("source") == "anchor"}
    for row in p7_rows:
        if row.get("source") == "anchor" and row.get("program", "") not in anchor_programs:
            selected.append(row)
            seen.add(row.get("candidate_id", ""))
            anchor_programs.add(row.get("program", ""))
    for row in p7_rows:
        if row.get("source") != "two_swap":
            continue
        if row.get("candidate_id", "") in seen:
            continue
        selected.append(row)
        seen.add(row.get("candidate_id", ""))
    return selected
```

`codegen_sensitivity.py` 中的核心指标：

```python
return {
    "DirectionComparisonCandidates": len(compare_rows),
    "DirectionAgreementCount": agreement,
    "DirectionAgreementRate": agreement / len(compare_rows) if compare_rows else 0.0,
    "SmallerUnderBothCount": sum(
        1
        for row in compare_rows
        if row["llc_direction"] == "smaller"
        and row["clang_direction"] == "smaller"
    ),
    "SmallerOnlyUnderLlcCount": sum(
        1
        for row in compare_rows
        if row["llc_direction"] == "smaller"
        and row["clang_direction"] != "smaller"
    ),
    "SmallerOnlyUnderClangCount": sum(
        1
        for row in compare_rows
        if row["llc_direction"] != "smaller"
        and row["clang_direction"] == "smaller"
    ),
}
```

`result_manifest.py` 中的 P8a manifest：

```python
def build_p8a_codegen_sensitivity_manifest(
    *,
    p6_object_size_csv: str | Path,
    p7_object_size_csv: str | Path,
    output_dir: str | Path,
    clang_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "p8a_codegen_sensitivity_report.md"
    return build_result_manifest(
        stage="P8a",
        description="Clang -c codegen sensitivity check for P6/P7b saved IR outputs.",
        inputs={
            "p6_object_size_csv": p6_object_size_csv,
            "p7_object_size_csv": p7_object_size_csv,
        },
        outputs={
            "output_dir": out,
            "p8a_clang_object_size_csv": out / "p8a_clang_object_size.csv",
            "p8a_codegen_direction_compare_csv": out / "p8a_codegen_direction_compare.csv",
            "p8a_codegen_sensitivity_report": report,
        },
        tools={
            "clang": clang_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8A_CODEGEN_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
    )
```

### 风险与备注

```text
1. P8a 仍然不是 runtime benchmark，只是 object .text size 对照。
2. P8a 没有新增 certificate，也没有重新跑 opt pipeline；它使用已有 IR 输出。
3. DirectionAgreementRate = 68.42% 说明 codegen path 会影响大量 equal candidate 的方向。
4. SmallerOnlyUnderLlcCount = 0 是好信号：本轮没有发现 llc-smaller 在 clang 下消失。
5. Queens 仍然是唯一已知 llc+clang 都 smaller 的程序；不能据此声称普遍优化。
```

### 下一步

建议进入 P8b benchmark expansion，而不是 depth=3：

```text
1. 从 E:\llvm-test-suite 选 8 个小程序。
2. 仍使用当前 8-pass scalar function pipeline。
3. 先跑 P4/P5/P6/P7b/P7b.5/P8a 的同口径最小扩展。
4. 观察 Depth1/Depth2SmallerPrograms 是否从 Stanford-8 的 1 个程序扩展到更多程序。
```
