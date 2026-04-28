<!-- GSD:project-start source:PROJECT.md -->
## Project

**BudgetBench**

A standardized community benchmark for local LLM agents to evaluate memory strategies across fixed active-context-budget tiers (2k/4k/8k/16k/32k). It provides a swappable third-party strategy interface for long-horizon tasks, targeting the reality of local consumer hardware where context length is a scarce resource.

**Core Value:** Provide the first standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs.

### Constraints

- **Type**: Technical — Must support 2K/4K/8K/16K/32K context budget tiers strictly.
- **Type**: Hardware — Must run on consumer hardware (RTX 5060 Ti 16GB, Mac M4/M5 Pro).
- **Type**: Evaluation — All tasks must have deterministic grading. No LLM-as-judge.
- **Type**: Timeline — Must ship initial pilot in 1 week, and arXiv preprint in 4 weeks.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
- **Python 3.10+**: Standard for LLM evaluation.
- **Harness Frameworks**: `mini-SWE-agent` (for SWE-bench), `lm-evaluation-harness` (for standard QA).
- **Inference Engine (Local GPU)**: `llama.cpp` (via `llama-cpp-python`) for KV-cache quantization on NVIDIA, `mlx-lm` for Apple Silicon.
- **Embeddings/RAG**: `FAISS` and `bge-small-en-v1.5` for local vector store and retrieval baselines.
- **Agent Memory Libs**: `LangChain` (for basic buffer/summary), `Mem0` and `Letta` for hierarchical agents.
## Rationale
## Avoid
- `vLLM`: Great for throughput, but high memory overhead making 32B models on consumer hardware at 32K impossible without complex multi-GPU setups.
- `ToolBench`: Grading relies on LLM-as-judge which violates the deterministic requirement.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
