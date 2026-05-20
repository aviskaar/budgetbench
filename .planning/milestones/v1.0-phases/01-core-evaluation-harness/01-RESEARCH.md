<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Wrap the LLM client call directly (framework agnostic).
- **D-02:** Trigger a retry loop with the memory strategy, failing after N attempts.
- **D-03:** JSON lines (JSONL) for simple append-only logging during long runs.
- **D-04:** Take and return a standardized message list (OpenAI format) for maximum compatibility.

### the agent's Discretion
No specific requirements — open to standard approaches.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HARN-01 | User can plug in custom memory strategies via a standardized `MemoryStrategy` Python ABC. | Architecture Patterns, Standard Stack |
| HARN-02 | System enforces active context budget tiers (2K, 4K, 8K, 16K, 32K) during LLM calls. | Architecture Patterns, Code Examples |
| HARN-03 | System raises violations if a memory strategy exceeds its active context tier. | Architecture Patterns, Code Examples |
| HARN-04 | System logs metrics: quality, mean used budget, peak budget, violation rate, and tokens-per-task-resolved. | Architecture Patterns, Standard Stack |
</phase_requirements>

# Phase 1: Core Evaluation Harness - Research

**Researched:** 2026-04-28
**Domain:** Core Application Foundation and Evaluation Metrics
**Confidence:** HIGH

## Summary

This phase establishes the foundational evaluation harness for BudgetBench. The critical technical challenge is orchestrating the interaction between arbitrary LLM clients, pluggable memory strategies, and strict budget enforcement. 

The primary recommendation is to implement a generic `LLMClientWrapper` that intercepts OpenAI-formatted message lists, validates token counts before passing them to the underlying model, and raises a specific `BudgetExceededError`. A robust runner orchestrates the retry mechanism (D-02) and logs the necessary metrics in a robust JSONL format (D-03).

**Primary recommendation:** Use Python's standard `abc` module for the memory strategy interface and a custom exception-driven retry loop for budget enforcement, with decoupled JSONL metrics logging.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tiktoken` | ^0.7.0 | Default Tokenizer | Industry standard for fast, offline token counting (proxy for standard lengths). |
| `pytest` | ^9.0.0 | Testing Framework | Standard for unit and integration tests. |
| `typing` / `abc` | stdlib | Interface definitions | Standard Python approach for defining ABCs without extra dependencies. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `tiktoken` | `transformers` AutoTokenizer | `transformers` provides exact local model tokenization but carries a massive dependency footprint. `tiktoken` is sufficient for a generic baseline wrapper. |
| Custom Validation | `pydantic` | `pydantic` adds weight but perfectly validates OpenAI dict structures. We defer to standard dicts initially for minimal dependencies unless complex validation is required. |

**Installation:**
```bash
pip install tiktoken pytest
```

## Architecture Patterns

### Recommended Project Structure
```
src/
└── budgetbench/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── strategy.py      # MemoryStrategy ABC
    │   ├── budget.py        # Token counting and budget enforcement
    │   └── exceptions.py    # BudgetExceededError
    ├── evaluation/
    │   ├── __init__.py
    │   ├── harness.py       # Retry loop and LLM wrapper
    │   └── metrics.py       # JSONL logging
    └── utils/
        └── types.py         # Type hints for OpenAI message format
```

### Pattern 1: Abstract Memory Strategy
**What:** Defines the contract for all baseline and third-party memory strategies.
**When to use:** To process a sequence of conversation messages before sending them to the LLM.
**Example:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MemoryStrategy(ABC):
    """
    Abstract base class for memory strategies.
    Takes an OpenAI-formatted message list and returns a budget-compliant list.
    """
    @abstractmethod
    def __call__(self, messages: List[Dict[str, Any]], active_budget: int) -> List[Dict[str, Any]]:
        pass
```

### Anti-Patterns to Avoid
- **Coupling tokenizer to the LLM Client:** Avoid hardcoding token counting logic into the wrapper. Pass a `tokenizer_fn` so it remains framework agnostic.
- **In-memory complex metrics collection:** Do not store all metrics in memory for a final write. Use JSONL append-only (D-03) to prevent data loss on long SWE-bench runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token Counting | Regex or text splitting | `tiktoken` / `tokenizer_fn` callable | Tokenization is complex and model-dependent. Off-the-shelf libraries handle BPE accurately. |
| Message Validation | Deep dict checking | Standard Python TypeDicts | Simplifies interface validation for the `MemoryStrategy` boundary. |

**Key insight:** Token counting needs to be fast and completely decoupled from the actual LLM inference engine to support various local runtimes.

## Common Pitfalls

### Pitfall 1: Infinite Retry Loops on Budget Exceeded
**What goes wrong:** The `MemoryStrategy` fails to sufficiently compress the context, but the harness retry loop keeps trying.
**Why it happens:** The strategy logic fails to account for the actual `active_budget` limits, or the system doesn't limit retries.
**How to avoid:** Implement a strict `max_retries` counter in the evaluation runner (D-02) and raise `BudgetExceededError` loudly when exceeded.
**Warning signs:** Process hangs indefinitely without outputting new logs or network requests.

### Pitfall 2: Silent Data Loss in Long Runs
**What goes wrong:** The benchmark runs for 4 hours and crashes, losing all metrics.
**Why it happens:** Storing results in a Python list and dumping to JSON at the very end.
**How to avoid:** Flush the JSONL append operation to disk immediately after each completed task run or budget violation using standard file append (`mode='a'`).

## Code Examples

### Budget Enforcement Wrapper with Retry Loop
```python
from typing import List, Dict, Any, Callable
from .exceptions import BudgetExceededError

def enforce_budget(messages: List[Dict[str, Any]], tokenizer_fn: Callable, max_tokens: int) -> int:
    # A generic implementation to count tokens
    token_count = sum(tokenizer_fn(m["content"]) for m in messages if "content" in m)
    if token_count > max_tokens:
        raise BudgetExceededError(f"Token count {token_count} exceeds active tier {max_tokens}")
    return token_count

def call_with_retry_loop(
    messages: List[Dict[str, Any]],
    strategy, # MemoryStrategy instance
    llm_client: Callable,
    tokenizer_fn: Callable,
    max_tokens: int,
    max_retries: int = 3
):
    current_messages = messages
    for attempt in range(max_retries):
        # 1. Apply the strategy to compress/filter context
        current_messages = strategy(current_messages, max_tokens)
        try:
            # 2. Check strict limits before calling model
            used_tokens = enforce_budget(current_messages, tokenizer_fn, max_tokens)
            
            # 3. Call actual model (framework agnostic)
            response = llm_client(current_messages)
            return response, used_tokens
        except BudgetExceededError:
            if attempt == max_retries - 1:
                raise # Bubble up violation if max retries reached
    raise RuntimeError("Unexpected retry exit")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom context formatting per framework | Standardized OpenAI Chat format | 2023 | Strategies can easily be swapped across completely different backend models and inference frameworks. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | [ASSUMED] `tiktoken` is an acceptable baseline proxy tokenizer for evaluating local LLMs early on. | Standard Stack | If exact local model token counts differ significantly, active budgets may be loosely enforced instead of strictly. Mitigation: Ensure tokenizer is passed as an injected `Callable` dependency. |
| A2 | [ASSUMED] The `MemoryStrategy` ABC must take `active_budget` as a standard runtime argument. | Architecture Patterns | If budget is only passed at instantiation, strategies cannot dynamically adjust during seamless multi-tier execution sweeps. |

## Open Questions (RESOLVED)

1. **Tokenizer Accuracy for Local Models**
   - What we know: `llama.cpp` handles tokenization internally based on the GGUF model's native tokenizer.
   - What's unclear: Will a generic `tiktoken` token counter diverge enough from the local model's actual tokens to matter for strict 2K/4K cutoffs?
   - Recommendation: Pass a `tokenizer_fn` callable to the wrapper, allowing later phases (e.g., Phase 2) to easily inject an exact `transformers` or `llama.cpp` token counting mechanism.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Core Runtime | ✓ | 3.14.2 | — |

**Missing dependencies with no fallback:**
- None for this core evaluation harness setup.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | none — see Wave 0 |
| Quick run command | `pytest -x tests/` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HARN-01 | Register custom `MemoryStrategy` | unit | `pytest tests/test_strategy.py::test_strategy_registration -x` | ❌ Wave 0 |
| HARN-02 | Enforce context budget tiers | unit | `pytest tests/test_budget.py::test_budget_enforcement -x` | ❌ Wave 0 |
| HARN-03 | Raise violation on budget exceed | unit | `pytest tests/test_budget.py::test_budget_violation_exception -x` | ❌ Wave 0 |
| HARN-04 | Log specific metrics to JSONL | unit | `pytest tests/test_metrics.py::test_jsonl_logging -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -x tests/`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_strategy.py` — covers HARN-01
- [ ] `tests/test_budget.py` — covers HARN-02, HARN-03
- [ ] `tests/test_metrics.py` — covers HARN-04
- [ ] `tests/conftest.py` — shared fixtures for dummy LLM client

## Sources

### Primary (HIGH confidence)
- `CONTEXT.md` - Phase constraints and technical decisions.
- `REQUIREMENTS.md` - Target requirements and evaluation expectations.

### Secondary (MEDIUM confidence)
- Python `abc` documentation - Standard patterns for Abstract Base Classes.
- JSON lines standard - Append-only file writing logic.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Standard Python primitives are sufficient for this foundational architecture.
- Architecture: HIGH - Dictated directly by constraints D-01 through D-04.
- Pitfalls: HIGH - Common issues seen in evaluation harnesses running heavy multi-hour workloads.

**Research date:** 2026-04-28
**Valid until:** Stable
