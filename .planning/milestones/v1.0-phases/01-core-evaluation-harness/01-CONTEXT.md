# Phase 1: Core Evaluation Harness - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the core evaluation harness, active budget protocol, and the foundational MemoryStrategy ABC.
</domain>

<decisions>
## Implementation Decisions

### Budget Enforcer Intervention Point
- **D-01:** Wrap the LLM client call directly (framework agnostic).

### Exception Handling for Budget Exceeded
- **D-02:** Trigger a retry loop with the memory strategy, failing after N attempts.

### Metrics Storage Format
- **D-03:** JSON lines (JSONL) for simple append-only logging during long runs.

### MemoryStrategy Interface Signature
- **D-04:** Take and return a standardized message list (OpenAI format) for maximum compatibility.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Requirements
- `.planning/ROADMAP.md` — Goal and success criteria.
- `.planning/REQUIREMENTS.md` — Core requirements to cover.
- `.planning/research/ARCHITECTURE.md` — Core components and data flow.
- `.planning/research/FEATURES.md` — Required features.
- `.planning/research/PITFALLS.md` — Common mistakes to avoid.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code assets yet. This phase establishes the foundation.

### Established Patterns
- Python 3.10+ standard patterns for ABCs and typing.

### Integration Points
- This harness will be the entry point for benchmark runs and memory strategy plugins.
</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.
</deferred>

---

*Phase: 01-core-evaluation-harness*
*Context gathered: 2026-04-28*