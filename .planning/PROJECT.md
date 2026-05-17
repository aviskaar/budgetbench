# BudgetBench

## What This Is

A standardized community benchmark for local LLM agents to evaluate memory strategies across fixed active-context-budget tiers (2k/4k/8k/16k/32k). It provides a swappable third-party strategy interface for long-horizon tasks, targeting the reality of local consumer hardware where context length is a scarce resource.

## Core Value

Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

## Requirements

### Validated

- [x] **HARN-01**: Implement the evaluation harness with a `MemoryStrategy` ABC.
- [x] **HARN-02**: Implement active-budget protocol (enforcer that wraps LLM calls and raises violations if tier ceiling is exceeded).
- [x] **BASE-01**: Implement Truncation + sliding-window baseline.
- [x] **BASE-02**: Implement Summary-buffer baseline.
- [x] **BASE-03**: Implement Vanilla RAG over an episodic FAISS store baseline.
- [x] **BASE-04**: Implement MemGPT/Letta baseline.
- [x] **BASE-05**: Implement Mem0 (or A-Mem) baseline.
- [x] **BASE-06**: Implement LLMLingua-2 prompt-compression baseline.
- [x] **TASK-01**: Integrate SWE-bench Verified 100-instance stratified subset with mini-SWE-agent harness.
- [x] **TASK-02**: Integrate τ²-bench retail + airline full sets (~200 tasks).
- [x] **TASK-03**: Integrate LongBench v2 multi-doc QA filtered to 8K–32K range + MuSiQue-Ans 1K dev items.
- [x] **EVAL-01**: Execute cheap pilot on 20 SWE + 50 LongBench v2 items at 3 budgets to validate hypothesis.

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

- **Technical Environment**: Target hardware includes RTX 5060 Ti 16GB, M4 Pro 64GB, and M5 Pro 48GB. Inference stacks will be llama.cpp (with Q8 KV-cache quantization) and MLX. Target models are Qwen2.5-14B, Qwen2.5-32B, and Qwen3-Coder-30B-A3B.
- **Ecosystem**: The space is moving extremely fast. ContextBudget/BACM-RL and BudgetMem have recently evaluated context budgets internally, but a community standard benchmark is missing.
- **Risks**: High risk of being scooped within 60 days. A 30-day timeline for an arXiv preprint is critical.
- **Target Venues**: NeurIPS 2026 Datasets & Benchmarks track, with an initial arXiv preprint.

## Constraints

- **Type**: Technical — Must support 2K/4K/8K/16K/32K context budget tiers strictly.
- **Type**: Hardware — Must run on consumer hardware (RTX 5060 Ti 16GB, Mac M4/M5 Pro).
- **Type**: Evaluation — All tasks must have deterministic grading. No LLM-as-judge.
- **Type**: Timeline — Must ship initial pilot in 1 week, and arXiv preprint in 4 weeks.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local LLMs only | Cloud models abstract away the budget problem; local deployment is where context is genuinely scarce. | — Pending |
| Deterministic graders only | Essential for peer-review credibility on a benchmark paper. | — Pending |
| 32K Max Context | Fits on target hardware and provides a clean 4x log-spaced sweep. | — Pending |

## Current Milestone: v1.1 Hardware Profiler

**Goal:** Add a `budgetbench profile` CLI command that detects user GPU/CPU/RAM and recommends the best model + budget tier combination for their hardware.

**Target features:**
- Hardware detection (GPU model, VRAM, CPU cores, system RAM)
- Model recommendation engine (matches hardware to optimal Qwen model + context budget tier)
- CLI entry point: `budgetbench profile`

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
*Last updated: 2026-05-16 — v1.1 Hardware Profiler milestone started*
