# BudgetBench

BudgetBench is a standardized community benchmark for local LLM agents to evaluate memory strategies across fixed active-context-budget tiers (2k/4k/8k/16k/32k). 

In the regime of local consumer hardware, context length is a scarce resource. BudgetBench provides standardized tradeoff curves of agent task quality versus token budget for pluggable memory strategies on local LLMs, allowing researchers and developers to understand how different memory-management approaches perform when context is constrained.

## 🚀 Core Value Proposition

**"How small can your context get?"**

BudgetBench enables you to answer this by fixing a local LLM and a task, then sweeping the active context budget across standardized tiers to see which memory strategy dominates at each level.

## 🛠 Architecture

BudgetBench is designed as a plug-and-play framework. The core components are:

- **`MemoryStrategy`**: A standardized interface (ABC) for any memory management logic. A strategy takes a list of messages and a budget, and returns a budget-compliant list.
- **Budget Enforcer**: A wrapper that ensures LLM calls strictly adhere to the specified token budget tier.
- **Evaluation Harness**: A runner that executes tasks and logs deterministic metrics without relying on LLM-as-judge.

### Supported Memory Strategies (Baselines)
BudgetBench includes several reference implementations:
- **Truncation**: Simple sliding-window approach.
- **Full Context**: Pass-through baseline for full-history comparisons and infeasibility checks.
- **Summary-Buffer**: Rolling summarization of conversation history.
- **RAG**: Vanilla retrieval over an episodic FAISS store.
- **Checkpoint-Context**: Extractive checkpoint plus recent tail plus retrieved evidence.
- **Mem0**: Production-grade hierarchical memory.
- **Letta**: OS-style hierarchical memory (MemGPT).
- **LLMLingua-2**: Prompt compression for smooth budget/quality curves.

### Evaluated Task Families
The benchmark focuses on long-horizon agentic tasks with deterministic grading:
1. **Software Engineering**: A SWE-bench Verified scaffold with deterministic patch-similarity proxy scoring.
2. **Long-Context QA**: LongBench v2 multiple-choice QA with exact-match grading.
3. **Memory-Agent Pilots**: A deterministic synthetic memory task and an opt-in LongMemEval oracle adapter.
4. **Tool-Use Chains**: Tau-bench/tau2-bench adapters where local data dependencies are installed.

## 📦 Installation

### Prerequisites
- Python 3.10+
- A local LLM server (e.g., [Ollama](https://ollama.com/), [llama.cpp](https://github.com/ggerganov/llama.cpp), or [MLX](https://github.com/ml-explore/mlx) for Apple Silicon).

### Setup
```bash
git clone https://github.com/your-repo/budgetbench.git
cd budgetbench
pip install -r requirements.txt
```
*(Note: Some strategies like `mem0`, `letta`, and `llmlingua` require optional dependencies; the harness skips them gracefully if not installed.)*

## 💻 Usage

### Running Benchmarks
The primary entry point for running evaluations is `scripts/run_pilot.py`.

**Basic Pilot Run:**
```bash
python scripts/run_pilot.py --model qwen2.5-14b --llm-url http://localhost:11434/v1/chat/completions
```

**Full Study (All 5 Budget Tiers):**
```bash
python scripts/run_pilot.py --full-study --model qwen2.5-14b
```

**Specific Tasks and Strategies:**
```bash
python scripts/run_pilot.py --tasks swe tau --strategies rag summary
```

**Public LongMemEval Oracle Pilot:**
Download `longmemeval_oracle.json` from the official
`xiaowu0162/longmemeval-cleaned` Hugging Face dataset to
`data/longmemeval_oracle.json`, then run:

```bash
python scripts/run_pilot.py --full-study \
  --run-id longmem_oracle_qwen15b_50_predictions \
  --tasks longmem \
  --strategies truncation rag lean_retrieval full_context \
  --budgets 2048 4096 8192 \
  --limit-tasks 50 \
  --model qwen2.5:1.5b
```

The LongMemEval adapter uses deterministic normalized-containment scoring for
local pilots; this is not the official LongMemEval judge.

Export prediction-bearing logs for external LongMemEval judge review:

```bash
python scripts/export_longmem_judge_inputs.py \
  --log-dir logs/full_study/longmem_oracle_qwen15b_50_predictions \
  --data-path data/longmemeval_oracle.json \
  --output results/longmem_judge_inputs_qwen15b_50_predictions.jsonl
```

The export includes every item-strategy-budget row; budget violations without
model predictions are marked as not judgeable instead of being silently dropped.

Run the external judge bridge with a real judge key when available:

```bash
python scripts/run_longmem_external_judge.py \
  --input results/longmem_judge_inputs_qwen15b_50_prediction_only.jsonl \
  --output results/longmem_external_judge_gpt4omini.jsonl \
  --aggregate-output results/longmem_external_judge_gpt4omini.csv \
  --judge-url https://openrouter.ai/api/v1/chat/completions \
  --judge-model openai/gpt-4o-mini \
  --api-key-env OPENROUTER_API_KEY \
  --strategies lean_retrieval full_context truncation \
  --budgets 2048 4096 8192
```

Use the judge model, prompt version, and provider URL in any reported result.
The bundled local smokes are only serializer/sanity checks; they do not count as
official LongMemEval evidence.

### Analyzing Results
BudgetBench saves results in JSONL format in the `logs/` directory. You can use the provided analysis scripts to visualize the tradeoff curves:

```bash
python scripts/plot_tradeoffs.py --log_dir logs/pilot/TIMESTAMP
```

## 🔬 Budget Tiers
Evaluations are conducted across the following strictly enforced budget tiers:
- **2K** (2,048 tokens)
- **4K** (4,096 tokens)
- **8K** (8,192 tokens)
- **16K** (16,384 tokens)
- **32K** (32,768 tokens)

## 🤝 Contributing
We welcome new `MemoryStrategy` implementations! To add a strategy:
1. Inherit from `budgetbench.core.strategy.MemoryStrategy`.
2. Implement the `__call__(self, messages, active_budget)` method.
3. Add your strategy to `budgetbench/strategies/` and register it in `scripts/run_pilot.py`.
