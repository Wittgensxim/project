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
9. `data/` 目录只保留必须保留的文件；阶段完成后清理 `*_work`、旧 final、旧 commit 输出和可再生成中间产物。

## 最新状态

- 当前分支：`feature/phase-ordering-footprint`
- 当前已完成阶段：MVP-0/P0、P1 certificate 闭环、P1.5 failure kind、P2 3x3 最小证书表、P2.5 summary report 和 feature scan、P2.6 not-certified diff report 和 3x8 matrix、P3 high-recall static filter、P3.5 per-program static filter hold-out 验证、P4 minimal lazy validation、P5 bounded local reorder exploration、P6 code size evaluator 最小版、P6.5 code size provenance/invariant hardening、P6.5 result manifest 与 candidate-source invariant、P7a bounded two-swap smoke test、P7a report/manifest/cache 收尾、P7b per-program top-3 seed bounded two-swap controlled experiment。
- 当前最新验证：`D:\Miniconda\envs\dlm\python.exe -m pytest -q`，结果 `79 passed`。
- 最新 P4 真实实验：8 个 Stanford 输入 × 7 个 anchor-adjacent pair，共 `56` 次 lazy validation；第一轮 `48` 个 candidate 动态测试、`8` 个 low_priority skip、`32` 个 certified、`16` 个 not-certified、`run_failed = 0`、`CertificateReproductionRate = 100.00%`。
- 最新 P4 cache 验证：第二轮同一批输入 `cache_hits = 48`、`dynamic_tests = 0`、`SecondRunCacheHitRate = 100.00%`。
- 最新 state-indexing safety 验证：input-state certificate 对 input hash 命中，对 `sroa` 后不同 prefix hash 不命中。
- 最新 P5 真实实验：输入 `data/outputs/lazy_validation_p4_e83c409_first.csv`，输出 `data/outputs/bounded_local_p5_p6_final/`；生成 `8` 个 anchor candidate 和 `16` 个 single-swap candidate；完整 pipeline 运行 `24` 次，`pipeline_run_failed = 0`，`same_as_anchor = 8`，`different_from_anchor = 16`。
- 最新 P5 report 修正：新增 `single_swap_same_as_anchor = 0`、`single_swap_different_from_anchor = 16`，并记录 `attempts_csv_sha256` 和 `pipeline_config_sha256`。
- 最新 P6 真实实验：输入 `data/outputs/bounded_local_p5_p6_final/`，输出 `data/outputs/code_size_p6_final/`；object build `24/24` 成功，`ObjectBuildFailed = 0`，`SizeParseFailed = 0`，`CodeSizeDeltaVsAnchor computed = 16`；single-swap text size 相对 anchor 为 `smaller_text = 1`、`equal_text = 15`、`larger_text = 0`；`SingleSwapP5SameAsAnchor = 0`、`SingleSwapP5DifferentFromAnchor = 16`、`IRDifferentButTextEqualCount = 15`、`IRDifferentButTextEqualRate = 93.75%`。
- 最新可提交结果清单：`docs/results/p6_5_code_size_manifest.json`，记录 P6.5 clean run commit、P5/P6 hash、LLVM codegen 工具 hash、P5/P6 summary 和 best smaller candidate。
- 最新 P7a 真实实验：输入 P6 中唯一 `.text` 变小的 one-swap seed，输出 `data/outputs/bounded_two_swap_p7a/` 和 `data/certs/bounded_two_swap_p7a/`；first-run 为 `seed_candidates = 1`、`attempted_second_swaps = 7`、`dynamic_tests = 7`、`certified_independent = 3`、`not_certified_independent = 4`、`unique_depth2_candidates = 3`、`duplicate_sequences = 1`、`pipeline_run_failed = 0`、`object_build_failed = 0`、`size_parse_failed = 0`；best depth2 `.text` delta 仍为 `-4.4017%`，没有超过 depth1 best。
- 最新 P7a manifest：`docs/results/p7a_bounded_two_swap_manifest.json`，记录 P7a 输入/输出 hash、工具 hash、seed、depth2 candidate 和 smoke summary。
- 最新 P7a cache 验证：同一个 `data/certs/bounded_two_swap_p7a/` 复跑到 `data/outputs/bounded_two_swap_p7a_second/`；clean commit `083ab55e639f289d65cd035f4b3c98e4c0c31ed7` 下 `cache_hits = 7`、`dynamic_tests = 0`、`validated_second_swaps = 7`、`unique_depth2_candidates = 3`、`pipeline_run_failed = 0`、`object_build_failed = 0`、`size_parse_failed = 0`。
- 最新 P7a cache manifest：`docs/results/p7a_cache_reuse_manifest.json`，由 `python -m ecpor.result_manifest p7a ...` 自动生成，记录 second-run 输入/输出 hash、工具 hash、summary、seed 和 depth2 vs parent delta。
- 最新 P7b 真实实验：源码 clean commit `3f9047942fe7b43e9e41f65e97e78af1ab6e8559`；输出 `data/outputs/bounded_two_swap_p7b/` 和 `data/certs/bounded_two_swap_p7b/`；`selected_seed_candidates = 16`、`selected_smaller_seeds = 1`、`selected_equal_seeds = 15`、`selected_seed_programs = 8`、`attempted_second_swaps = 112`、`validated_second_swaps = 100`、`dynamic_tests = 95`、`cache_hits = 5`、`certified_independent = 58`、`not_certified_independent = 42`、`run_failed = 0`、`unique_depth2_candidates = 22`、`budget_skipped_depth2_candidates = 0`、`pipeline_run_failed = 0`、`object_build_failed = 0`、`size_parse_failed = 0`。
- 最新 P7b code-size 结果：depth1 seed `.text` 相对 anchor 为 `1` 个 smaller、`15` 个 equal、`0` 个 larger；depth2 candidate 为 `3` 个 smaller、`16` 个 equal、`3` 个 larger；best depth1 和 best depth2 均为 `-4.4017%`，`depth2_improves_over_depth1_best = False`，`best_candidate_depth = 1`。
- 最新 P7b cache 验证：同一个 `data/certs/bounded_two_swap_p7b/` 复跑到 `data/outputs/bounded_two_swap_p7b_second/`；`cache_hits = 100`、`dynamic_tests = 0`、`validated_second_swaps = 100`、`unique_depth2_candidates = 22`，pipeline/object/size 失败均为 `0`。
- 最新 P7b manifests：`docs/results/p7b_bounded_two_swap_manifest.json` 与 `docs/results/p7b_cache_reuse_manifest.json`，均记录 `ecpor_git_dirty = false`、输入/输出 hash、工具 hash、seed 列表、depth2 candidates 和 summary。
- 最新 data 清理：新增 `docs/data_retention_manifest.md`；以后 `data/` 只保留必须保留的文件；删除 `*_work`、旧 P5 commit 输出和重复 P4 final 目录；保留 `data/inputs/`、P4 e83c409、P5/P6 final、pair_tests。清理后 `data/outputs` 约 `21.57 MB`，`data/certs` 约 `0.62 MB`。
- 重要语义边界：static filter 只做 candidate generation / low priority 排序；lazy validation 只在当前 state 上查询或生成 certificate；input-state certificate 不得复用于 prefix-state。
- 下一步建议：先分析 P7b 的 per-program seed/depth2 分布和 code-size 结果，再决定是否进入更大的 bounded search；仍不直接做 Alive2、loop pass、inline 或 O2/O3。

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
| 2026-07-01 | P5 bounded local reorder exploration | [2026-07-01-15-p5-bounded-local-reorder.md](progress/2026-07-01-15-p5-bounded-local-reorder.md) |
| 2026-07-01 | P6 code size evaluator 最小版 | [2026-07-01-16-p6-code-size-evaluator.md](progress/2026-07-01-16-p6-code-size-evaluator.md) |
| 2026-07-01 | data 目录保守清理 | [2026-07-01-17-data-retention-cleanup.md](progress/2026-07-01-17-data-retention-cleanup.md) |
| 2026-07-01 | P6.5 code size provenance 与 invariant 加固 | [2026-07-01-18-p6-5-code-size-hardening.md](progress/2026-07-01-18-p6-5-code-size-hardening.md) |
| 2026-07-02 | P6.5 result manifest 与 candidate-source invariant | [2026-07-02-19-p6-5-manifest-source-invariant.md](progress/2026-07-02-19-p6-5-manifest-source-invariant.md) |
| 2026-07-02 | P7a bounded two-swap smoke test | [2026-07-02-20-p7a-bounded-two-swap-smoke.md](progress/2026-07-02-20-p7a-bounded-two-swap-smoke.md) |
| 2026-07-02 | P7a report 字段、manifest 自动化与 cache 复跑 | [2026-07-02-21-p7a-cache-report-manifest-wrapup.md](progress/2026-07-02-21-p7a-cache-report-manifest-wrapup.md) |
| 2026-07-02 | P7b per-program top-3 seed bounded two-swap controlled experiment | [2026-07-02-22-p7b-bounded-two-swap-controlled.md](progress/2026-07-02-22-p7b-bounded-two-swap-controlled.md) |

## 旧文档拆分说明

原 `docs/project_progress.md` 中的历史进度和代码快照已经按事件拆分到 `docs/progress/`。本索引只维护文档组织方式和当前阶段摘要。
