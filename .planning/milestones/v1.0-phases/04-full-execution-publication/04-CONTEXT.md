# Phase 4: Full Execution & Publication - Context

**Gathered:** 2026-05-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Execute the full BudgetBench parameter sweep (3 models × 5 budget tiers × 6 strategies × 2 tasks), generate publication-ready tradeoff curves, and produce the arXiv preprint. Pre-work includes fixing the RAG+LongBench violation gap identified in Phase 3 and extending the runner script.

</domain>

<decisions>
## Implementation Decisions

### Execution Infrastructure
- LLM backend: Ollama (already proven in pilot, easy model swaps via --model flag)
- Budget tiers: All 5 — 2K / 4K / 8K / 16K / 32K (ROADMAP standard, publication-required)
- Model priority: Qwen2.5-14B first; Qwen2.5-32B and Qwen3-Coder-30B-A3B if hardware allows
- Runner: Extend run_pilot.py with --full-study flag (all 5 tiers, all 6 strategies, standard item counts)

### RAG Fix for LongBench
- Fix location: task wrapper — LongBenchV2Task.format_message() pre-chunks context into multiple messages so RAGStrategy.__call__() can retrieve from conversation history as intended
- Chunk size: min(budget/4, 512) tokens per chunk (adaptive to budget tier)
- RAGStrategy unchanged — no modifications to rag.py
- Edge case: if context fits within single chunk, pass as-is (avoids unnecessary chunking overhead)

### Results & Visualization
- Output format: matplotlib PNG plots (static, paper-ready)
- Figure layout: Separate panels per task (SWE-bench + LongBench) combined in one multi-panel figure
- Metrics to plot: accuracy vs budget AND violation_rate vs budget (two subplot rows)
- Output location: results/ for aggregated data, results/figures/ for generated plots

### arXiv Preprint
- LaTeX template: NeurIPS 2026 (target venue: NeurIPS D&B track)
- Paper scope: Full scaffold with all sections — intro, related work, method, experiments, results, conclusion + appendix
- Location: paper/ subdirectory at repo root
- Preliminary results: Include Phase 3 pilot data in experiments section as harness validation baseline

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/run_pilot.py`: Full pilot runner — extend with --full-study flag, 5 tiers, all strategies
- `src/budgetbench/strategies/`: All 6 strategies implemented (truncation, summary, rag, mem0, letta, llmlingua)
- `src/budgetbench/tasks/long.py`: LongBenchV2Task — needs format_message() chunking fix
- `src/budgetbench/evaluation/runner.py`: TaskRunner — already supports budget, limit, logger params
- `src/budgetbench/evaluation/metrics.py`: MetricsLogger — in-place, no changes needed

### Established Patterns
- Strategies: optional import with graceful skip (build_strategies() in run_pilot.py)
- Logging: JSONL per (task × strategy × budget) combination + summary.jsonl
- Grading: deterministic (MCQ letter match for LongBench, diff-presence for SWE)
- Budget enforcement: raise-on-exceed, retry × 3, fail gracefully

### Integration Points
- New analysis script connects to existing logs/ JSONL output
- New figure generation script reads from results/ aggregated CSV/JSONL
- Paper scaffold is standalone in paper/ — no code dependency

</code_context>

<specifics>
## Specific Ideas
- Phase 3 pilot run ID: 20260429_004124 — include pilot table in paper as preliminary results
- RAG violation root cause: LongBench context placed as single 36K–464K token user message; fix by chunking before passing to RAGStrategy
- Full study target: 20 SWE items + 50 LongBench items per combination (same as pilot's intended scale)
- Figures: x-axis = budget tier (log scale), y-axis = accuracy / violation rate, one line per strategy

</specifics>

<deferred>
## Deferred Ideas
- τ²-bench full sweep (integration wired in Phase 3; requires tau2-bench install to enable — Phase 4 if feasible)
- EVAL-04: Continuous λ-weighted Pareto frontier (v2 stretch goal)
- LEAD-01: Public leaderboard with strategy submissions (v2)
- Interactive HTML visualization (plotly) — static matplotlib sufficient for paper

</deferred>

---

*Phase: 04-full-execution-publication*
*Context gathered: 2026-05-07*
