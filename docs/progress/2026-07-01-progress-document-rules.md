# ECPOR 进度记录：进度文档规则调整

## 2026-07-01：进度文档规则调整

### 当前目标

按用户要求调整进度记录方式：进度文档必须用中文写，并且每次更新进度文档时同步附上相关代码。

### 已完成内容

- [x] 将 `docs/project_progress.md` 改为中文结构。
- [x] 添加“文档维护规则”。
- [x] 明确后续每次更新进度文档都要附相关代码快照。
- [x] 本次附上 MVP-0 当前核心代码和配置。

### 验证结果

本次只修改文档，没有修改运行代码。文档更新后已执行轻量验证：

```powershell
python -m unittest discover -s tests -v
```

结果：`Ran 9 tests ... OK`

同时复跑了一个真实 LLVM runner 烟测：

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; p='function(sroa,early-cse,instcombine,simplifycfg,reassociate,gvn,dce,adce)'; r=run_opt('data/inputs/testsuite_stanford_bubblesort.ll', p, 'data/outputs/testsuite_stanford_bubblesort.scalar.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"
```

结果：`0 True a4d1feea43fe4dd9ff80201f4cd0bffdf2b6729635a4e28a3aceaaa94c0b2f4e`

### 下一步

后续任何实现性更新，都在本文件对应日期条目下增加：

- 进度说明
- 验证结果
- 风险/备注
- 下一步
- 相关代码快照

---
