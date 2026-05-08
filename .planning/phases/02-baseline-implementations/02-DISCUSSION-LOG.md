# Phase 2: Baseline Implementations - Discussion Log

**Date:** 2026-04-28
**Participants:** Orchestrator (Gemini CLI)

## Discussion Points

### 1. Strategy Implementation Order
- **Decision:** Start with simpler strategies (Truncation, Summary-buffer) before moving to complex ones (RAG, Mem0, Letta, LLMLingua-2). This ensures the harness is battle-tested with simpler logic first.
- **Rationale:** Progressive complexity helps in identifying interface issues early.

### 2. Dependency Management
- **Decision:** Explicitly install `llmlingua`, `letta`, and `faiss-cpu` at the start of the phase.
- **Rationale:** These are required for advanced baselines and were identified as missing in research.

### 3. Resetting Strategy State
- **Decision:** Add a `reset()` method to the `MemoryStrategy` ABC or ensure strategies are instantiated per-task.
- **Rationale:** RAG and persistent memory strategies must be isolated between tasks to ensure benchmark integrity.
- **Refinement:** Since `__call__` is the primary interface, we will add a `reset()` method to the ABC and ensure the harness calls it if it exists.

### 4. LLM for Summarization
- **Decision:** The `SummaryBufferStrategy` will require an LLM client. We will pass the `llm_client` to its constructor.
- **Rationale:** Summarization is inherently an LLM-based task.

## Final Decisions for Wave 1
1. Update `MemoryStrategy` ABC with an optional `reset()` method.
2. Implement `TruncationStrategy` (BASE-01).
3. Implement `SummaryBufferStrategy` (BASE-02).
4. Create test files for both.

---

*Status: Ready for Planning*
