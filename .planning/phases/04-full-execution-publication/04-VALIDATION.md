---
phase: 4
slug: full-execution-publication
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-07
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `conftest.py` (root) + `tests/conftest.py` |
| **Quick run command** | `python -m pytest tests/ -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~23 seconds (52 tests) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -v`
- **After every plan wave:** Run `python -m pytest tests/ -v` (full suite must be green)
- **Before `/gsd-verify-work`:** Full suite green + 3-item Qwen2.5-14B smoke test
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | RAG-FIX | format_message() chunks context at correct sizes | unit | `python -m pytest tests/test_tasks_wave1.py::test_longbench_chunking -x` | ✅ | ✅ green |
| 4-01-02 | 01 | 1 | RAG-FIX | RAGStrategy retrieves from chunks (not full context blob) | unit | `python -m pytest tests/test_rag.py::test_rag_longbench_chunked -x` | ✅ | ✅ green |
| 4-01-03 | 01 | 1 | RAG-FIX | LongBench smoke runs through chunked task path | smoke | `python scripts/run_pilot.py --full-study --tasks swe long --strategies truncation --model qwen2.5:14b --limit-tasks 1 --limit-budgets 1 --run-id audit_swe_long_smoke` | ✅ | ✅ green |
| 4-02-01 | 02 | 2 | EVAL-02 | Full study runner respects --full-study flag (5 tiers, correct items) | unit | `python -m pytest tests/test_runner_full_study.py -x` | ✅ | ✅ green |
| 4-02-02 | 02 | 2 | EVAL-02 | Resume skips completed (task, strategy, budget) combinations | unit | `python -m pytest tests/test_runner_full_study.py::test_resume_skip -x` | ✅ | ✅ green |
| 4-02-03 | 02 | 2 | EVAL-02 | summary.jsonl includes model field | unit | `python -m pytest tests/test_runner_full_study.py::test_summary_schema -x` | ✅ | ✅ green |
| 4-03-01 | 03 | 3 | DOCS-01 | analyze_results.py produces valid CSV from summary.jsonl | unit | `python -m pytest tests/test_analysis.py -x` | ✅ | ✅ green |
| 4-03-02 | 03 | 3 | DOCS-01 | plot_tradeoffs.py generates PNG without error on test data | unit | `python -m pytest tests/test_visualization.py -x` | ✅ | ✅ green |
| 4-03-03 | 03 | 3 | DOCS-01 | paper/ dir contains valid LaTeX scaffold (all sections present) | manual | `grep -l "\\\\section" paper/main.tex` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_tasks_wave1.py` — add `test_longbench_chunking` for format_message() chunk count and sizes across budget tiers
- [x] `tests/test_rag.py` — add `test_rag_longbench_chunked` for end-to-end chunked retrieval (RAGStrategy receives chunked messages, retrieves correctly)
- [x] `tests/test_runner_full_study.py` — new file covering --full-study flag, task selection, resume logic, model field in summary schema
- [x] `tests/test_analysis.py` — new file covering analyze_results.py with fixture JSONL files (no live model required)
- [x] `tests/test_visualization.py` — new file covering plot_tradeoffs.py with matplotlib Agg backend (no display required)

*Note: Existing baseline remained green; current suite is 52 tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LaTeX compiles to PDF | DOCS-01 | pdflatex not guaranteed available; arXiv accepts .tex directly | `cd paper && pdflatex main.tex` — expect `main.pdf` output with no fatal errors |
| Qwen2.5-14B RAG smoke test passes (0% violation rate) | RAG-FIX + EVAL-02 | Requires Ollama with model loaded; takes ~5 min | `python scripts/run_pilot.py --limit-tasks 2 --strategies rag --model qwen2.5:14b --limit-budgets 2` — verify violation_rate=0 in logs |
| Full sweep produces non-trivial accuracy variance across budget tiers | EVAL-02 | Requires 17h Qwen2.5-14B run | Check `results/summary_qwen2.5-14b.csv` — at least 2 strategies should show accuracy > 0 at 32K tier |

---

## Environment Availability

| Dependency | Required By | Available | Version |
|------------|------------|-----------|---------|
| Ollama | EVAL-02, EVAL-03 | ✓ | 0.23.1 |
| qwen2.5:14b | EVAL-02 | ✓ | 9.0 GB |
| qwen2.5:32b | EVAL-03 | ✓ | 19 GB |
| qwen3-coder:30b | EVAL-03 | ✓ | 18 GB |
| tau2-bench data | TASK-02, EVAL-02 | ✓ | `.deps/tau2-bench/data` |
| matplotlib | DOCS-01 | ✓ | 3.10.9 |
| pandas | DOCS-01 | ✓ | 2.3.0 |
| numpy | DOCS-01 | ✓ | 2.4.4 |
| pytest | validation | ✓ | 9.0.3 |
| tiktoken | RAG chunking | ✓ | 0.12.0 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete
