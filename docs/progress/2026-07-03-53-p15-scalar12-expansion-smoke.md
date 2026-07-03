# P15 scalar12 expansion protocol / candidate smoke

## 当前目标

P14.5 证明了 program-local graph 仍有分解信号，但它也说明不能直接扩大到很多 pass，更不能马上引入 loop / module / inline / vectorization。P15 的目标是先做一个受控的 pass expansion protocol：

```text
从 P11 registry snapshot 中选择 function-level scalar / cleanup 候选；
对每个候选运行 single-pass function(candidate) smoke；
只选择 4 个稳定候选，形成 scalar12 配置；
不新增 certificate，不启动 search，不运行 runtime benchmark。
```

本阶段的产物是为 P16 做准备，而不是声称 scalar12 已经完成 full matrix 或 depth1 chain。

## 完成内容

新增配置：

```text
configs/pass_expansion_candidates.yaml
configs/pipeline_scalar12.yaml
configs/passspec_scalar12.yaml
```

新增代码与测试：

```text
src/ecpor/pass_expansion_smoke.py
tests/test_pass_expansion_smoke.py
src/ecpor/manifest_builders.py
src/ecpor/manifest_cli.py
tests/test_result_manifest.py
```

新增保留输出与 manifest：

```text
data/outputs/pass_expansion_smoke/pass_expansion_smoke.csv
data/outputs/pass_expansion_smoke/pass_expansion_smoke_report.md
docs/results/pass_expansion_smoke_manifest.json
```

`data/outputs/pass_expansion_smoke/pass_outputs/` 是临时 IR 输出目录，默认在 smoke 结束后清理，不保留。

## 候选 pass

第一版 P15 候选只包含 function-level scalar / cleanup 类 pass：

```yaml
stage: P15
source_registry_snapshot: data/outputs/pass_registry_snapshot/pass_registry_snapshot.json
selection_goal: scalar12
constraints:
  - function_level_only
  - no_loop_passes
  - no_module_passes
  - no_inline_passes
  - no_vectorization_passes
  - no_backend_passes
candidates:
  - name: instsimplify
    expected_level: function
    reason: scalar_simplification_candidate
    source: pass_registry_snapshot
  - name: bdce
    expected_level: function
    reason: scalar_cleanup_candidate
    source: pass_registry_snapshot
  - name: sccp
    expected_level: function
    reason: scalar_constant_propagation_candidate
    source: pass_registry_snapshot
  - name: correlated-propagation
    expected_level: function
    reason: scalar_branch_value_candidate
    source: pass_registry_snapshot
  - name: jump-threading
    expected_level: function
    reason: scalar_cfg_candidate
    source: pass_registry_snapshot
  - name: dse
    expected_level: function
    reason: memory_cleanup_candidate
    source: pass_registry_snapshot
  - name: sink
    expected_level: function
    reason: scalar_motion_candidate
    source: pass_registry_snapshot
  - name: memcpyopt
    expected_level: function
    reason: memory_cleanup_candidate
    source: pass_registry_snapshot
```

## 真实运行命令

使用 dlm Python 环境运行 smoke：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.pass_expansion_smoke
```

生成 manifest：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest pass-expansion-smoke `
  --out-manifest docs\results\pass_expansion_smoke_manifest.json `
  --candidate-config configs\pass_expansion_candidates.yaml `
  --registry-snapshot data\outputs\pass_registry_snapshot\pass_registry_snapshot.json `
  --baseline-pipeline configs\pipeline_scalar.yaml `
  --baseline-passspec configs\passspec.yaml `
  --scalar12-pipeline configs\pipeline_scalar12.yaml `
  --scalar12-passspec configs\passspec_scalar12.yaml `
  --output-dir data\outputs\pass_expansion_smoke `
  --repo-root . `
  --result-generated-from-commit dae69145fed1ebea743d3e3603664b6994efe628
```

做了一次 scalar12 static filter 兼容性 smoke，确认新配置可被现有静态过滤入口读取：

```powershell
$env:PYTHONPATH='src'
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter `
  --pipeline configs\pipeline_scalar12.yaml `
  --passspec configs\passspec_scalar12.yaml `
  --benchmark-config configs\benchmarks_diverse8.yaml `
  --mode per-program `
  --out-csv data\outputs\pass_expansion_smoke\scalar12_static_smoke_decisions.csv `
  --out-report data\outputs\pass_expansion_smoke\scalar12_static_smoke_report.md
```

该 static filter smoke 输出为临时验证产物，验证后已删除，只保留 pass expansion smoke 的 CSV / report。

## 结果

P15 smoke report 的核心值：

```text
CandidatePasses: 8
RegistryPresentCandidates: 8
Programs: 24
ProgramsAttempted: 192
SelectedNewPasses: 4
RunFailedCandidates: 0
TimeoutCandidates: 0
VerifierFailedCandidates: 0
ChangedIrCandidates: 8
Scalar12PassCount: 12
NewExperiments: True
NewCertificates: False
NewSearch: False
SelectedForScalar12: instsimplify,bdce,sccp,correlated-propagation
```

候选明细：

| pass | attempted | run_failed | verifier_failed | changed_ir | selected | rejection |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| instsimplify | 24 | 0 | 0 | 24 | True |  |
| bdce | 24 | 0 | 0 | 24 | True |  |
| sccp | 24 | 0 | 0 | 24 | True |  |
| correlated-propagation | 24 | 0 | 0 | 24 | True |  |
| jump-threading | 24 | 0 | 0 | 24 | False | selection_limit |
| dse | 24 | 0 | 0 | 24 | False | selection_limit |
| sink | 24 | 0 | 0 | 24 | False | selection_limit |
| memcpyopt | 24 | 0 | 0 | 24 | False | selection_limit |

解释：

```text
8 个候选都在当前 LLVM registry snapshot 中存在；
8 个候选都能在 24 个 retained program 上完成 function(candidate) smoke；
没有 run_failed、timeout、verifier_failed 或 output_missing；
8 个候选都产生 changed IR；
P15 按协议只选前 4 个，避免一次扩展过大。
```

## scalar12 配置

生成的新 pipeline：

```yaml
name: scalar12_function_scalar
pipeline: function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce,instsimplify,bdce,sccp,correlated-propagation)
passes:
- sroa
- early-cse
- instcombine
- simplifycfg
- reassociate
- gvn
- dce
- adce
- instsimplify
- bdce
- sccp
- correlated-propagation
source_pipeline: configs/pipeline_scalar.yaml
created_in_stage: P15
```

`configs/passspec_scalar12.yaml` 没有覆盖旧 `configs/passspec.yaml`，而是复制旧 schema 后为 4 个新 pass 增加低置信度、可审计的 generated entry。例如：

```yaml
instsimplify:
  level: function
  requires_any:
  - instruction
  may_consume:
  - scalar_value
  - instruction
  may_produce:
  - scalar12_candidate_effect:
      source: generated_registry
      confidence: low
      created_in_stage: P15
      support:
      - pass: instsimplify
        evidence: single_pass_smoke
      note: Generated by P15 pass expansion smoke; not an LLVM semantic claim.
  tags:
  - scalar12_candidate
```

## 代码快照

候选配置读取：

```python
@dataclass(frozen=True)
class PassExpansionCandidate:
    name: str
    expected_level: str
    reason: str
    source: str
    manual_note: str = ""


def load_expansion_candidates(path: str | Path) -> list[PassExpansionCandidate]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError(f"candidate config must contain list 'candidates': {path}")
    loaded: list[PassExpansionCandidate] = []
    for item in candidates:
        if not isinstance(item, Mapping):
            raise ValueError(f"candidate entry must be a mapping: {path}")
        loaded.append(
            PassExpansionCandidate(
                name=str(item.get("name", "")).strip(),
                expected_level=str(item.get("expected_level", "")).strip(),
                reason=str(item.get("reason", "")).strip(),
                source=str(item.get("source", "")).strip(),
                manual_note=str(item.get("manual_note", "")).strip(),
            )
        )
    if any(not candidate.name for candidate in loaded):
        raise ValueError(f"candidate entry missing name: {path}")
    return loaded
```

smoke 构建的 scope 边界：

```python
return {
    "stage": "P15",
    "scope": {
        "pass_expansion_protocol_only": True,
        "new_experiments": True,
        "new_certificates": False,
        "new_search": False,
        "runtime_benchmarks": False,
        "loop_passes": False,
        "module_passes": False,
        "inline_passes": False,
    },
    "smoke_rows": rows,
    "summary": summary,
}
```

单 pass smoke 的核心路径：

```python
def _run_candidate_smoke(
    *,
    candidate: PassExpansionCandidate,
    programs: Sequence[Program],
    runner: Runner,
    opt_path: OptPath,
    output_dir: Path,
    timeout_sec: float,
) -> dict[str, Any]:
    attempts = 0
    run_failed = 0
    timed_out = 0
    verifier_failed = 0
    output_missing = 0
    changed = 0
    noop = 0
    elapsed: list[float] = []
    for program, input_path in programs:
        attempts += 1
        pipeline = f"function({candidate.name})"
        output_path = output_dir / candidate.name / f"{_safe_name(program)}.ll"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        input_hash = hard_hash(input_path)
        result = runner(
            input_path,
            pipeline,
            output_path,
            opt_path=opt_path,
            timeout_sec=timeout_sec,
        )
```

结果输出时默认清理临时 pass outputs：

```python
smoke_csv = out / SMOKE_CSV_NAME
report = out / REPORT_NAME
_write_csv(smoke_csv, SMOKE_FIELDS, analysis["smoke_rows"])
report.write_text(render_report(analysis), encoding="utf-8")
if not keep_pass_outputs and pass_output_dir.exists():
    shutil.rmtree(pass_output_dir)
return {"smoke_csv": smoke_csv, "report": report}
```

manifest 记录 P15 的边界，防止后续把它误读成 certificate 或 search 结果：

```python
"scope_limits": {
    "stage": "P15",
    "summary_only": True,
    "pass_expansion_protocol_only": True,
    "single_pass_smoke_only": True,
    "new_experiments": True,
    "new_certificates": False,
    "new_search": False,
    "runtime_benchmarks": False,
    "loop_passes": False,
    "module_passes": False,
    "inline_passes": False,
    "baseline_scalar8_configs_unchanged": True,
}
```

## 测试与验证

本轮已完成的验证：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_pass_expansion_smoke.py tests/test_result_manifest.py::ResultManifestTests::test_result_manifest_split_modules_keep_compatibility_exports tests/test_result_manifest.py::ResultManifestTests::test_builds_pass_expansion_smoke_manifest -q
```

结果：

```text
4 passed in 0.12s
```

P15 代码提交前后均跑过全量测试：

```text
166 passed in 23.27s
166 passed in 22.82s
```

最终收尾验证：

```text
166 passed in 22.81s
```

## 风险与备注

1. P15 的 `changed_ir_count > 0` 只说明 pass 在当前 24 个输入上不是全 noop，不说明它一定带来 objective benefit。
2. `passspec_scalar12.yaml` 中的新 pass metadata 是 generated / low-confidence，不是 LLVM 官方语义声明。
3. `jump-threading`、`dse`、`sink`、`memcpyopt` 也通过 smoke，但由于 P15 限制只选 4 个，没有进入 scalar12。
4. 旧 scalar8 配置保持不变；后续实验必须显式选择 `pipeline_scalar12.yaml` 和 `passspec_scalar12.yaml`。
5. P15 没有生成 pair certificate；P16 才能讨论 `12 * 11 / 2 = 66` 个 unordered pair 的 full matrix。

## 下一步

进入 P16，但仍然保持受控：

```text
P16a: scalar12 full matrix
  24 programs x 66 unordered pairs = 1584 certificates

P16b: scalar12 per-program reduced components
  对比 scalar8 vs scalar12 的 program-local component 变化

P16c: scalar12 depth1-only chain
  只跑 prefix-state lazy validation、one-swap、object size、clang-c sensitivity
```

仍然不要做：

```text
two-swap
depth=3
beam search
runtime benchmark
Alive2
loop / module / inline pass
完整 O2/O3 pipeline
```
