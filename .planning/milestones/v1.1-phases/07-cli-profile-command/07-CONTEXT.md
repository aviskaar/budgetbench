# Phase 07: CLI Profile Command - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Take the HardwareReport from Phase 5 and RecommendationReport from Phase 6, combine them into a human-readable `budgetbench profile` CLI command with `--json` export. Also expose `budgetbench.profile()` as a Python callable.

</domain>

<decisions>
## Implementation Decisions

### CLI Framework
- **D-01:** Use `argparse` (stdlib) — no new dependencies for a simple CLI.
- **D-02:** CLI entry point is `budgetbench.cli:main` (already in pyproject.toml).
- **D-03:** `budgetbench profile` prints formatted text; `budgetbench profile --json` prints JSON.

### Python API
- **D-04:** `budgetbench.profile()` in `__init__.py` calls `detect_hardware()` + `detect_best_model()` and returns the combined dict.

### Module Structure
- **D-05:** `src/budgetbench/cli.py` — CLI entry point (argparse, print, json.dump).
- **D-06:** `src/budgetbench/profile.py` — `profile()` function that combines hardware + recommendation.
- **D-07:** Update `__init__.py` to export `profile`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 7 goal and success criteria.

### Existing Code
- `src/budgetbench/utils/hardware.py` — `detect_hardware()`, `HardwareReport`.
- `src/budgetbench/utils/recommendation.py` — `detect_best_model()`, `RecommendationReport`.
- `src/budgetbench/pyproject.toml` — CLI entry point: `budgetbench = "budgetbench.cli:main"`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `detect_hardware()` from hardware.py — produces HardwareReport.
- `detect_best_model()` from recommendation.py — produces RecommendationReport.
- Both return plain dicts — easy to combine and format.

### Established Patterns
- argparse for CLI (standard library).
- `if __name__ == "__main__"` guard in cli.py.
- `__init__.py` exports for public API.

</code_context>

<specifics>
## Specific Ideas

- CLI format:
  ```
  BudgetBench Hardware Profile
  ============================
  GPU:      Apple M4 Pro
  VRAM:     64 GB
  CPU:      Apple M4 Pro (14 cores)
  RAM:      64 GB

  Recommendation: Qwen3-Coder-30B-A3B @ 32K tier
  VRAM needed: 4.3 GB / 64 GB available
  ```
- JSON output: full combined dict (hardware + recommendation).
- `budgetbench.profile()` returns the same dict.

</specifics>

<deferred>
## Deferred Ideas

- Color/emoji output (keep it simple for now).
- Config file for model overrides.
- `budgetbench run` subcommand for full benchmark execution (future phase).

</deferred>

---
*Phase: 07-cli-profile-command*
*Context gathered: 2026-05-19*
