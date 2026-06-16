---
phase: 01
slug: core-evaluation-harness
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-28
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest -x tests/` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -x tests/`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | HARN-01 | — | N/A | unit | `pytest tests/test_strategy.py::test_strategy_registration -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | HARN-02 | — | N/A | unit | `pytest tests/test_budget.py::test_budget_enforcement -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | HARN-03 | — | N/A | unit | `pytest tests/test_budget.py::test_budget_violation_exception -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | HARN-04 | — | N/A | unit | `pytest tests/test_metrics.py::test_jsonl_logging -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_strategy.py` — stubs for HARN-01
- [ ] `tests/test_budget.py` — stubs for HARN-02, HARN-03
- [ ] `tests/test_metrics.py` — stubs for HARN-04
- [ ] `tests/conftest.py` — shared fixtures

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending