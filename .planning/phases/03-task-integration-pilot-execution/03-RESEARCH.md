# Phase 3: Task Integration & Pilot Execution - Research

**Researched:** 2026-04-28
**Domain:** Benchmark Integration & Pilot Execution
**Confidence:** HIGH

## Summary

Phase 3 focuses on integrating three benchmark tasks (SWE-bench Verified, τ²-bench, and LongBench v2) into the BudgetBench harness and executing a cheap pilot experiment. The research confirms that all three benchmarks have stable, deterministic evaluation paths and can be integrated using lightweight wrappers or specialized "mini-harnesses" to minimize token overhead and dependencies.

The "mini-swe-agent" has been identified as the optimal harness for SWE-bench Verified due to its minimalist design (~100 lines) and bash-only interface. τ²-bench provides a robust simulator for multi-turn tool-use, and LongBench v2 offers a clean MCQ-based evaluation for long-context reasoning.

Hardware requirements for the pilot (Qwen2.5-14B GGUF with 32K context) are verified to fit within 12-16GB VRAM using KV-cache quantization in `llama.cpp`.

**Primary recommendation:** Use `mini-swe-agent` as a library, wrapping its environment and agent logic to inject `MemoryStrategy` and budget enforcement at each turn of the agent loop.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mini-swe-agent` | [latest] | SWE-bench harness | Radically simple (100 lines), low token overhead, standard for open models. [VERIFIED: GitHub/SWE-agent] |
| `tau2-bench` | [latest] | τ²-bench simulator | Official Sierra Research benchmark for tool-use reliability. [CITED: sierra-research/tau2-bench] |
| `datasets` | 4.0.0+ | Data loading | Standard for LongBench v2 and MuSiQue-Ans. [VERIFIED: Hugging Face] |
| `llama-cpp-python` | [latest] | Inference engine | Best for local GGUF execution with KV-cache quantization on consumer hardware. [VERIFIED: llama.cpp docs] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `docker` | 29.1.3+ | Sandboxing | Required for SWE-bench task execution. [VERIFIED: local env] |
| `hf` | [latest] | Model download | Successor to `huggingface-cli` for downloading GGUF weights. [VERIFIED: local env] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `mini-swe-agent` | `OpenHands` | OpenHands is much heavier, higher overhead, and harder to budget-track. |
| `vLLM` | `llama.cpp` | `vLLM` has high memory overhead for KV cache; `llama.cpp` allows strict 4-bit/8-bit KV quantization. |

**Installation:**
```bash
# SWE-bench dependencies
pip install docker datasets

# llama-cpp-python with Metal support (Mac)
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# Benchmark repositories (to be cloned as submodules or via scripts)
# github.com/SWE-agent/mini-swe-agent
# github.com/sierra-research/tau2-bench
```

## Architecture Patterns

### Recommended Project Structure
```
src/budgetbench/
├── tasks/           # Task integration wrappers
│   ├── __init__.py
│   ├── swe.py       # SWE-bench Verified (mini-swe-agent)
│   ├── tau.py       # τ²-bench (retail/airline)
│   └── long.py      # LongBench v2 / MuSiQue
└── evaluation/
    └── harness.py   # Main entry point (updated for multi-turn)
```

### Pattern 1: Multi-turn Budget Enforcement
**What:** Injecting the `MemoryStrategy` and budget check into each turn of an agent loop.
**When to use:** For SWE-bench and τ²-bench.
**Example:**
```python
# Conceptual integration for mini-swe-agent
for turn in range(max_turns):
    # 1. Strategy applies context management
    processed_history = strategy(agent.history, budget_tier)
    
    # 2. Enforce budget
    token_count = enforce_budget(processed_history, tokenizer_fn, budget_tier)
    
    # 3. Call LLM through the strategy-aware wrapper
    action = model.query(processed_history)
    
    # 4. Step environment
    obs, done = env.step(action)
    agent.history.append({"role": "user", "content": obs})
```

### Anti-Patterns to Avoid
- **LLM-as-Judge:** Avoid using models to grade outcomes; use deterministic test results (SWE-bench pytest) or DB state (τ²-bench).
- **Hidden Context:** Ensure the "mini-harness" system prompt is included in the token count; otherwise, the budget is cheated.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SWE-bench Grading | Custom parser | Official Docker Grader | Handles complex dependency environments and edge cases. |
| τ²-bench Simulation | Custom user model | `tau2` User Simulator | Pinned version ensures peer-review comparability. |
| MCQ Extraction | Custom Regex | LongBench v2 logic | Handles CoT and formatting variations as per benchmark standards. |

## Common Pitfalls

### Pitfall 1: Docker Permissions
**What goes wrong:** `mini-swe-agent` fails to start Docker containers in restricted environments.
**How to avoid:** Ensure the user is in the `docker` group and Docker Desktop/Engine is running.

### Pitfall 2: KV-Cache OOM
**What goes wrong:** Qwen2.5-14B at 32K context exceeds VRAM on 12GB/16GB cards.
**How to avoid:** Mandatory use of `--cache-type-k q4_0 --cache-type-v q4_0` (or similar) in `llama.cpp`. [VERIFIED: VRAM research]

### Pitfall 3: Python 3.14 Compatibility
**What goes wrong:** Some binary wheels (like `llama-cpp-python`) may not yet be available for Python 3.14.
**How to avoid:** Use a virtual environment with Python 3.10-3.12 if compilation fails.

## Code Examples

### LongBench v2 Data Loading
```python
from datasets import load_dataset
# Source: THUDM/LongBench-v2
dataset = load_dataset('THUDM/LongBench-v2', split='train')
sample = dataset[0]
# Context, question, choice_A/B/C/D, answer
```

### τ²-bench Step Logic
```python
from tau2.envs import get_env
# Source: sierra-research/tau2-bench
env = get_env("airline")
obs, info = env.reset()
action = {"role": "assistant", "content": "...", "tool_calls": []}
obs, reward, done, truncated, info = env.step(action)
success = info['success']
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SWE-bench | SWE-bench Verified | 2024 | Human-filtered to remove unsolvable/flaky issues. |
| LongBench (v1) | LongBench v2 | 2024 | Shifted from F1/ROUGE to MCQ for objective eval. |
| ToolBench | τ²-bench | 2024 | Multi-turn with deterministic simulator vs LLM-judge. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `mini-swe-agent` can be used as a library | Summary | Might require some refactoring if designed purely as a CLI. |
| A2 | Python 3.14 supports required libs | Pitfalls | `llama-cpp-python` might need manual compilation if wheels missing. |

## Open Questions (RESOLVED)

1. **MuSiQue-Ans Grading:**
   - **RESOLVED:** We will use Normalized Exact Match (strip punctuation, lower case) for consistency with deterministic requirements.
2. **Tau-bench Pilot:**
   - **RESOLVED:** We will integrate it in Phase 3 as planned, but exclude it from the *initial* cheap pilot execution to prioritize SWE and LongBench results. It will be part of the full suite in Phase 4.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | SWE-bench | ✓ | 29.1.3 | — |
| Python | Core | ✓ | 3.14.2 | Use 3.12 venv |
| GCC/Clang | llama-cpp-python | ✓ | 17.0.0 | — |
| hf | Model download | ✓ | latest | — |
| Datasets | LongBench | ✓ | 4.0.0 | — |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/tasks/ -m "smoke"` |
| Full suite command | `pytest tests/tasks/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TASK-01 | SWE-bench integration | integration | `pytest tests/tasks/test_swe.py` | ❌ Wave 0 |
| TASK-02 | τ²-bench integration | integration | `pytest tests/tasks/test_tau.py` | ❌ Wave 0 |
| TASK-03 | LongBench v2 integration | integration | `pytest tests/tasks/test_long.py` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `tests/tasks/test_swe.py` — Mocked SWE-bench run.
- [ ] `tests/tasks/test_tau.py` — Mocked τ²-bench run.
- [ ] `tests/tasks/test_long.py` — Mocked LongBench run.
- [ ] Framework install: `pip install pytest pytest-mock`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Validate task IDs and budget parameters. |
| V12 File System | yes | Sandboxed execution for SWE-bench (Docker). |

### Known Threat Patterns for Local LLM Agent

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Arbitrary Code Execution | Tampering | Execute SWE-bench tasks ONLY inside Docker. |
| Resource Exhaustion | Denial of Service | Budget tiers and max_turns limit. |

## Sources

### Primary (HIGH confidence)
- [SWE-agent/mini-swe-agent] - Verified architecture and "100 lines" claim.
- [sierra-research/tau2-bench] - Verified Python API and simulator logic.
- [THUDM/LongBench-v2] - Verified MCQ data format and loading.

### Secondary (MEDIUM confidence)
- [VRAM research] - Calculated for Qwen2.5-14B + 32K context based on llama.cpp benchmarks.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Libraries are well-known and recently updated.
- Architecture: HIGH - Fits the existing `MemoryStrategy` pattern.
- Pitfalls: MEDIUM - Environment-specific issues (Docker/Python version) may arise.

**Research date:** 2026-04-28
**Valid until:** 2026-05-28
