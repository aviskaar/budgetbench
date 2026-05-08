---
phase: 04-full-execution-publication
plan: "01"
subsystem: evaluation
tags: [longbench, rag, chunking, budget-enforcement, testing]
requires:
  - phase: 03-task-integration-pilot-execution
    provides: "Pilot identified LongBench+RAG budget violation gap"
provides:
  - "LongBenchV2Task context chunking with budget-aware message formatting"
  - "RAG integration coverage proving chunked LongBench messages are indexed"
affects: [full-study-runner, result-analysis, phase-04]
tech-stack:
  added: []
  patterns:
    - "LongBench context is split into intermediate user messages so RAG can index messages[1:-1]"
key-files:
  created: []
  modified:
    - src/budgetbench/tasks/long.py
    - tests/test_tasks_wave1.py
    - tests/test_rag.py
key-decisions:
  - "Kept final LongBench question as the last user message so RAG treats it as the retrieval query."
  - "Used the planned 4-character/token heuristic with 512-token maximum chunk size."
requirements-completed: [EVAL-02]
duration: 15 min
completed: 2026-05-08
---

# Phase 4 Plan 01: RAG LongBench Chunking Summary

**LongBench context now becomes budget-sized retrievable chunks, allowing RAG to index context instead of receiving an empty retrieval corpus.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-08T00:00:00Z
- **Completed:** 2026-05-08T00:15:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `budget` support to `LongBenchV2Task.format_message()` without breaking existing callers.
- Split oversized LongBench context into intermediate user messages and kept the MCQ question as the final query message.
- Added unit coverage for chunk count, chunk size, short-context behavior, and RAG indexing over chunked LongBench messages.

## Task Commits

1. **Task 1-2: LongBench chunking and RAG tests** - `f5c3d44` (feat)

## Files Created/Modified

- `src/budgetbench/tasks/long.py` - Adds budget-aware chunking and passes `max_tokens` through from `run()`.
- `tests/test_tasks_wave1.py` - Adds `test_longbench_chunking`.
- `tests/test_rag.py` - Adds `test_rag_longbench_chunked`.

## Decisions Made

- Kept context and question in separate messages even for short contexts, yielding `[system, context, question]` consistently.
- Did not modify `RAGStrategy`; the fix is localized to LongBench message formatting as planned.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created local test environment**
- **Found during:** Verification for Plan 04-01
- **Issue:** The checkout had no `.venv`, and system Python was missing project dependencies while also being externally managed.
- **Fix:** Created `.venv` and installed required test/runtime dependencies locally.
- **Files modified:** None tracked; `.venv/` is ignored.
- **Verification:** Targeted tests ran through `.venv/bin/python`.
- **Committed in:** Not committed; environment setup only.

---

**Total deviations:** 1 auto-fixed (1 blocking environment issue).
**Impact on plan:** No product scope change. The local environment was necessary to verify the planned tests.

## Issues Encountered

Initial test collection failed on missing dependencies (`datasets`, `tiktoken`, then `docker`) until the local virtual environment was created and populated.

## User Setup Required

None - no external service configuration required.

## Test Results

- `rtk .venv/bin/python -m pytest tests/test_tasks_wave1.py -q` — 3 passed
- `rtk .venv/bin/python -m pytest tests/test_rag.py -q` — 4 passed, 1 warning from ChromaDB dependency

## Self-Check: PASSED

- `format_message(self, item: Dict[str, Any], budget: int = 8192)` exists.
- `run()` calls `format_message(item, budget=max_tokens)`.
- `Context part` branch exists for oversized context.
- Targeted tests pass.

## Next Phase Readiness

Plan 04-02 can now extend the runner for full-study execution using the fixed LongBench+RAG formatting.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-08*
