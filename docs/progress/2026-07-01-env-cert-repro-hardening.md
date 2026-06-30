# ECPOR 进度记录：加强环境指纹、证书唯一性和复现闭环

## 2026-07-01：加强环境指纹、证书唯一性和复现闭环

### 当前目标

根据最新 review，把当前 P1 certificate 闭环从“能跑通”推进到“更可复现、更不易覆盖、更适合后续批量实验”的状态。优先处理 `env_id`、`cert_id`、输出目录、CLI、reproduction test 和 git 边界。

### 已完成内容

- [x] 将测试和运行环境统一保持为 `D:\Miniconda\envs\dlm\python.exe`。
- [x] 新增 `file_sha256()`，并把 `opt.exe`、`clang.exe`、`llvm-size.exe`、`llvm-config.exe` 的 SHA-256 纳入 `LLVMEnvironment`。
- [x] 将 LLVM build 信息纳入环境记录：`CMAKE_BUILD_TYPE=Release`、`LLVM_ENABLE_ASSERTIONS=OFF`、`CMakeCache.txt` hash。
- [x] 更新 `configs/env.yaml`，新的 `env_id` 为 `3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e`。
- [x] 扩展 `PairCertificate` schema，新增 `input_ir_path`、`nesting`、`pipeline_ab`、`pipeline_ba`、`extra_flags`、pass instance、`region_id`、`ecpor_git_commit`、`ecpor_git_dirty`。
- [x] 扩展 `make_cert_id()`，使证书 ID 对 `nesting`、AB/BA pipeline、`extra_flags`、pass instance 和 region 敏感。
- [x] 将 pair-test 输出目录改为 `data/outputs/pair_tests/<cert_id>/ab.ll` 和 `ba.ll`，并同步写入 `input_hash.txt`、`stdout_*.txt`、`stderr_*.txt`、`cert.json`。
- [x] 增加 `reproduce_certificate()`，可以读取已保存 certificate，复跑 AB/BA，并比较 label 与 hard hash。
- [x] 增加 `python -m ecpor.pair_test` CLI，支持生成 JSON certificate。
- [x] 新增 `.gitignore`，排除 pycache、pytest cache、生成的 outputs/certs 和临时产物。
- [x] 更新 `README.md`，加入 pair-test certificate 和 reproduction 命令。

### 验证结果

单元测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
20 passed in 1.19s
```

真实 LLVM certificate 生成：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.pair_test import test_adjacent_swap; cert=test_adjacent_swap('data/inputs/testsuite_stanford_bubblesort.ll','instcombine','dce',opt_path='E:/llvm/build/bin/opt.exe',output_dir='data/outputs/pair_tests',env_id='3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e',llvm_version='23.0.0git'); cert.save('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json'); print(cert.cert_id, cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba, cert.output_ab, cert.output_ba)"
```

结果：

```text
e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954 certified_independent True 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ab.ll data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ba.ll
```

真实 LLVM certificate reproduction：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0,'src'); from ecpor.pair_test import reproduce_certificate; r=reproduce_certificate('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json', opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests/repro'); print(r.reproduced, r.original_label, r.reproduced_label, r.original_hash_ab, r.reproduced_hash_ab, r.original_hash_ba, r.reproduced_hash_ba, r.reason)"
```

结果：

```text
True certified_independent certified_independent 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 label and hashes match
```

### 风险与备注

- `E:/llvm` 当前没有可读出的 git commit，因此 `llvm_source_git_commit` 仍为 `unknown`，但二进制工具 hash 已经能区分本地 rebuild。
- `verifier_ok` 的语义仍是“`opt` 退出成功且输出存在”，还没有拆成 `opt_success`、`output_exists`、`failure_kind` 等更细字段。
- 测试文件仍通过 `sys.path.insert` 或 CLI 的 `PYTHONPATH=src` 使用本地包；editable install 留到后续整理。
- 本轮保持在 function scalar pass 子集，没有扩展到 loop、CGSCC 或 module 级 pass。

### 下一步

1. 初始化 git 仓库并提交当前 MVP-0/P1 边界。
2. 在 certificate 中进一步区分 runner failure kind，澄清 `verifier_ok` 语义。
3. 生成 3 个 Stanford 输入乘 3 个 pass pair 的最小证书表。
4. 证书闭环稳定后，再进入 `feature_scan.py` 和静态过滤。

### 本次代码快照：`src/ecpor/environment.py` 关键片段

```python
@dataclass(frozen=True)
class LLVMEnvironment:
    opt_path: str
    clang_path: str
    llvm_size_path: str
    llvm_config_path: str
    llvm_version: str
    clang_version: str
    clang_commit: str
    target_triple: str
    host_cpu: str
    execution_model: str = DEFAULT_EXECUTION_MODEL
    debug_policy: str = DEFAULT_DEBUG_POLICY
    metadata_policy: str = DEFAULT_METADATA_POLICY
    normalizer_version: str = DEFAULT_NORMALIZER_VERSION
    opt_sha256: str = "unknown"
    clang_sha256: str = "unknown"
    llvm_size_sha256: str = "unknown"
    llvm_config_sha256: str = "unknown"
    llvm_source_root: str = "E:/llvm"
    llvm_source_git_commit: str = "unknown"
    llvm_source_git_dirty: bool | None = None
    llvm_build_type: str = "unknown"
    llvm_assertions: str = "unknown"
    cmake_cache_sha256: str = "unknown"


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
```

### 本次代码快照：`src/ecpor/cert.py` 关键片段

```python
@dataclass(frozen=True)
class PairCertificate:
    cert_id: str
    label: str
    reason: str
    pass_a: str
    pass_b: str
    input_state_hash: str
    env_id: str
    execution_model: str
    llvm_version: str
    command_ab: list[str]
    command_ba: list[str]
    input_ir_path: str
    output_ab: str
    output_ba: str
    hash_ab: str | None
    hash_ba: str | None
    hard_equal: bool
    normalizer_version: str
    verifier_ab: bool
    verifier_ba: bool
    exit_code_ab: int
    exit_code_ba: int
    nesting: str
    pipeline_ab: str
    pipeline_ba: str
    extra_flags: list[str]
    pass_a_instance: str
    pass_b_instance: str
    region_id: str
    ecpor_git_commit: str
    ecpor_git_dirty: bool | None
    scope: str = "state-specific"
```

```python
def make_cert_id(
    *,
    pass_a: str,
    pass_b: str,
    input_state_hash: str,
    env_id: str,
    execution_model: str,
    normalizer_version: str,
    nesting: str,
    pipeline_ab: str,
    pipeline_ba: str,
    extra_flags: list[str] | tuple[str, ...],
    pass_a_instance: str | None = None,
    pass_b_instance: str | None = None,
    region_id: str = "function_scalar_mvp",
) -> str:
    payload = {
        "pass_a": pass_a,
        "pass_b": pass_b,
        "pass_a_instance": pass_a_instance or f"{pass_a}@unknown",
        "pass_b_instance": pass_b_instance or f"{pass_b}@unknown",
        "region_id": region_id,
        "input_state_hash": input_state_hash,
        "env_id": env_id,
        "execution_model": execution_model,
        "normalizer_version": normalizer_version,
        "nesting": nesting,
        "pipeline_ab": pipeline_ab,
        "pipeline_ba": pipeline_ba,
        "extra_flags": list(extra_flags),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
```

### 本次代码快照：`src/ecpor/pair_test.py` 关键片段

```python
input_state_hash = hard_hash(state_path)
pass_a_instance = pass_a_instance or f"{pass_a}@unknown"
pass_b_instance = pass_b_instance or f"{pass_b}@unknown"
cert_id = make_cert_id(
    pass_a=pass_a,
    pass_b=pass_b,
    pass_a_instance=pass_a_instance,
    pass_b_instance=pass_b_instance,
    region_id=region_id,
    input_state_hash=input_state_hash,
    env_id=env_id,
    execution_model=execution_model,
    normalizer_version=normalizer_version,
    nesting=nesting,
    pipeline_ab=pipeline_ab,
    pipeline_ba=pipeline_ba,
    extra_flags=flags,
)
cert_dir = out_dir / cert_id
cert_dir.mkdir(parents=True, exist_ok=True)
output_ab = cert_dir / "ab.ll"
output_ba = cert_dir / "ba.ll"
(cert_dir / "input_hash.txt").write_text(input_state_hash + "\n", encoding="utf-8")
```

```python
def reproduce_certificate(
    cert_path: str | Path,
    *,
    opt_path: OptPath | None = None,
    output_dir: str | Path | None = None,
    timeout_sec: float = 30.0,
) -> CertificateReproduction:
    original = load_certificate(cert_path)
    replay_opt_path = opt_path or _infer_opt_path(original)
    replay_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else Path(original.output_ab).parent.parent / f"{original.cert_id}_repro"
    )
    reproduced_cert = test_adjacent_swap(
        original.input_ir_path,
        original.pass_a,
        original.pass_b,
        opt_path=replay_opt_path,
        output_dir=replay_output_dir,
        env_id=original.env_id,
        execution_model=original.execution_model,
        llvm_version=original.llvm_version,
        normalizer_version=original.normalizer_version,
        nesting=original.nesting,
        extra_flags=original.extra_flags,
        pass_a_instance=original.pass_a_instance,
        pass_b_instance=original.pass_b_instance,
        region_id=original.region_id,
        ecpor_git_commit=original.ecpor_git_commit,
        ecpor_git_dirty=original.ecpor_git_dirty,
        timeout_sec=timeout_sec,
    )
```

### 本次代码快照：`configs/env.yaml`

```yaml
llvm:
  opt_path: "E:/llvm/build/bin/opt.exe"
  clang_path: "E:/llvm/build/bin/clang.exe"
  llvm_size_path: "E:/llvm/build/bin/llvm-size.exe"
  llvm_config_path: "E:/llvm/build/bin/llvm-config.exe"
  llvm_version: "23.0.0git"
  clang_version: "23.0.0git"
  clang_commit: "aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2"
  opt_sha256: "f4a10cdc53c8f1288bb4051318af63ca8b07aae0f0b8ffb13b788fc98ace2543"
  clang_sha256: "7813948a1b853beb1806fd1bb28b09917bcbd9e35d67b43345af02c100b93551"
  llvm_size_sha256: "f425ef87d64380ff5f8fd055ddb52e1f0d38f3031bb2a5bbddd557d71c5bc589"
  llvm_config_sha256: "3622511cbec368b9fbe9bc01fdf6b679cdecf16381c349f447c1ff30f26c1bde"
  env_id: "3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e"

llvm_source:
  root: "E:/llvm"
  git_commit: "unknown"
  git_dirty: null

llvm_build:
  build_type: "Release"
  assertions: "OFF"
  cmake_cache_sha256: "9e56132f8c33227089b371b05906adccfff0ad4f92a72f303cc8ac39eec7b0f2"
```

### 本次代码快照：`.gitignore`

```gitignore
__pycache__/
.pytest_cache/
*.pyc
data/outputs/
data/certs/
*.o
*.obj
*.exe
*.ll.tmp
!data/inputs/*.ll
```

---
