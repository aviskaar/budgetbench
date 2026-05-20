# Phase 2: Baseline Implementations - Research

**Researched:** 2026-04-28
**Domain:** Agent Memory Strategies
**Confidence:** HIGH

## Summary

This phase focuses on implementing six foundational memory strategies for the BudgetBench benchmark. These strategies range from simple FIFO truncation to advanced agentic memory and prompt compression. 

**Primary recommendation:** Use a modular approach where each strategy is a standalone class in `src/budgetbench/strategies/`, inheriting from the `MemoryStrategy` ABC. Leverage existing high-quality libraries (`tiktoken`, `mem0ai`, `llmlingua`, `chromadb`) to avoid hand-rolling complex logic like vector search or token classification.

## User Constraints (from CONTEXT.md)

> Note: CONTEXT.md does not yet exist for Phase 2. Using constraints from ROADMAP.md and PHASE 1.

### Locked Decisions
- All strategies must implement the `MemoryStrategy` ABC.
- Strategies must respect the `active_budget` (token count).
- Target models: Qwen2.5 (14B, 32B), Qwen3-Coder (30B).

### the agent's Discretion
- Implementation details of each strategy.
- Selection of supporting libraries (e.g., choice of vector store).
- Specific configurations for RAG (top-k) and LLMLingua (model variant).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BASE-01 | Truncation (FIFO) baseline | Standard implementation using `tiktoken`. |
| BASE-02 | Summary-buffer baseline | Uses LLM-based summarization of old context. |
| BASE-03 | Simple RAG baseline | Uses `sentence-transformers` and `chromadb`/`faiss`. |
| BASE-04 | MemGPT/Letta style baseline | Integrated via `letta` or custom core-memory logic. |
| BASE-05 | Mem0 baseline | Integrated via `mem0ai` library. |
| BASE-06 | LLMLingua-2 compression baseline | Integrated via `llmlingua` with token-level pruning. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tiktoken` | 0.12.0 | Token counting | Industry standard for OpenAI-compatible tokenization. [VERIFIED: pip list] |
| `chromadb` | 1.5.2 | Vector Store | Reliable, local-first vector database. [VERIFIED: pip list] |
| `sentence-transformers` | 5.4.1 | Embeddings | Efficient local embedding models (e.g., `all-MiniLM-L6-v2`). [VERIFIED: pip list] |
| `mem0ai` | 1.0.3 | Persistent Memory | Specialized in graph-based additive memory. [VERIFIED: pip list] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| `llmlingua` | 0.2.2+ | Prompt Compression | Required for BASE-06. [CITED: llmlingua.com] |
| `letta` | 0.16.x | Agentic Memory | Required for BASE-04. [CITED: letta.com] |
| `torch` | 2.11.0 | DL Backend | Needed for `sentence-transformers` and `llmlingua`. [VERIFIED: pip list] |

**Installation:**
```bash
pip install letta llmlingua faiss-cpu
```

## Architecture Patterns

### Recommended Project Structure
```
src/budgetbench/
├── core/
│   └── strategy.py       # ABC definition
└── strategies/
    ├── __init__.py
    ├── truncation.py     # BASE-01
    ├── summary.py        # BASE-02
    ├── rag.py            # BASE-03
    ├── memgpt.py         # BASE-04
    ├── mem0.py           # BASE-05
    └── llmlingua.py      # BASE-06
```

### Pattern: State Management in Strategies
Strategies like RAG, Mem0, and Letta maintain internal state (vector indexes, memories).
**Recommendation:** Ensure strategies can be reset or initialized with a unique `user_id` per evaluation task to prevent cross-contamination between benchmark runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token Counting | String splitting | `tiktoken` | Accuracy for LLM context windows. |
| Vector Search | Cosine similarity | `chromadb` | Handles indexing, persistence, and efficient retrieval. |
| Summarization | Custom prompts | `langchain` chains | Well-tested summary templates and logic (optional). |
| Compression | Heuristic pruning | `LLMLingua-2` | Uses a trained model to identify token importance. |

## Common Pitfalls

### Pitfall 1: Token Counting Mismatch
**What goes wrong:** Strategy thinks it is within budget, but the Runner's `tokenizer_fn` (or the actual LLM) disagrees.
**How to avoid:** Always use the same `tokenizer_fn` passed to the strategy or ensure consistent `tiktoken` encoding (e.g., `o200k_base` for newer models).

### Pitfall 2: Context Fragmentation in RAG
**What goes wrong:** Retrieving messages out of order breaks the conversation flow.
**How to avoid:** Retrieve relevant chunks but re-sort them by timestamp/index before presenting to the LLM.

### Pitfall 3: LLMLingua-2 Resource Usage
**What goes wrong:** Large encoder models can be slow on CPU.
**How to avoid:** Use the `bert-base` variant instead of `xlm-roberta-large` for local CPU-bound benchmarking.

## Code Examples

### BASE-06: LLMLingua-2 Integration
```python
# Source: LLMLingua-2 Official Docs
from llmlingua import PromptCompressor

class LLMLinguaStrategy(MemoryStrategy):
    def __init__(self, model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"):
        self.compressor = PromptCompressor(model_name=model_name, use_llmlingua2=True)

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        full_text = "\n".join([m["content"] for m in messages])
        # Calculate rate based on budget vs current tokens
        # ... logic to keep system prompt intact ...
        compressed = self.compressor.compress_prompt(full_text, rate=0.5)
        return [{"role": "user", "content": compressed["compressed_prompt"]}]
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| tiktoken | All | ✓ | 0.12.0 | — |
| sentence-transformers | RAG | ✓ | 5.4.1 | — |
| mem0ai | Mem0 | ✓ | 1.0.3 | — |
| chromadb | RAG, Mem0 | ✓ | 1.5.2 | — |
| llmlingua | LLMLingua-2 | ✗ | — | Install via pip |
| letta | Letta | ✗ | — | Install via pip |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | None |
| Quick run command | `pytest tests/test_strategy.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| BASE-01 | Truncates messages to fit budget | Unit | `pytest tests/test_truncation.py` |
| BASE-02 | Summarizes old messages | Unit | `pytest tests/test_summary.py` |
| BASE-06 | Compresses prompt text | Unit | `pytest tests/test_llmlingua.py` |

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | Validate `OpenAIMessage` structure. |

## Sources

### Primary (HIGH confidence)
- `pip list` - Verified installed package versions.
- Official `mem0ai` and `llmlingua` documentation.
- `src/budgetbench/core/strategy.py` - Existing ABC definition.

## Metadata
**Confidence breakdown:**
- Standard stack: HIGH
- Architecture: HIGH
- Pitfalls: MEDIUM

**Research date:** 2026-04-28
**Valid until:** 2026-05-28
