---
phase: 03-task-integration-pilot-execution
plan: "04"
subsystem: tau-bench-integration
tags: [tau-bench, testing, documentation, gap-closure, phase3]
dependency_graph:
  requires: ["03-03"]
  provides: ["tau-importerror-behavior", "tau-tests", "pilot-scope-docs"]
  affects: [".planning/REQUIREMENTS.md", ".planning/phases/03-task-integration-pilot-execution/PILOT_RESULTS.md"]
tech_stack:
  added: ["conftest.py root sys.path fix"]
  patterns: ["TAU2_AVAILABLE flag pattern", "pytest.patch for module-level flags"]
key_files:
  created:
    - src/budgetbench/tasks/tau.py (rewritten with ImportError fallback)
    - tests/test_tau.py (4 tests for absent/mocked-present paths)
    - conftest.py (root-level sys.path fix for src/ layout)
  modified:
    - tests/test_tasks_wave2.py (updated to expect ImportError, not mock success)
    - .planning/REQUIREMENTS.md (TASK-02 marked Partial)
    - .planning/phases/03-task-integration-pilot-execution/PILOT_RESULTS.md (scope note + Phase 4 verdict)
decisions:
  - "Root conftest.py added to expose src/ layout to pytest without requiring pip install (auto-fix Rule 3)"
  - "test_tau_wrapper and test_runner updated to expect ImportError: aligns tests with correct tau.py contract"
  - "TASK-02 marked Partial (not Pending) in REQUIREMENTS.md: reflects integration-wired reality"
metrics:
  duration: "~4 minutes"
  completed_date: "2026-05-07"
  tasks_completed: 2
  files_changed: 6
---

# Phase 3 Plan 04: Gap Closure — τ²-bench Stub and Pilot Scope Summary

**One-liner:** Fixed tau.py to raise ImportError when tau2-bench absent, added 4-test suite, and re-framed PILOT_RESULTS.md to explicitly scope quality-vs-budget curves to Phase 4.

## What Was Built

Two gap-closure items left from the Phase 3 verification report (03-VERIFICATION.md):

### Gap 1: τ²-bench Silent Mock (Resolved)

`tau.py` previously returned `{"success": True, "turns": 1}` when `tau2-bench` was not installed, making TASK-02 untestable and hiding integration failures at runtime.

**Fix applied:**
- Replaced `get_env = None` pattern with `TAU2_AVAILABLE` boolean flag
- `get_dataset()` now raises `ImportError("tau2-bench is not installed...")` when absent
- `run()` now raises `ImportError("tau2-bench is not installed...")` when absent
- Existing multi-turn loop (calls `run_evaluation_task`, `env.step()`) preserved exactly

**New test file `tests/test_tau.py`** (4 tests):
1. `test_tau_raises_importerror_when_tau2_absent` — both `run()` and `get_dataset()` raise `ImportError`
2. `test_tau_dataset_calls_env_when_available` — with mocked tau2, `get_dataset()` calls `env.get_dataset()`
3. `test_tau_dataset_limit` — `get_dataset(limit=1)` correctly slices to 1 item
4. `test_tau_run_calls_harness_when_available` — with mocked tau2, `run()` calls `run_evaluation_task`

### Gap 2: Tradeoff Curve Scope Mismatch (Resolved)

`PILOT_RESULTS.md` contained a projected/qualitative tradeoff table without explicitly framing it as a projection.

**Documentation updates:**
- Added explicit scope note block above "Initial Tradeoff Curves" section explaining the table is a projection, not measured data
- Added "Phase 3 verdict" line at the end of the Validation Pilot vs Full Study table
- Updated `REQUIREMENTS.md` TASK-02 row from "Pending" to "Partial — integration wired, full sweep deferred to Phase 4"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Root conftest.py missing — budgetbench not importable without src/ in sys.path**

- **Found during:** Task 1 RED phase — `patch("budgetbench.tasks.tau.TAU2_AVAILABLE", ...)` failed with `ModuleNotFoundError: No module named 'budgetbench'`
- **Issue:** Project uses `src/` layout (package at `src/budgetbench/`) but has no `pyproject.toml`, `setup.py`, or root `conftest.py` adding `src/` to `sys.path`. All tests were broken for direct `import budgetbench` calls; only worked if run from a context where the path was already set.
- **Fix:** Created `conftest.py` at project root with `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))`.
- **Files modified:** `conftest.py` (new)
- **Commit:** a4b27f0

**2. [Rule 1 - Bug] test_tau_wrapper and test_runner relied on mock success behavior**

- **Found during:** Task 1 GREEN phase — after fixing tau.py, existing test_tasks_wave2.py tests failed
- **Issue:** `test_tau_wrapper` asserted `task.grade(result, item) is True` expecting the old mock return value; `test_runner` asserted `results[0]["is_correct"] is True` for the same reason.
- **Fix:** Updated both tests to `pytest.raises(ImportError, match="tau2-bench")` — the correct contract now that tau.py raises instead of mocking.
- **Files modified:** `tests/test_tasks_wave2.py`
- **Commit:** a4b27f0

## Test Results

All 38 tests pass:
- `tests/test_tau.py`: 4 passed (new)
- `tests/test_tasks_wave2.py`: 3 passed (updated)
- All other test files: 31 passed (unchanged)

## Self-Check: PASSED

Files created/modified:
- FOUND: src/budgetbench/tasks/tau.py
- FOUND: tests/test_tau.py
- FOUND: conftest.py
- FOUND: tests/test_tasks_wave2.py
- FOUND: .planning/REQUIREMENTS.md (contains "Partial")
- FOUND: .planning/phases/03-task-integration-pilot-execution/PILOT_RESULTS.md (contains "Phase 4 deliverable")

Commits:
- a4b27f0: feat(03-04): fix tau.py fallback — raise ImportError when tau2 absent, add tests
- cdc6942: docs(03-04): update TASK-02 scope and PILOT_RESULTS phase framing
