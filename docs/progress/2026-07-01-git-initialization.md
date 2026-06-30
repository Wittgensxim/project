# ECPOR 进度记录：Git 仓库初始化与首次提交边界

## 2026-07-01：Git 仓库初始化与首次提交边界

### 当前目标

完成 review 中提出的 P0 阻塞项：把 `E:\project` 初始化为 git 仓库，用提交边界固定当前 MVP-0/P1 代码、测试、配置、文档和输入 IR。

### 已完成内容

- [x] 执行 `git init`，创建本地仓库。
- [x] 切换到工作分支 `feature/phase-ordering-footprint`。
- [x] 暂存并提交代码、测试、配置、文档、micro benchmark 和 `data/inputs/*.ll`。
- [x] 首次提交：
  - message: `mvp0 runner and p1 adjacent swap certificate`
  - commit: `1d5b84531c305bf8bdbfbdf4691db6002c1cb21e`
- [x] 提交后复跑真实 LLVM certificate，证书记录：
  - `ecpor_git_commit=1d5b84531c305bf8bdbfbdf4691db6002c1cb21e`
  - `ecpor_git_dirty=False`

### 验证结果

提交后全量测试：

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

结果：

```text
20 passed in 1.45s
```

提交后真实 LLVM certificate：

```text
e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954 certified_independent True 1d5b84531c305bf8bdbfbdf4691db6002c1cb21e False 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56
```

提交后 certificate reproduction：

```text
True certified_independent certified_independent 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 4293ecb2c9650931c99cb43a1f0553264b094d149b33b888b6bbafab5a9bad56 label and hashes match
```

### 风险与备注

- `git status` 会提示无法访问 `C:\Users\17335/.config/git/ignore`，这是全局 git ignore 文件权限问题；本仓库状态和提交不受影响。
- `data/outputs/` 和 `data/certs/` 被 `.gitignore` 排除，真实 LLVM 产物不会污染代码提交。

### 下一步

1. 拆分 `runner.py` 的失败原因字段，澄清 `verifier_ok` 语义。
2. 生成 3 个 Stanford 输入乘 3 个 pass pair 的最小证书表。
3. 再进入 `feature_scan.py` 和静态过滤。

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

### 本次代码快照：README 中的 certificate 命令

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.pair_test --state data\inputs\testsuite_stanford_bubblesort.ll --A instcombine --B dce --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert data\certs\testsuite_stanford_bubblesort__instcombine__dce.json --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

---
