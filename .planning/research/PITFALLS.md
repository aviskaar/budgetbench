# Pitfalls Research

**Domain:** Local Agent Memory Benchmark

## Common Mistakes
- **LLM-as-Judge Variability**: Contaminates results. *Prevention: Strict exact-match or state-comparison testing.*
- **Hidden Context Overheads**: System prompts taking up large chunks of the active budget without being accounted for. *Prevention: Budget enforcer intercepts raw token lengths immediately before generation.*
- **KV Cache Out-Of-Memory**: Crashing halfway through an evaluation run. *Prevention: Pre-allocate static KV sizes with MLX/llama.cpp and use Q8 KV quantization.*