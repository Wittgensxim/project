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
- three C microbenchmarks for smoke testing

## Local LLVM

This project currently uses:

```text
E:/llvm/build/bin/clang.exe
E:/llvm/build/bin/opt.exe
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

Scan soft IR features for one output:

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.feature_scan data\outputs\pair_tests\e4ca9139c215300ca724c57abdd48765563ebac9de2297a8ff3d69bf1201e954\ab.ll
```
