# ECPOR 进度记录：切换到 dlm Python 环境

## 2026-07-01：切换到 dlm Python 环境

### 当前目标

按用户要求，后续测试、开发和运行命令统一使用 `dlm` Python 环境。

### 已完成内容

- [x] 定位 `dlm` 环境：
  - `D:\Miniconda\envs\dlm\python.exe`
- [x] 确认 `dlm` Python 版本：
  - `Python 3.10.20`
- [x] 确认 `dlm` 环境中已有 `pip`：
  - `pip 26.0.1`
- [x] 确认 `dlm` 环境中已有 `pytest`：
  - `pytest 9.1.1`
- [x] 更新 `README.md` 中的测试命令和 smoke-test Python 命令。
- [x] 更新 `docs/superpowers/plans/2026-07-01-mvp0-environment-runner.md` 中的 Python 测试命令。

### 验证结果

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest --version
```

结果：`pytest 9.1.1`

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：`14 passed in 0.42s`

真实 LLVM pair-test 复跑：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.pair_test import test_adjacent_swap; cert=test_adjacent_swap('data/inputs/testsuite_stanford_bubblesort.ll','instcombine','dce',opt_path='E:/llvm/build/bin/opt.exe',output_dir='data/outputs/pair_tests',env_id='b87a818a5b1ba7b3913d179fd1bee2d02ece540ff5552aacce4ef5a77fec6c84',llvm_version='23.0.0git'); print(cert.label, cert.hard_equal, cert.hash_ab, cert.hash_ba)"
```

结果：

```text
certified_independent True 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56
```

### 风险与备注

- 系统默认 `python` 仍指向 `C:\msys64\ucrt64\bin\python.exe`，不要依赖裸 `python`。
- 后续命令统一显式使用 `D:\Miniconda\envs\dlm\python.exe`。
- 之前安装到 `D:\Miniconda\python.exe` base 环境的 pytest 保留不动；当前项目以后以 `dlm` 环境为准。

### 下一步

继续 P1/P2：

1. 给 `pair_test.py` 增加 CLI。
2. 增加 certificate reproduction 测试。
3. 增加 `feature_scan.py` 第一版。

---
## 本次代码快照：切换 dlm Python 环境

### `README.md` 相关片段

````markdown
## Unit Tests

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

## Smoke Test

Generate LLVM IR:

```powershell
E:\llvm\build\bin\clang.exe -O0 -Xclang -disable-O0-optnone -S -emit-llvm benchmarks\micro\dead_code.c -o data\inputs\dead_code.ll
```

Run a minimal `opt` pipeline through the Python runner:

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; r = run_opt('data/inputs/dead_code.ll', 'function(instcombine,dce)', 'data/outputs/dead_code.opt.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"
```
````

### `docs/superpowers/plans/2026-07-01-mvp0-environment-runner.md` 相关片段

```markdown
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_environment.py -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_normalizer.py -q`
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_runner.py -q`
- [ ] Run all unit tests: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
```

---
