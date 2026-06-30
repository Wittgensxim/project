# ECPOR 进度记录：按先后顺序命名进度文件

## 2026-07-01：按先后顺序命名进度文件

### 当前目标

按用户要求，把 `docs/progress/` 下的进度文件改成按先后顺序编号命名；以后新建进度文件时也沿用这个规则。

### 已完成内容

- [x] 将现有 8 个进度文件统一改名为 `YYYY-MM-DD-NN-topic.md` 格式。
- [x] 顺序号按事件发生顺序从 `01` 到 `08` 排列。
- [x] 将本次规则调整记录为第 `09` 个进度文件：
  - `2026-07-01-09-progress-file-ordering.md`
- [x] 更新 `docs/project_progress.md` 的维护规则：
  - 新文件命名使用 `YYYY-MM-DD-NN-简短主题.md`
  - `NN` 是两位顺序号
  - 同一天的新文件从当前最大编号继续递增
- [x] 更新索引表中所有链接，指向新的顺序编号文件名。
- [x] 更新 `2026-07-01-08-progress-file-split.md` 中的历史文件名说明。

### 验证结果

链接检查：

```powershell
D:\Miniconda\envs\dlm\python.exe -c "from pathlib import Path; import re; base=Path('docs'); text=Path('docs/project_progress.md').read_text(encoding='utf-8'); links=re.findall(r'\]\((progress/[^)]+)\)', text); missing=[link for link in links if not (base/link).exists()]; print('links', len(links)); print('missing', missing)"
```

预期结果：

```text
links 9
missing []
```

本次只调整文档文件名和索引规则，不修改运行代码。

### 风险与备注

- 旧文件名已经不再作为索引入口使用；以后统一看 `docs/project_progress.md` 的索引表。
- 当前规则只按单日内顺序编号，不表达阶段优先级；同一天新建文件时继续递增即可。
- 这次变更会让打开旧路径的编辑器标签失效，需要从新文件名重新打开。

### 下一步

1. 以后新增大改动记录时，先查看 `docs/progress/` 中当天最大编号。
2. 新文件使用下一个编号，例如当天已有 `09`，下一份写成 `2026-07-01-10-topic.md`。
3. 同步更新 `docs/project_progress.md` 的最新状态和索引表。

### 本次代码快照：命名规则片段

```markdown
3. 文件命名使用 `YYYY-MM-DD-NN-简短主题.md`，其中 `NN` 是两位顺序号，例如 `2026-07-01-09-progress-file-ordering.md`；主题用英文小写和连字符，便于搜索和排序。
8. 大改动完成后，把新进度文件链接追加到下方索引，并更新“最新状态”；同一天的新文件顺序号从当前最大编号继续递增。
```

### 本次代码快照：顺序命名后的文件列表

```text
2026-07-01-01-mvp0-environment-runner.md
2026-07-01-02-progress-document-rules.md
2026-07-01-03-p1-p2-certificate-loop.md
2026-07-01-04-dlm-python-environment.md
2026-07-01-05-env-cert-repro-hardening.md
2026-07-01-06-git-initialization.md
2026-07-01-07-failure-kind-and-3x3-matrix.md
2026-07-01-08-progress-file-split.md
2026-07-01-09-progress-file-ordering.md
```
