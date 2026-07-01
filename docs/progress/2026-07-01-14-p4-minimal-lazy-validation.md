# ECPOR 进度记录：P4 minimal lazy validation 与 cache reuse

## 2026-07-01：P4 anchor-adjacent lazy validation

### 当前目标

本轮进入 P4，但仍然不做完整 searcher。目标是建立最小 lazy validation 控制流：

- 对 anchor pipeline 的相邻 pass pair 逐个验证。
- 每个相邻 pair 都在真实 prefix state 上重新扫描 features。
- 对当前 prefix state 先查 certificate cache；命中则复用。
- 静态决策为 `candidate` 时才动态生成 certificate。
- 静态决策为 `low_priority` 时跳过动态测试并冻结默认顺序，但不声明 independent。
- 验证 input-state certificate 不会被错误复用于 prefix-state。

### 已完成内容

- [x] 新增 `src/ecpor/certificate_db.py`：
  - 文件系统 JSON certificate index。
  - lookup key 包含 `state_hash`。
  - lookup 检查 `env_id / execution_model / normalizer_version / nesting / region_id / extra_flags`。
  - lookup 支持 reversed pair。
- [x] 新增 `src/ecpor/state_materializer.py`：
  - materialize prefix pipeline。
  - 空 prefix 直接返回 input state。
  - 非空 prefix 运行 `opt -passes=function(...)`。
  - prefix state 使用 cache key 复用。
- [x] 新增 `src/ecpor/lazy_validator.py`：
  - cache hit 直接返回 certificate。
  - low_priority 只跳过动态测试，不产生 independence claim。
  - candidate 调用 `test_adjacent_swap()` 生成 certificate，并立即 reproduction。
- [x] 新增 `src/ecpor/adjacent_swap_driver.py`：
  - 针对 anchor pipeline 运行相邻 swap validation。
  - 每个 prefix state 重新调用 `scan_ir_file()`。
  - 每个 pair 使用当前 state features 调用 `classify_pair()`。
  - 输出 attempt CSV 和 summary report。
- [x] 新增测试：
  - `tests/test_certificate_db.py`
  - `tests/test_state_materializer.py`
  - `tests/test_lazy_validator.py`
  - `tests/test_adjacent_swap_driver.py`
- [x] 更新 `README.md` 和 `docs/project_progress.md`。

### TDD 验证

RED 测试命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_certificate_db.py tests\test_state_materializer.py tests\test_lazy_validator.py tests\test_adjacent_swap_driver.py -q
```

初始失败符合预期：

```text
10 failed
ModuleNotFoundError: No module named 'ecpor.certificate_db'
ModuleNotFoundError: No module named 'ecpor.state_materializer'
ModuleNotFoundError: No module named 'ecpor.adjacent_swap_driver'
```

实现后 targeted tests：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest tests\test_certificate_db.py tests\test_state_materializer.py tests\test_lazy_validator.py tests\test_adjacent_swap_driver.py -q
```

结果：

```text
11 passed in 2.35s
```

全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
53 passed in 5.73s
```

### P4 真实实验：第一轮

运行命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.adjacent_swap_driver import main; raise SystemExit(main(['--program-preset','stanford-8','--opt','E:/llvm/build/bin/opt.exe','--cert-dir','data/certs/lazy_validation_p4_final','--out','data/outputs/lazy_validation_p4_final','--attempts-csv','data/outputs/lazy_validation_p4_final_first.csv','--report','data/outputs/lazy_validation_p4_final_first.md','--env-id','3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e','--llvm-version','23.0.0git']))"
```

结果：

```text
attempted_adjacent_swaps: 56
candidate_swaps: 48
low_priority_skipped: 8
cache_hits: 0
dynamic_tests: 48
certified_independent: 32
not_certified_independent: 16
run_failed: 0
HardFalseIndependent: 0
CertificateReproductionRate: 100.00%
CertifiedPruningRatioAttempted: 57.14%
CertifiedPruningRatioDynamic: 66.67%
SecondRunCacheHitRate: 0.00%
```

说明：

- 8 个 Stanford 程序 × 7 个 anchor-adjacent pairs = 56 次尝试。
- 其中 48 次被当前 prefix-state static filter 判为 `candidate`，并动态测试。
- 8 次为 `low_priority`，当前 MVP 中跳过并保持原顺序。
- 动态测试生成的 certificate 全部 reproduction 成功。

### P4 真实实验：第二轮 cache reuse

第二轮使用同一个 cert-dir，验证 on-demand certificate reuse：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.adjacent_swap_driver import main; raise SystemExit(main(['--program-preset','stanford-8','--opt','E:/llvm/build/bin/opt.exe','--cert-dir','data/certs/lazy_validation_p4_final','--out','data/outputs/lazy_validation_p4_final','--attempts-csv','data/outputs/lazy_validation_p4_final_second.csv','--report','data/outputs/lazy_validation_p4_final_second.md','--env-id','3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e','--llvm-version','23.0.0git']))"
```

结果：

```text
attempted_adjacent_swaps: 56
candidate_swaps: 48
low_priority_skipped: 8
cache_hits: 48
dynamic_tests: 0
certified_independent: 32
not_certified_independent: 16
run_failed: 0
HardFalseIndependent: 0
CertificateReproductionRate: 100.00%
CertifiedPruningRatioAttempted: 57.14%
CertifiedPruningRatioDynamic: 0.00%
SecondRunCacheHitRate: 100.00%
```

说明：

- 第二轮对同一批 candidate swaps 全部命中 cache。
- 第二轮没有新增 dynamic test。
- `SecondRunCacheHitRate` 的分母是 candidate swaps，不包括 low_priority skipped。

### State-indexing safety 实测

命令：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from ecpor.cert import load_certificate; from ecpor.certificate_db import CertificateDB; from ecpor.state_materializer import materialize_prefix_state; cert=load_certificate('data/certs/pair_tests/testsuite_stanford_bubblesort__instcombine__dce.json'); db=CertificateDB('data/certs/state_index_safety_work'); db.save(cert); input_hit=db.lookup(cert.pass_a, cert.pass_b, cert.input_state_hash, env_id=cert.env_id, execution_model=cert.execution_model, normalizer_version=cert.normalizer_version, nesting=cert.nesting, region_id=cert.region_id, extra_flags=cert.extra_flags); prefix=materialize_prefix_state('data/inputs/testsuite_stanford_bubblesort.ll', ['sroa'], opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/state_index_safety_work', env_id=cert.env_id, nesting=cert.nesting, normalizer_version=cert.normalizer_version, extra_flags=cert.extra_flags); prefix_hit=db.lookup(cert.pass_a, cert.pass_b, prefix.state_hash, env_id=cert.env_id, execution_model=cert.execution_model, normalizer_version=cert.normalizer_version, nesting=cert.nesting, region_id=cert.region_id, extra_flags=cert.extra_flags); print('input_hit', input_hit is not None); print('prefix_hash_differs', prefix.state_hash != cert.input_state_hash); print('prefix_hit', prefix_hit is not None); print('prefix_state_hash', prefix.state_hash)"
```

结果：

```text
input_hit True
prefix_hash_differs True
prefix_hit False
prefix_state_hash ec57bcbca0a602b4feb285724a949257f5d9578c3fee6a745f7f07e84f8e87d3
```

结论：同一个 `instcombine,dce` input-state certificate 可以在 input state 上命中，但不能错误命中 `sroa` 后的 prefix state。

### 本次代码快照：`src/ecpor/certificate_db.py`

```python
class CertificateDB:
    def __init__(self, cert_dir: str | Path):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def save(self, cert: PairCertificate) -> Path:
        path = self.cert_dir / f"{cert.cert_id}.json"
        cert.save(path)
        return path

    def lookup(
        self,
        pass_a: str,
        pass_b: str,
        state_hash: str,
        *,
        env_id: str,
        execution_model: str,
        normalizer_version: str,
        nesting: str,
        region_id: str,
        extra_flags: Sequence[str] = (),
    ) -> PairCertificate | None:
        pair_key = _unordered_pair_key(pass_a, pass_b)
        flags = list(extra_flags)
        for path in sorted(self.cert_dir.rglob("*.json")):
            cert = load_certificate(path)
            if _unordered_pair_key(cert.pass_a, cert.pass_b) != pair_key:
                continue
            if cert.input_state_hash != state_hash:
                continue
            if cert.env_id != env_id:
                continue
            if cert.execution_model != execution_model:
                continue
            if cert.normalizer_version != normalizer_version:
                continue
            if cert.nesting != nesting:
                continue
            if cert.region_id != region_id:
                continue
            if cert.extra_flags != flags:
                continue
            return cert
        return None
```

### 本次代码快照：`src/ecpor/state_materializer.py`

```python
def materialize_prefix_state(
    input_ir: str | Path,
    prefix_passes: Sequence[str],
    *,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    nesting: str = "function",
    normalizer_version: str = NORMALIZER_VERSION,
    extra_flags: Sequence[str] = (),
    timeout_sec: float = 30.0,
) -> MaterializedState:
    input_path = Path(input_ir)
    passes = list(prefix_passes)
    if not passes:
        return MaterializedState(
            path=input_path,
            state_hash=hard_hash(input_path),
            prefix_passes=[],
            pipeline="input",
            run_result=None,
            cache_hit=False,
        )
```

### 本次代码快照：`src/ecpor/lazy_validator.py`

```python
def validate_adjacent_swap(
    state_ll: str | Path,
    pass_a: str,
    pass_b: str,
    *,
    static_decision: str,
    cert_db: CertificateDB,
    opt_path: OptPath,
    output_dir: str | Path,
    env_id: str,
    llvm_version: str,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    normalizer_version: str = NORMALIZER_VERSION,
    nesting: str = "function",
    extra_flags: Sequence[str] = (),
    region_id: str = "function_scalar_mvp",
    timeout_sec: float = 30.0,
) -> LazyValidationResult:
    state_path = Path(state_ll)
    state_hash = hard_hash(state_path)
    cached = cert_db.lookup(
        pass_a,
        pass_b,
        state_hash,
        env_id=env_id,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
        nesting=nesting,
        region_id=region_id,
        extra_flags=extra_flags,
    )
    if cached is not None:
        return LazyValidationResult(..., action="cache_hit", ...)

    if static_decision != "candidate":
        return LazyValidationResult(..., action="skipped_low_priority", ...)

    cert = test_adjacent_swap(...)
    cert_path = cert_db.save(cert)
    reproduction = reproduce_certificate(cert_path, ...)
```

### 本次代码快照：`src/ecpor/adjacent_swap_driver.py`

```python
for index in range(len(passes) - 1):
    prefix = list(passes[:index])
    pass_a = passes[index]
    pass_b = passes[index + 1]
    state = materialize_prefix_state(
        input_ir,
        prefix,
        opt_path=opt_path,
        output_dir=program_root / "prefix_states",
        env_id=env_id,
        nesting=nesting,
        normalizer_version=normalizer_version,
        extra_flags=extra_flags,
        timeout_sec=timeout_sec,
    )
    features = scan_ir_file(state.path)
    decision = classify_pair(
        pass_a,
        pass_b,
        passspec,
        program_features=features,
        distance=1,
        window_size=window_size,
    )
    validation = validate_adjacent_swap(
        state.path,
        pass_a,
        pass_b,
        static_decision=decision["decision"],
        cert_db=cert_db,
        opt_path=opt_path,
        output_dir=program_root / "lazy_validation",
        env_id=env_id,
        llvm_version=llvm_version,
        execution_model=execution_model,
        normalizer_version=normalizer_version,
        nesting=nesting,
        extra_flags=extra_flags,
        region_id=region_id,
        timeout_sec=timeout_sec,
    )
```

### 风险与备注

- 本轮 P4 仍不是完整 searcher，只验证 anchor pipeline 中的相邻 pair。
- `low_priority_skipped` 不是 independence 证明，只表示当前 MVP 不动态测试并保持原顺序。
- `certificate_db.py` 第一版是文件系统扫描；当前规模足够，后续规模变大后再考虑 SQLite 或 manifest index。
- P4 使用 prefix-state features，而不是复用 P3.5 的 per-program decision CSV。
- 本轮 final 实验应在最终提交后复跑，确保新生成 certificate 绑定最终 commit 且 `ecpor_git_dirty = false`。

### 下一步

- 保持 P4 final 两轮实验结果，并在后续提交变更后重新复跑。
- P4 稳定后进入 P5：bounded local reorder exploration。
- 仍暂不做完整 searcher、code size evaluator、Alive2、loop pass、inline、完整 O2/O3。
