# Requirements: BudgetBench

**Defined:** 2026-04-28
**Core Value:** Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

## v1 Requirements

### Evaluation Harness
- [x] **HARN-01**: User can plug in custom memory strategies via a standardized `MemoryStrategy` Python ABC.
- [x] **HARN-02**: System enforces active context budget tiers (2K, 4K, 8K, 16K, 32K) during LLM calls.
- [ ] **HARN-03**: System raises violations if a memory strategy exceeds its active context tier.
- [x] **HARN-04**: System logs metrics: quality, mean used budget, peak budget, violation rate, and tokens-per-task-resolved.

### Baseline Strategies
- [ ] **BASE-01**: System provides Truncation + sliding-window baseline.
- [ ] **BASE-02**: System provides Summary-buffer baseline.
- [x] **BASE-03**: System provides Vanilla RAG over an episodic FAISS store.
- [ ] **BASE-04**: System provides MemGPT/Letta hierarchical OS-style memory baseline.
- [x] **BASE-05**: System provides Mem0 (or A-Mem) hierarchical memory baseline.
- [ ] **BASE-06**: System provides LLMLingua-2 prompt-compression baseline with sweeps.

### Task Integration
- [x] **TASK-01**: System executes SWE-bench Verified (100-instance stratified subset) via mini-SWE-agent harness.
- [ ] **TASK-02**: System executes τ²-bench retail + airline full sets (~200 tasks) with deterministic user-simulator. _(Integration wired in Phase 3; full sweep deferred to Phase 4. Install tau2-bench to enable.)_
- [x] **TASK-03**: System executes LongBench v2 multi-doc QA (8K–32K range) and MuSiQue-Ans (1K dev items).

### Publication
- [ ] **DOCS-01**: System outputs a comprehensive summary of tradeoff curves for arXiv preprint.

## v2 Requirements

### Stretch Goals
- **EVAL-04**: Continuous λ-weighted Pareto-frontier formulation alongside discrete tiers.
- **TASK-04**: WebArena lite integration.
- **LEAD-01**: Public leaderboard with strategy submissions.

## Out of Scope

| Feature | Reason |
|---------|--------|
| API-based cloud models (Claude, GPT-4) | Cloud models abstract away the budget problem; local deployment is where context is genuinely scarce. |
| LLM-as-judge grading | Must use deterministic graders only for peer-review credibility. |
| 70B+ parameter models | Cannot comfortably fit context sweeps on target local hardware (RTX 5060 Ti 16GB, M4 Pro 64GB, M5 Pro 48GB). |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HARN-01 | Phase 1 | Complete |
| HARN-02 | Phase 1 | Complete |
| HARN-03 | Phase 1 | Pending |
| HARN-04 | Phase 1 | Complete |
| BASE-01 | Phase 2 | Pending |
| BASE-02 | Phase 2 | Pending |
| BASE-03 | Phase 2 | Complete |
| BASE-04 | Phase 2 | Pending |
| BASE-05 | Phase 2 | Complete |
| BASE-06 | Phase 2 | Pending |
| TASK-01 | Phase 3 | Complete |
| TASK-02 | Phase 3 | Partial — integration wired, full sweep deferred to Phase 4 |
| TASK-03 | Phase 3 | Complete |
| DOCS-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-04-28 after initial definition*
