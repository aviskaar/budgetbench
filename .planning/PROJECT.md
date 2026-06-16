# BudgetBench

## What This Is

A standardized community benchmark for local LLM agents to evaluate memory strategies across fixed active-context-budget tiers (2k/4k/8k/16k/32k). It provides a swappable third-party strategy interface for long-horizon tasks, targeting the reality of local consumer hardware where context length is a scarce resource.

## Core Value

Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

## Requirements

### Validated

- [x] **HARN-01**: Implement the evaluation harness with a `MemoryStrategy` ABC. — v1.0
- [x] **HARN-02**: Implement active-budget protocol (enforcer that wraps LLM calls and raises violations if tier ceiling is exceeded). — v1.0
- [x] **HARN-03**: System raises violations if a memory strategy exceeds its active context tier. — v1.0
- [x] **HARN-04**: System logs metrics: quality, mean used budget, peak budget, violation rate, and tokens-per-task-resolved. — v1.0
- [x] **BASE-01**: Implement Truncation + sliding-window baseline. — v1.0
- [x] **BASE-02**: Implement Summary-buffer baseline. — v1.0
- [x] **BASE-03**: Implement Vanilla RAG over an episodic FAISS store baseline. — v1.0
- [x] **BASE-04**: Implement MemGPT/Letta baseline. — v1.0
- [x] **BASE-05**: Implement Mem0 (or A-Mem) baseline. — v1.0
- [x] **BASE-06**: Implement LLMLingua-2 prompt-compression baseline. — v1.0
- [x] **TASK-01**: Integrate SWE-bench Verified 100-instance stratified subset with mini-SWE-agent harness. — v1.0
- [x] **TASK-02**: Integrate τ²-bench retail + airline full sets (~200 tasks). — v1.0
- [x] **TASK-03**: Integrate LongBench v2 multi-doc QA filtered to 8K–32K range + MuSiQue-Ans 1K dev items. — v1.0
- [x] **EVAL-01**: Execute cheap pilot on 20 SWE + 50 LongBench v2 items at 3 budgets to validate hypothesis. — v1.0
- [x] **PROF-01**: System detects GPU model name and VRAM size via torch/psutil/system_profiler fallbacks. — v1.1
- [x] **PROF-02**: System detects CPU core count and total system RAM. — v1.1
- [x] **PROF-03**: System recommends an optimal model + budget tier combination based on detected hardware constraints. — v1.1
- [x] **PROF-04**: CLI entry point `budgetbench profile` prints a human-readable hardware report with recommendation. — v1.1
- [x] **PROF-05**: `budgetbench profile --json` exports the report as structured JSON. — v1.1

### Active

- [ ] **EVAL-02**: Execute full sweep on Qwen2.5-14B across all three tasks at 5 budget tiers.
- [ ] **EVAL-03**: Execute full sweep on Qwen2.5-32B and Qwen3-Coder-30B-A3B (MoE).
- [ ] **DOCS-01**: Write and publish arXiv preprint within 30 days.

### Out of Scope

- Evaluating on 70B+ models — Cannot comfortably fit context sweeps on target local hardware (RTX 5060 Ti 16GB, M4 Pro 64GB, M5 Pro 48GB).
- Using LLM-as-judge for grading — Must use deterministic graders only for peer-review credibility.
- Custom RL fine-tuning of the policy — Focus is on pluggable memory strategies, not model fine-tuning.
- Testing API-only models like Claude or GPT-4 — Focus is entirely on the local-LLM deployment regime.

## Context

- **Shipped:** v1.0 (MVP) on 2026-05-09, v1.1 (Hardware Profiler) on 2026-05-20
- **Technical Environment:** Target hardware includes RTX 5060 Ti 16GB, M4 Pro 64GB, and M5 Pro 48GB. Inference stacks will be llama.cpp (with Q8 KV-cache quantization) and MLX. Target models are Qwen2.5-14B, Qwen2.5-32B, and Qwen3-Coder-30B-A3B.
- **Ecosystem:** The space is moving extremely fast. ContextBudget/BACM-RL and BudgetMem have recently evaluated context budgets internally, but a community standard benchmark is missing.
- **Risks:** High risk of being scooped within 60 days. A 30-day timeline for an arXiv preprint is critical.
- **Target Venues:** NeurIPS 2026 Datasets & Benchmarks track, with an initial arXiv preprint.
- **v1.1 Delivered:** 416 lines of Python (hardware detection, recommendation engine, CLI profile command), 37 tests passing.

## Constraints

- **Type:** Technical — Must support 2K/4K/8K/16K/32K context budget tiers strictly.
- **Type:** Hardware — Must run on consumer hardware (RTX 5060 Ti 16GB, Mac M4/M5 Pro).
- **Type:** Evaluation — All tasks must have deterministic grading. No LLM-as-judge.
- **Type:** Timeline — Must ship initial pilot in 1 week, and arXiv preprint in 4 weeks.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local LLMs only | Cloud models abstract away the budget problem; local deployment is where context is genuinely scarce. | ✓ Good |
| Deterministic graders only | Essential for peer-review credibility on a benchmark paper. | ✓ Good |
| 32K Max Context | Fits on target hardware and provides a clean 4x log-spaced sweep. | ✓ Good |
| psutil + CLI fallbacks for hardware detection | Avoids heavy torch dependency for simple detection; cross-platform via shell commands. | ✓ Good |
| Apple Silicon VRAM = total RAM | Correct for unified memory architecture on M-series chips. | ✓ Good |

## Current State

Shipped v1.0 (MVP) and v1.1 (Hardware Profiler). All 7 phases complete across 2 milestones.

Next: Full benchmark execution (EVAL-02, EVAL-03) and arXiv publication (DOCS-01).

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-20 — v1.1 Hardware Profiler milestone shipped*
