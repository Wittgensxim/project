# ECPOR 进度记录：P8c Queens effect attribution

## 2026-07-02：解释当前最稳定的 Queens 顺序交互

### 当前目标

本轮进入 P8c，但仍然不做 depth=3、不做 beam search、不扩大 benchmark。目标是解释当前最稳定的 case：

```text
program: testsuite_stanford_queens
anchor order: instcombine,simplifycfg
winning order: simplifycfg,instcombine
prefix: sroa,early-cse
suffix: reassociate,gvn,dce,adce
```

P8c 只输出 observed attribution hypothesis，不写成跨程序因果证明。

### 已完成内容

- [x] 新增 `src/ecpor/effect_attribution.py`：
  - materialize 7 个 IR state：`S`、`A`、`B`、`AB_local`、`BA_local`、`AB_final`、`BA_final`。
  - 对每个 state 记录 hard hash 和 text-level IR feature。
  - 比较 `local_AB_vs_BA` 与 `final_AB_vs_BA` 的 feature delta。
  - 对 `AB_final` / `BA_final` 同时运行 `llc` 与 `clang -c` object-size measurement。
  - 生成 `attribution_report.md`，回答 5 个归因问题。
- [x] 扩展 `src/ecpor/result_manifest.py`：
  - 新增 `build_queens_effect_attribution_manifest()`。
  - 新增 CLI：`python -m ecpor.result_manifest p8c-attribution ...`
- [x] 新增测试：
  - `tests/test_effect_attribution.py`
  - 更新 `tests/test_result_manifest.py`
- [x] 生成真实输出：
  - `data/outputs/effect_attribution_queens/states.csv`
  - `data/outputs/effect_attribution_queens/feature_deltas.csv`
  - `data/outputs/effect_attribution_queens/object_size.csv`
  - `data/outputs/effect_attribution_queens/attribution_report.md`
- [x] 生成 tracked manifest：
  - `docs/results/queens_effect_attribution_manifest.json`

### TDD 验证

先写 RED tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py::EffectAttributionTests::test_runs_queens_attribution_and_writes_required_outputs
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_p8c_queens_attribution_manifest
```

初始失败符合预期：

```text
ModuleNotFoundError: No module named 'ecpor.effect_attribution'
ImportError: cannot import name 'build_queens_effect_attribution_manifest'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py::EffectAttributionTests::test_runs_queens_attribution_and_writes_required_outputs
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_result_manifest.py::ResultManifestTests::test_builds_p8c_queens_attribution_manifest
```

结果：

```text
1 passed in 0.54s
1 passed in 0.08s
```

相关测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests\test_effect_attribution.py tests\test_result_manifest.py tests\test_object_size_runner.py tests\test_feature_scan.py
```

结果：

```text
15 passed in 1.00s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
90 passed in 11.53s
```

源码提交：

```text
b3dcad808adec8ffc8a163075c3d31b7e2273a8b
add Queens effect attribution
```

### 真实运行命令

生成 P8c attribution 输出：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.effect_attribution --input-ir data\inputs\testsuite_stanford_queens.ll --out data\outputs\effect_attribution_queens --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

生成 tracked manifest：

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p8c-attribution --out-manifest docs\results\queens_effect_attribution_manifest.json --input-ir data\inputs\testsuite_stanford_queens.ll --output-dir data\outputs\effect_attribution_queens --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --clang E:\llvm\build\bin\clang.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --repo-root . --result-generated-from-commit b3dcad808adec8ffc8a163075c3d31b7e2273a8b
```

manifest provenance：

```text
stage: P8c
result_generated_from_commit: b3dcad808adec8ffc8a163075c3d31b7e2273a8b
ecpor_git_commit: b3dcad808adec8ffc8a163075c3d31b7e2273a8b
ecpor_git_dirty: False
```

### State feature 结果

路径：

```text
data/outputs/effect_attribution_queens/states.csv
```

核心表：

| state | instructions | basic blocks | branches | calls |
| --- | ---: | ---: | ---: | ---: |
| S | 154 | 6 | 34 | 6 |
| A | 154 | 6 | 34 | 6 |
| B | 141 | 6 | 27 | 6 |
| AB_local | 141 | 6 | 27 | 6 |
| BA_local | 140 | 6 | 27 | 6 |
| AB_final | 143 | 6 | 27 | 6 |
| BA_final | 142 | 6 | 27 | 6 |

解释：

```text
S 是 prefix 后 state。
A = instcombine(S)。
B = simplifycfg(S)。
AB_local = instcombine;simplifycfg(S)。
BA_local = simplifycfg;instcombine(S)。
AB_final / BA_final 是分别加上 suffix 后的最终 pipeline 输出。
```

### Feature delta 结果

路径：

```text
data/outputs/effect_attribution_queens/feature_deltas.csv
```

关键比较：

| comparison | hard hash equal | num instructions delta | num branch delta | num call delta |
| --- | --- | ---: | ---: | ---: |
| local_AB_vs_BA | False | -1 | 0 | 0 |
| final_AB_vs_BA | False | -1 | 0 | 0 |
| AB_local_to_final | False | 2 | 0 | 0 |
| BA_local_to_final | False | 2 | 0 | 0 |

解释：

```text
局部 pair 后 AB 与 BA 已经 hard hash 不同。
局部 BA 比 AB 少 1 条 instruction。
加上 suffix 后，最终 BA 仍比 AB 少 1 条 instruction。
因此当前最直接的 feature-level 观察是：instruction delta 在 suffix 后保持。
```

### Object-size 结果

路径：

```text
data/outputs/effect_attribution_queens/object_size.csv
```

核心表：

| mode | state | text | anchor text | delta | delta pct | direction |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| llc | AB_final | 727 | 727 | 0 | 0.000000 | equal |
| llc | BA_final | 695 | 727 | -32 | -4.401651 | smaller |
| clang | AB_final | 956 | 956 | 0 | 0.000000 | equal |
| clang | BA_final | 940 | 956 | -16 | -1.673640 | smaller |

解释：

```text
BA_final 在 llc 与 clang-c 两条 codegen path 下都保持 smaller。
这说明 Queens 的这个收益不是 llc-only 假象。
```

### P8c 报告回答的 5 个问题

路径：

```text
data/outputs/effect_attribution_queens/attribution_report.md
```

答案摘要：

```text
1. AB 和 BA 在局部 pair 后是否已经 hard hash 不同？
   是，LocalABBAHardHashEqual = False。

2. 局部 AB/BA 的 feature delta 是什么？
   num_instructions_delta = -1。

3. 加上 suffix 后，最终 feature delta 是否扩大、缩小或保持？
   FeatureDeltaPropagation = kept，FinalInstructionDelta = -1。

4. llc 和 clang-c 下的 .text delta 是否仍然都是 smaller？
   是，BothCodegenSmaller = True。

5. observed attribution hypothesis 是什么？
   在 Queens 的 prefix state 上，交换 simplifycfg 与 instcombine 已经产生局部 IR 差异；
   该差异在 suffix 后仍然可见，并且 BA_final 在 llc 与 clang-c 下都对应更小的 .text。
   这支持一个观察性假设：该顺序改变了 CFG/scalar cleanup 机会，进而影响目标层 code size。
```

### 关键代码快照

P8c 固定 case 定义：

```python
PROGRAM = "testsuite_stanford_queens"
DEFAULT_PREFIX = ("sroa", "early-cse")
DEFAULT_PASS_A = "instcombine"
DEFAULT_PASS_B = "simplifycfg"
DEFAULT_SUFFIX = ("reassociate", "gvn", "dce", "adce")
```

7 个 state 的生成逻辑：

```python
def _state_definitions(
    prefix: Sequence[str], pass_a: str, pass_b: str, suffix: Sequence[str]
) -> dict[str, list[str]]:
    base = list(prefix)
    return {
        "S": base,
        "A": [*base, pass_a],
        "B": [*base, pass_b],
        "AB_local": [*base, pass_a, pass_b],
        "BA_local": [*base, pass_b, pass_a],
        "AB_final": [*base, pass_a, pass_b, *suffix],
        "BA_final": [*base, pass_b, pass_a, *suffix],
    }
```

object-size 比较只对最终 pipeline 做：

```python
final_states = [
    row for row in state_rows if row["state_name"] in {"AB_final", "BA_final"}
]
for mode, compiler, compile_mode in [
    ("llc", llc_path, "llc"),
    ("clang", clang_path, "clang"),
]:
    for state in final_states:
        state_name = state["state_name"]
        object_path = object_root / f"{mode}__{state_name}.o"
        record = measure_object_size(
            program=program,
            candidate_id=f"{program}__{state_name}__{mode}",
            ir_path=state["ir_path"],
            object_path=object_path,
            compiler_path=compiler if compile_mode == "clang" else None,
            llc_path=compiler,
            llvm_size_path=llvm_size_path,
            timeout_sec=timeout_sec,
            compile_mode=compile_mode,
        )
```

P8c manifest：

```python
def build_queens_effect_attribution_manifest(
    *,
    input_ir: str | Path,
    output_dir: str | Path,
    opt_path: str | Path,
    llc_path: str | Path,
    clang_path: str | Path,
    llvm_size_path: str | Path,
    repo_root: str | Path = ".",
    result_generated_from_commit: str | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    report = out / "attribution_report.md"
    return build_result_manifest(
        stage="P8c",
        description="Queens instcombine/simplifycfg observed effect attribution.",
        inputs={"input_ir": input_ir},
        outputs={
            "output_dir": out,
            "states_csv": out / "states.csv",
            "feature_deltas_csv": out / "feature_deltas.csv",
            "object_size_csv": out / "object_size.csv",
            "attribution_report": report,
        },
        tools={
            "opt": opt_path,
            "llc": llc_path,
            "clang": clang_path,
            "llvm_size": llvm_size_path,
        },
        summary=_filter_keys(
            _parse_key_value_report(report),
            P8C_ATTRIBUTION_SUMMARY_KEYS,
        ),
        repo_root=repo_root,
        result_generated_from_commit=result_generated_from_commit,
        extra={
            "scope_limits": {
                "single_program": "testsuite_stanford_queens",
                "runtime_benchmarks": False,
                "new_certificates": False,
                "new_search": False,
                "observed_attribution_not_causal_proof": True,
            }
        },
    )
```

### 风险与备注

```text
1. P8c 是单程序、单 state、单 pair 的 observed attribution，不是普遍性证明。
2. 本轮没有新增 certificate，也没有扩大搜索空间。
3. `FeatureDeltaPropagation = kept` 只说明当前 text-level feature 的 instruction delta 在 suffix 后保持，不说明所有语义差异都被解释完。
4. object-size 仍然只是 `.text` 静态大小，不是 runtime benchmark。
5. 当前结论可以支撑下一步 benchmark expansion，但不能支撑 depth=3 或 beam search 的必要性。
```

### 下一步

P8c 完成后，下一步建议进入 P8b benchmark expansion，而不是加深搜索：

```text
P8b-1: 新 8 个小程序 × 28 pair full matrix，验证 static filter recall。
P8b-2: 新 8 个小程序跑 P4/P5/P6/P8a，观察 depth1 smaller programs 是否增加。
P8b-3: 只有当 P8b-2 出现更多 smaller programs 时，再跑 P7b two-swap。
```
