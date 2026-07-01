# P7b.5 Two-Swap Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build P7b.5 result interpretation tooling for the existing P7b bounded two-swap experiment.

**Architecture:** Add a pure CSV analysis module that consumes P7b outputs plus the P6 object-size baseline, writes five stable CSV audit tables and one Markdown report, then extend result manifests to track those analysis artifacts. Keep the analysis offline: it must not rerun LLVM, mutate certificates, or depend on untracked temporary state.

**Tech Stack:** Python standard library CSV/argparse/dataclasses, existing ECPOR manifest helpers, pytest.

---

### Task 1: Add RED tests for analysis tables

**Files:**
- Create: `tests/test_two_swap_analysis.py`
- Create later: `src/ecpor/two_swap_analysis.py`

- [ ] **Step 1: Write failing tests**

Add tests that build tiny in-memory CSV fixtures under a temp directory and call the desired API:

```python
from ecpor.two_swap_analysis import run_two_swap_analysis

result = run_two_swap_analysis(
    seeds_csv=tmp / "two_swap_seeds.csv",
    attempts_csv=tmp / "two_swap_attempts.csv",
    candidates_csv=tmp / "two_swap_candidates.csv",
    pipeline_runs_csv=tmp / "two_swap_pipeline_runs.csv",
    object_size_csv=tmp / "two_swap_object_size.csv",
    p6_object_size_csv=tmp / "p6_object_size.csv",
    output_dir=tmp / "analysis",
)
assert result.summary["programs"] == 2
assert result.summary["depth2_smaller_text"] == 2
assert result.summary["depth2_improves_program_depth1_best_count"] == 1
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_analysis.py
```

Expected:

```text
ModuleNotFoundError: No module named 'ecpor.two_swap_analysis'
```

### Task 2: Implement `two_swap_analysis.py`

**Files:**
- Create: `src/ecpor/two_swap_analysis.py`
- Modify: `src/ecpor/__init__.py`

- [ ] **Step 1: Add dataclass and CSV field constants**

Create `TwoSwapAnalysis` with rows for program summary, pair summary, depth2 details, cache audit, duplicate audit, plus summary metadata.

- [ ] **Step 2: Implement `run_two_swap_analysis(...)`**

Load:

```text
two_swap_seeds.csv
two_swap_attempts.csv
two_swap_candidates.csv
two_swap_pipeline_runs.csv
two_swap_object_size.csv
P6 object_size.csv
```

Compute:

```text
p7b_program_summary.csv
p7b_pair_summary.csv
p7b_depth2_details.csv
p7b_cache_audit.csv
p7b_duplicate_audit.csv
p7b_analysis_report.md
```

- [ ] **Step 3: Add CLI**

Expose:

```powershell
python -m ecpor.two_swap_analysis --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --out data\outputs\bounded_two_swap_p7b_analysis
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_two_swap_analysis.py
```

Expected:

```text
all tests pass
```

### Task 3: Extend tracked result manifests

**Files:**
- Modify: `src/ecpor/result_manifest.py`
- Modify: `tests/test_result_manifest.py`

- [ ] **Step 1: Add failing manifest test**

Assert `build_p7b_analysis_manifest(...)` includes:

```text
stage = P7b.5
outputs.p7b_program_summary_csv
outputs.p7b_cache_audit_csv
summary.depth2_smaller_text
```

- [ ] **Step 2: Implement manifest builder and CLI subcommand**

Add:

```python
def build_p7b_analysis_manifest(...): ...
```

CLI:

```powershell
python -m ecpor.result_manifest p7b-analysis ...
```

- [ ] **Step 3: Verify tests**

Run:

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q tests/test_result_manifest.py tests/test_two_swap_analysis.py
```

### Task 4: Run real P7b.5 analysis

**Files:**
- Generated only: `data/outputs/bounded_two_swap_p7b_analysis/`
- Generated tracked manifest: `docs/results/p7b_analysis_manifest.json`

- [ ] **Step 1: Run analysis**

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.two_swap_analysis --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --out data\outputs\bounded_two_swap_p7b_analysis
```

- [ ] **Step 2: Generate manifest**

```powershell
$env:PYTHONPATH = "src"
D:\Miniconda\envs\dlm\python.exe -m ecpor.result_manifest p7b-analysis --out-manifest docs\results\p7b_analysis_manifest.json --p7-dir data\outputs\bounded_two_swap_p7b --p6-object-size data\outputs\code_size_p6_final\object_size.csv --analysis-dir data\outputs\bounded_two_swap_p7b_analysis --repo-root . --result-generated-from-commit <source-commit>
```

### Task 5: Update docs and verify

**Files:**
- Modify: `README.md`
- Modify: `docs/project_progress.md`
- Modify: `docs/data_retention_manifest.md`
- Create: `docs/progress/2026-07-02-23-p7b5-two-swap-analysis.md`

- [ ] **Step 1: Update docs**

Add commands, retention entries, and Chinese progress notes with code snapshots and result numbers.

- [ ] **Step 2: Verify**

Run:

```powershell
D:\Miniconda\envs\dlm\python.exe -m pytest -q
D:\Miniconda\envs\dlm\python.exe -m json.tool docs\results\p7b_analysis_manifest.json
git diff --check
```

- [ ] **Step 3: Commit**

```powershell
git add ...
git commit -m "add P7b analysis reports"
```
