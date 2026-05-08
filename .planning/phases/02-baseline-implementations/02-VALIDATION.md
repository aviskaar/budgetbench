---
phase: 02
slug: baseline-implementations
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-28
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for baseline implementations.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | none |
| **Quick run command** | `pytest -x tests/` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30 seconds (includes model loading for complex strategies) |

---

## Sampling Rate

- **After every task commit:** Run `pytest -x tests/test_<relevant_strategy>.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds (unit) / 60 seconds (integration)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | HARN-01 | N/A | unit | `pytest tests/test_strategy.py` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | BASE-01 | N/A | unit | `pytest tests/test_truncation.py` | ❌ | ⬜ pending |
| 02-01-03 | 01 | 1 | BASE-02 | N/A | unit | `pytest tests/test_summary.py` | ❌ | ⬜ pending |
| 02-02-01 | 02 | 2 | BASE-03 | N/A | integration | `pytest tests/test_rag.py` | ❌ | ⬜ pending |
| 02-02-02 | 02 | 2 | BASE-05 | N/A | integration | `pytest tests/test_mem0.py` | ❌ | ⬜ pending |
| 02-03-01 | 03 | 3 | BASE-04 | N/A | integration | `pytest tests/test_letta.py` | ❌ | ⬜ pending |
| 02-03-02 | 03 | 3 | BASE-06 | N/A | integration | `pytest tests/test_llmlingua.py` | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_truncation.py` — stubs for BASE-01
- [ ] `tests/test_summary.py` — stubs for BASE-02
- [ ] `tests/test_rag.py` — stubs for BASE-03
- [ ] `tests/test_mem0.py` — stubs for BASE-05
- [ ] `tests/test_letta.py` — stubs for BASE-04
- [ ] `tests/test_llmlingua.py` — stubs for BASE-06

---

## Manual-Only Verifications

*None. All behaviors are covered by automated unit or integration tests.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** Orchestrator (Gemini CLI)
