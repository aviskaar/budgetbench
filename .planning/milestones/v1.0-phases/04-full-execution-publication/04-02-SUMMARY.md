---
phase: 04-full-execution-publication
plan: "02"
<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
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
=======
subsystem: full-study-runner
tags: [runner, full-study, resume, jsonl, cli]
requires:
  - phase: 04-full-execution-publication
    provides: [rag-longbench-budget-fix]
provides:
  - Full-study budget tiers
  - Resumable summary.jsonl execution
  - Model-aware summary schema
affects: [phase-04-analysis, publication-results]
tech-stack:
  added: []
  patterns: [resume-skip-by-combination, model-tagged-summary-rows, direct-script-src-bootstrap]
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md
key-files:
  created:
    - tests/test_runner_full_study.py
  modified:
    - scripts/run_pilot.py
key-decisions:
<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
  - "Full-study mode ignores --limit-budgets so the complete 5-tier sweep is stable."
  - "Ollama's OpenAI-compatible endpoint is now the default runner URL."
requirements-completed: [EVAL-02, EVAL-03]
duration: 20 min
completed: 2026-05-08
=======
  - "Full-study mode always uses [2048, 4096, 8192, 16384, 32768] and ignores --limit-budgets."
  - "summary.jsonl rows include the model argument for multi-model aggregation."
  - "Direct script execution bootstraps src/ so documented CLI commands work without package installation."
patterns-established:
  - "Completed combinations are identified by (task, strategy, budget) tuples from summary.jsonl."
requirements-completed:
  - EVAL-02
  - EVAL-03
duration: 6 min
completed: 2026-05-09
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md
---

# Phase 4 Plan 02: Full-Study Runner Summary

<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
**The pilot runner now supports resumable 5-tier full-study execution with model-tagged summary rows.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-08T00:15:00Z
- **Completed:** 2026-05-08T00:35:00Z
=======
**Resumable full-study runner with five budget tiers, model-tagged summaries, and deterministic run directories.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-09T02:14:25Z
- **Completed:** 2026-05-09T02:20:14Z
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]`.
<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
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
=======
- Added `load_completed_combinations()` to support resume/skip behavior from partial `summary.jsonl` files.
- Added `--full-study` and `--run-id` CLI flags.
- Routed full-study logs to `logs/full_study/{run_id_or_timestamp}/`.
- Added `"model": args.model or "unknown"` to success and error summary rows.
- Changed the default LLM endpoint to Ollama's OpenAI-compatible default: `http://localhost:11434/v1/chat/completions`.
- Added focused tests for full-study tiers, resume parsing, malformed summary rows, missing files, and schema expectations.

## Task Commits

1. **Task 1: Add full-study runner behavior** - `69e09fb` (`feat(04-02)`)
2. **Task 2: Write full-study runner tests** - `851740b` (`test(04-02)`)

## Files Created/Modified

- `scripts/run_pilot.py` - Adds full-study mode, resume logic, model field, run-id support, direct `src/` bootstrap, and RAG optional-skip handling.
- `tests/test_runner_full_study.py` - Adds 5 focused tests for the new full-study helpers and summary schema.

## Decisions Made

- Resume keys are limited to `(task, strategy, budget)` because the summary file is scoped to a single run directory and model.
- Malformed `summary.jsonl` lines are skipped so interrupted runs can still resume.
- RAG initialization is now guarded like the other model-backed optional strategies, so `--dry-run` remains useful in offline environments.
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md

## Deviations from Plan

### Auto-fixed Issues

<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
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
=======
**1. [Rule 3 - Blocking] Direct script execution could not import `budgetbench`**
- **Found during:** CLI verification with `python scripts/run_pilot.py --help`.
- **Issue:** The repository uses a `src/` layout without package installation; direct script execution did not inherit pytest's `conftest.py` path setup.
- **Fix:** Added a local `sys.path` bootstrap for `../src` at the top of `scripts/run_pilot.py`.
- **Files modified:** `scripts/run_pilot.py`.
- **Verification:** `python scripts/run_pilot.py --help` exits 0 and shows `--full-study` / `--run-id`.
- **Committed in:** `69e09fb`.

**2. [Rule 3 - Blocking] Dry-run crashed when RAG embedding model was unavailable**
- **Found during:** CLI verification with `python scripts/run_pilot.py --full-study --dry-run --model qwen2.5:14b`.
- **Issue:** `build_strategies()` instantiated `RAGStrategy()` unguarded, which attempted a HuggingFace download in offline environments.
- **Fix:** Wrapped RAG initialization in the same skip-on-error pattern already used for Mem0, Letta, and LLMLingua.
- **Files modified:** `scripts/run_pilot.py`.
- **Verification:** Full-study dry-run exits 0 and prints DRY RUN rows for available strategies across all 5 tiers.
- **Committed in:** `69e09fb`.

---

**Total deviations:** 2 auto-fixed (Rule 3).
**Impact on plan:** Both fixes were necessary for the documented CLI verification commands. Production execution still uses available strategy implementations when dependencies are present.

## Issues Encountered

None remaining. The dry-run command reports unavailable optional strategies in this sandbox, then continues with available strategies.

## Verification

- `python -m pytest tests/test_runner_full_study.py -v` — 5 passed.
- `python scripts/run_pilot.py --help` — shows `--full-study` and `--run-id`.
- `python scripts/run_pilot.py --full-study --dry-run --model qwen2.5:14b` — exits 0 and prints DRY RUN rows for all 5 budget tiers.
- `grep -v '^#' scripts/run_pilot.py | grep -c "FULL_STUDY_BUDGET_TIERS"` — 2.
- `grep -c '"model".*args.model' scripts/run_pilot.py` — 2.
- `python -m pytest tests/ -v` — 45 passed, 2 warnings.
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md

## User Setup Required

None - no external service configuration required.

<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-02-SUMMARY.md
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
=======
## Next Phase Readiness

Ready for `04-03`: summary rows now include `model`, full-study logs have deterministic directories, and resume-safe output is available for analysis aggregation.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-09*
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-02-SUMMARY.md
