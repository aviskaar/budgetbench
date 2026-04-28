# Features Research

**Domain:** Local Agent Memory Benchmark

## Table Stakes
- **Active Budget Tracking**: System accurately measures pre-call context length.
- **Strategy Abstraction**: Interface for any external memory logic to intercept and mutate context windows.
- **Deterministic Metrics**: Metric generation (e.g., `pass^k`, % Resolved, Exact Match) must not rely on LLM judges.

## Differentiators
- **Local Priority**: Specific constraints optimized for <24GB VRAM running 8B to 32B quantized models.
- **Multi-task Horizon**: Web QA, Coding, and Multi-turn Tool-use combined into one suite.

## Anti-Features
- **Leaderboard for 70B+ / Cloud APIs**: Distracts from the local LLM focus.
- **Subjective "Vibe" Checks**: Must strictly avoid non-deterministic pass/fail rates.