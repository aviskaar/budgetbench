---
phase: 04-full-execution-publication
plan: "03"
<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-03-SUMMARY.md
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
=======
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
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-03-SUMMARY.md
key-files:
  created:
    - scripts/analyze_results.py
    - scripts/plot_tradeoffs.py
<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-03-SUMMARY.md
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
=======
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
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-03-SUMMARY.md
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

<<<<<<< HEAD:.planning/phases/04-full-execution-publication/04-03-SUMMARY.md
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
=======
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
>>>>>>> 0ccf9764595932d8721286debdfabf3c1f0ba8b4:.planning/milestones/v1.0-phases/04-full-execution-publication/04-03-SUMMARY.md
