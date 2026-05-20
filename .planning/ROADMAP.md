# Roadmap: BudgetBench

**Core Value:** Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

## Phases

### Phase 1: Core Evaluation Harness
**Goal:** Implement the core evaluation harness, active budget protocol, and the foundational MemoryStrategy ABC.
**Requirements:** HARN-01, HARN-02, HARN-03, HARN-04

**Plans:** 3 plans
- [x] 01-00-PLAN.md — Set up initial project infrastructure and shared test fixtures
- [x] 01-01-PLAN.md — Implement foundational types, budget tiers, MemoryStrategy interface, and metrics logger
- [x] 01-02-PLAN.md — Implement budget enforcement logic and evaluation harness with metrics integration

**Success Criteria:**
1. A dummy memory strategy can be registered via `MemoryStrategy` ABC.
2. The active budget protocol successfully raises an error when a dummy LLM call exceeds the 2K tier.
3. The system correctly records and outputs metrics for a single mocked task run.

### Phase 2: Baseline Implementations
**Goal:** Implement all 6 core memory baseline strategies to be tested in the benchmark.
**Requirements:** BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06

**Plans:** 3 plans
- [x] 02-01-PLAN.md — Initialize strategy infrastructure and implement Simple baselines (Truncation, Summary-buffer)
- [x] 02-02-PLAN.md — Implement Retrieval and Persistent baselines (RAG, Mem0)
- [x] 02-03-PLAN.md — Implement Advanced baselines (Letta/MemGPT, LLMLingua-2)

**Success Criteria:**
1. Truncation and summary-buffer baselines implemented and pass unit tests.
2. RAG, MemGPT/Letta, and Mem0 baselines integrated and functioning.
3. LLMLingua-2 baseline implemented with compression ratio sweeps.

### Phase 3: Task Integration & Pilot Execution
**Goal:** Integrate the 3 target benchmark tasks and execute the cheap pilot study to validate the memory strategy tradeoff hypothesis.
**Requirements:** TASK-01, TASK-02, TASK-03, EVAL-01

**Plans:** 4/4 plans complete
- [x] 03-01-PLAN.md — Integrate LongBench v2 and SWE-bench Verified wrappers
- [x] 03-02-PLAN.md — Integrate τ²-bench and implement unified task interface
- [x] 03-03-PLAN.md — Execute pilot study (20 SWE + 50 LongBench) and generate initial tradeoff curves
- [x] 03-04-PLAN.md — Gap closure: fix τ²-bench stub (TASK-02) and re-frame tradeoff curve scope (EVAL-01)

**Success Criteria:**
1. SWE-bench Verified subset integrated via mini-SWE-agent harness.
2. τ²-bench and LongBench v2 integrated with deterministic evaluation.
3. Cheap pilot executed on 20 SWE + 50 LongBench items across 3 budgets.

### Phase 4: Full Execution & Publication
**Goal:** Execute the full benchmark suite across all target models and budget tiers, and publish the arXiv preprint.
**Requirements:** DOCS-01, EVAL-02, EVAL-03

**Plans:** 3/3 plans complete
- [x] 04-01-PLAN.md — Fix RAG + LongBench budget violation
- [x] 04-02-PLAN.md — Extend full-study runner with resume support
- [x] 04-03-PLAN.md — Add analysis pipeline, plots, and paper scaffold

**Success Criteria:**
1. Full parameter sweeps executed on Qwen2.5-14B, Qwen2.5-32B, and Qwen3-Coder-30B-A3B.
2. Data synthesis into tradeoff curves comparing token budget vs task quality.
3. arXiv preprint is written and ready for publication within the 30-day window.

### Phase 5: Hardware Detection
**Goal:** Detect user's GPU (model + VRAM), CPU cores, and system RAM with cross-platform fallbacks.
**Requirements:** PROF-01, PROF-02

**Plans:** 3/3 plans complete
- [x] 05-00-PLAN.md — Implement hardware detection module (psutil + CLI fallbacks)
- [x] 05-01-PLAN.md — Write tests for hardware detection
- [x] 05-02-PLAN.md — Verify end-to-end on target hardware

**Success Criteria:**
1. Running hardware detection on any target platform (Linux/NVIDIA, macOS/Apple Silicon, CPU-only) returns GPU model name (or "CPU-only") and VRAM in GB.
2. Hardware detection returns accurate CPU core count and system RAM in GB.
3. Fallback detection paths work: `torch`/`psutil` primary, `nvidia-smi` on Linux, `system_profiler` on macOS.

### Phase 6: Recommendation Engine
**Goal:** Match detected hardware to optimal Qwen model + context budget tier based on VRAM vs model weights + KV-cache footprint.
**Requirements:** PROF-03

**Plans:** 1/1 plans complete
- [x] 06-06-PLAN.md — Implement recommendation engine with model registry and greedy largest-first selection

**Success Criteria:**
1. Given 8 GB VRAM, the recommender selects a model + tier that fits within VRAM constraints (weights + KV-cache).
2. Given 16 GB VRAM, the recommender selects a higher-tier model or larger context budget than for 8 GB.
3. Given 48+ GB RAM (M4/M5 Pro), the recommender suggests the highest viable model + 32K tier.
4. CPU-only systems receive a conservative recommendation with explicit VRAM limitation notice.

### Phase 7: CLI Profile Command
**Goal:** Provide a `budgetbench profile` CLI command that prints a human-readable hardware report with recommendation, plus `--json` export.
**Requirements:** PROF-04, PROF-05

**Plans:** 1/1 plans complete
- [x] 07-07-PLAN.md — Implement CLI profile command with argparse, profile() function, and package export

**Success Criteria:**
1. Running `budgetbench profile` prints a formatted hardware report showing GPU, CPU, RAM, and model+tier recommendation.
2. Running `budgetbench profile --json` outputs valid JSON containing the same hardware data and recommendation.
3. The CLI command is importable and callable from Python: `budgetbench.profile()` returns the report dict.

## Phase Details

### Phase 1: Core Evaluation Harness
**Goal:** Implement the core evaluation harness, active budget protocol, and the foundational MemoryStrategy ABC.
**Depends on:** Nothing
**Requirements:** HARN-01, HARN-02, HARN-03, HARN-04
**Success Criteria (what must be TRUE):**
   1. A dummy memory strategy can be registered via `MemoryStrategy` ABC.
   2. The active budget protocol successfully raises an error when a dummy LLM call exceeds the 2K tier.
   3. The system correctly records and outputs metrics for a single mocked task run.
**Plans:** TBD
**UI hint**: no

### Phase 2: Baseline Implementations
**Goal:** Implement all 6 core memory baseline strategies to be tested in the benchmark.
**Depends on:** Phase 1
**Requirements:** BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06
**Success Criteria (what must be TRUE):**
   1. Truncation and summary-buffer baselines implemented and pass unit tests.
   2. RAG, MemGPT/Letta, and Mem0 baselines integrated and functioning.
   3. LLMLingua-2 baseline implemented with compression ratio sweeps.
**Plans:** TBD
**UI hint**: no

### Phase 3: Task Integration & Pilot Execution
**Goal:** Integrate the 3 target benchmark tasks and execute the cheap pilot study to validate the memory strategy tradeoff hypothesis.
**Depends on:** Phase 2
**Requirements:** TASK-01, TASK-02, TASK-03, EVAL-01
**Success Criteria (what must be TRUE):**
   1. SWE-bench Verified subset integrated via mini-SWE-agent harness.
   2. τ²-bench and LongBench v2 integrated with deterministic evaluation.
   3. Cheap pilot executed on 20 SWE + 50 LongBench items across 3 budgets.
**Plans:** TBD
**UI hint**: no

### Phase 4: Full Execution & Publication
**Goal:** Execute the full benchmark suite across all target models and budget tiers, and publish the arXiv preprint.
**Depends on:** Phase 3
**Requirements:** DOCS-01, EVAL-02, EVAL-03
**Success Criteria (what must be TRUE):**
   1. Full parameter sweeps executed on Qwen2.5-14B, Qwen2.5-32B, and Qwen3-Coder-30B-A3B.
   2. Data synthesis into tradeoff curves comparing token budget vs task quality.
   3. arXiv preprint is written and ready for publication within the 30-day window.
**Plans:** TBD
**UI hint**: no

### Phase 5: Hardware Detection
**Goal:** Detect user's GPU (model + VRAM), CPU cores, and system RAM with cross-platform fallbacks.
**Depends on:** Nothing (standalone module, no dependency on evaluation harness)
**Requirements:** PROF-01, PROF-02
**Success Criteria (what must be TRUE):**
   1. Running hardware detection on any target platform (Linux/NVIDIA, macOS/Apple Silicon, CPU-only) returns GPU model name (or "CPU-only") and VRAM in GB.
   2. Hardware detection returns accurate CPU core count and total system RAM in GB.
   3. Fallback detection paths work: `torch`/`psutil` primary, `nvidia-smi` on Linux, `system_profiler` on macOS.
**Plans:** TBD
**UI hint**: no

### Phase 6: Recommendation Engine
**Goal:** Match detected hardware to optimal Qwen model + context budget tier based on VRAM vs model weights + KV-cache footprint.
**Depends on:** Phase 5
**Requirements:** PROF-03
**Success Criteria (what must be TRUE):**
   1. Given 8 GB VRAM, the recommender selects a model + tier that fits within VRAM constraints (weights + KV-cache).
   2. Given 16 GB VRAM, the recommender selects a higher-tier model or larger context budget than for 8 GB.
   3. Given 48+ GB RAM (M4/M5 Pro), the recommender suggests the highest viable model + 32K tier.
   4. CPU-only systems receive a conservative recommendation with explicit VRAM limitation notice.
**Plans:** TBD
**UI hint**: no

### Phase 7: CLI Profile Command
**Goal:** Provide a `budgetbench profile` CLI command that prints a human-readable hardware report with recommendation, plus `--json` export.
**Depends on:** Phase 6
**Requirements:** PROF-04, PROF-05
**Success Criteria (what must be TRUE):**
   1. Running `budgetbench profile` prints a formatted hardware report showing GPU, CPU, RAM, and model+tier recommendation.
   2. Running `budgetbench profile --json` outputs valid JSON containing the same hardware data and recommendation.
   3. The CLI command is importable and callable from Python: `budgetbench.profile()` returns the report dict.
**Plans:** TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Evaluation Harness | 3/3 | Complete | - |
| 2. Baseline Implementations | 3/3 | Complete | - |
| 3. Task Integration & Pilot | 4/4 | Complete | - |
| 4. Full Execution & Publication | 3/3 | Complete | - |
| 5. Hardware Detection | 3/3 | Complete | - |
| 6. Recommendation Engine | 1/1 | Complete | - |
| 7. CLI Profile Command | 1/1 | Complete | - |
