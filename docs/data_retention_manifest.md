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
data/outputs/pair_tests_p8b_misc8/
data/outputs/cert_summary_p8b_misc8_pre.csv
data/outputs/cert_summary_report_p8b_misc8_pre.txt
data/outputs/static_filter_decisions_p8b_misc8_pre.csv
data/outputs/static_filter_report_p8b_misc8_pre.md
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p4_e83c409_second.csv
data/outputs/lazy_validation_p4_e83c409_first.md
data/outputs/lazy_validation_p4_e83c409_second.md
data/certs/pair_tests/
data/certs/pair_tests_p8b_misc8/
data/certs/lazy_validation_p4_e83c409/
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
