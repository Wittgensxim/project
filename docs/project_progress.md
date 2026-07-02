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
- 当前已完成阶段：MVP-0/P0、P1 certificate 闭环、P1.5 failure kind、P2 3x3 最小证书表、P2.5 summary report 和 feature scan、P2.6 not-certified diff report 和 3x8 matrix、P3 high-recall static filter、P3.5 per-program static filter hold-out 验证、P4 minimal lazy validation、P5 bounded local reorder exploration、P6 code size evaluator 最小版、P6.5 code size provenance/invariant hardening、P6.5 result manifest 与 candidate-source invariant、P7a bounded two-swap smoke test、P7a report/manifest/cache 收尾、P7b per-program top-3 seed bounded two-swap controlled experiment、P7b.5 two-swap result interpretation and distribution analysis、P8a clang-c codegen sensitivity、P8a.5 core evidence report、P8a.6 core evidence 语义收尾、P8c Queens effect attribution、P8c.1 opcode-level attribution、P8c.2 attribution summary in core evidence、P8b-0 benchmark ingestion、P8b-1 Misc8 full matrix 与 static filter pre 评估、P8b-2 static filter false-negative repair、P8b-3-lite Misc8 depth1 chain、P8b-3.5 Misc8 depth1 analysis 与 ffbench attribution。
- 当前最新验证：`D:\Miniconda\envs\dlm\python.exe -m pytest -q`，结果 `105 passed`。
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
- 最新 P7b.5 结果解释：新增 `src/ecpor/two_swap_analysis.py`，输出 `data/outputs/bounded_two_swap_p7b_analysis/`；核心结论为 `RawDepth2Candidates = 42`、`UniqueDepth2Candidates = 22`、`DuplicateSequences = 20`、`DuplicateSequenceRate = 47.62%`、`Depth2SmallerText = 3`、`Depth2SmallerPrograms = 1`、`Depth2SmallerFromSameParent = 3`、`Depth2ImprovesProgramDepth1Best = 0`、`Depth2ImprovesGlobalDepth1Best = 0`、`FirstRunCacheHits = 5`。
- 最新 P7b.5 分析解释：3 个 smaller depth2 candidate 全部来自 `testsuite_stanford_queens`，且都没有超过该程序已有 depth1 best；P7b 增加了 smaller 候选数量，但没有扩大 smaller-text program 数量。
- 最新 P7b.5 manifest：`docs/results/p7b_analysis_manifest.json`，记录 P7b 输入 hash、分析输出 hash、`ecpor_git_dirty = false` 和 analysis-only scope。
- 最新 P8a 真实实验：输入 P6 `object_size.csv` 与 P7b `two_swap_object_size.csv`，输出 `data/outputs/codegen_sensitivity_p8a/`；`IRInputs = 46`、`AnchorInputs = 8`、`SingleSwapInputs = 16`、`Depth2Inputs = 22`、`ClangObjectBuildsAttempted = 46`、`ClangObjectBuildFailed = 0`、`ClangSizeParseFailed = 0`。
- 最新 P8a 方向对照：`DirectionComparisonCandidates = 38`、`DirectionAgreementCount = 26`、`DirectionAgreementRate = 68.42%`、`SmallerUnderBothCount = 4`、`SmallerOnlyUnderLlcCount = 0`、`SmallerOnlyUnderClangCount = 5`、`DirectionDisagreementCount = 12`。
- 最新 P8a 结论：code-size 方向存在 codegen-path sensitivity；但 Queens 的 1 个 depth1 smaller 和 3 个 depth2 smaller 在 `clang -c` 下仍然 smaller，当前关键收益不是 llc-only 假象。
- 最新 P8a manifest：`docs/results/p8a_codegen_sensitivity_manifest.json`，记录 P6/P7b 输入 hash、P8a 输出 hash、`clang.exe` / `llvm-size.exe` hash、`ecpor_git_dirty = false` 和 no-runtime/no-new-certificate scope。
- 最新 P8a.6 core evidence report：`src/ecpor/core_evidence_report.py` 将旧的单一 reduction funnel 拆成 `ecpor_validation_funnel.csv` 与 `ecpor_candidate_propagation_funnel.csv`；P8a codegen 方向比较单独写入 `ecpor_objective_layer_summary.csv`。
- 最新 P8a.6 validation funnel：P4 为 `56` attempts、`48` static candidates、`48` dynamic tests、`32` certified events、`16` not-certified events、`8` low-priority events、`run_failed = 0`；P7b 为 `112` attempts、`100` static candidates、`95` dynamic tests、`5` cache hits、`58` certified events、`42` not-certified events、`12` low-priority events、`run_failed = 0`。
- 最新 P8a.6 candidate propagation funnel：P5 为 `8` anchors 和 `16` single-swap candidates；P6 对 `16` 个 single-swap candidates 做 object-size evaluation；P7b 为 `42` raw depth2、`20` duplicates removed、`22` unique depth2；P8a 为 `38` clang-c direction comparison candidates。
- 最新 P8a.6 evidence summary：`certified_independent_events = 90` 是 P4/P7b state-indexed adjacent swap event 级 hard-prune evidence；`not_certified_events = 58` 是 hard negative，必须保留；`low_priority_events = 20` 只是 static hint；`sequence_duplicates = 20` 只是 sequence-level dedup；`llc_clang_both_smaller_object = 4` 是目标层 observation。
- 最新 P8a.6 objective-layer summary：`DirectionComparisonCandidates = 38`、`DirectionAgreementCount = 26`、`DirectionAgreementRate = 68.42%`、`SmallerUnderBothCount = 4`、`SmallerOnlyUnderLlcCount = 0`、`SmallerOnlyUnderClangCount = 5`、`DirectionDisagreementCount = 12`。
- P8a.6 manifest 语义已被 P8c.2 继承并扩展：`docs/results/core_evidence_manifest.json` 现在仍记录 P4/P5/P6/P7b/P7b.5/P8a 输入 hash 与 validation/candidate-propagation/objective-layer 输出 hash，但当前阶段号以后以 P8c.2 为准。
- 最新 P8c Queens effect attribution：新增 `src/ecpor/effect_attribution.py`，输出 `data/outputs/effect_attribution_queens/`；materialize `S/A/B/AB_local/BA_local/AB_final/BA_final` 7 个 state，不新增搜索、不新增 certificate。
- 最新 P8c feature 结论：`LocalABBAHardHashEqual = False`、`FinalABBAHardHashEqual = False`、`LocalInstructionDelta = -1`、`FinalInstructionDelta = -1`、`FeatureDeltaPropagation = kept`；说明 Queens 的 `simplifycfg,instcombine` 顺序差异在局部 pair 后已经出现，并在 suffix 后保持。
- 最新 P8c object-size 结论：`BA_final` 相对 `AB_final` 在 `llc` 下 `.text = 695 vs 727`，`LlcTextDelta = -32`、`-4.401651%`；在 `clang -c` 下 `.text = 940 vs 956`，`ClangTextDelta = -16`、`-1.673640%`；`BothCodegenSmaller = True`。
- 最新 P8c manifest：`docs/results/queens_effect_attribution_manifest.json`，记录 input IR、P8c 输出 hash、`opt.exe` / `llc.exe` / `clang.exe` / `llvm-size.exe` hash、`ecpor_git_dirty = false` 和 single-program observed-attribution scope。
- 最新 P8c.1 opcode-level attribution：`data/outputs/effect_attribution_queens/opcode_delta.csv` 显示 `local_AB_vs_BA` 与 `final_AB_vs_BA` 的非零 opcode delta 都是 `num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1`；说明净少 1 条 instruction 来自 icmp/select 减少与 add 增加的组合变化。
- 最新 P8c.1 manifest：`docs/results/queens_effect_attribution_manifest.json` 已更新到 clean commit `70fd929761117597d3adaf932e9baad8fccfb9bd`，并新增 `opcode_delta_csv` hash 与 `FinalOpcodeDeltaNonZero` summary。
- 最新 P8c.2 core evidence attribution summary：`src/ecpor/core_evidence_report.py` 新增可选 P8c 输入，输出 `data/outputs/core_evidence_report/ecpor_attribution_summary.csv`，并在主报告加入 `Observed Attribution Summary`；不新增搜索、不新增 certificate、不运行 runtime。
- 最新 P8c.2 结果：`AttributionCases = 1`，唯一 attribution case 为 `testsuite_stanford_queens` 的 `simplifycfg,instcombine`，`local_feature_delta = num_instructions_delta=-1`，`final_feature_delta = num_instructions_delta=-1`，`opcode_delta = num_icmp_delta=-1;num_select_delta=-1;num_add_delta=1`，`llc_text_delta_pct = -4.401651`，`clang_text_delta_pct = -1.673640`。
- 最新 P8c.2 manifest：`docs/results/core_evidence_manifest.json` 已更新为 `stage = P8c.2`，记录 P8c attribution 输入 hash、`ecpor_attribution_summary_csv` 输出 hash、`AttributionCases = 1`、`AttributionObservedButNotCausalProof = True`、`ecpor_git_dirty = false`。
- 最新 P8b-0 benchmark ingestion：新增 `src/ecpor/benchmark_ingest.py` 和 `configs/benchmarks_p8b.yaml`，从 `E:\llvm-test-suite` 的 `SingleSource/Benchmarks/Misc`、`SingleSource/Regression/C`、`SingleSource/UnitTests` 扫描 C 源；只做 benchmark ingestion，不运行 pair matrix、不新增 certificate、不新增搜索。
- 最新 P8b-0 真实结果：`CandidateSourceFilesScanned = 20`、`AcceptedPrograms = 8`、`RejectedPrograms = 12`、`IRGenerationOk = 18`、`ScalarPipelineOk = 8`、`LlcObjectOk = 8`、`ClangObjectOk = 8`、`SizeParseOk = 8`；失败分布为 `ir_generation:clang_failed = 2` 和 `selection:accepted_limit_reached = 10`。
- 最新 P8b-0 accepted inputs：`testsuite_misc_aarch64_init_cpu_features`、`testsuite_misc_evalloop`、`testsuite_misc_ffbench`、`testsuite_misc_flops_1`、`testsuite_misc_flops_2`、`testsuite_misc_flops_3`、`testsuite_misc_flops_4`、`testsuite_misc_flops_5`，对应 `.ll` 已保存在 `data/inputs/`。
- 最新 P8b-0 manifest：`docs/results/benchmark_ingest_p8b_manifest.json`，记录 `configs/benchmarks_p8b.yaml`、8 个 accepted IR、ingest summary/report、LLVM 工具 hash、`ecpor_git_dirty = false` 和 ingestion-only scope。
- 最新 P8b-1 tooling：新增 `p8b-misc8x28` batch preset、`p8b-misc8` static filter preset 和 `ecpor.result_manifest p8b-matrix`；tooling clean commit 为 `ed4cff79a13e0cb455a4c917fa10a3b9243fdf45`。
- 最新 P8b-1 full matrix：8 个 Misc 输入 × 28 个 unordered pass pair，共 `224` 个 certificate；`reproduced = 224/224`、`CertificateReproductionRate = 100.00%`、`HardFalseIndependent = 0`、`CertifiedFeatureMismatchCount = 0`、`run_failed = 0`、`certified_independent = 148`、`not_certified_independent = 76`。
- 最新 P8b-1 static filter pre 评估：`candidate = 184`、`low_priority = 40`、`frozen = 0`、`StaticCandidateRecall = 93.42%`、`MacroStaticCandidateRecall = 94.39%`、`StaticFalseNegativeObserved = 5`、`StaticCandidateReduction = 17.86%`；false negatives 为 `sroa,adce` on `ffbench`，`sroa,dce` / `sroa,adce` on `flops_1` 和 `flops_2`。
- 最新 P8b-1 manifest：`docs/results/p8b_misc8_matrix_manifest.json`，记录 P8b-1 summary/static report hash、`opt.exe` hash、`ecpor_git_dirty = false`、`passspec_tuning = false` 和 `pre_tuning_static_filter_eval = true`。
- 最新 P8b-2 passspec 修复：在 `sroa.may_produce` 中新增 `dce_opportunity`，来源为 P8b-1 Misc8 false-negative repair；`dce/adce` 原本已经消费 `dce_opportunity`，所以没有扩大到全局 cleanup tag。
- 最新 P8b-2 static filter post 评估：不重跑 224 个 certificate，只基于 `data/outputs/cert_summary_p8b_misc8_pre.csv` 重跑 static filter；结果为 `candidate = 200`、`low_priority = 24`、`frozen = 0`、`StaticCandidateRecall = 100.00%`、`MacroStaticCandidateRecall = 100.00%`、`StaticFalseNegativeObserved = 0`、`StaticCandidateReduction = 10.71%`。
- 最新 P8b-2 manifest：`docs/results/p8b_misc8_static_filter_repair_manifest.json`，记录 pre/post static report hash、`PassSpecRepair = sroa.may_produce += dce_opportunity`、`StaticFalseNegativeDelta = 5`、`ecpor_git_dirty = false`、`new_certificates = false` 和 `certificate_matrix_rerun = false`。
- 最新 P8b-3-lite tooling：P4/P5 driver 支持 `--program-preset p8b-misc8`；`codegen_sensitivity.py` 支持 `--p6-only`；`result_manifest.py` 新增 `p8b-lazy-validation`、`p8b-bounded-local`、`p8b-code-size`、`p8b-codegen` 四个 manifest builder。
- 最新 P8b-3a/P8b-3b 结果：Misc8 上 `attempted_adjacent_swaps = 56`、`candidate_swaps = 48`、`dynamic_tests = 48`、`certified_independent = 32`、`not_certified_independent = 16`、`run_failed = 0`、`CertificateReproductionRate = 100.00%`；P5 生成 `8` 个 anchor 和 `16` 个 single-swap candidate，`pipeline_runs = 24`、`pipeline_run_failed = 0`、`single_swap_different_from_anchor = 16`。
- 最新 P8b-3c/P8b-3d 结果：`llc` object-size 中 `CodeSizeDeltaVsAnchor = 16`、`smaller_text = 1`、`equal_text = 15`、`larger_text = 0`，唯一 both-smaller depth1 case 是 `testsuite_misc_ffbench__swap_2__instcombine__simplifycfg`；`clang -c` sensitivity 中 `IRInputs = 24`、`Depth2Inputs = 0`、`DirectionAgreementRate = 93.75%`、`SmallerUnderBothCount = 1`、`DirectionDisagreementCount = 1`。
- 最新 P8b-3 manifests：`docs/results/p8b_misc8_lazy_validation_manifest.json`、`docs/results/p8b_misc8_bounded_local_manifest.json`、`docs/results/p8b_misc8_code_size_manifest.json`、`docs/results/p8b_misc8_codegen_sensitivity_manifest.json`，均记录 `result_generated_from_commit = 9a449ee4e2b59a4a3b153ee06d136278d7b5373a` 与 `ecpor_git_dirty = false`。
- 最新 P8b-3.5 depth1 分析：新增 `src/ecpor/depth1_analysis.py`；Misc8 上 `SingleSwapCandidates = 16`、`ObjectEvaluated = 16`、`SmallerText = 1`、`EqualText = 15`、`IRDifferentButTextEqualRate = 93.75%`、`DirectionAgreementRate = 93.75%`、`BothSmallerCases = 1`、`Depth1BothSmallerPrograms = 1`，说明当前仍不应进入 Misc8 two-swap。
- 最新 P8b-3.5 ffbench attribution：`testsuite_misc_ffbench` 的 `instcombine,simplifycfg` case 中 `LocalABBAHardHashEqual = False`、`FinalABBAHardHashEqual = False`、`LocalInstructionDelta = 0`、`FinalInstructionDelta = 0`、`LlcTextDelta = -16`、`ClangTextDelta = -3`、`BothCodegenSmaller = True`、`FinalOpcodeDeltaNonZero = num_select_delta=-1;num_or_delta=1`。
- 最新 P8b-3.5 evidence supplement：`data/outputs/core_evidence_report_misc8/` 汇总 `AttemptedSwaps = 56`、`CertifiedIndependentEvents = 32`、`SingleSwapCandidates = 16`、`ObjectSizeEvaluatedCandidates = 16`、`BothSmallerPrograms = 1`、`AttributionCases = 1`、`AttributionObservedButNotCausalProof = True`。
- 最新 P8b-3.5 manifests：`docs/results/p8b_misc8_depth1_analysis_manifest.json`、`docs/results/ffbench_effect_attribution_manifest.json`、`docs/results/core_evidence_misc8_manifest.json`，均记录 `result_generated_from_commit = fc662c18b7d0bf8c78f1e8609ecb5a94e12bd3e3` 与 `ecpor_git_dirty = false`。
- 最新 data 清理：新增 `docs/data_retention_manifest.md`；以后 `data/` 只保留必须保留的文件；删除 `*_work`、旧 P5 commit 输出和重复 P4 final 目录；保留 `data/inputs/`、P4 e83c409、P5/P6 final、pair_tests、P8b-1 pre full matrix 和 P8b-2 static repair 对照。清理后 `data/outputs` 约 `39.75 MB`，`data/certs` 约 `1.42 MB`。
- 重要语义边界：static filter 只做 candidate generation / low priority 排序；lazy validation 只在当前 state 上查询或生成 certificate；input-state certificate 不得复用于 prefix-state。
- 下一步建议：进入 P8b-4，扩展 benchmark ingestion 到 16 或 24 个稳定 C benchmark，但仍保持 depth1-only；只有 both-smaller programs 明显增加后再讨论 bounded two-swap。

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
| 2026-07-02 | P7b.5 two-swap 结果解释与分布分析 | [2026-07-02-23-p7b5-two-swap-analysis.md](progress/2026-07-02-23-p7b5-two-swap-analysis.md) |
| 2026-07-02 | P8a clang-c codegen sensitivity | [2026-07-02-24-p8a-clang-codegen-sensitivity.md](progress/2026-07-02-24-p8a-clang-codegen-sensitivity.md) |
| 2026-07-02 | P8a.5 core evidence report | [2026-07-02-25-p8a5-core-evidence-report.md](progress/2026-07-02-25-p8a5-core-evidence-report.md) |
| 2026-07-02 | P8a.6 core evidence 语义收尾 | [2026-07-02-26-p8a6-core-evidence-semantics.md](progress/2026-07-02-26-p8a6-core-evidence-semantics.md) |
| 2026-07-02 | P8c Queens effect attribution | [2026-07-02-27-p8c-queens-effect-attribution.md](progress/2026-07-02-27-p8c-queens-effect-attribution.md) |
| 2026-07-02 | P8c.1 opcode-level attribution | [2026-07-02-28-p8c1-opcode-attribution.md](progress/2026-07-02-28-p8c1-opcode-attribution.md) |
| 2026-07-02 | P8c.2 attribution summary 纳入 core evidence | [2026-07-02-29-p8c2-core-evidence-attribution-summary.md](progress/2026-07-02-29-p8c2-core-evidence-attribution-summary.md) |
| 2026-07-02 | P8b-0 benchmark ingestion | [2026-07-02-30-p8b0-benchmark-ingest.md](progress/2026-07-02-30-p8b0-benchmark-ingest.md) |
| 2026-07-02 | P8b-1 Misc8 full matrix 与 static filter pre 评估 | [2026-07-02-31-p8b1-misc8-full-matrix.md](progress/2026-07-02-31-p8b1-misc8-full-matrix.md) |
| 2026-07-02 | P8b-2 static filter false-negative repair | [2026-07-02-32-p8b2-static-filter-repair.md](progress/2026-07-02-32-p8b2-static-filter-repair.md) |
| 2026-07-02 | P8b-3-lite Misc8 depth1 chain | [2026-07-02-33-p8b3-lite-misc8-depth1.md](progress/2026-07-02-33-p8b3-lite-misc8-depth1.md) |
| 2026-07-02 | P8b-3.5 Misc8 depth1 结果解释与 ffbench 归因 | [2026-07-02-34-p8b35-misc8-depth1-analysis.md](progress/2026-07-02-34-p8b35-misc8-depth1-analysis.md) |

## 旧文档拆分说明

原 `docs/project_progress.md` 中的历史进度和代码快照已经按事件拆分到 `docs/progress/`。本索引只维护文档组织方式和当前阶段摘要。
