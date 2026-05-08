---
phase: 04-full-execution-publication
plan: "02"
subsystem: evaluation-runner
tags: [full-study, resume, jsonl, ollama, testing]
requires:
  - phase: 04-full-execution-publication
    provides: "04-01 LongBench chunking fix"
provides:
  - "Full-study runner mode with 5 budget tiers"
  - "Resume support from summary.jsonl"
  - "Model field in summary rows"
affects: [analysis-pipeline, publication, phase-04]
tech-stack:
  added: []
  patterns:
    - "summary.jsonl resume guard keyed by task, strategy, and budget"
key-files:
  created:
    - tests/test_runner_full_study.py
  modified:
    - scripts/run_pilot.py
key-decisions:
  - "Full-study mode ignores --limit-budgets so the complete 5-tier sweep is stable."
  - "Ollama's OpenAI-compatible endpoint is now the default runner URL."
requirements-completed: [EVAL-02, EVAL-03]
duration: 20 min
completed: 2026-05-08
---

# Phase 4 Plan 02: Full-Study Runner Summary

**The pilot runner now supports resumable 5-tier full-study execution with model-tagged summary rows.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-08T00:15:00Z
- **Completed:** 2026-05-08T00:35:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]`.
- Added `--full-study` and `--run-id`, routing full-study logs to `logs/full_study/{run_id}/`.
- Added `load_completed_combinations()` and skip logic for already completed `(task, strategy, budget)` rows.
- Added `model` to both success and error summary rows.
- Added focused tests for budget tiers, resume parsing, malformed JSONL tolerance, missing files, and summary schema.

## Task Commits

1. **Task 1-2: Full-study runner and tests** - `e9392ad` (feat)

## Files Created/Modified

- `scripts/run_pilot.py` - Adds full-study mode, resume support, model summary field, run IDs, Ollama default URL, and direct script import bootstrap.
- `tests/test_runner_full_study.py` - Covers full-study constants, resume parsing, malformed lines, missing summary files, and model summary schema.

## Decisions Made

- Kept dry-run behavior free of summary writes, matching existing pilot semantics.
- Loaded completed combinations once per task before iterating strategies and budgets.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added script-local src path bootstrap**
- **Found during:** CLI verification for `python scripts/run_pilot.py --help`
- **Issue:** Running the script directly failed with `ModuleNotFoundError: No module named 'budgetbench'` because pytest uses `conftest.py` to expose `src/`, but direct script execution did not.
- **Fix:** Added `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))` before importing `budgetbench`.
- **Files modified:** `scripts/run_pilot.py`
- **Verification:** `python scripts/run_pilot.py --help` exits 0 and shows `--full-study` / `--run-id`.
- **Committed in:** `e9392ad`

**2. [Rule 3 - Blocking] Installed optional llmlingua dependency in local test environment**
- **Found during:** Full suite verification
- **Issue:** Existing `tests/test_llmlingua.py` expects `llmlingua` to be installed.
- **Fix:** Installed `llmlingua` into ignored `.venv/`.
- **Files modified:** None tracked.
- **Verification:** Full suite passed after installation.
- **Committed in:** Not committed; environment setup only.

---

**Total deviations:** 2 auto-fixed (2 blocking).
**Impact on plan:** Both fixes enabled planned verification and direct CLI execution. No product scope drift.

## Issues Encountered

Full-suite verification initially failed on missing `llmlingua`; after installing it locally, all tests passed.

## User Setup Required

None - no external service configuration required.

## Test Results

- `rtk .venv/bin/python -m pytest tests/test_runner_full_study.py -q` — 5 passed
- `rtk .venv/bin/python scripts/run_pilot.py --help` — exits 0, shows `--full-study` and `--run-id`
- `rtk .venv/bin/python scripts/run_pilot.py --full-study --dry-run --model qwen2.5:14b --strategies truncation --limit-tasks 1` — exits 0, prints all five budget tiers
- `rtk .venv/bin/python -m pytest tests/ -q` — 45 passed, 2 dependency warnings

## Self-Check: PASSED

- `FULL_STUDY_BUDGET_TIERS` exists with all five tiers.
- `load_completed_combinations()` returns `(task, strategy, budget)` tuples and skips malformed JSONL lines.
- Success and error summary rows include `"model": args.model or "unknown"`.
- `--full-study` and `--run-id` appear in CLI help.

## Next Phase Readiness

Plan 04-03 can now consume full-study `summary.jsonl` rows with stable `model`, `task`, `strategy`, `budget`, and `duration_sec` fields.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-08*
