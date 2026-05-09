---
phase: 04-full-execution-publication
plan: "03"
subsystem: analysis-publication
tags: [analysis, plotting, matplotlib, pandas, latex, neurips]
requires:
  - phase: 04-full-execution-publication
    provides: [full-study-runner, model-summary-schema]
provides:
  - JSONL to CSV result aggregation
  - Tradeoff curve PNG generation
  - NeurIPS 2026 D&B paper scaffold
affects: [publication, full-study-analysis]
tech-stack:
  added: []
  patterns: [summary-jsonl-aggregation, per-combination-violation-rate, static-matplotlib-paper-figures]
key-files:
  created:
    - scripts/analyze_results.py
    - scripts/plot_tradeoffs.py
    - tests/test_analysis.py
    - tests/test_visualization.py
    - paper/main.tex
  modified: []
key-decisions:
  - "Aggregation reads summary.jsonl across one or more run directories and computes violation_rate from per-combination JSONL files."
  - "Plotting produces a static 2x2 matplotlib figure for paper use."
  - "The paper scaffold embeds Phase 3 pilot numbers and leaves explicit placeholders for post-sweep content."
patterns-established:
  - "Use results/full_study_{model}_{timestamp}.csv for aggregation output."
  - "Use results/figures/tradeoff_curves_{model}.png for figure output."
requirements-completed:
  - DOCS-01
  - EVAL-02
  - EVAL-03
duration: 8 min
completed: 2026-05-09
---

# Phase 4 Plan 03: Analysis Pipeline and Publication Scaffold Summary

**JSONL aggregation, matplotlib tradeoff curves, and NeurIPS 2026 paper scaffold for BudgetBench publication.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-09T02:20:53Z
- **Completed:** 2026-05-09T02:28:39Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `scripts/analyze_results.py` to load one or more `summary.jsonl` files, compute per-combination violation rates, and write model-scoped CSV output.
- Added `scripts/plot_tradeoffs.py` to generate 2x2 paper-ready PNG figures: accuracy and violation rate by budget for SWE-bench and LongBench.
- Added tests for summary loading, missing directories, malformed/missing per-combination JSONL files, and plotting empty/non-empty data.
- Added `paper/main.tex`, a NeurIPS 2026 Datasets & Benchmarks scaffold with required sections, appendix placeholders, and embedded Phase 3 pilot results.

## Task Commits

1. **Task 1: Create analysis and plotting scripts** - `5bd70de` (`feat(04-03)`)
2. **Task 2: Add tests and paper scaffold** - `7dc9aaf` (`test(04-03)`)

## Files Created/Modified

- `scripts/analyze_results.py` - Aggregates `summary.jsonl` rows and computes `violation_rate` from per-combination logs.
- `scripts/plot_tradeoffs.py` - Generates static 2x2 tradeoff figures with a sandbox-safe matplotlib cache path.
- `tests/test_analysis.py` - Covers aggregation and violation-rate computation.
- `tests/test_visualization.py` - Covers PNG generation for populated and empty model data.
- `paper/main.tex` - Provides NeurIPS 2026 D&B paper scaffold and pilot results table.

## Decisions Made

- Missing per-combination JSONL files produce `None` violation rates so partial runs can still be analyzed.
- Empty plot inputs still produce a PNG; this keeps automation robust during early or partial sweeps.
- The scaffold uses anonymous authors and explicit comments rather than macros for post-sweep TODO content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Matplotlib cache path was not writable in the sandbox**
- **Found during:** Focused import and visualization test verification.
- **Issue:** Matplotlib attempted to write cache data under the home directory and fontconfig cache paths, creating warnings and slow startup.
- **Fix:** Set `MPLCONFIGDIR` and `XDG_CACHE_HOME` to temp-directory paths before importing matplotlib.
- **Files modified:** `scripts/plot_tradeoffs.py`.
- **Verification:** `python -c "import scripts.plot_tradeoffs as p; print(callable(p.plot_tradeoff_curves))"` exits 0; visualization tests pass.
- **Committed in:** `5bd70de`.

---

**Total deviations:** 1 auto-fixed (Rule 3).
**Impact on plan:** Improves reliability in sandboxed and CI environments. No change to plot semantics.

## Issues Encountered

None remaining.

## Verification

- `python -m pytest tests/test_analysis.py tests/test_visualization.py -v` — 6 passed.
- `python -c "import scripts.analyze_results; import scripts.plot_tradeoffs; print('ok')"` — exits 0.
- `grep -c 'usepackage\[eandd\]{neurips_2026}' paper/main.tex` — 1.
- `grep -c '\\section{' paper/main.tex` — 10.
- `grep -c 'def load_summary_files' scripts/analyze_results.py` — 1.
- `grep -c 'matplotlib.use("Agg")' scripts/plot_tradeoffs.py` — 1.
- `python -m pytest tests/ -v` — 51 passed, 2 warnings.

## User Setup Required

None - no external service configuration required. To compile the paper locally, download `neurips_2026.sty` from NeurIPS as noted in `paper/main.tex`.

## Next Phase Readiness

All Phase 4 planned artifacts are present. The project is ready for `$gsd-verify-work 4` and then milestone completion.

---
*Phase: 04-full-execution-publication*
*Completed: 2026-05-09*
