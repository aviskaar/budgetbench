---
phase: 4
slug: full-execution-publication
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Estimated runtime** | ~30 seconds (38 baseline tests) |

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
| 4-01-01 | 01 | 1 | RAG-FIX | format_message() chunks context at correct sizes | unit | `python -m pytest tests/test_tasks_wave1.py::test_longbench_chunking -x` | ❌ Wave 0 | ⬜ pending |
| 4-01-02 | 01 | 1 | RAG-FIX | RAGStrategy retrieves from chunks (not full context blob) | unit | `python -m pytest tests/test_rag.py::test_rag_longbench_chunked -x` | ❌ Wave 0 | ⬜ pending |
| 4-01-03 | 01 | 1 | RAG-FIX | Violation rate is 0% for LongBench+RAG with chunked messages | smoke | `python scripts/run_pilot.py --limit-tasks 2 --strategies rag --model qwen2.5:14b --limit-budgets 2` | depends on runner | ⬜ pending |
| 4-02-01 | 02 | 2 | EVAL-02 | Full study runner respects --full-study flag (5 tiers, correct items) | unit | `python -m pytest tests/test_runner_full_study.py -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-02 | 02 | 2 | EVAL-02 | Resume skips completed (task, strategy, budget) combinations | unit | `python -m pytest tests/test_runner_full_study.py::test_resume_skip -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-03 | 02 | 2 | EVAL-02 | summary.jsonl includes model field | unit | `python -m pytest tests/test_runner_full_study.py::test_summary_schema -x` | ❌ Wave 0 | ⬜ pending |
| 4-03-01 | 03 | 3 | DOCS-01 | analyze_results.py produces valid CSV from summary.jsonl | unit | `python -m pytest tests/test_analysis.py -x` | ❌ Wave 0 | ⬜ pending |
| 4-03-02 | 03 | 3 | DOCS-01 | plot_tradeoffs.py generates PNG without error on test data | unit | `python -m pytest tests/test_visualization.py -x` | ❌ Wave 0 | ⬜ pending |
| 4-03-03 | 03 | 3 | DOCS-01 | paper/ dir contains valid LaTeX scaffold (all sections present) | manual | `grep -l "\\\\section" paper/main.tex` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tasks_wave1.py` — add `test_longbench_chunking` for format_message() chunk count and sizes across budget tiers
- [ ] `tests/test_rag.py` — add `test_rag_longbench_chunked` for end-to-end chunked retrieval (RAGStrategy receives chunked messages, retrieves correctly)
- [ ] `tests/test_runner_full_study.py` — new file covering --full-study flag, resume logic, model field in summary schema
- [ ] `tests/test_analysis.py` — new file covering analyze_results.py with fixture JSONL files (no live model required)
- [ ] `tests/test_visualization.py` — new file covering plot_tradeoffs.py with matplotlib Agg backend (no display required)

*Note: Existing 38-test baseline must remain green throughout all waves.*

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
| matplotlib | DOCS-01 | ✓ | 3.10.9 |
| pandas | DOCS-01 | ✓ | 2.3.0 |
| numpy | DOCS-01 | ✓ | 2.4.4 |
| pytest | validation | ✓ | 9.0.3 |
| tiktoken | RAG chunking | ✓ | 0.12.0 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
