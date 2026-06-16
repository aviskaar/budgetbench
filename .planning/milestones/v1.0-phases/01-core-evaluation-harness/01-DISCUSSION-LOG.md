# Phase 1: Core Evaluation Harness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 1-Core Evaluation Harness
**Areas discussed:** Budget Enforcer Intervention Point, Exception Handling for Budget Exceeded, Metrics Storage Format, MemoryStrategy Interface Signature

---

## Budget Enforcer Intervention Point

| Option | Description | Selected |
|--------|-------------|----------|
| Wrap LLM client directly | Framework agnostic, catches all tokens | ✓ |
| Intercept at framework level | Easier to implement but might miss tokens | |

**User's choice:** [auto] Wrap LLM client directly (recommended default)
**Notes:** Auto-selected via --auto flag.

---

## Exception Handling for Budget Exceeded

| Option | Description | Selected |
|--------|-------------|----------|
| Trigger retry loop | Allows strategy to compress context and retry | ✓ |
| Fail task immediately | Too strict for dynamic strategies | |

**User's choice:** [auto] Trigger retry loop (recommended default)
**Notes:** Auto-selected via --auto flag.

---

## Metrics Storage Format

| Option | Description | Selected |
|--------|-------------|----------|
| JSONL | Simple append-only logging, resilient to crashes | ✓ |
| SQLite | Better querying but higher overhead | |

**User's choice:** [auto] JSONL (recommended default)
**Notes:** Auto-selected via --auto flag.

---

## MemoryStrategy Interface Signature

| Option | Description | Selected |
|--------|-------------|----------|
| Standardized message list | OpenAI format, maximum compatibility | ✓ |
| Raw string | Too simplistic for tool use | |

**User's choice:** [auto] Standardized message list (recommended default)
**Notes:** Auto-selected via --auto flag.

---

## Claude's Discretion

None.

## Deferred Ideas

None.