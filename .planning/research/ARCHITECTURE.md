# Architecture Research

**Domain:** Local Agent Memory Benchmark

## Core Components
1. **Runner / Simulator Engine**: The main event loop for long-horizon agent interactions.
2. **Budget Enforcer**: Wraps the inference call, tracks tokens, throws `BudgetExceeded` exceptions.
3. **Memory Strategy Plugins**: Objects conforming to `MemoryStrategy` ABC. These are invoked when `BudgetExceeded` is hit to compress/trim context.
4. **Task Environments**: Interfaces bounding `mini-SWE-agent`, `τ²-bench`, and `LongBench v2`.

## Data Flow
Environment -> Memory Strategy -> Budget Enforcer -> Inference Engine -> Environment.