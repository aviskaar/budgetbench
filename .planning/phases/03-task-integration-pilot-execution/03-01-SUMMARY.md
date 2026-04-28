---
phase: 03-task-integration-pilot-execution
plan: 01
subsystem: tasks
tags: [longbench, swe-bench, docker, integration]
requires: [TASK-01, TASK-03]
provides: [LongBenchV2Task, SWEBenchTask]
affects: [src/budgetbench/tasks/]
tech-stack: [datasets, docker, pytest]
key-files: [src/budgetbench/tasks/long.py, src/budgetbench/tasks/swe.py]
decisions:
  - "Used docker-py for SWE-bench environment management."
  - "Implemented MCQ extraction with regex for LongBench v2 to handle varying LLM output formats."
metrics:
  duration: "30m"
  completed_date: "2026-04-28"
---

# Phase 3 Plan 01: Task Integration Wave 1 Summary

Integrated LongBench v2 and SWE-bench Verified into the BudgetBench task system. These wrappers enable evaluating memory strategies on long-context QA and multi-turn coding tasks.

## Key Changes

### LongBench v2 Wrapper (`src/budgetbench/tasks/long.py`)
- Loaded `THUDM/LongBench-v2` dataset using `datasets`.
- Formatted messages into OpenAI-style (System, Context, Question).
- Implemented deterministic MCQ grading with regex fallback.
- Integrated with `run_evaluation_task` for budget enforcement.

### SWE-bench Verified Wrapper (`src/budgetbench/tasks/swe.py`)
- Implemented multi-turn agent loop following the `mini-swe-agent` pattern.
- Integrated `docker-py` for task environment sandboxing.
- Ensured system prompts and conversation history are tracked within the token budget.
- Implemented basic patch grading logic for pilot execution.

## Verification Results

### Automated Tests
- `tests/test_tasks_wave1.py` passed with 2 tests.
- Verified LongBench MCQ grading with various response formats.
- Verified SWE-bench multi-turn loop and command parsing using mocks.

```bash
tests/test_tasks_wave1.py ..                                                                                                                                                             [100%]
====================================================================================== 2 passed in 0.57s =======================================================================================
```

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

- **SWE-bench Grading:** The `grade` method in `swe.py` uses a simplified check (presence of diff format) for the pilot. Full evaluation requires running the `test_patch` in the Docker container, which is planned for Phase 4.
- **Docker Setup:** Repository cloning and environment setup within the Docker container are placeholder comments in `swe.py` for the pilot.

## Self-Check: PASSED
