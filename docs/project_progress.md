# ECPOR 项目进度索引

本文档是 ECPOR 原型项目的进度索引和维护规则。详细进度记录已拆分到 `docs/progress/`。以后每次大改动都新建一个独立进度文件，不再把长篇记录追加到本索引里。

## 文档维护规则

1. 进度文档统一使用中文记录。
2. 每次大改动、新阶段、批量实验、验证结果或风险变化，都在 `docs/progress/` 下新建一个进度文件。
3. 文件命名使用 `YYYY-MM-DD-简短主题.md`，主题用英文小写和连字符，便于搜索和排序。
4. `docs/project_progress.md` 只维护索引、规则和最新状态摘要，不再承载完整长文。
5. 每个独立进度文件必须包含：当前目标、完成内容、验证结果、风险/备注、下一步。
6. 每个独立进度文件都要附上与本次进度相关的代码快照；优先附完整源代码或完整配置，文件过大时可附关键完整片段并说明原因。
7. 生成产物如 `.ll`、`.o`、大体量报告、批量日志默认不贴全文，只记录路径、命令、hash 和验证结果。
8. 大改动完成后，把新进度文件链接追加到下方索引，并更新“最新状态”。

## 最新状态

- 当前分支：`feature/phase-ordering-footprint`
- 当前已完成阶段：MVP-0/P0、P1 certificate 闭环、P1.5 failure kind、P2 3×3 最小证书表。
- 当前最新验证：`D:\Miniconda\envs\dlm\python.exe -m pytest -q`，结果 `24 passed`。
- 最新真实实验：3 个 Stanford 输入 × 3 个 pass pair，`9/9` reproduction，`HardFalseIndependent = 0`。
- 下一步建议：基于 `cert_summary.csv` 增加小型汇总报告读取器；稳定后再进入 `feature_scan.py`。

## 进度文件索引

| 日期 | 主题 | 文件 |
| --- | --- | --- |
| 2026-07-01 | MVP-0/P0 环境与 Runner 基础 | [2026-07-01-mvp0-environment-runner.md](progress/2026-07-01-mvp0-environment-runner.md) |
| 2026-07-01 | 进度文档规则调整 | [2026-07-01-progress-document-rules.md](progress/2026-07-01-progress-document-rules.md) |
| 2026-07-01 | 安装 pytest，并继续 P1/P2 证书闭环 | [2026-07-01-p1-p2-certificate-loop.md](progress/2026-07-01-p1-p2-certificate-loop.md) |
| 2026-07-01 | 切换到 dlm Python 环境 | [2026-07-01-dlm-python-environment.md](progress/2026-07-01-dlm-python-environment.md) |
| 2026-07-01 | 加强环境指纹、证书唯一性和复现闭环 | [2026-07-01-env-cert-repro-hardening.md](progress/2026-07-01-env-cert-repro-hardening.md) |
| 2026-07-01 | Git 仓库初始化与首次提交边界 | [2026-07-01-git-initialization.md](progress/2026-07-01-git-initialization.md) |
| 2026-07-01 | P1.5 failure kind 与 P2 3×3 最小证书表 | [2026-07-01-failure-kind-and-3x3-matrix.md](progress/2026-07-01-failure-kind-and-3x3-matrix.md) |
| 2026-07-01 | 拆分进度文件并建立索引规则 | [2026-07-01-progress-file-split.md](progress/2026-07-01-progress-file-split.md) |

## 旧文档拆分说明

原 `docs/project_progress.md` 中的历史进度和代码快照已经按事件拆分到 `docs/progress/`。本次拆分只调整文档组织方式，不改变运行代码。
