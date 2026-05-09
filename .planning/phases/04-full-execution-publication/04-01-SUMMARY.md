---
phase: 04-full-execution-publication
plan: "01"
subsystem: rag-longbench
tags: [longbench, rag, chunking, tests, offline-fixtures]
requires:
  - phase: 03-task-integration-pilot-execution
    provides: [pilot-results, rag-budget-gap]
provides:
  - LongBench context chunking for RAG indexing
  - Offline deterministic RAG/Letta/LLMLingua strategy tests
affects: [phase-04-full-study-runner, phase-04-analysis]
tech-stack:
  added: []
  patterns: [budget-aware context chunking, deterministic model-backed test doubles]
key-files:
  created: []
  modified:
    - src/budgetbench/tasks/long.py
    - tests/test_tasks_wave1.py
    - tests/test_rag.py
    - tests/test_letta.py
    - tests/test_llmlingua.py
key-decisions:
  - "LongBench context is split into user-message chunks before the final question so RAG indexes messages[1:-1]."
  - "Model-backed strategy tests use deterministic local doubles instead of downloading HuggingFace models."
patterns-established:
  - "Chunk LongBench context by active budget using a 4 chars/token heuristic."
  - "Unit tests for model-backed strategies must not require network access."
requirements-completed:
  - EVAL-02
duration: 10 min
completed: 2026-05-09
---

# Phase 4 Plan 01: RAG + LongBench Budget Fix Summary

**Budget-aware LongBench chunking gives RAG an indexable retrieval corpus and keeps strategy tests offline.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-05-09T02:03:36Z
- **Completed:** 2026-05-09T02:13:32Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Updated `LongBenchV2Task.format_message()` to accept `budget: int = 8192`, split large context into multiple user messages, and keep the final question as the query message.
- Wired `LongBenchV2Task.run()` to pass `budget=max_tokens` into `format_message()`.
- Added unit coverage for 10K-character LongBench chunking and RAG indexing of chunked context messages.
- Made model-backed strategy tests deterministic and offline-safe so the full suite no longer depends on HuggingFace downloads.

## Task Commits

1. **Task 1: Chunk format_message() and wire budget into run()** - `8505112` (`feat(04-01)`)
2. **Task 2: Add chunking unit test and RAG integration test** - `15d8cf4` (`test(04-01)`)
3. **Deviation: Isolate model-backed strategy tests** - `7930277` (`test(04-01)`)

## Files Created/Modified

- `src/budgetbench/tasks/long.py` - Adds budget-aware context chunking and passes active budget through `run()`.
- `tests/test_tasks_wave1.py` - Adds `test_longbench_chunking`.
- `tests/test_rag.py` - Adds offline embedding double and `test_rag_longbench_chunked`.
- `tests/test_letta.py` - Adds offline embedding double for Letta tests.
- `tests/test_llmlingua.py` - Adds offline compressor double for LLMLingua tests.

## Decisions Made

- Kept the chunking heuristic from the plan: `chunk_size = min(budget // 4, 512)` and `chunk_chars = chunk_size * 4`.
- Preserved backward compatibility by defaulting `format_message(..., budget=8192)`.
- Used test doubles for embedding/compression dependencies because unit tests should validate local strategy logic, not model download availability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Full suite depended on network-backed model downloads**
- **Found during:** Plan-level verification.
- **Issue:** `tests/test_letta.py` and `tests/test_llmlingua.py` instantiated strategies that download HuggingFace models. In the sandbox, this failed with DNS/connect errors even though the 04-01 focused tests passed.
- **Fix:** Added deterministic local test doubles for `SentenceTransformer` and `PromptCompressor`.
- **Files modified:** `tests/test_letta.py`, `tests/test_llmlingua.py`.
- **Verification:** `python -m pytest tests/ -v` passes with 40 tests.
- **Committed in:** `7930277`.

---

**Total deviations:** 1 auto-fixed (Rule 3).
**Impact on plan:** Required to satisfy the plan's full-suite verification gate. No production behavior changed.

## Issues Encountered

Initial focused RAG test run failed because `RAGStrategy()` attempted to download `all-MiniLM-L6-v2`; `tests/test_rag.py` now patches the embedding model locally. Full-suite verification then exposed the same network-dependency pattern in Letta and LLMLingua tests, which was fixed as the deviation above.

## Verification

- `python -m pytest tests/test_tasks_wave1.py tests/test_rag.py -v` — 7 passed.
- `python -m pytest tests/ -v` — 40 passed, 2 warnings.
- `grep -n "def format_message" src/budgetbench/tasks/long.py` — confirms `budget: int = 8192`.
- `grep -n "format_message(item, budget=max_tokens)" src/budgetbench/tasks/long.py` — confirms `run()` passes active budget.
- `grep -c "Context part" src/budgetbench/tasks/long.py` — multi-chunk branch present.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `04-02`: the LongBench/RAG budget violation gap is closed, and the full-study runner can rely on RAG receiving chunked LongBench context.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-09*
