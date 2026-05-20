---
phase: 03
slug: task-integration-pilot-execution
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-28
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for task integration and pilot execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | none |
| **Quick run command** | `pytest -x tests/tasks/` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~1 minute (mocked) / ~20 hours (live pilot) |

---

## Sampling Rate

- **After every task commit:** Run `pytest -x tests/tasks/test_<relevant_task>.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds (mocked unit tests)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TASK-03 | N/A | unit/mocked | `pytest tests/tasks/test_long.py` | ❌ | ⬜ pending |
| 03-01-02 | 01 | 1 | TASK-01 | Sandbox (Docker) | unit/mocked | `pytest tests/tasks/test_swe.py` | ❌ | ⬜ pending |
| 03-02-01 | 02 | 2 | TASK-02 | N/A | unit/mocked | `pytest tests/tasks/test_tau.py` | ❌ | ⬜ pending |
| 03-02-02 | 02 | 2 | EVAL-01 | N/A | unit | `pytest tests/test_runner.py` | ❌ | ⬜ pending |
| 03-03-01 | 03 | 3 | EVAL-02 | N/A | smoke | `python scripts/run_pilot.py --smoke-test` | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/tasks/test_long.py` — mocked LongBench v2 data loading
- [ ] `tests/tasks/test_swe.py` — mocked mini-swe-agent env
- [ ] `tests/tasks/test_tau.py` — mocked tau2 simulator
- [ ] `tests/test_runner.py` — TaskRunner tests

---

## Manual-Only Verifications

- **Pilot Data Quality Check:** Manually inspect the first 3 entries of `pilot_results.jsonl` to ensure metrics are correctly captured.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s (for mocked tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** Orchestrator (Gemini CLI)
