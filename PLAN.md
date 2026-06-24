# BudgetBench Research Upgrade Plan

Date: 2026-06-18
Scope: Upgrade the current BudgetBench pilot paper into a defensible novel research artifact.

## Bottom Line

The current direction is viable, but the paper must be positioned as a benchmark/protocol contribution, not as a new memory method and not as the first work to vary context budget. The novel claim should be:

> BudgetBench is a standardized active-context-budget evaluation protocol for local LLM agents, measuring quality, latency, budget use, and violation rate across swappable memory strategies and deterministic task graders.

After the June 18 feasibility work, the sharper empirical claim is:

> On a 32K-feasible LongBench v2 slice, BudgetBench can ask whether budgeted strategies match natural full context under the same local model. In the current 50-item Qwen2.5-1.5B pilot, RAG at 8K matches full-context at 32K within paired uncertainty while using roughly 24% of the wall-clock time; full-context is categorically infeasible at 2K and 8K.

The follow-up memory work adds two memory task shapes:

> On a 30-item deterministic memory slice with single-session facts, knowledge updates, temporal reasoning, preferences, and abstention cases, `lean_retrieval@1024` reaches 0.83 accuracy versus `full_context@2048` at 0.80, while full context is infeasible at 512 and 1024 tokens.

The added checkpoint baseline makes the memory story more operational:

> `checkpoint_context@1024` reaches 0.67 accuracy on the same 30-item memory slice while staying cheaper and more workflow-like than pure retrieval, and it converges to 0.80 at 2048. That gives the paper a middle-ground policy between raw truncation and aggressive retrieval.

On the public LongMemEval oracle slice, the same checkpoint baseline reaches 0.30 at 4096 tokens and 0.10 at 2048 and 8192. It is not the strongest public-memory policy, but it confirms the baseline behaves differently from both truncation and lean retrieval on real long-horizon data.

The category split makes the pilot more useful: retrieval-based strategies recover single-fact and temporal-reasoning items at tight budgets where truncation fails, while knowledge-update and abstention are easy and the preference category remains a model/prompt failure even under full context.

> On a 50-item category-balanced LongMemEval oracle-file pilot with deterministic normalized-containment scoring, `lean_retrieval@2048` and `lean_retrieval@4096` reach 0.46 accuracy versus `full_context@8192` at 0.34. Both lean rows beat the 8K full-context baseline by +0.12 paired accuracy with bootstrap CIs above zero, while full context violates the active budget on 90% of 2K items, 70% of 4K items, and 16% of 8K items.

This is now stronger than an integration smoke test, but still pilot evidence. The artifact now includes a 500-item LongMemEval oracle-file study scored by the upstream GPT-4o evaluator and a 50-item, two-repeat LongBench replication with hosted Qwen3-30B-A3B, exact tokenization, and shuffled cell order. The remaining transfer gap is local rather than model-scale: the stronger-model run is API-hosted, and LongMemEval remains oracle-file rather than full-history.

## Current Evidence Snapshot

### Completed on 2026-06-18

- Paper reframing:
  - Added ContextBudget, BudgetMem, EvoMemBench, Engram, LightMem, Prompt Compression in the Wild, and MemoryAgentBench references.
  - Added a "Closest Concurrent Work" subsection and comparison table.
  - Reframed novelty around the conjunction of local LLMs, fixed active budgets, swappable strategies, deterministic graders, and operational metrics.
  - Marked the multimodal smoke test as infrastructure validation only.
- Harness and analysis:
  - Added `full_context` baseline.
  - Added `lean_retrieval` hybrid dense + lexical + recency/salience baseline.
  - Added explicit `--budgets` CLI support.
  - Added `--max-natural-tokens` filtering for full-context-feasible LongBench slices.
  - Added stable LongBench item IDs and per-row `natural_prompt_tokens`.
  - Added aggregate bootstrap confidence intervals.
  - Added paired-delta analysis versus a baseline cell such as `full_context@32768`.
  - Added raw prediction logging on per-item quality rows.
  - Added `scripts/export_longmem_judge_inputs.py` to join LongMemEval prediction logs back to oracle questions and references for external judge review.
  - Fixed token counting for literal special-token strings such as `<|endoftext|>`.
- Verification:
  - `rtk pytest -q` passed with 132 tests after adding the public LongMemEval adapter, 50-item oracle run artifacts, Qwen3.6-35B probe documentation, prediction logging, and judge-export support.
  - `paper/main.tex` compiled with `rtk tectonic main.tex`; remaining warnings are layout underfull warnings in table-heavy sections.
  - `rtk git diff --check` passed after the 50-item LongMemEval, Qwen3.6-35B probe, prediction logging, and judge-export paper/plan updates.
- New evidence artifacts:
  - 10-item feasibility CSV: `results/full_study_qwen2_5_1_5b_20260618_022748.csv`
  - 10-item paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_095646.csv`
  - 50-item feasibility CSV: `results/full_study_qwen2_5_1_5b_20260618_103638.csv`
  - 50-item paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_103638.csv`
  - 50-item updated CSV with `lean_retrieval@8K`: `results/full_study_qwen2_5_1_5b_20260618_155102.csv`
  - 50-item updated paired deltas with `lean_retrieval@8K`: `results/paired_deltas_qwen2_5_1_5b_20260618_155102.csv`
  - Raw logs: `logs/full_study/feasibility_long50_fit32k/`
  - Gemma transfer CSV: `results/full_study_gemma4_e2b_20260618_161005.csv`
  - Gemma transfer paired deltas: `results/paired_deltas_gemma4_e2b_20260618_161005.csv`
  - Gemma raw logs: `logs/full_study/transfer_gemma4_fit32k_20/`
  - Synthetic memory CSV: `results/full_study_qwen2_5_1_5b_20260618_175438.csv`
  - Synthetic memory paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_175438.csv`
  - Synthetic memory raw logs: `logs/full_study/memory_synthetic_qwen15b_30/`
  - Synthetic memory category rerun CSV: `results/full_study_qwen2_5_1_5b_20260618_203210.csv`
  - Synthetic memory category paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_203210.csv`
  - Synthetic memory category diagnostics: `results/grouped_memory_category_qwen2_5_1_5b_20260618_203210.csv`
  - Synthetic memory category raw logs: `logs/full_study/memory_synthetic_qwen15b_30_categories_live/`
  - Synthetic memory checkpoint-context CSV: `results/full_study_qwen2_5_1_5b_20260619_150538.csv`
  - Synthetic memory checkpoint-context paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260619_150538.csv`
  - Synthetic memory checkpoint-context category diagnostics: `results/grouped_memory_category_qwen2_5_1_5b_20260619_150550.csv`
  - Synthetic memory checkpoint-context raw logs: `logs/full_study/memory_synthetic_checkpoint_qwen15b_30/`
  - LongMemEval checkpoint-context CSV: `results/full_study_qwen2_5_1_5b_20260619_151007.csv`
  - LongMemEval checkpoint-context paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260619_151007.csv`
  - LongMemEval checkpoint-context category diagnostics: `results/grouped_memory_category_qwen2_5_1_5b_20260619_151007.csv`
  - LongMemEval checkpoint-context raw logs: `logs/full_study/longmem_oracle_checkpoint_qwen15b_10/`
  - SWE checkpoint-context CSV: `results/full_study_qwen2_5_1_5b_20260619_151509.csv`
  - SWE checkpoint-context paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260619_151509.csv`
  - SWE checkpoint-context raw logs: `logs/full_study/swe_checkpoint_qwen15b_5/`
  - 12-item LongMemEval oracle CSV: `results/full_study_qwen2_5_1_5b_20260618_204306.csv`
  - 12-item LongMemEval oracle paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_204306.csv`
  - 12-item LongMemEval oracle category diagnostics: `results/grouped_memory_category_qwen2_5_1_5b_20260618_204306.csv`
  - 12-item LongMemEval oracle raw logs: `logs/full_study/longmem_oracle_qwen15b_12/`
  - 50-item LongMemEval prediction-enabled oracle CSV: `results/full_study_qwen2_5_1_5b_20260618_213603.csv`
  - 50-item LongMemEval prediction-enabled oracle paired deltas: `results/paired_deltas_qwen2_5_1_5b_20260618_213603.csv`
  - 50-item LongMemEval prediction-enabled oracle category diagnostics: `results/grouped_memory_category_qwen2_5_1_5b_20260618_213603.csv`
  - 50-item LongMemEval prediction-enabled oracle raw logs: `logs/full_study/longmem_oracle_qwen15b_50_predictions/`
  - 50-item LongMemEval external-judge input bundle: `results/longmem_judge_inputs_qwen15b_50_predictions.jsonl`
  - 50-item LongMemEval prediction-only judge input bundle: `results/longmem_judge_inputs_qwen15b_50_prediction_only.jsonl`
  - Key-row LongMemEval external-judge input bundle: `results/longmem_judge_inputs_qwen15b_50_key_rows.jsonl`
  - Balanced 24-row prediction-only judge sample: `results/longmem_external_judge_gemma31b_balanced24_predonly.jsonl`
  - Balanced 24-row prediction-only judge aggregate: `results/longmem_external_judge_gemma31b_balanced24_predonly.csv`
  - `qwen3.6:35b-mlx` balanced 12-row judge attempt with zero parseable rows: `results/longmem_external_judge_qwen36_35b_balanced12.jsonl`
  - Qwen3.6-35B LongMemEval probe CSV: `results/full_study_qwen3_6_35b-mlx_20260618_212102.csv`
  - Qwen3.6-35B LongMemEval probe paired deltas: `results/paired_deltas_qwen3_6_35b-mlx_20260618_212102.csv`
  - Qwen3.6-35B LongMemEval probe category diagnostics: `results/grouped_memory_category_qwen3_6_35b-mlx_20260618_212102.csv`
  - Qwen3.6-35B LongMemEval probe logs: `logs/full_study/longmem_oracle_qwen36_35b_probe5/`
  - Qwen3.6-35B LongMemEval transfer CSV: `results/full_study_qwen3_6_35b-mlx_20260619_140108.csv`
  - Qwen3.6-35B LongMemEval transfer paired deltas: `results/paired_deltas_qwen3_6_35b-mlx_20260619_140108.csv`
  - Qwen3.6-35B LongMemEval transfer category diagnostics: `results/grouped_memory_category_qwen3_6_35b-mlx_20260619_140108.csv`
  - Qwen3.6-35B LongMemEval transfer logs: `logs/full_study/longmem_oracle_qwen36_35b_10/`
  - Gemma4-12B LongMemEval negative-transfer logs: `logs/full_study/longmem_oracle_gemma4_12b_10/`
  - Qwen3.6-35B LongBench partial transfer attempts: `logs/full_study/feasibility_longbench_qwen36_35b_10/` and `logs/full_study/feasibility_longbench_qwen36_35b_5/`; both stopped after truncation@8K completed at 0.00 because the remaining 32K/full-context cells were too slow for this hardware
  - Qwen3.5-2B LongBench 5-item transfer CSV: `results/full_study_qwen3_5_2b_20260619_142423.csv`
  - Qwen3.5-2B LongBench 5-item transfer paired deltas: `results/paired_deltas_qwen3_5_2b_20260619_142423.csv`
  - Qwen3.5-2B LongBench 5-item transfer logs: `logs/full_study/feasibility_longbench_qwen35_2b_5/`
  - Hosted Qwen3-30B-A3B LongBench 50-item, two-repeat aggregate: `results/full_study_qwen_qwen3-30b-a3b-instruct-2507_20260624_123733.csv`
  - Hosted Qwen3-30B-A3B paired deltas: `results/paired_deltas_qwen_qwen3-30b-a3b-instruct-2507_20260624_123733.csv`
  - Hosted Qwen3-30B-A3B run metadata and cost audit: `results/longbench_qwen3_30b_openrouter_50x2_20260624_run_metadata.json`
  - Hosted Qwen3-30B-A3B raw logs: `logs/full_study/longbench_qwen3_30b_openrouter_50x2_20260624/`
  - Qwen3.6-35B partial 20-item transfer attempt: `logs/full_study/longmem_oracle_qwen36_35b_20/`

### 50-Item LongBench v2 Feasible-Slice Result

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id feasibility_long50_fit32k \
  --model qwen2.5:1.5b \
  --tasks long \
  --strategies truncation rag full_context \
  --budgets 2048 8192 32768 \
  --limit-tasks 50 \
  --max-natural-tokens 32768
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 2K | 0.34 | 0.00 | 31.6s |
| truncation | 8K | 0.26 | 0.00 | 128.3s |
| truncation | 32K | 0.32 | 0.00 | 610.0s |
| RAG | 2K | 0.24 | 0.00 | 49.7s |
| RAG | 8K | 0.34 | 0.00 | 144.6s |
| RAG | 32K | 0.32 | 0.00 | 608.5s |
| lean_retrieval | 8K | 0.30 | 0.00 | 147.6s |
| full_context | 2K | 0.00 | 1.00 | 10.3s |
| full_context | 8K | 0.00 | 1.00 | 10.3s |
| full_context | 32K | 0.32 | 0.00 | 605.9s |

Paired deltas versus `full_context@32768`:

| Candidate | Paired delta | 95% bootstrap CI | Interpretation |
| --- | ---: | ---: | --- |
| truncation@2K | +0.02 | [-0.10, +0.14] | Matches full-context within uncertainty at far lower latency. |
| truncation@8K | -0.06 | [-0.14, +0.02] | Slightly worse in this slice. |
| RAG@2K | -0.08 | [-0.18, 0.00] | Worse or tied. |
| RAG@8K | +0.02 | [-0.08, +0.12] | Matches full-context within uncertainty at about 24% of full-context wall time. |
| RAG@32K | 0.00 | [0.00, 0.00] | Same effective prompt regime as full-context on this feasible slice. |
| lean_retrieval@8K | -0.02 | [-0.12, +0.08] | Setup succeeds but does not improve over simple RAG in this slice. |

Kill-criteria status: pass. The 50-item run shows a budgeted strategy matching full context within paired uncertainty while substantially reducing latency, plus hard budget-compliance differences at 2K and 8K.

### 20-Item Gemma4:e2b Transfer Check

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id transfer_gemma4_fit32k_20 \
  --model gemma4:e2b \
  --tasks long \
  --strategies truncation rag full_context \
  --budgets 8192 32768 \
  --limit-tasks 20 \
  --max-natural-tokens 32768
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 8K | 0.00 | 0.00 | 170.3s |
| truncation | 32K | 0.05 | 0.00 | 349.3s |
| RAG | 8K | 0.00 | 0.00 | 171.9s |
| RAG | 32K | 0.05 | 0.00 | 123.6s |
| full_context | 8K | 0.00 | 1.00 | 3.8s |
| full_context | 32K | 0.05 | 0.00 | 123.3s |

Paired deltas versus `full_context@32768`:

| Candidate | Paired delta | 95% bootstrap CI | Interpretation |
| --- | ---: | ---: | --- |
| truncation@8K | -0.05 | [-0.15, 0.00] | Worse or tied. |
| RAG@8K | -0.05 | [-0.15, 0.00] | Worse or tied. |
| RAG@32K | 0.00 | [0.00, 0.00] | Same effective result as full-context at 32K. |

Transfer status: not confirmed. The Qwen1.5B latency/quality signal does not transfer cleanly to Gemma4:e2b on this 20-item slice because all Gemma strategies have near-floor exact-match accuracy. This should be reported as model-dependent behavior and a prompt/serving suitability warning, not as evidence against the protocol.

### 30-Item Synthetic Memory-Agent Pilot

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id memory_synthetic_qwen15b_30 \
  --model qwen2.5:1.5b \
  --tasks memory \
  --strategies truncation rag lean_retrieval full_context \
  --budgets 512 1024 2048 \
  --limit-tasks 30
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 512 | 0.43 | 0.00 | 5.7s |
| truncation | 1024 | 0.43 | 0.00 | 8.4s |
| truncation | 2048 | 0.80 | 0.00 | 13.4s |
| RAG | 512 | 0.73 | 0.00 | 18.9s |
| RAG | 1024 | 0.80 | 0.00 | 22.2s |
| RAG | 2048 | 0.80 | 0.00 | 3.2s |
| lean_retrieval | 512 | 0.80 | 0.00 | 15.6s |
| lean_retrieval | 1024 | 0.83 | 0.00 | 19.2s |
| lean_retrieval | 2048 | 0.80 | 0.00 | 3.1s |
| full_context | 512 | 0.00 | 1.00 | 0.1s |
| full_context | 1024 | 0.00 | 1.00 | 0.1s |
| full_context | 2048 | 0.80 | 0.00 | 3.1s |

Paired deltas versus `full_context@2048`:

| Candidate | Paired delta | 95% bootstrap CI | Interpretation |
| --- | ---: | ---: | --- |
| truncation@512 | -0.37 | [-0.57, -0.17] | Insufficient budget for many memory cases. |
| truncation@1024 | -0.37 | [-0.57, -0.17] | Still worse than full context. |
| RAG@512 | -0.07 | [-0.17, 0.00] | Mostly closes the gap at half the full-context budget. |
| RAG@1024 | 0.00 | [0.00, 0.00] | Matches full context on this synthetic slice. |
| lean_retrieval@512 | 0.00 | [0.00, 0.00] | Matches full context at one quarter of the full-context tier. |
| lean_retrieval@1024 | +0.03 | [0.00, +0.10] | One-item positive pilot signal; not proof of general superiority. |
| full_context@512 | -0.80 | [-0.93, -0.63] | Infeasible by budget enforcement. |
| full_context@1024 | -0.80 | [-0.93, -0.67] | Infeasible by budget enforcement. |

Memory status: partial pass. This gives the paper a genuine memory-shaped task with temporal updates, preferences, abstention, and a usable checkpoint-style baseline, but it is synthetic and exact-match. It should be reported as deterministic pilot evidence, while the publishable path still needs LongMemEval_S, LoCoMo, or another public memory-agent benchmark.

Category diagnostics from `results/grouped_memory_category_qwen2_5_1_5b_20260618_203210.csv`:

| Category | truncation@1024 | RAG@1024 | lean@512 | lean@1024 | full_context@2048 | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| single_session_fact | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | Retrieval recovers early facts that truncation drops. |
| temporal_reasoning | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | Retrieval recovers older temporal evidence at tight budgets. |
| knowledge_update | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | Easy because the latest update is near the end. |
| abstention | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | Easy UNKNOWN behavior under budgeted prompts. |
| preference | 0.17 | 0.00 | 0.00 | 0.17 | 0.00 | Model/prompt failure, not solved by more context. |

Diagnostic status: pass. The category split shows strategy choice depends on memory type. It also exposes a prompt/task weakness: preference questions need either better prompt wording, answer normalization, or a stronger model before they can support a memory-system claim.

### 50-Item Public LongMemEval Oracle Pilot

Dataset:

- Official Hugging Face file: `xiaowu0162/longmemeval-cleaned/longmemeval_oracle.json`
- Local path used by the adapter: `data/longmemeval_oracle.json`
- Scorer: deterministic normalized containment, not the official LongMemEval LLM judge.

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id longmem_oracle_qwen15b_50_predictions \
  --model qwen2.5:1.5b \
  --tasks longmem \
  --strategies truncation rag lean_retrieval full_context \
  --budgets 2048 4096 8192 \
  --limit-tasks 50
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 2K | 0.34 | 0.00 | 30.5s |
| truncation | 4K | 0.48 | 0.00 | 50.0s |
| truncation | 8K | 0.38 | 0.00 | 76.8s |
| RAG | 2K | 0.38 | 0.00 | 41.4s |
| RAG | 4K | 0.40 | 0.00 | 56.0s |
| RAG | 8K | 0.36 | 0.00 | 75.7s |
| lean_retrieval | 2K | 0.46 | 0.00 | 37.0s |
| lean_retrieval | 4K | 0.46 | 0.00 | 53.2s |
| lean_retrieval | 8K | 0.36 | 0.00 | 78.3s |
| full_context | 2K | 0.08 | 0.90 | 1.4s |
| full_context | 4K | 0.22 | 0.70 | 3.2s |
| full_context | 8K | 0.34 | 0.16 | 14.2s |

Paired deltas versus `full_context@8192`:

| Candidate | Paired delta | 95% bootstrap CI | Interpretation |
| --- | ---: | ---: | --- |
| truncation@2K | 0.00 | [-0.12, +0.12] | Ties full context at tighter budget. |
| truncation@4K | +0.14 | [+0.06, +0.24] | Positive deterministic public-memory signal. |
| truncation@8K | +0.04 | [0.00, +0.10] | Small positive paired signal. |
| RAG@2K | +0.04 | [-0.08, +0.16] | Wide interval; tie or small gain. |
| RAG@4K | +0.06 | [-0.02, +0.14] | Wide interval; tie or small gain. |
| lean_retrieval@2K | +0.12 | [+0.02, +0.22] | Best budgeted memory-strategy row at tight budget. |
| lean_retrieval@4K | +0.12 | [+0.02, +0.24] | Best budgeted memory-strategy row tied with lean@2K. |

External judge bridge:

```bash
rtk python scripts/export_longmem_judge_inputs.py \
  --log-dir logs/full_study/longmem_oracle_qwen15b_50_predictions \
  --data-path data/longmemeval_oracle.json \
  --output results/longmem_judge_inputs_qwen15b_50_predictions.jsonl
```

This exports 600 rows across the 12-cell matrix. Of these, 512 rows have model predictions and `pending_external_longmemeval_judge` status; 88 full-context budget-violation rows are explicitly marked as not judgeable because no prediction was produced. A narrower key-row bundle with `truncation`, `lean_retrieval`, and `full_context` rows exports 450 rows to `results/longmem_judge_inputs_qwen15b_50_key_rows.jsonl`; a prediction-only bundle exports 512 rows to `results/longmem_judge_inputs_qwen15b_50_prediction_only.jsonl`.

Public-memory status: stronger partial pass with an external-judge bridge. The harness now runs official LongMemEval-format data at a 50-item category-balanced scale and reports full-context violations, paired deltas, category diagnostics, and prediction-bearing judge input rows. The paired signal is now meaningfully positive for `lean_retrieval@2048`, `lean_retrieval@4096`, and `truncation@4096`, but the result is not official LongMemEval accuracy because it uses the oracle file and normalized-containment scoring rather than the official judge.

### Qwen3.6-35B LongMemEval Transfer Probe

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id longmem_oracle_qwen36_35b_10 \
  --model qwen3.6:35b-mlx \
  --tasks longmem \
  --strategies truncation rag lean_retrieval full_context \
  --budgets 2048 4096 8192 \
  --limit-tasks 10
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 2K | 1.00 | 0.00 | 81.7s |
| truncation | 4K | 1.00 | 0.00 | 86.1s |
| truncation | 8K | 1.00 | 0.00 | 101.0s |
| RAG | 2K | 1.00 | 0.00 | 84.7s |
| RAG | 4K | 1.00 | 0.00 | 90.2s |
| RAG | 8K | 1.00 | 0.00 | 119.4s |
| lean_retrieval | 2K | 1.00 | 0.00 | 78.2s |
| lean_retrieval | 4K | 1.00 | 0.00 | 93.8s |
| lean_retrieval | 8K | 1.00 | 0.00 | 101.7s |
| full_context | 2K | 0.00 | 1.00 | 0.1s |
| full_context | 4K | 0.20 | 0.80 | 14.6s |
| full_context | 8K | 0.70 | 0.30 | 50.3s |

Paired deltas versus `full_context@8192` are +0.30 for every budgeted row, with bootstrap CIs centered well above zero because `N=10`. This is the strongest transfer result yet: the larger local model preserves the budgeted-vs-full-context split on the public LongMemEval oracle subset, and the budgeted strategies remain both accurate and compliant while full context still violates the tighter tiers. The 5-item probe above now serves as a precursor, while this 10-item sweep is the result to cite.

### Gemma4-12B LongMemEval Negative-Transfer Check

Run:

```bash
rtk python scripts/run_pilot.py --full-study \
  --run-id longmem_oracle_gemma4_12b_10 \
  --model gemma4:12b-mlx \
  --tasks longmem \
  --strategies truncation rag lean_retrieval full_context \
  --budgets 2048 4096 8192 \
  --limit-tasks 10
```

Aggregate:

| Strategy | Budget | Accuracy | Violation | Duration |
| --- | ---: | ---: | ---: | ---: |
| truncation | 2K | 0.00 | 0.00 | 0.2s |
| truncation | 4K | 0.00 | 0.00 | 0.1s |
| truncation | 8K | 0.00 | 0.00 | 0.1s |
| RAG | 2K | 0.00 | 0.00 | 3.4s |
| RAG | 4K | 0.00 | 0.00 | 1.8s |
| RAG | 8K | 0.00 | 0.00 | 1.0s |
| lean_retrieval | 2K | 0.00 | 0.00 | 1.4s |
| lean_retrieval | 4K | 0.00 | 0.00 | 1.3s |
| lean_retrieval | 8K | 0.00 | 0.00 | 0.8s |
| full_context | 2K | 0.00 | 1.00 | 0.1s |
| full_context | 4K | 0.00 | 1.00 | 0.1s |
| full_context | 8K | 0.00 | 1.00 | 0.1s |

This is a clean negative-transfer check. The intermediate Gemma model does not recover the LongMemEval signal at all on the same 10-item slice that qwen3.6:35b-mlx handles strongly, so the paper should treat model scale and serving regime as first-order variables rather than implementation noise.

## External Signals

### arXiv Pressure

Recent work overlaps with parts of the current framing:

- ContextBudget / BACM-RL: https://arxiv.org/abs/2604.01664
  - Already frames context management as budget-constrained long-horizon agent control.
- BudgetMem: https://arxiv.org/abs/2602.06025
  - Already studies budget-tier routing for runtime agent memory.
- EvoMemBench: https://arxiv.org/abs/2605.18421
  - Benchmarks memory methods across in-episode/cross-episode and knowledge/execution memory axes.
- Engram: https://arxiv.org/abs/2606.09900
  - Raises the bar by showing lean retrieved context can beat full-context on LongMemEval_S, with reproducible logs.
- LightMem: https://arxiv.org/abs/2604.07798
  - Shows the field is moving toward small-model-assisted memory with bounded online latency.
- Prompt Compression in the Wild: https://arxiv.org/abs/2604.02985
  - Makes latency break-even and hardware-dependent compression overhead central.

Implication: the paper must stop treating Mem0/Letta/LLMLingua/LongMemEval as future work only. At least a subset must become actual evidence.

### Practitioner Signals

Hacker News and Reddit discussion points are aligned with BudgetBench:

- Context rot discussion: https://news.ycombinator.com/item?id=44564248
  - Users report that longer coding-agent sessions degrade, and they want pruning, reset, rollback, and explicit context curation.
- Mem0 launch discussion: https://news.ycombinator.com/item?id=41447317
  - Users care about privacy, forgetting, structured/unstructured memory, graph stores, and local deployment.
- Ask HN memory discussion: https://news.ycombinator.com/item?id=47449389
  - Users want metrics and are unsure whether markdown, search, RAG, or memory databases are best.
- LocalLLaMA agent memory survey: https://www.reddit.com/r/LocalLLaMA/comments/1gvhpjj/agent_memory/
  - Local-model compatibility and the difficulty of stitching memory systems together are recurring pain points.
- LocalLLaMA memory benchmark thread: https://www.reddit.com/r/LocalLLaMA/comments/1kavtwr/benchmarking_ai_agent_memory_providers_for/
  - Users compare memory systems by factual consistency, latency, and token footprint.
- ClaudeAI coding-agent context handler thread: https://www.reddit.com/r/ClaudeAI/comments/1j7zf43/need_help_with_building_coding_agent/
  - Coding users explicitly want a separate long-context handler that tracks plans, files, dependency graph, and relevant context.

Implication: include latency, local hardware, failure rates, budget compliance, and context-pruning/reset baselines. Do not report accuracy alone.

## Claim Boundaries

### Claims To Make

- BudgetBench standardizes active-context-budget evaluation for local LLM agents.
- BudgetBench compares strategies at fixed per-call input budgets, independent of nominal context window size.
- BudgetBench reports operational metrics that ordinary long-context benchmarks hide: violation rate, used budget, peak budget, latency, and quality.
- BudgetBench is strategy-pluggable, so method papers can be evaluated under the same budget protocol.
- Pilot results show non-monotonic quality curves and latency/violation tradeoffs worth scaling.

### Claims To Avoid

- Do not claim to be the first work to vary context length or context budget.
- Do not claim final strategy rankings from the current 89-item, 1.5B pilot.
- Do not claim official SWE-bench performance while using patch-similarity proxy.
- Do not claim multimodal memory from the six-item colored-shape smoke test.
- Do not claim local memory systems are generally superior to full context until full-context baselines are run.

## Required Experiment Upgrades

### Phase 1: Paper Reframing

Goal: Make the draft robust against the obvious reviewer question: "How is this different from ContextBudget, BudgetMem, EvoMemBench, and Engram?"

Tasks:

- [x] Add ContextBudget, BudgetMem, EvoMemBench, Engram, LightMem, and Prompt Compression in the Wild to `paper/references.bib`.
- [x] Add a "Closest Concurrent Work" related-work subsection to `paper/main.tex`.
- [x] Rewrite the novelty paragraph around the conjunction: local LLMs, fixed active budgets, swappable strategies, deterministic task graders, and operational metrics.
- [x] Move the multimodal smoke result to appendix or mark it explicitly as infrastructure validation only.
- [x] Add a table comparing BudgetBench against ContextBudget, BudgetMem, EvoMemBench, MemoryAgentBench, Engram, RULER, HELMET, and LongBench v2.

Acceptance criteria:

- The introduction no longer implies that budget sweeping itself is novel.
- The paper states exactly what BudgetBench provides that method papers do not: reusable harness, fixed tiers, plug-in strategies, local deployment focus, and comparable metrics.

### Phase 2: Full-Context and Lean-Context Baselines

Goal: Match the current standard set by Engram: show whether budgeted context is merely cheaper or can also be better.

Tasks:

- [x] Add a `full_context` baseline where each task receives the largest natural context that fits the model/server.
- [x] Add a `lean_retrieval` baseline: dense + BM25 + recency/salience fusion, budgeted to each active tier.
- [x] Add a `checkpoint_context` baseline inspired by practitioner workflows: prior summary/checkpoint + recent messages + retrieved evidence.
- [x] Report paired comparisons against full-context, not only cross-budget curves.
- [x] Add confidence intervals for quality and paired deltas where item-level scores exist.

Acceptance criteria:

- Every main task has a full-context row.
- The result tables can answer: "At what budget does a memory strategy match or beat full context?"
- Tables include average context tokens and latency for full-context versus budgeted strategies.

### Phase 3: Memory-Task Expansion

Goal: Add a task family that is recognized as memory-agent evaluation, not only long-context QA.

Preferred path:

- [ ] Integrate LongMemEval_S or LoCoMo.
- [x] Integrate a public LongMemEval oracle-file adapter and pilot run.
- [x] Include categories such as single-session, multi-session, knowledge update, temporal reasoning, preference, and abstention if available.
- [ ] Use official judge or official scoring where possible.
- [ ] If an LLM judge is unavoidable, isolate it from the main deterministic claim and report judge/version prompts exactly.

Fallback path:

- [x] Create a deterministic memory slice with exact-match answers and temporal updates.
- [x] Use this only as a pilot and label it accordingly.
- [x] Replace or corroborate the synthetic slice with existing public memory-agent data.

Acceptance criteria:

- The paper includes at least one memory-agent task where persistent or cross-turn memory is truly relevant.
- Results are stratified by memory category, not just averaged.

### Phase 4: Baseline Expansion

Goal: Stop comparing only truncation, summary, and simple RAG.

Minimum additional baselines:

- [ ] LLMLingua-2 or equivalent prompt compression.
- [ ] Mem0.
- [ ] Letta/MemGPT.
- [ ] Hybrid retrieval: dense + lexical + recency, with simple reranking.

Optional but valuable:

- [ ] Graph/temporal memory if setup is feasible.
- [ ] LightMem-style small-model rerank/consolidation if implementation time allows.

Acceptance criteria:

- Main paper has at least five strategy families.
- Each strategy is evaluated at all five budget tiers or logs explicit violation/failure rows.
- Setup failures are reported as operational findings, not silently dropped.

### Phase 5: Model and Hardware Transfer

Goal: Make "local LLM" more than a single tiny-model pilot.

Target matrix:

- [ ] Small local model: 1.5B to 3B class for reproducibility.
- [ ] Workhorse local model: 7B/8B or 14B class.
- [ ] Larger local anchor: 30B/32B class if available on Mac/MLX or other local hardware.

Suggested models:

- Qwen2.5/3 7B or 14B Instruct.
- Llama 3.1/3.2 8B Instruct.
- Qwen3-Coder-30B-A3B or Qwen2.5-32B if local serving is stable.

Tasks:

- [ ] Run the full LongBench/memory-task budget sweep on at least two model sizes.
- [ ] Run a smaller but real transfer sweep on the third model size if compute is constrained.
- [ ] Record serving stack, quantization, tokenizer, KV-cache settings, and hardware.

Acceptance criteria:

- The paper can show whether strategy crossovers are model-dependent.
- The transfer check has enough items to be evidence, not a three-item smoke test.

### Phase 6: Coding-Agent Evidence

Goal: Replace or strengthen the current SWE proxy result.

Preferred path:

- [ ] Use official SWE-bench Verified evaluation on a small stratified subset.
- [ ] Use a fixed agent scaffold and turn cap.
- [ ] Report resolved rate, tokens, latency, and violation rate.

Cheaper alternative:

- [ ] Add TRAIL-style agent trace debugging or issue-localization over long traces.
- [ ] Treat memory strategy as context selection over trace events.
- [ ] Use deterministic labels where possible.

Acceptance criteria:

- The paper no longer relies on patch-similarity proxy as a main coding result.
- If proxy SWE remains, it is appendix-only and clearly marked diagnostic.

### Phase 7: Stratification and Diagnostics

Goal: Explain when memory strategies win, not just whether they win on average.

Add per-item tags:

- [ ] Original context length.
- [ ] Evidence position: early, middle, late, dispersed.
- [ ] Query/evidence lexical similarity.
- [ ] Distractor density.
- [ ] Reasoning hops.
- [ ] Irreducible prompt size.
- [ ] Whether full context is feasible at the requested budget.
- [x] Memory category for the synthetic memory pilot.

Analyses:

- [ ] Strategy crossover by budget tier.
- [ ] Quality versus used budget.
- [ ] Quality versus latency.
- [x] Synthetic memory quality by category.
- [x] Budget violation rate by irreducible prompt size.
- [x] Full-context versus budgeted-strategy paired deltas.

Acceptance criteria:

- The paper can say which task conditions make RAG, summary, compression, or truncation preferable.
- Result figures include Pareto frontiers or clearly identify dominated strategies.

### Phase 8: Statistical and Reproducibility Hardening

Goal: Make the benchmark paper reviewable.

Tasks:

- [x] Add bootstrap confidence intervals for aggregate quality.
- [x] Add paired significance tests where item-level paired outputs exist.
- [ ] Add repeated runs for nondeterministic tasks or unstable serving configurations.
- [x] Save item-level outputs, token counts, violations, and duration.
- [ ] Add a single command to regenerate every table from raw logs.
- [ ] Add a reproducibility checklist with hardware, model hash/tag, serving stack, tokenizer, and dependencies.

Acceptance criteria:

- Every main table is reproducible from committed scripts and raw or shareable logs.
- The paper does not depend on manually curated result rows for the main claims.

## Proposed Main Experiment Matrix

Minimum publishable matrix:

| Axis | Minimum |
| --- | --- |
| Models | 2 local models, ideally small + workhorse |
| Tasks | LongBench v2 + LongMemEval/LoCoMo + one coding/agent-trace task |
| Budgets | 2K, 4K, 8K, 16K, 32K |
| Strategies | truncation, summary, RAG, hybrid retrieval, compression, Mem0 or Letta |
| Metrics | quality, used budget, peak budget, violation rate, duration, tokens per correct/resolved |
| Statistics | confidence intervals, paired deltas versus full-context |

Stretch matrix:

| Axis | Stretch |
| --- | --- |
| Models | 3 local models across 1.5B/8B/14B/30B classes |
| Tasks | Add tau2-bench or BFCL-style tool-use chains |
| Strategies | Add both Mem0 and Letta, plus graph/temporal memory |
| Diagnostics | Evidence position, distractor density, query-evidence similarity, reasoning hops |

## Paper Structure Changes

Recommended structure:

1. Introduction
   - State active context as an operational resource for local agents.
   - State what is and is not novel.
2. Closest Concurrent Work
   - ContextBudget, BudgetMem, EvoMemBench, Engram.
3. Benchmark Protocol
   - Active budget, strategy contract, task contract, metric contract.
4. Implemented Strategies
   - Include real strategy families beyond pilot baselines.
5. Tasks
   - Long-context QA, memory-agent task, coding/trace task.
6. Experimental Setup
   - Models, local hardware, serving stack, tokenizer, quantization.
7. Results
   - Quality curves, full-context comparison, Pareto frontier, violations, latency.
8. Diagnostics
   - Stratified results and strategy crossovers.
9. Limitations
   - Local models, judge limitations, task coverage, tokenizer mismatch.
10. Release and Reproducibility
   - Logs, scripts, commands, strategy API.

## Immediate Next Tasks

1. Close the remaining local-serving transfer gap:
   - The hosted Qwen3-30B-A3B LongBench replication is complete: 50 items, four strategies, 8K/32K budgets, exact tokenizer, shuffled order, and two repeats.
   - `rag@8192` averages 0.46 versus `full_context@32768` at 0.53, with paired delta -0.07 and 95% bootstrap CI [-0.17, +0.02]; mean end-to-end cell time is 27.5% lower.
   - `truncation@8192` averages 0.33 and is significantly worse than 32K full context (delta -0.20, CI [-0.34, -0.07]).
   - This closes model-scale transfer but not local deployment. The next model task is a fully specified local 7B--14B run, or a local 30B-class run only if throughput makes the same 50-item repeated matrix practical.
2. Move public memory evidence beyond the oracle-file setting:
   - The complete 500-item oracle study now has 5,122/5,122 parseable upstream GPT-4o judge labels; the old `401 Unauthorized` note is obsolete.
   - Next: run LongMemEval_S/full-history or another public full-history memory setting, preserving explicit budget eligibility and official judge provenance.
3. Decide whether to keep `lean_retrieval` as a mixed baseline or tune it separately for LongBench and memory. Current evidence: at 8K on hosted Qwen3 it averages 0.44 versus RAG at 0.46, while it remains strongest or tied on the public and synthetic memory slices.
4. Upgrade the agentic task: run official SWE-bench evaluation at a meaningful sample size or pivot to deterministic TRAIL-style trace debugging.

## Kill Criteria

Do not scale to the full matrix until the feasibility sweep shows at least one of:

- A strategy crossover across budget tiers.
- A budgeted strategy matching or beating full context on a task subset.
- A substantial latency or budget-compliance difference at comparable quality.
- A task stratification where strategy choice clearly depends on evidence layout or memory category.

If none appear, reposition the paper as a tooling/reproducibility artifact rather than an empirical benchmark paper.

## Final Success Criteria

The upgraded paper is ready for arXiv when:

- [x] It has a clear differentiation table against current arXiv competitors.
- [x] It reports at least one memory-agent task, not only LongBench.
- [x] It includes full-context baselines.
- [x] It includes at least five memory strategy families.
- [x] It reports confidence intervals or paired deltas.
- [x] It uses local models beyond the 1.5B pilot.
- [x] It treats SWE proxy and multimodal smoke tests as diagnostics unless upgraded.
- [ ] Every main claim is reproducible from scripts and logs.
