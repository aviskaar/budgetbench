# Stack Research

**Domain:** Local Agent Memory Benchmark

## Recommended Stack
- **Python 3.10+**: Standard for LLM evaluation.
- **Harness Frameworks**: `mini-SWE-agent` (for SWE-bench), `lm-evaluation-harness` (for standard QA).
- **Inference Engine (Local GPU)**: `llama.cpp` (via `llama-cpp-python`) for KV-cache quantization on NVIDIA, `mlx-lm` for Apple Silicon.
- **Embeddings/RAG**: `FAISS` and `bge-small-en-v1.5` for local vector store and retrieval baselines.
- **Agent Memory Libs**: `LangChain` (for basic buffer/summary), `Mem0` and `Letta` for hierarchical agents.

## Rationale
A lightweight, headless framework ensures no hidden overhead when calculating token usage. `llama.cpp` and `mlx` are the only realistic ways to push a 32K context window onto an RTX 5060 Ti / M4 Pro using strict KV-cache quantization.

## Avoid
- `vLLM`: Great for throughput, but high memory overhead making 32B models on consumer hardware at 32K impossible without complex multi-GPU setups.
- `ToolBench`: Grading relies on LLM-as-judge which violates the deterministic requirement.