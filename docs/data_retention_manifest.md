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
data/outputs/lazy_validation_p4_e83c409_first.csv
data/outputs/lazy_validation_p4_e83c409_second.csv
data/outputs/lazy_validation_p4_e83c409_first.md
data/outputs/lazy_validation_p4_e83c409_second.md
data/certs/pair_tests/
data/certs/lazy_validation_p4_e83c409/
data/certs/bounded_two_swap_p7a/
data/certs/bounded_two_swap_p7b/
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
