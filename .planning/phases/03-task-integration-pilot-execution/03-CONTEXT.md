# Phase 3: Task Integration & Pilot Execution - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate SWE-bench Verified, τ²-bench, and LongBench v2 into the BudgetBench harness and execute a cheap pilot.
</domain>

<decisions>
## Implementation Decisions

### Wrapper Pattern
- Benchmark-specific wrappers in `src/budgetbench/tasks/`.
- Wrappers instrument the benchmark loop with `MemoryStrategy` calls.

### Harness Selection
- `mini-swe-agent` for SWE-bench Verified.
- Official `tau2` simulator for τ²-bench.
- MCQ-based Accuracy for LongBench v2.

### Inference Setup
- `llama-cpp-python` as the local backend.
- Mandatory KV-cache quantization (Q4) for 32K context.

</decisions>

<canonical_refs>
## Canonical References

### Architecture & Requirements
- `.planning/ROADMAP.md` — Goals and success criteria.
- `.planning/phases/03-task-integration-pilot-execution/03-RESEARCH.md` — Integration details.
- `src/budgetbench/evaluation/harness.py` — Target for integration.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/budgetbench/evaluation/harness.py`: `run_evaluation_task` with retry loop.
- `src/budgetbench/strategies/`: All 6 baseline memory strategies.

### Integration Points
- `run_evaluation_task` will be used by task wrappers to perform LLM calls.

</code_context>

<specifics>
## Specific Ideas
- 20 SWE + 50 LongBench for pilot.
- 3 budget tiers: 2K, 8K, 32K.
</specifics>

<deferred>
## Deferred Ideas
- Tau-bench full sweep (deferred to Phase 4, integration only in Phase 3).
</deferred>

---

*Phase: 03-task-integration-pilot-execution*
*Context gathered: 2026-04-28*
