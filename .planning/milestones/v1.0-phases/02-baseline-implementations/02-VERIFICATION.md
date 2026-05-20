# Phase 2 Verification: Baseline Implementations

**Status:** PASS  
**Verified:** 2026-05-08

## Requirements Verified

| Requirement | Result | Evidence |
|-------------|--------|----------|
| BASE-01 | PASS | Truncation/sliding-window baseline implemented and covered by strategy tests. |
| BASE-02 | PASS | Summary-buffer baseline implemented and covered by strategy tests. |
| BASE-03 | PASS | RAG baseline implemented and covered by RAG tests. |
| BASE-04 | PASS | Letta hierarchical memory baseline implemented and covered by isolated Letta tests. |
| BASE-05 | PASS | Mem0 baseline implemented; local config now uses current mem0 `chroma` provider and Ollama LLM config. |
| BASE-06 | PASS | LLMLingua baseline implemented and covered by isolated LLMLingua tests. |

## Validation Evidence

- `python -m pytest tests/ -q` -> 52 passed, 2 warnings.
- `TAU2_DATA_DIR=.deps/tau2-bench/data python scripts/run_pilot.py --full-study --dry-run --model qwen2.5:14b --limit-tasks 1 --tasks swe long tau --run-id audit_all_tasks_strategies_dry` enumerated all 3 task families, 6 strategies, and 5 budget tiers.

## Residual Risk

The model-backed baselines require local runtime dependencies and model assets. Those were hydrated and validated during the Phase 4 audit dry-run; full accuracy conclusions still depend on completing long model sweeps.
