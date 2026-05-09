---
phase: 04-full-execution-publication
plan: "02"
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
key-files:
  created:
    - tests/test_runner_full_study.py
  modified:
    - scripts/run_pilot.py
key-decisions:
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
---

# Phase 4 Plan 02: Full-Study Runner Summary

**Resumable full-study runner with five budget tiers, model-tagged summaries, and deterministic run directories.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-09T02:14:25Z
- **Completed:** 2026-05-09T02:20:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]`.
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

## Deviations from Plan

### Auto-fixed Issues

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

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `04-03`: summary rows now include `model`, full-study logs have deterministic directories, and resume-safe output is available for analysis aggregation.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-09*
