# ECPOR 项目进度索引

本文档是 ECPOR 原型项目的进度索引和维护规则。详细进度记录已经拆分到 `docs/progress/`。以后每次大改动都新建一个独立进度文件，不再把长篇记录追加到本索引里。

## 文档维护规则

1. 进度文档统一使用中文记录。
2. 每次大改动、新阶段、批量实验、验证结果或风险变化，都在 `docs/progress/` 下新建一个进度文件。
3. 文件命名使用 `YYYY-MM-DD-NN-short-topic.md`，其中 `NN` 是两位顺序号，例如 `2026-07-01-14-p4-minimal-lazy-validation.md`。
4. `docs/project_progress.md` 只维护索引、规则和最新状态摘要，不承载完整长文。
5. 每个独立进度文件必须包含：当前目标、完成内容、验证结果、风险/备注、下一步。
6. 每个独立进度文件都要附上与本次进度相关的代码快照；文件过大时可附关键完整片段并说明原因。
7. 生成产物如 `.ll`、`.o`、大体量报告、批量日志默认不贴全文，只记录路径、命令、hash 和验证结果。
8. 大改动完成后，把新进度文件链接追加到下方索引，并更新“最新状态”。

## 最新状态

- 当前分支：`feature/phase-ordering-footprint`
- 当前已完成阶段：MVP-0/P0、P1 certificate 闭环、P1.5 failure kind、P2 3x3 最小证书表、P2.5 summary report 和 feature scan、P2.6 not-certified diff report 和 3x8 matrix、P3 high-recall static filter、P3.5 per-program static filter hold-out 验证、P4 minimal lazy validation。
- 当前最新验证：`D:\Miniconda\envs\dlm\python.exe -m pytest -q`，结果 `53 passed`。
- 最新 P4 真实实验：8 个 Stanford 输入 × 7 个 anchor-adjacent pair，共 `56` 次 lazy validation；第一轮 `48` 个 candidate 动态测试、`8` 个 low_priority skip、`32` 个 certified、`16` 个 not-certified、`run_failed = 0`、`CertificateReproductionRate = 100.00%`。
- 最新 P4 cache 验证：第二轮同一批输入 `cache_hits = 48`、`dynamic_tests = 0`、`SecondRunCacheHitRate = 100.00%`。
- 最新 state-indexing safety 验证：input-state certificate 对 input hash 命中，对 `sroa` 后不同 prefix hash 不命中。
- 重要语义边界：static filter 只做 candidate generation / low priority 排序；lazy validation 只在当前 state 上查询或生成 certificate；input-state certificate 不得复用于 prefix-state。
- 下一步建议：P4 稳定后进入 P5 bounded local reorder exploration；仍不直接做完整 searcher、code size evaluator、Alive2、loop pass、inline 或 O2/O3。

## 进度文件索引

| 日期 | 主题 | 文件 |
| --- | --- | --- |
| 2026-07-01 | MVP-0/P0 环境与 Runner 基础 | [2026-07-01-01-mvp0-environment-runner.md](progress/2026-07-01-01-mvp0-environment-runner.md) |
| 2026-07-01 | 进度文档规则调整 | [2026-07-01-02-progress-document-rules.md](progress/2026-07-01-02-progress-document-rules.md) |
| 2026-07-01 | 安装 pytest，并继续 P1/P2 证书闭环 | [2026-07-01-03-p1-p2-certificate-loop.md](progress/2026-07-01-03-p1-p2-certificate-loop.md) |
| 2026-07-01 | 切换到 dlm Python 环境 | [2026-07-01-04-dlm-python-environment.md](progress/2026-07-01-04-dlm-python-environment.md) |
| 2026-07-01 | 加强环境指纹、证书唯一性和复现闭环 | [2026-07-01-05-env-cert-repro-hardening.md](progress/2026-07-01-05-env-cert-repro-hardening.md) |
| 2026-07-01 | Git 仓库初始化与首次提交边界 | [2026-07-01-06-git-initialization.md](progress/2026-07-01-06-git-initialization.md) |
| 2026-07-01 | P1.5 failure kind 与 P2 3x3 最小证书表 | [2026-07-01-07-failure-kind-and-3x3-matrix.md](progress/2026-07-01-07-failure-kind-and-3x3-matrix.md) |
| 2026-07-01 | 拆分进度文件并建立索引规则 | [2026-07-01-08-progress-file-split.md](progress/2026-07-01-08-progress-file-split.md) |
| 2026-07-01 | 按先后顺序命名进度文件 | [2026-07-01-09-progress-file-ordering.md](progress/2026-07-01-09-progress-file-ordering.md) |
| 2026-07-01 | P2.5 summary report 与 feature scan soft evidence | [2026-07-01-10-summary-report-feature-scan.md](progress/2026-07-01-10-summary-report-feature-scan.md) |
| 2026-07-01 | P2.6 diff report 与 3x8 matrix | [2026-07-01-11-diff-report-and-3x8-matrix.md](progress/2026-07-01-11-diff-report-and-3x8-matrix.md) |
| 2026-07-01 | P3 passspec 与 static filter 评估 | [2026-07-01-12-passspec-static-filter-eval.md](progress/2026-07-01-12-passspec-static-filter-eval.md) |
| 2026-07-01 | P3.5 per-program static filter 与 hold-out 验证 | [2026-07-01-13-static-filter-per-program-holdout.md](progress/2026-07-01-13-static-filter-per-program-holdout.md) |
| 2026-07-01 | P4 minimal lazy validation 与 cache reuse | [2026-07-01-14-p4-minimal-lazy-validation.md](progress/2026-07-01-14-p4-minimal-lazy-validation.md) |

## 旧文档拆分说明

原 `docs/project_progress.md` 中的历史进度和代码快照已经按事件拆分到 `docs/progress/`。本索引只维护文档组织方式和当前阶段摘要。
