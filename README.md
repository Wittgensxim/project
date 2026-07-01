# ECPOR

ECPOR is an evidence-carrying phase-ordering reduction prototype for LLVM IR pipelines.

The current workspace implements MVP-0/P0:

- fixed local LLVM environment metadata
- conservative hard IR hashing
- structured `opt` runner results
- minimal scalar pipeline config
- state-indexed adjacent-swap pair certificates
- certificate summary reporting, not-certified diff reports, and text-level IR feature scanning
- high-recall static pair-filter candidate reports
- minimal lazy validation and bounded local one-swap exploration
- three C microbenchmarks for smoke testing

## Local LLVM

This project currently uses:

```text
E:/llvm/build/bin/clang.exe
E:/llvm/build/bin/opt.exe
E:/llvm/build/bin/llc.exe
E:/llvm/build/bin/llvm-size.exe
E:/llvm/build/bin/llvm-config.exe
```

Detected LLVM version: `23.0.0git`.

## Benchmarks

The formal benchmark root is:

```text
E:/llvm-test-suite
```

See `configs/benchmarks.yaml` for the current MVP subset. The files under `benchmarks/micro` are quick smoke-test inputs only.

## Unit Tests

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
```

## Smoke Test

Generate LLVM IR:

```powershell
E:\llvm\build\bin\clang.exe -O0 -Xclang -disable-O0-optnone -S -emit-llvm benchmarks\micro\dead_code.c -o data\inputs\dead_code.ll
```

Run a minimal `opt` pipeline through the Python runner:

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; r = run_opt('data/inputs/dead_code.ll', 'function(instcombine,dce)', 'data/outputs/dead_code.opt.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"
```

Generate a state-indexed adjacent-swap certificate:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.pair_test --state data\inputs\testsuite_stanford_bubblesort.ll --A instcombine --B dce --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert data\certs\testsuite_stanford_bubblesort__instcombine__dce.json --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

Reproduce a saved certificate:

```powershell
D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.pair_test import reproduce_certificate; r = reproduce_certificate('data/certs/testsuite_stanford_bubblesort__instcombine__dce.json', opt_path='E:/llvm/build/bin/opt.exe', output_dir='data/outputs/pair_tests/repro'); print(r.reproduced, r.original_label, r.reproduced_label, r.reason)"
```

Generate the 3 Stanford programs by 8 pass-pair certificate matrix:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates --preset stanford-3x8 --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert-dir data\certs\pair_tests --summary data\outputs\cert_summary.csv --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

Generate the 3 Stanford programs by the full 28 unordered pass-pair matrix:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates --preset stanford-3x28 --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert-dir data\certs\pair_tests --summary data\outputs\cert_summary.csv --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

Generate the 8 Stanford calibration/hold-out programs by the full 28 unordered pass-pair matrix:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.batch_certificates --preset stanford-8x28 --opt E:\llvm\build\bin\opt.exe --out data\outputs\pair_tests --cert-dir data\certs\pair_tests --summary data\outputs\cert_summary.csv --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

Generate a text summary report from `cert_summary.csv`:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.summary_report data\outputs\cert_summary.csv --out data\outputs\cert_summary_report.txt
```

Generate the not-certified feature-delta report:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.diff_report data\outputs\cert_summary.csv --out-md data\outputs\not_certified_diff_report.md --out-csv data\outputs\not_certified_diff_summary.csv
```

Generate static filter decisions and evaluate them against `cert_summary.csv`:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter --program-preset stanford-3 --observed-summary data\outputs\cert_summary.csv --out-csv data\outputs\static_filter_decisions.csv --out-report data\outputs\static_filter_report.md --window-size 7
```

Generate per-program static filter decisions for the 8-program calibration/hold-out set:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.static_filter --program-preset stanford-8 --mode per-program --observed-summary data\outputs\cert_summary.csv --out-csv data\outputs\static_filter_decisions_per_program.csv --out-report data\outputs\static_filter_report_per_program.md --window-size 7
```

Run minimal P4 anchor-adjacent lazy validation:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.adjacent_swap_driver --program-preset stanford-8 --opt E:\llvm\build\bin\opt.exe --cert-dir data\certs\lazy_validation_p4 --out data\outputs\lazy_validation_p4 --attempts-csv data\outputs\lazy_validation_p4_first.csv --report data\outputs\lazy_validation_p4_first.md --env-id 3c3dab32ea1756773748a56d639e6bb201042576bb0653fd466e109d1946298e --llvm-version 23.0.0git
```

Run P5 bounded local one-swap exploration from a P4 attempts CSV:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_local_driver --program-preset stanford-8 --pipeline configs\pipeline_scalar.yaml --attempts-csv data\outputs\lazy_validation_p4_e83c409_first.csv --out data\outputs\bounded_local_p5_p6_final --opt E:\llvm\build\bin\opt.exe --timeout-sec 30
```

Run P6 code-size evaluation for P5 outputs:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.code_size_evaluator --p5-dir data\outputs\bounded_local_p5_p6_final --out data\outputs\code_size_p6_final --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

Run P7a bounded two-swap smoke test:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7a --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

Run P7a second-run cache reuse check:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7a_second --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30
```

Generate a tracked P7a result manifest:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p7a --out-manifest docs\results\p7a_cache_reuse_manifest.json --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --output-dir data\outputs\bounded_two_swap_p7a_second --cert-dir data\certs\bounded_two_swap_p7a --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --stage-name P7a-cache --description "P7a second-run cache reuse check with the first P7a certificate directory."
```

Run P7b per-program top-3 seed bounded two-swap experiment:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --seed-mode top-k-per-program --max-seeds-per-program 3 --max-unique-depth2-per-program 5 --max-total-depth2 40 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7b --cert-dir data\certs\bounded_two_swap_p7b --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30 --stage-name P7b
```

Run P7b second-run cache reuse check:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.bounded_two_swap_driver --program-preset stanford-8 --seed-mode top-k-per-program --max-seeds-per-program 3 --max-unique-depth2-per-program 5 --max-total-depth2 40 --p5-dir data\outputs\bounded_local_p5_p6_final --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --out data\outputs\bounded_two_swap_p7b_second --cert-dir data\certs\bounded_two_swap_p7b --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --timeout-sec 30 --stage-name P7b-cache
```

Generate a tracked P7b result manifest:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p7a --out-manifest docs\results\p7b_bounded_two_swap_manifest.json --p5-candidates data\outputs\bounded_local_p5_p6_final\candidates.csv --p5-pipeline-runs data\outputs\bounded_local_p5_p6_final\pipeline_runs.csv --p6-object-size data\outputs\code_size_p6_final\object_size.csv --passspec configs\passspec.yaml --output-dir data\outputs\bounded_two_swap_p7b --cert-dir data\certs\bounded_two_swap_p7b --opt E:\llvm\build\bin\opt.exe --llc E:\llvm\build\bin\llc.exe --llvm-size E:\llvm\build\bin\llvm-size.exe --stage-name P7b --description "P7b per-program top-3 seed bounded two-swap controlled experiment."
```

Scan soft IR features for one output:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.feature_scan data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ab.ll
```
