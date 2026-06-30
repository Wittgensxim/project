# ECPOR MVP-0 Environment Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP-0/P0 foundation: fixed LLVM environment discovery, conservative hard hashing, structured `opt` runner results, configs, and smoke-test inputs.

**Architecture:** Keep the first slice small and auditable. `environment.py` detects and fingerprints LLVM tools, `normalizer.py` computes conservative text-based hard hashes, and `runner.py` runs `opt` and returns structured run records. Tests use only standard-library `unittest` plus a fake `opt` script; real LLVM is exercised only in the final smoke test.

**Tech Stack:** Python 3.14 standard library, local LLVM tools in `E:\llvm\build\bin`, `unittest`, PowerShell for verification commands.

---

### File Structure

- Create: `docs/project_progress.md`
- Create: `pyproject.toml`
- Create: `configs/env.yaml`
- Create: `configs/pipeline_scalar.yaml`
- Create: `src/ecpor/__init__.py`
- Create: `src/ecpor/environment.py`
- Create: `src/ecpor/normalizer.py`
- Create: `src/ecpor/runner.py`
- Create: `tests/test_environment.py`
- Create: `tests/test_normalizer.py`
- Create: `tests/test_runner.py`
- Create: `benchmarks/micro/dead_code.c`
- Create: `benchmarks/micro/branch.c`
- Create: `benchmarks/micro/alloca.c`
- Modify: `docs/project_progress.md`

### Task 1: RED Tests

- [ ] Write `tests/test_environment.py` to require parsing `opt --version`, parsing `clang --version`, and stable environment IDs.
- [ ] Write `tests/test_normalizer.py` to require newline-stable hard hashes and metadata preservation.
- [ ] Write `tests/test_runner.py` to require a structured success result and structured failure result from a fake `opt`.
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
- [ ] Expected: tests fail because `ecpor.environment`, `ecpor.normalizer`, and `ecpor.runner` do not exist yet.

### Task 2: Environment Module

- [ ] Implement `src/ecpor/environment.py` with `LLVMEnvironment`, `parse_opt_version`, `parse_clang_version`, `compute_env_id`, and `detect_environment`.
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_environment.py -q`
- [ ] Expected: all environment tests pass.

### Task 3: Normalizer Module

- [ ] Implement `src/ecpor/normalizer.py` with `hard_canonicalize`, `hard_hash_text`, and `hard_hash`.
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_normalizer.py -q`
- [ ] Expected: all normalizer tests pass.

### Task 4: Runner Module

- [ ] Implement `src/ecpor/runner.py` with `RunResult`, `build_opt_command`, and `run_opt`.
- [ ] Run: `D:\Miniconda\envs\dlm\python.exe -m pytest tests/test_runner.py -q`
- [ ] Expected: all runner tests pass.

### Task 5: Configs And Microbenchmarks

- [ ] Add `configs/env.yaml` using the detected local LLVM paths.
- [ ] Add `configs/pipeline_scalar.yaml` with the MVP function scalar pipeline.
- [ ] Add three C microbenchmarks: dead code, branch simplification, and alloca/SROA.
- [ ] Update `docs/project_progress.md`.

### Task 6: Verification

- [ ] Run all unit tests: `D:\Miniconda\envs\dlm\python.exe -m pytest -q`
- [ ] Generate one IR input:
  `E:\llvm\build\bin\clang.exe -O0 -Xclang -disable-O0-optnone -S -emit-llvm benchmarks\micro\dead_code.c -o data\inputs\dead_code.ll`
- [ ] Run real opt through the Python runner:
  `D:\Miniconda\envs\dlm\python.exe -c "import sys; sys.path.insert(0, 'src'); from ecpor.runner import run_opt; r = run_opt('data/inputs/dead_code.ll', 'function(instcombine,dce)', 'data/outputs/dead_code.opt.ll', opt_path='E:/llvm/build/bin/opt.exe'); print(r.exit_code, r.verifier_ok, r.hard_hash)"`
- [ ] Expected: unit tests pass, clang exits 0, runner prints exit code `0`, verifier `True`, and a SHA-256 hash.

### Self-Review

- Spec coverage: MVP-0 environment, runner, hard hash, configs, microbenchmarks, and progress tracking are covered.
- Placeholder scan: no `TBD`, `TODO`, or missing code references remain in this plan.
- Type consistency: the plan consistently uses `LLVMEnvironment`, `RunResult`, `hard_hash`, and `run_opt`.
