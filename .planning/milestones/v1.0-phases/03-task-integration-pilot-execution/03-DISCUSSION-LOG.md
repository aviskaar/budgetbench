# Phase 3: Task Integration & Pilot Execution - Discussion Log

**Date:** 2026-04-28
**Participants:** Orchestrator (Gemini CLI)

## Discussion Points

### 1. Integration Strategy for Benchmark Tasks
- **Decision:** Use a "mini-harness" wrapper pattern. Each task (SWE, Tau, Long) will have a dedicated wrapper in `src/budgetbench/tasks/` that adapts the specific benchmark API to the BudgetBench `MemoryStrategy` and `run_evaluation_task` harness.
- **Rationale:** Keeps the core harness clean while allowing for specialized handling (e.g., Docker for SWE, Simulator for Tau).

### 2. SWE-bench Harness Selection
- **Decision:** Use `mini-swe-agent`.
- **Rationale:** It's minimalist, low-overhead, and easier to instrument for budget tracking than full frameworks like OpenHands.

### 3. Pilot Execution Scope
- **Decision:** Execute the pilot on 20 SWE-bench Verified and 50 LongBench v2 items across 3 tiers (2K, 8K, 32K). 
- **Rationale:** This provides sufficient data to validate the core hypothesis while keeping execution time manageable for a first run (~15-20 hours). Tau-bench integration will be completed but excluded from the *initial* pilot to save time.

### 4. Hardware/Environment
- **Decision:** Use `llama-cpp-python` with KV-cache quantization.
- **Rationale:** Essential for fitting Qwen2.5-14B with 32K context into 12-16GB VRAM.
- **Constraint:** Python 3.14 may require manual compilation; we will fall back to 3.12 if needed.

## Final Decisions for Wave 1
1. Implement `src/budgetbench/tasks/long.py` for LongBench v2 (simplest, no Docker).
2. Implement `src/budgetbench/tasks/swe.py` for SWE-bench (requires Docker setup).
3. Create a unified `TaskRunner` to orchestrate multi-task sweeps.

---

*Status: Ready for Planning*
