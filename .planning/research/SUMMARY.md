# Research Summary

**Domain:** Local Agent Memory Benchmark

## Key Findings
- **Stack**: Python 3.10+, `llama.cpp` (NVIDIA) and `mlx` (Mac), `FAISS` for vector indexing, `mini-SWE-agent`.
- **Table Stakes**: Active budget tracking, strict `MemoryStrategy` abstraction, and deterministic metrics.
- **Watch Out For**: LLM-as-judge variability, hidden context prompt overheads, and KV Cache OOM crashes on consumer hardware.
- **Architecture**: A pipeline flowing from Environment -> Memory Strategy -> Budget Enforcer -> Inference Engine.

The local agent memory benchmark is viable but must rigorously avoid cloud API reliance and non-deterministic grading to stand out against recent unstandardized method papers.