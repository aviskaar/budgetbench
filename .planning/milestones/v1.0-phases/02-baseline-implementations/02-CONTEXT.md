# Phase 2: Baseline Implementations - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement all 6 core memory baseline strategies to be tested in the benchmark.
</domain>

<decisions>
## Implementation Decisions

### Modular Strategy Design
- Each strategy is a standalone class in `src/budgetbench/strategies/`.
- All inherit from `MemoryStrategy` ABC.

### Dependency Handling
- Install `llmlingua`, `letta`, and `faiss-cpu` during Phase 2 setup.

### Strategy Isolation
- Implement `reset()` method in `MemoryStrategy` to clear vector stores/buffers between tasks.

### LLM-Based Strategies
- `SummaryBufferStrategy` and `MemGPT` will take an `llm_client` in their constructors.

</decisions>

<canonical_refs>
## Canonical References

### Architecture & Requirements
- `.planning/ROADMAP.md` — Phase goal and success criteria.
- `.planning/phases/02-baseline-implementations/02-RESEARCH.md` — Technical recommendations.
- `src/budgetbench/core/strategy.py` — Interface definition.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/budgetbench/core/strategy.py`: `MemoryStrategy` ABC.
- `src/budgetbench/utils/types.py`: `OpenAIMessage`.

### Established Patterns
- Strategy pattern for context compression.
- Standardized `OpenAIMessage` format.

</code_context>

<specifics>
## Specific Ideas
- Use `all-MiniLM-L6-v2` for the RAG baseline embedding model.
- Use `bert-base` for LLMLingua-2 to keep resource usage low during benchmarking.
</specifics>

<deferred>
### Deferred Ideas
- Exact `letta` integration details (server vs library) to be finalized during Plan 03.
</deferred>

---

*Phase: 02-baseline-implementations*
*Context gathered: 2026-04-28*
