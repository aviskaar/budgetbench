# BudgetBench

[![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](https://arxiv.org/abs/XXXX.XXXXX)

<!-- TODO: replace XXXX.XXXXX above and in the Citation section once arXiv announces the ID -->

BudgetBench is a pilot evaluation protocol and reference harness for local LLM agents to compare memory strategies across fixed active-context-budget tiers (2k/4k/8k/16k/32k). 

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
The current pilot focuses on long-horizon agentic tasks with deterministic or explicitly labeled proxy grading:
1. **Software Engineering**: A SWE-bench Verified scaffold with deterministic patch-similarity proxy scoring. This is infrastructure-only evidence, not official SWE-bench resolution.
2. **Long-Context QA**: LongBench v2 multiple-choice QA with exact-match grading.
3. **Memory-Agent Pilots**: A deterministic synthetic memory task and an opt-in LongMemEval oracle adapter with approximate local scoring unless external or official judge results are added.
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

### Running Pilot Studies
The primary entry point for running evaluations is `scripts/run_pilot.py`.

**Basic Pilot Run:**
```bash
python scripts/run_pilot.py --model qwen2.5-14b --llm-url http://localhost:11434/v1/chat/completions
```

For claim-bearing runs, pass an explicit tokenizer for budget enforcement so
the logged violation rates reflect the served model's tokenizer rather than the
default fallback approximation:

```bash
python scripts/run_pilot.py \
  --model qwen2.5:1.5b \
  --tokenizer Qwen/Qwen2.5-1.5B-Instruct
```

**Full Study (All 5 Budget Tiers):**
```bash
python scripts/run_pilot.py --full-study --model qwen2.5-14b
```

**Specific Tasks and Strategies:**
```bash
python scripts/run_pilot.py --tasks swe tau --strategies rag summary
```

**Repeated, order-randomized runs for latency/stability checks:**
```bash
python scripts/run_pilot.py \
  --full-study \
  --model qwen2.5:1.5b \
  --tokenizer Qwen/Qwen2.5-1.5B-Instruct \
  --repeat-cells 3 \
  --shuffle-cells
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

To produce the exact official LongMemEval hypothesis format
(`question_id`, `hypothesis`) for the upstream evaluator:

```bash
python scripts/export_longmem_official_hypotheses.py \
  --log-dir logs/full_study/longmem_oracle_qwen15b_50_predictions \
  --data-path data/longmemeval_oracle.json \
  --strategies lean_retrieval \
  --budgets 2048 \
  --output results/longmemeval_lean2048_hypotheses.jsonl
```

Then run the official evaluator from a cloned `longmemeval` checkout:

```bash
python scripts/run_longmemeval_official_eval.py \
  --repo-dir /path/to/longmemeval \
  --judge-model gpt-4o \
  --hypotheses results/longmemeval_lean2048_hypotheses.jsonl \
  --data-file /path/to/longmemeval/data/longmemeval_oracle.json
```

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

### SWE-bench Official Evaluation Path

Export one SWE bucket into the exact official SWE-bench prediction schema:

```bash
python scripts/export_swebench_predictions.py \
  --log-dir logs/full_study/final_qwen25_15b_89items \
  --strategy truncation \
  --budget 2048 \
  --output results/swe_truncation_2048_predictions.jsonl
```

If this exporter reports that no prediction-bearing rows exist, the selected
bucket came from an older pilot log format that did not persist SWE patches.
In that case, rerun the desired SWE bucket with the current runner before using
the official evaluator.

Then run the official containerized SWE-bench harness:

```bash
python scripts/run_swebench_official_eval.py \
  --predictions results/swe_truncation_2048_predictions.jsonl \
  --dataset-name princeton-nlp/SWE-bench_Verified \
  --run-id bb_swe_truncation_2048 \
  --max-workers 2 \
  --clean
```

This wrapper follows the official Docker-based evaluation path from the upstream
SWE-bench repository. In this workspace, a focused rerun has already been
executed through the official harness, producing
`qwen2.5:1.5b.budgetbench_official2fix_20260623.json` plus per-instance logs
under `logs/run_evaluation/budgetbench_official2fix_20260623/`. The improved
rerun filters out one structurally invalid patch before official evaluation,
but the remaining two submitted patches still fail official patch application.
This artifact therefore records a completed official evaluation with negative
patch-quality outcomes rather than SWE task success.

### Analyzing Results
BudgetBench saves results in JSONL format in the `logs/` directory. You can use the provided analysis scripts to visualize the tradeoff curves:

```bash
python scripts/plot_tradeoffs.py --log_dir logs/pilot/TIMESTAMP
```

Each per-cell JSONL now records prompt-audit rows with:
- tokenizer identity and backend
- a hash of the post-strategy prompt
- the serialized post-strategy prompt itself
- the counted prompt tokens before enforcement

These audit rows are separate from the per-item metric row so older analysis
logic remains stable.

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

## Scope Note

This repository currently supports a protocol/tooling paper more strongly than a datasets-and-benchmarks claim. For benchmark-grade claims, the remaining required upgrades are:

- official or validated LongMemEval judging, if LongMemEval remains claim-bearing
- larger powered slices and stronger evaluated baselines

## 📄 Citation

If you use BudgetBench, please cite the preprint:

```bibtex
@misc{rao2026budgetbench,
  title        = {BudgetBench: A Budget-Tiered Protocol and Pilot Harness for Memory Strategy Evaluation in Local Large Language Model Agents},
  author       = {Rao, Aditya Karnam Gururaj and Jaggi, Arjun},
  year         = {2026},
  eprint       = {XXXX.XXXXX},
  archivePrefix = {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/XXXX.XXXXX}
}
```

> The arXiv identifier (`XXXX.XXXXX`) will be filled in once the preprint is announced.
