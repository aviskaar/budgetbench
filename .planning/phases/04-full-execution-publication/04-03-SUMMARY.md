---
phase: 04-full-execution-publication
plan: "03"
subsystem: publication
tags: [analysis, visualization, csv, matplotlib, neurips, paper]
requires:
  - phase: 04-full-execution-publication
    provides: "04-02 model-tagged full-study summary rows"
provides:
  - "JSONL to CSV aggregation script"
  - "CSV to 2x2 tradeoff curve plotting script"
  - "NeurIPS 2026 Datasets and Benchmarks paper scaffold"
affects: [publication, full-study-analysis, phase-04]
tech-stack:
  added: []
  patterns:
    - "Analysis computes violation_rate from per-combination JSONL, not summary.jsonl"
    - "Visualization uses matplotlib Agg backend for headless testability"
key-files:
  created:
    - scripts/analyze_results.py
    - scripts/plot_tradeoffs.py
    - paper/main.tex
    - tests/test_analysis.py
    - tests/test_visualization.py
  modified: []
key-decisions:
  - "Missing per-combination JSONL files map to null violation_rate so partial runs can still be aggregated."
  - "Paper scaffold stays anonymous and result-placeheld until full sweeps complete."
requirements-completed: [DOCS-01, EVAL-02, EVAL-03]
duration: 20 min
completed: 2026-05-08
---

# Phase 4 Plan 03: Analysis Pipeline and Paper Scaffold Summary

**Full-study logs can now be aggregated into CSVs, plotted as paper-ready tradeoff curves, and inserted into a NeurIPS D&B scaffold.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-08T00:35:00Z
- **Completed:** 2026-05-08T00:55:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `scripts/analyze_results.py` to load one or more `summary.jsonl` files, compute per-combination violation rates, and write ordered CSV output.
- Added `scripts/plot_tradeoffs.py` to generate 2x2 accuracy and violation-rate panels for SWE-bench and LongBench v2.
- Added tests for summary loading, malformed/missing logs, violation-rate computation, plotting with data, and plotting empty model subsets.
- Added `paper/main.tex` with NeurIPS 2026 Datasets and Benchmarks style usage, all required sections, pilot table, and figure placeholders.

## Task Commits

1. **Task 1-2: Analysis pipeline, visualization tests, and paper scaffold** - `0102355` (feat)

## Files Created/Modified

- `scripts/analyze_results.py` - Aggregates full-study JSONL logs into CSV and computes `violation_rate`.
- `scripts/plot_tradeoffs.py` - Produces paper-ready PNG tradeoff curves with matplotlib Agg backend.
- `tests/test_analysis.py` - Covers JSONL loading and violation-rate computation.
- `tests/test_visualization.py` - Covers plotting with normal and empty model-filtered data.
- `paper/main.tex` - Provides the publication scaffold and embedded pilot-results table.

## Decisions Made

- Represent missing per-combination metric files as `None`/blank CSV values instead of failing aggregation.
- Kept the paper scaffold result placeholders explicit so full-sweep data can be inserted without rewriting the structure.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

The `rtk rg` pattern used to count LaTeX `\section{}` headings did not return matches, so the heading verification was performed by reading `paper/main.tex` directly. The scaffold contains the required sections and appendix sections.

## User Setup Required

None - no external service configuration required.

## Test Results

- `rtk .venv/bin/python -m pytest tests/test_analysis.py tests/test_visualization.py -q` — 6 passed
- `rtk .venv/bin/python -c "import scripts.analyze_results as a; import scripts.plot_tradeoffs as p; ..."` — exits 0
- `rtk .venv/bin/python -m pytest tests/ -q` — 51 passed, 1 dependency warning

## Self-Check: PASSED

- `scripts/analyze_results.py` contains `def load_summary_files`.
- `scripts/plot_tradeoffs.py` contains `def plot_tradeoff_curves` and `matplotlib.use("Agg")`.
- `paper/main.tex` contains `\usepackage[eandd]{neurips_2026}`.
- `paper/main.tex` contains required sections: Abstract, Introduction, Related Work, BudgetBench Framework, Experiments, Results and Analysis, Discussion, Conclusion, and appendix material.

## Next Phase Readiness

All Phase 4 plans are executed. The phase is ready for verification and then full-study operation.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-08*
