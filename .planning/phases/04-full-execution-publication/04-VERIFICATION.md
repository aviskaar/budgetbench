---
phase: 04-full-execution-publication
status: gaps_found
verified: 2026-05-08
score: 5/8
---

# Phase 4 Verification

## Verdict

**GAPS FOUND.** All three Phase 4 implementation plans were executed and the automated test suite is green, but the roadmap goal is broader than the implemented plans: the live full benchmark sweeps across target models have not been run, and the paper still contains result placeholders.

## Automated Checks

- `rtk .venv/bin/python -m pytest tests/ -q` — 51 passed, 1 dependency warning.
- `scripts/analyze_results.py` imports successfully and exposes `load_summary_files`.
- `scripts/plot_tradeoffs.py` imports successfully and exposes `plot_tradeoff_curves`.
- `paper/main.tex` contains `\usepackage[eandd]{neurips_2026}` and the required paper sections.

## Must-Have Verification

| Requirement | Status | Evidence |
|-------------|--------|----------|
| RAG + LongBench budget gap fixed | VERIFIED | `LongBenchV2Task.format_message(..., budget=8192)` chunks context; `tests/test_rag.py::test_rag_longbench_chunked` passes. |
| Full-study runner supports 5 budget tiers | VERIFIED | `FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]`; runner dry-run printed all five tiers. |
| Full-study resume support exists | VERIFIED | `load_completed_combinations()` and skip guard implemented; `tests/test_runner_full_study.py` passes. |
| Analysis pipeline computes violation rates from per-combination JSONL | VERIFIED | `compute_violation_rates()` reads `{task}_{strategy}_{budget}.jsonl`; `tests/test_analysis.py` passes. |
| Plotting pipeline produces 2x2 tradeoff PNGs | VERIFIED | `plot_tradeoff_curves()` implemented; `tests/test_visualization.py` passes. |
| Full parameter sweeps executed on Qwen2.5-14B, Qwen2.5-32B, Qwen3-Coder-30B-A3B | GAP | No full-study logs exist for the target models in `logs/full_study/`; only dry-run output was executed. |
| Tradeoff curves synthesized from full-study data | GAP | Plotting code exists, but no full-study CSV/PNG from real target-model logs exists yet. |
| arXiv preprint ready for publication | GAP | `paper/main.tex` is a scaffold with placeholders; final results, citations, and local style file remain. |

## Requirement Traceability

| Requirement | Verification |
|-------------|--------------|
| EVAL-02 | PARTIAL — runner support exists; Qwen2.5-14B full sweep not executed. |
| EVAL-03 | PARTIAL — runner support exists; Qwen2.5-32B and Qwen3-Coder-30B-A3B full sweeps not executed. |
| DOCS-01 | PARTIAL — analysis/plotting and paper scaffold exist; comprehensive results summary not produced from live data. |

## Gaps

### Gap 1: Execute Qwen2.5-14B full study

Run the full-study runner against `qwen2.5:14b`, preserving the run ID for resume:

```bash
rtk .venv/bin/python scripts/run_pilot.py --full-study --model qwen2.5:14b --run-id 20260508_qwen25_14b
```

### Gap 2: Execute EVAL-03 target model sweeps

Run the same full-study command for `qwen2.5:32b` and `qwen3-coder:30b`.

### Gap 3: Generate final CSVs, figures, and complete paper text

After the live sweeps finish, run `scripts/analyze_results.py`, `scripts/plot_tradeoffs.py`, insert generated figures into `paper/main.tex`, replace placeholders with measured results, and add final bibliography/style assets.

## Next Step

Plan gap closure:

```bash
$gsd-plan-phase 4 --gaps
```

