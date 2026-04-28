# Roadmap: BudgetBench

**Core Value:** Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

## Phases

### Phase 1: Core Evaluation Harness
**Goal:** Implement the core evaluation harness, active budget protocol, and the foundational MemoryStrategy ABC.
**Requirements:** HARN-01, HARN-02, HARN-03, HARN-04

**Success Criteria:**
1. A dummy memory strategy can be registered via `MemoryStrategy` ABC.
2. The active budget protocol successfully raises an error when a dummy LLM call exceeds the 2K tier.
3. The system correctly records and outputs metrics for a single mocked task run.

### Phase 2: Baseline Implementations
**Goal:** Implement all 6 core memory baseline strategies to be tested in the benchmark.
**Requirements:** BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06

**Success Criteria:**
1. Truncation and summary-buffer baselines implemented and pass unit tests.
2. RAG, MemGPT/Letta, and Mem0 baselines integrated and functioning.
3. LLMLingua-2 baseline implemented with compression ratio sweeps.

### Phase 3: Task Integration & Pilot Execution
**Goal:** Integrate the 3 target benchmark tasks and execute the cheap pilot to validate the hypothesis.
**Requirements:** TASK-01, TASK-02, TASK-03

**Success Criteria:**
1. SWE-bench Verified subset integrated via mini-SWE-agent harness.
2. τ²-bench and LongBench v2 integrated with deterministic evaluation.
3. Cheap pilot executed on 20 SWE + 50 LongBench items across 3 budgets.

### Phase 4: Full Execution & Publication
**Goal:** Execute the full benchmark suite across all target models and budget tiers, and publish the arXiv preprint.
**Requirements:** DOCS-01

**Success Criteria:**
1. Full parameter sweeps executed on Qwen2.5-14B, Qwen2.5-32B, and Qwen3-Coder-30B-A3B.
2. Data synthesis into tradeoff curves comparing token budget vs task quality.
3. arXiv preprint is written and ready for publication within the 30-day window.