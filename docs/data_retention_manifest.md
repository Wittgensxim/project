# ECPOR data retention manifest

本清单用于约束 `data/` 目录的保留与清理。硬规则是：`data/` 只保留必须保留的文件；输入保留、当前 final 结果保留、仍支撑复现或人工检查的证据保留，其余可再生成的中间产物阶段完成后清理。

## 保留

```text
data/inputs/
data/outputs/pair_tests/
data/outputs/lazy_validation_p4_e83c409/
data/outputs/bounded_local_p5_p6_final/
data/outputs/code_size_p6_final/
data/outputs/bounded_two_swap_p7a/
data/outputs/bounded_two_swap_p7a_second/
data/outputs/bounded_two_swap_p7b/
data/outputs/bounded_two_swap_p7b_second/
data/outputs/bounded_two_swap_p7b_analysis/
data/outputs/codegen_sensitivity_p8a/
data/outputs/core_evidence_report/
data/outputs/effect_attribution_queens/
data/outputs/benchmark_ingest_p8b/
data/outputs/benchmark_ingest_diverse8/
data/outputs/pair_tests_p8b_misc8/
data/outputs/pair_tests_p9_diverse8/
data/outputs/lazy_validation_p9_diverse8/
data/outputs/bounded_local_p9_diverse8/
data/outputs/code_size_p9_diverse8/
data/outputs/codegen_sensitivity_p9_diverse8/
data/outputs/depth1_analysis_p9_diverse8/
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_report_p8b_misc8_pre.txt
data/outputs/static_filter_decisions_p8b_misc8_pre.csv
data/outputs/static_filter_report_p8b_misc8_pre.md
data/outputs/cert_summary_p9_diverse8_pre.csv
data/outputs/cert_summary_report_p9_diverse8_pre.txt
data/outputs/static_filter_decisions_p9_diverse8_pre.csv
data/outputs/static_filter_report_p9_diverse8_pre.md
data/outputs/static_filter_decisions_p8b_misc8_post.csv
data/outputs/static_filter_report_p8b_misc8_post.md
data/outputs/static_filter_repair_report_p8b_misc8.md
data/outputs/lazy_validation_p8b_misc8/
data/outputs/bounded_local_p8b_misc8/
data/outputs/code_size_p8b_misc8/
data/outputs/codegen_sensitivity_p8b_misc8/
data/outputs/depth1_analysis_p8b_misc8/
data/outputs/effect_attribution_ffbench/
data/outputs/core_evidence_report_misc8/
data/outputs/final_mvp_summary/
data/outputs/combined_depth1_summary/
data/outputs/passspec_audit/
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p4_e83c409_second.csv
data/outputs/lazy_validation_p4_e83c409_first.md
data/outputs/lazy_validation_p4_e83c409_second.md
data/certs/pair_tests/
data/certs/pair_tests_p8b_misc8/
data/certs/pair_tests_p9_diverse8/
data/certs/lazy_validation_p4_e83c409/
data/certs/lazy_validation_p8b_misc8/
data/certs/lazy_validation_p9_diverse8/
data/certs/bounded_two_swap_p7a/
data/certs/bounded_two_swap_p7b/
```

`data/outputs/core_evidence_report/` 当前只保留 P8c.2 必要文件：

```text
ecpor_attribution_summary.csv
ecpor_candidate_propagation_funnel.csv
ecpor_certified_pruning_summary.csv
ecpor_core_evidence_report.md
ecpor_objective_layer_summary.csv
ecpor_validation_funnel.csv
```

旧版 `ecpor_reduction_funnel.csv` 与 `ecpor_codegen_sensitivity_summary.csv` 已删除；它们可由旧提交再生成，但当前语义下不再保留。

`data/outputs/effect_attribution_queens/` 当前保留 P8c 必要文件：

```text
states.csv
feature_deltas.csv
opcode_delta.csv
object_size.csv
attribution_report.md
state_outputs/
object_outputs/
```

原因：P8c 是单程序归因证据，`states.csv` / `feature_deltas.csv` / `object_size.csv` 是可读摘要；`state_outputs/` 和 `object_outputs/` 用于人工复查具体 IR 与目标文件大小来源。

`data/outputs/benchmark_ingest_p8b/` 当前只保留 P8b-0 必要文件：

```text
ingest_summary.csv
report.md
```

原因：P8b-0 的 accepted `.ll` 已作为 `data/inputs/testsuite_misc_*.ll` 跟踪；`ingest_summary.csv` 和 `report.md` 记录筛选成功/失败原因。scratch IR、scalar IR 和 object 文件默认不保留。

`data/outputs/benchmark_ingest_diverse8/` 当前只保留 P9-4a 必要文件：

```text
ingest_summary.csv
report.md
```

原因：P9-4a 的 accepted `.ll` 已作为 `data/inputs/testsuite_diverse_*.ll` 跟踪；`ingest_summary.csv` 和 `report.md` 记录 diverse8 的 source-dir stratification、family cap 和 LLVM/object-size gate 结果。scratch IR、scalar IR 和 object 文件默认不保留。

P8b-1 当前保留 pre-tuning full matrix 必要文件：

```text
data/outputs/pair_tests_p8b_misc8/
data/certs/pair_tests_p8b_misc8/
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_report_p8b_misc8_pre.txt
data/outputs/static_filter_decisions_p8b_misc8_pre.csv
data/outputs/static_filter_report_p8b_misc8_pre.md
```

原因：P8b-1 在 Misc8 × 28 full matrix 上发现 `StaticFalseNegativeObserved = 5`，这些 pre-tuning 输出必须保留，后续 passspec 修正需要与它做 post 对照。`data/outputs/pair_tests_p8b_misc8/repro/` 已删除；它只是 certificate reproduction 的临时输出，可由证书再生成。

P9-4b 当前保留 diverse8 pre-tuning full matrix 必要文件：

```text
data/outputs/pair_tests_p9_diverse8/
data/certs/pair_tests_p9_diverse8/
data/outputs/cert_summary_p9_diverse8_pre.csv
data/outputs/cert_summary_report_p9_diverse8_pre.txt
data/outputs/static_filter_decisions_p9_diverse8_pre.csv
data/outputs/static_filter_report_p9_diverse8_pre.md
```

原因：P9-4b 是 P9-4a diverse8 输入集上的证书层和 static filter pre 评估证据。结果为 `224/224` reproduced、`HardFalseIndependent = 0`、`RunFailed = 0`、`StaticFalseNegativeObserved = 0`，后续 P9-4c depth1 链路需要引用这一组 pre 证据。`repro/` 子目录属于 certificate reproduction 临时输出，可由证书再生成，阶段清理时可以删除。

P9-4c 当前保留 Diverse8 depth1 final 证据：

```text
data/outputs/lazy_validation_p9_diverse8/
data/certs/lazy_validation_p9_diverse8/
data/outputs/bounded_local_p9_diverse8/
data/outputs/code_size_p9_diverse8/
data/outputs/codegen_sensitivity_p9_diverse8/
data/outputs/depth1_analysis_p9_diverse8/
```

原因：P9-4c 是 P9-Diverse8 的 depth1 链路证据，覆盖 P4 prefix-state lazy validation、P5 one-swap candidate propagation、P6 `llc` object-size、P8a-style `clang -c` sensitivity 和 depth1 analysis。结果为 `attempted_adjacent_swaps = 56`、`CertificateReproductionRate = 100.00%`、`run_failed = 0`、`pipeline_run_failed = 0`、`ObjectBuildFailed = 0`、`ClangObjectBuildFailed = 0`、`Depth1BothSmallerPrograms = 0`。这些输出由 tracked manifests 对应：

```text
docs/results/p9_diverse8_lazy_validation_manifest.json
docs/results/p9_diverse8_bounded_local_manifest.json
docs/results/p9_diverse8_code_size_manifest.json
docs/results/p9_diverse8_codegen_sensitivity_manifest.json
docs/results/p9_diverse8_depth1_analysis_manifest.json
```

P8b-2 当前保留 static filter repair 对照文件：

```text
data/outputs/static_filter_decisions_p8b_misc8_post.csv
data/outputs/static_filter_report_p8b_misc8_post.md
data/outputs/static_filter_repair_report_p8b_misc8.md
```

原因：P8b-2 修改了 `configs/passspec.yaml`，需要保留 pre/post 对照证明 `StaticFalseNegativeObserved` 从 `5` 降到 `0`，同时记录 candidate reduction 从 `17.86%` 降到 `10.71%` 的代价。

P8b-3-lite 当前保留 Misc8 depth1 final 证据：

```text
data/outputs/lazy_validation_p8b_misc8/
data/certs/lazy_validation_p8b_misc8/
data/outputs/bounded_local_p8b_misc8/
data/outputs/code_size_p8b_misc8/
data/outputs/codegen_sensitivity_p8b_misc8/
```

原因：P8b-3-lite 是 Misc8 上的 P4/P5/P6/P8a depth1 链路验证，证明该 benchmark set 在不进入 two-swap 的情况下可复现 certificate、生成 one-swap candidate、计算 `llc` code-size 并进行 `clang -c` sensitivity 对照。当前 only both-smaller case 与后续 attribution 直接相关，因此保留 final 输出和 lazy-validation certificates；中间 object 输出仍可按阶段清理，但本轮先作为 final 证据保留。

P8b-3.5 当前保留 Misc8 depth1 解释与 ffbench 归因证据：

```text
data/outputs/depth1_analysis_p8b_misc8/
data/outputs/effect_attribution_ffbench/
data/outputs/core_evidence_report_misc8/
```

原因：P8b-3.5 不新增搜索、不新增 certificate、不运行 runtime，只把 P8b-3-lite 的 depth1 结果解释清楚。`depth1_analysis_p8b_misc8/` 记录 16 个 single-swap candidate 中只有 1 个 both-smaller program；`effect_attribution_ffbench/` 记录唯一 both-smaller case 的 state、feature、opcode 和 object-size 归因；`core_evidence_report_misc8/` 将 validation、candidate propagation、objective layer 与 attribution 汇总为可引用证据。三个目录均有 tracked manifest 对应：

```text
docs/results/p8b_misc8_depth1_analysis_manifest.json
docs/results/ffbench_effect_attribution_manifest.json
docs/results/core_evidence_misc8_manifest.json
```

P9-1 当前保留 MVP 总结表：

```text
data/outputs/final_mvp_summary/
```

原因：P9-1 是当前阶段的主结果入口，不新增实验，只汇总 Stanford-8 与 Misc8 已有证据。目录中保留：

```text
benchmark_set_summary.csv
reduction_summary.csv
objective_summary.csv
attribution_case_summary.csv
mvp_summary_report.md
```

对应 tracked manifest：

```text
docs/results/mvp_summary_manifest.json
```

P9-5 当前保留 post-MVP 24-program depth1 总结表：

```text
data/outputs/combined_depth1_summary/
```

原因：P9-5 不新增实验、不新增 certificate、不新增搜索，只汇总 Stanford-8、Misc8、Diverse8 的 depth1-only 证据。目录中保留：

```text
benchmark_set_summary.csv
depth1_reduction_summary.csv
depth1_objective_summary.csv
depth1_codegen_summary.csv
combined_depth1_report.md
```

对应 tracked manifest：

```text
docs/results/combined_depth1_summary_manifest.json
```

P10 当前保留 PassSpec provenance audit：

```text
data/outputs/passspec_audit/
```

原因：P10 不新增实验、不新增 certificate、不新增 search，只把 `configs/passspec.yaml` 中的经验性 repair hint 升级为带 provenance 的 metadata，并生成可审计摘要。目录中保留：
```text
passspec_hint_summary.csv
passspec_audit_report.md
```

对应 tracked manifest：
```text
docs/results/passspec_audit_manifest.json
```

## 可删除：临时或重复目录

```text
data/outputs/lazy_validation_p4_work/
data/outputs/lazy_validation_p4_final/
data/outputs/bounded_local_p5_work/
data/outputs/bounded_local_p5_92bcc03/
data/outputs/bounded_local_p5_final/
data/outputs/bounded_local_p5_p6_work/
data/outputs/code_size_p6_work/
data/outputs/state_index_safety_work/
data/outputs/state_index_safety_final/
data/outputs/state_index_safety_e83c409/
data/outputs/negative/
data/outputs/pair_tests_p8b_misc8/repro/
data/certs/lazy_validation_p4_work/
data/certs/lazy_validation_p4_final/
data/certs/state_index_safety_work/
data/certs/state_index_safety_final/
data/certs/state_index_safety_e83c409/
```

## 暂不删除

```text
data/outputs/pair_tests/
data/certs/pair_tests/
```

原因：`data/certs/pair_tests/*.json` 中仍记录 `output_ab` / `output_ba` 路径。虽然 pair-test 输出理论上可以再生成，但当前保留它们能让历史证书和 diff report 更容易人工检查。

## 规则

1. `data/inputs/*.ll` 是实验输入，必须保留并允许 Git 跟踪。
2. `data/outputs/` 与 `data/certs/` 是生成产物，默认不进 Git。
3. 每个阶段只保留一个当前 final 输出目录，除非某个旧目录被进度文档明确引用为复现依据。
4. `*_work` 目录默认可删除。
5. 旧 commit 命名目录若已有更新 final 目录替代，可删除。
6. 能由现有命令稳定再生成、且不被当前报告或证书直接引用的中间 `.ll`、`.o`、日志和批量输出不保留。
7. 删除前先确认路径位于 `E:\project\data` 下，不对仓库外路径执行递归删除。
