# ECPOR 进度记录：拆分进度文件并建立索引规则

## 2026-07-01：拆分进度文件并建立索引规则

### 当前目标

按用户要求，把原来的单一长进度文件拆分成多个独立进度文件；以后每次大改动都在 `docs/progress/` 下新建一个进度文件，`docs/project_progress.md` 只保留索引、维护规则和最新状态摘要。

### 已完成内容

- [x] 新建 `docs/progress/` 目录。
- [x] 将原 `docs/project_progress.md` 中的历史记录按事件拆成 7 个文件：
  - `2026-07-01-mvp0-environment-runner.md`
  - `2026-07-01-progress-document-rules.md`
  - `2026-07-01-p1-p2-certificate-loop.md`
  - `2026-07-01-dlm-python-environment.md`
  - `2026-07-01-env-cert-repro-hardening.md`
  - `2026-07-01-git-initialization.md`
  - `2026-07-01-failure-kind-and-3x3-matrix.md`
- [x] 将 `docs/project_progress.md` 改成项目进度索引。
- [x] 在索引中明确新规则：以后大改动、新阶段、批量实验、验证结果或风险变化，都新建独立进度文件。
- [x] 修正索引链接，使其从 `docs/project_progress.md` 相对跳转到 `progress/*.md`。

### 验证结果

本次只调整文档结构，没有修改运行代码。

已检查：

```powershell
rg -n "^# |^## " docs\project_progress.md docs\progress
```

结果确认：

```text
docs/project_progress.md 只保留索引、规则、最新状态和拆分说明
docs/progress/ 下已有 8 个独立进度文件
```

### 风险与备注

- 旧记录内容按事件迁移；拆分方式保留了原有代码快照。
- `docs/project_progress.md` 之后不再追加长篇进度正文，只追加索引行和最新状态摘要。
- 后续每次大改动仍然要在独立进度文件中附上相关代码快照。

### 下一步

1. 后续功能改动时，新建 `docs/progress/YYYY-MM-DD-topic.md`。
2. 在 `docs/project_progress.md` 索引表中追加新文件链接。
3. 保持每个进度文件包含目标、完成内容、验证结果、风险/备注、下一步和代码快照。

### 本次代码快照：`docs/project_progress.md` 索引规则片段

```markdown
## 文档维护规则

1. 进度文档统一使用中文记录。
2. 每次大改动、新阶段、批量实验、验证结果或风险变化，都在 `docs/progress/` 下新建一个进度文件。
3. 文件命名使用 `YYYY-MM-DD-简短主题.md`，主题用英文小写和连字符，便于搜索和排序。
4. `docs/project_progress.md` 只维护索引、规则和最新状态摘要，不再承载完整长文。
5. 每个独立进度文件必须包含：当前目标、完成内容、验证结果、风险/备注、下一步。
6. 每个独立进度文件都要附上与本次进度相关的代码快照；优先附完整源代码或完整配置，文件过大时可附关键完整片段并说明原因。
7. 生成产物如 `.ll`、`.o`、大体量报告、批量日志默认不贴全文，只记录路径、命令、hash 和验证结果。
8. 大改动完成后，把新进度文件链接追加到下方索引，并更新“最新状态”。
```

### 本次代码快照：拆分后的索引表片段

```markdown
| 日期 | 主题 | 文件 |
| --- | --- | --- |
| 2026-07-01 | MVP-0/P0 环境与 Runner 基础 | [2026-07-01-mvp0-environment-runner.md](progress/2026-07-01-mvp0-environment-runner.md) |
| 2026-07-01 | P1.5 failure kind 与 P2 3×3 最小证书表 | [2026-07-01-failure-kind-and-3x3-matrix.md](progress/2026-07-01-failure-kind-and-3x3-matrix.md) |
| 2026-07-01 | 拆分进度文件并建立索引规则 | [2026-07-01-progress-file-split.md](progress/2026-07-01-progress-file-split.md) |
```
