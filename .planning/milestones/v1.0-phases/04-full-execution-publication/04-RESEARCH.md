# Phase 4: Full Execution & Publication - Research

**Researched:** 2026-05-07
**Domain:** Benchmark sweep execution, results aggregation, matplotlib visualization, NeurIPS LaTeX paper scaffold
**Confidence:** HIGH (codebase verified), MEDIUM (NeurIPS 2026 requirements from live docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Execution Infrastructure**
- LLM backend: Ollama (already proven in pilot, easy model swaps via --model flag)
- Budget tiers: All 5 — 2K / 4K / 8K / 16K / 32K (ROADMAP standard, publication-required)
- Model priority: Qwen2.5-14B first; Qwen2.5-32B and Qwen3-Coder-30B-A3B if hardware allows
- Runner: Extend run_pilot.py with --full-study flag (all 5 tiers, all 6 strategies, standard item counts)

**RAG Fix for LongBench**
- Fix location: task wrapper — LongBenchV2Task.format_message() pre-chunks context into multiple messages so RAGStrategy.__call__() can retrieve from conversation history as intended
- Chunk size: min(budget/4, 512) tokens per chunk (adaptive to budget tier)
- RAGStrategy unchanged — no modifications to rag.py
- Edge case: if context fits within single chunk, pass as-is (avoids unnecessary chunking overhead)

**Results & Visualization**
- Output format: matplotlib PNG plots (static, paper-ready)
- Figure layout: Separate panels per task (SWE-bench + LongBench) combined in one multi-panel figure
- Metrics to plot: accuracy vs budget AND violation_rate vs budget (two subplot rows)
- Output location: results/ for aggregated data, results/figures/ for generated plots

**arXiv Preprint**
- LaTeX template: NeurIPS 2026 (target venue: NeurIPS D&B track)
- Paper scope: Full scaffold with all sections — intro, related work, method, experiments, results, conclusion + appendix
- Location: paper/ subdirectory at repo root
- Preliminary results: Include Phase 3 pilot data in experiments section as harness validation baseline

### Claude's Discretion

(No discretion areas defined in CONTEXT.md — all decisions locked above.)

### Deferred Ideas (OUT OF SCOPE)

- τ²-bench full sweep (integration wired in Phase 3; requires tau2-bench install to enable — Phase 4 if feasible)
- EVAL-04: Continuous λ-weighted Pareto frontier (v2 stretch goal)
- LEAD-01: Public leaderboard with strategy submissions (v2)
- Interactive HTML visualization (plotly) — static matplotlib sufficient for paper
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | System outputs a comprehensive summary of tradeoff curves for arXiv preprint | NeurIPS 2026 D&B track requirements documented; paper structure mapped; matplotlib figures planned |
| EVAL-02 | Execute full sweep on Qwen2.5-14B across all three tasks at 5 budget tiers | Model confirmed available in Ollama (`qwen2.5:14b`); duration estimates computed; runner extension pattern documented |
| EVAL-03 | Execute full sweep on Qwen2.5-32B and Qwen3-Coder-30B-A3B (MoE) | Both models confirmed in Ollama (`qwen2.5:32b`, `qwen3-coder:30b`); same runner path as EVAL-02 |
</phase_requirements>

---

## Summary

Phase 4 has four concrete deliverables: (1) fix the RAG+LongBench violation gap identified in Phase 3, (2) execute the full parameter sweep, (3) aggregate results into tradeoff curves, and (4) write the arXiv paper. All foundational code is in place and verified — the pilot run proves the runner, logger, and strategy dispatch work end-to-end.

The most critical pre-execution action is the LongBench chunking fix in `LongBenchV2Task.format_message()`. The root cause is confirmed: the raw context is passed as a single user message up to 464K tokens; RAGStrategy indexes messages[1:-1] and correctly retrieves from them, but there is only one message to index (the full context blob). Chunking it into multiple messages of `min(budget//4, 512)` tokens each gives RAGStrategy a retrievable corpus per the formula chosen.

The sweep itself will take approximately 16-17 hours per model on Qwen2.5-14B running on the Mac (Apple Silicon Ollama). With three models, budget for 40-50 hours of unattended compute. A checkpoint/resume mechanism (skip already-written summary.jsonl combinations) is critical for this length of run. Qwen2.5-14B (`qwen2.5:14b`, 9.0 GB) and Qwen2.5-32B (`qwen2.5:32b`, 19 GB) and Qwen3-Coder-30B-A3B (`qwen3-coder:30b`, 18 GB) are all confirmed present in Ollama already.

**Primary recommendation:** Start with the RAG fix (one function change), do a 3-item smoke test, then launch the full Qwen2.5-14B sweep with resume support. Run EVAL-03 (larger models) only after EVAL-02 data is confirmed valid.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LongBench context chunking | Task wrapper (long.py) | — | Strategy is unchanged; chunking is pre-processing in format_message() |
| Budget enforcement | Harness (harness.py) | Core (budget.py) | Existing enforce_budget() wraps every LLM call; no change needed |
| Full sweep orchestration | Script (run_pilot.py extended) | — | All sweep logic lives in the runner script; evaluation infra unchanged |
| JSONL metrics logging | MetricsLogger + JSONLMetricsLogger | — | Existing pattern; summary.jsonl per run, per-combination JSONL per file |
| Results aggregation | Analysis script (new) | pandas DataFrame | Read summary.jsonl files; pivot to wide table by strategy × budget |
| Tradeoff curve generation | Visualization script (new) | matplotlib | Two subplot rows (accuracy, violation_rate); one PNG per task set |
| Paper scaffold | LaTeX (paper/ dir) | — | Standalone; no code dependency; NeurIPS 2026 eandd template |

---

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | 3.10.9 | Tradeoff curve PNG generation | Already installed; `pip show matplotlib` confirmed [VERIFIED: pip registry] |
| pandas | 2.3.0 | JSONL aggregation, DataFrame pivot | Already installed; industry standard for tabular data [VERIFIED: pip registry] |
| numpy | 2.4.4 | Array math for curve smoothing | Already installed as transitive dep [VERIFIED: pip registry] |
| tiktoken | 0.12.0 | Token counting for chunk size formula | Already used in RAGStrategy [VERIFIED: pip registry] |
| pytest | 9.0.3 | Test suite (38 tests currently green) | Already installed; all tests pass [VERIFIED: `python -m pytest tests/ -v`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| seaborn | not installed | Publication-quality style | Optional; matplotlib rcParams with `seaborn-v0_8-paper` style achieves same result without extra dep |
| scipy | not installed | Curve fitting / confidence intervals | Optional; only needed if adding error bars to curves |

### Model Tags (Ollama — all confirmed present)

| Model | Ollama Tag | Size | Use |
|-------|------------|------|-----|
| Qwen2.5-14B | `qwen2.5:14b` | 9.0 GB | EVAL-02 primary model |
| Qwen2.5-32B | `qwen2.5:32b` | 19 GB | EVAL-03 first variant |
| Qwen3-Coder-30B-A3B | `qwen3-coder:30b` | 18 GB | EVAL-03 second variant |

[VERIFIED: `ollama list` output — all three models present, confirmed 2026-05-07]

### Installation (nothing new required for execution)

```bash
# Verify all deps present before sweep
python -m pytest tests/ -v  # 38 tests should pass
```

---

## Architecture Patterns

### System Architecture Diagram

```
LongBench Dataset (HuggingFace)
        |
        v
LongBenchV2Task.format_message()  <-- CHANGE HERE: chunk context into N messages
        |
        v
[system_msg, chunk_1, chunk_2, ..., chunk_N, question_msg]
        |
        v
RAGStrategy.__call__(messages, budget)  <-- UNCHANGED: indexes messages[1:-1]
        | indexes chunks, retrieves top-K by relevance
        v
enforce_budget() --> llm_client(Ollama) --> grade() --> MetricsLogger (JSONL)
        |
        v
summary.jsonl (per run) + {task}_{strategy}_{budget}.jsonl (per combination)
        |
        v
scripts/analyze_results.py (new)
        | pandas.read_json(lines=True), pivot by strategy x budget
        v
results/full_study_{timestamp}.csv
        |
        v
scripts/plot_tradeoffs.py (new)
        | matplotlib 2x2 panel figure
        v
results/figures/tradeoff_curves_{timestamp}.png
        |
        v
paper/ (LaTeX scaffold)
        | \includegraphics{tradeoff_curves}
        v
arXiv preprint
```

### Recommended Project Structure (additions)

```
budgetbench/
├── scripts/
│   ├── run_pilot.py          # EXTEND: add --full-study flag
│   ├── analyze_results.py    # NEW: JSONL → aggregated CSV
│   └── plot_tradeoffs.py     # NEW: CSV → PNG figures
├── results/
│   ├── full_study_YYYYMMDD_HHMMSS.csv    # aggregated
│   └── figures/
│       └── tradeoff_curves_YYYYMMDD.png
├── paper/
│   ├── main.tex              # NeurIPS 2026 scaffold
│   ├── neurips_2026.sty      # downloaded from NeurIPS
│   └── figures/              # symlink or copy from results/figures/
└── src/budgetbench/
    └── tasks/long.py         # CHANGE: format_message() chunking
```

---

## Pattern 1: RAG Fix — LongBench Chunking in format_message()

**What:** Pre-chunk the raw LongBench context string into multiple OpenAI messages before returning from format_message(). RAGStrategy treats messages[1:-1] as the indexable episodic history. By splitting context into N messages of chunk_size tokens each, we give RAGStrategy a proper corpus to retrieve from.

**Chunk size formula:** `chunk_size = min(budget // 4, 512)` — locks at 512 for budgets >= 2K, which is already within budget for all 5 tiers. At 2K: chunk=512, fits ~3 chunks in remaining budget after system+question overhead. At 32K: chunk=512, fits ~63 chunks.

**Edge case:** If the total context token count is less than chunk_size, return the context as a single message (no chunking overhead).

**Implementation:**

```python
# Source: verified against rag.py logic (messages[1:-1] is the indexed window)
# In src/budgetbench/tasks/long.py — LongBenchV2Task.format_message()

def format_message(self, item: Dict[str, Any], budget: int = 8192) -> List[OpenAIMessage]:
    context = item.get("context", "")
    question = item.get("question", "")

    choices_text = ""
    for char in ['A', 'B', 'C', 'D']:
        val = item.get(f"choice_{char}")
        if val:
            choices_text += f"\n{char}: {val}"

    system_prompt = (
        "You are a helpful assistant. Answer the following multiple choice question "
        "based on the provided context. Respond only with the letter of the correct answer (A, B, C, or D)."
    )
    question_msg: OpenAIMessage = {
        "role": "user",
        "content": f"Question: {question}{choices_text}"
    }

    # Chunk context into retrievable messages
    chunk_size = min(budget // 4, 512)  # tokens, not chars
    # Approximate chars: 4 chars/token heuristic (matches existing fallback in run_pilot.py)
    chunk_chars = chunk_size * 4

    if len(context) <= chunk_chars:
        # Small context — single message, no overhead
        context_messages: List[OpenAIMessage] = [{"role": "user", "content": f"Context:\n{context}"}]
    else:
        # Split into chunks of ~chunk_chars characters
        context_messages = []
        for i in range(0, len(context), chunk_chars):
            chunk_text = context[i : i + chunk_chars]
            context_messages.append({"role": "user", "content": f"Context part {i//chunk_chars + 1}:\n{chunk_text}"})

    system_msg: OpenAIMessage = {"role": "system", "content": system_prompt}
    return [system_msg] + context_messages + [question_msg]
```

**Caller change:** The `run()` method must pass `max_tokens` to `format_message()`:

```python
def run(self, item, strategy, llm_client, tokenizer_fn, max_tokens, logger):
    messages = self.format_message(item, budget=max_tokens)  # pass budget
    ...
```

**Backward compatibility:** The `budget` parameter defaults to 8192, so existing tests that call `format_message(item)` without a budget argument continue to work without modification.

---

## Pattern 2: Full Study Runner — Extending run_pilot.py

**What:** Add `--full-study` flag that sets budget tiers to all 5 [2048, 4096, 8192, 16384, 32768], item counts to 20 SWE / 50 LongBench, and enables checkpoint/resume.

**Checkpoint/resume pattern:** Before starting each (task, strategy, budget) combination, check if `summary.jsonl` already has a row with matching keys. If found, skip. This allows a multi-hour run to survive interruptions.

```python
# Source: [ASSUMED] — standard pattern for long ML sweeps; no library needed
FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]

def load_completed_combinations(summary_file: str) -> set:
    """Returns set of (task, strategy, budget) tuples already in summary.jsonl."""
    completed = set()
    if not os.path.exists(summary_file):
        return completed
    with open(summary_file) as f:
        for line in f:
            try:
                row = json.loads(line)
                completed.add((row["task"], row["strategy"], row["budget"]))
            except (json.JSONDecodeError, KeyError):
                pass
    return completed

# In the inner loop:
completed = load_completed_combinations(summary_file)
for task_cfg in tasks_config:
    for strategy_name, strategy in selected_strategies.items():
        for budget in budgets:
            key = (task_name, strategy_name, budget)
            if key in completed:
                print(f"  > [SKIP] {task_name} | {strategy_name} | {budget} — already done")
                continue
            # ... run as before
```

**--full-study flag behavior:**
- Sets `budgets = FULL_STUDY_BUDGET_TIERS` (overrides --limit-budgets)
- Sets default item limits to 20/50 (unchanged from current defaults)
- Enables resume mode (always on for full study)
- Logs to `logs/full_study/{timestamp}/` instead of `logs/pilot/{timestamp}/`

**Per-model runs:** Add `--model` flag (already exists) — caller passes `--model qwen2.5:14b`, `--model qwen2.5:32b`, `--model qwen3-coder:30b`. The summary.jsonl should also record the model name for multi-model aggregation:

```python
summary = {
    "timestamp": timestamp,
    "model": args.model or "unknown",  # ADD: record model
    "task": task_name,
    "strategy": strategy_name,
    "budget": budget,
    "accuracy": accuracy,
    "total": total_count,
    "success": success_count,
    "duration_sec": duration,
}
```

---

## Pattern 3: Results Aggregation Script

**What:** `scripts/analyze_results.py` reads one or more summary.jsonl files (across runs/models), loads into a pandas DataFrame, and writes a unified CSV.

**Input schema** (verified from pilot logs):

```jsonl
{"timestamp":"20260429_004124","task":"swe","strategy":"truncation","budget":2048,"accuracy":0.0,"total":3,"success":0,"duration_sec":34.5}
```

**New schema** (with model field added in runner):

```jsonl
{"timestamp":"...","model":"qwen2.5:14b","task":"swe","strategy":"truncation","budget":2048,"accuracy":0.0,...}
```

**Aggregation pattern:**

```python
# Source: [ASSUMED] standard pandas pattern
import pandas as pd, glob, json

def load_summary_files(log_dirs: list[str]) -> pd.DataFrame:
    rows = []
    for log_dir in log_dirs:
        summary_path = os.path.join(log_dir, "summary.jsonl")
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                for line in f:
                    rows.append(json.loads(line))
    return pd.DataFrame(rows)

# Pivot for per-strategy tradeoff table
def make_tradeoff_table(df: pd.DataFrame, task: str, model: str) -> pd.DataFrame:
    sub = df[(df["task"] == task) & (df["model"] == model)]
    pivot = sub.pivot_table(index="strategy", columns="budget", values="accuracy")
    return pivot
```

**Output:** `results/full_study_{model}_{timestamp}.csv` with columns: model, task, strategy, budget, accuracy, violation_rate (derived from per-combination JSONL), duration_sec.

---

## Pattern 4: Tradeoff Curve Generation

**What:** `scripts/plot_tradeoffs.py` reads the aggregated CSV and generates a multi-panel figure.

**Figure layout:** 2 rows × 2 columns:
- Row 1: accuracy vs budget (SWE left, LongBench right)
- Row 2: violation_rate vs budget (SWE left, LongBench right)
- x-axis: log2 scale (2K, 4K, 8K, 16K, 32K) with explicit tick labels
- y-axis: [0, 1] for accuracy; [0, 1] for violation_rate
- One line per strategy (6 lines), with distinct markers

**Paper-ready matplotlib pattern:**

```python
# Source: matplotlib 3.10.9 stable docs [CITED: matplotlib.org/stable]
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]
BUDGET_LABELS = ["2K", "4K", "8K", "16K", "32K"]
STRATEGY_COLORS = {
    "truncation": "tab:blue",
    "summary": "tab:orange",
    "rag": "tab:green",
    "mem0": "tab:red",
    "letta": "tab:purple",
    "llmlingua": "tab:brown",
}
STRATEGY_MARKERS = {
    "truncation": "o", "summary": "s", "rag": "^",
    "mem0": "D", "letta": "v", "llmlingua": "P"
}

def plot_tradeoff_curves(df: pd.DataFrame, model: str, out_path: str):
    plt.rcParams.update({
        "font.size": 10,
        "font.family": "serif",
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey="row")
    tasks = [("swe", "SWE-bench Verified"), ("long", "LongBench v2")]

    for col, (task_id, task_label) in enumerate(tasks):
        sub = df[(df["task"] == task_id) & (df["model"] == model)]
        for strategy in df["strategy"].unique():
            s_data = sub[sub["strategy"] == strategy].sort_values("budget")
            x = s_data["budget"].tolist()
            y_acc = s_data["accuracy"].tolist()
            y_viol = s_data["violation_rate"].tolist()
            axes[0][col].plot(x, y_acc, label=strategy,
                              color=STRATEGY_COLORS.get(strategy),
                              marker=STRATEGY_MARKERS.get(strategy))
            axes[1][col].plot(x, y_viol, label=strategy,
                              color=STRATEGY_COLORS.get(strategy),
                              marker=STRATEGY_MARKERS.get(strategy))

        for row in range(2):
            axes[row][col].set_xscale("log", base=2)
            axes[row][col].set_xticks(BUDGET_TIERS)
            axes[row][col].set_xticklabels(BUDGET_LABELS)
            axes[row][col].set_xlim(1500, 40000)

        axes[0][col].set_title(f"{task_label}\nAccuracy vs Budget")
        axes[0][col].set_ylabel("Accuracy")
        axes[1][col].set_title(f"{task_label}\nViolation Rate vs Budget")
        axes[1][col].set_ylabel("Violation Rate")
        axes[1][col].set_xlabel("Context Budget (tokens)")

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"BudgetBench Tradeoff Curves — {model}", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close()
```

---

## Pattern 5: NeurIPS 2026 D&B Track Paper Scaffold

**Template:** `\usepackage[eandd]{neurips_2026}` [CITED: neurips.cc/Conferences/2026/EvaluationsDatasetsFAQ]

**Page limit:** 9 content pages (main text + figures + tables). References, appendix, checklist are uncounted. Accepted papers get +1 page at camera-ready. [CITED: neurips.cc/Conferences/2026/MainTrackHandbook]

**Submission deadline:** May 6, 2026 (already passed — target arXiv preprint first, then next cycle or workshop).

**Required paper sections for a benchmark D&B paper:**

```latex
\section{Introduction}
% - Problem: local LLMs face hard context budget constraints
% - Gap: no standardized benchmark for strategy comparison
% - Contribution: BudgetBench — 5 tiers × 6 strategies × 2 tasks
% - Key finding: [teaser result from EVAL-02]

\section{Related Work}
% - Context compression: LLMLingua, AutoCompressor
% - Memory-augmented agents: MemGPT/Letta, Mem0
% - LLM benchmarks: SWE-bench, LongBench v2
% - Budget-constrained eval: ContextBudget/BACM-RL, BudgetMem (note: no standardized benchmark yet)

\section{BudgetBench Framework}
\subsection{Task Suite}
% SWE-bench, LongBench v2, τ²-bench (if enabled)
\subsection{Memory Strategy Interface}
% MemoryStrategy ABC, 6 baselines
\subsection{Budget Enforcement Protocol}
% enforce_budget(), raise-on-exceed, retry × 3

\section{Experiments}
\subsection{Pilot Results (Phase 3 — Harness Validation)}
% Table: 18 combinations, 3 items each, qwen2.5:1.5b — confirms harness correctness
\subsection{Full Study: Qwen2.5-14B}
% Main results table + tradeoff curve figure
\subsection{Full Study: Qwen2.5-32B and Qwen3-Coder-30B-A3B}
% Comparative results — model size effect

\section{Results and Analysis}
% Key findings: which strategies dominate at tight budgets?
% Which strategies benefit most from larger budgets?
% Violation rate profiles per strategy

\section{Conclusion}
% BudgetBench enables standardized comparison; findings; future: leaderboard

\appendix
\section{Reproducibility Details}
% Seeds, model hashes (ollama model digest), HuggingFace dataset versions
% Hardware specs, inference stack, timing

\section{Strategy Implementation Details}
% Brief description of each strategy's mechanism
```

**Dataset/code requirements** (NeurIPS D&B track):
- Code must be publicly available by camera-ready deadline
- Croissant metadata required for the benchmark dataset
- Host on HuggingFace (preferred for ML community)
- For arXiv preprint: no deadline pressure, but include GitHub link

**Reproducibility fields required in paper/appendix:**
- Random seed: 42 (set in run_pilot.py, must be propagated to full runner)
- Model hashes: `ollama show --modelfile qwen2.5:14b` captures the manifest digest
- HuggingFace dataset versions: `datasets.load_dataset(..., revision="...")` — pin at runtime
- Hardware: M4 Pro 64GB or RTX 5060 Ti 16GB (document which ran which model)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Custom tokenizer | tiktoken (already in codebase) | Already tested, consistent with RAGStrategy |
| Log-scale x-axis ticks | Custom tick formatter | `ax.set_xscale("log", base=2)` + `ax.set_xticks(BUDGET_TIERS)` | matplotlib handles all edge cases |
| DataFrame joins/pivots | Manual dict merging | pandas pivot_table() | Handles missing combinations gracefully |
| JSONL reading with malformed lines | try/except per line | pandas read_json(lines=True) fallback or manual per-line | Malformed lines (e.g., from interrupted runs) must be handled |
| LaTeX template | Custom .sty | NeurIPS 2026 official neurips_2026.sty | Required by submission system; custom styles trigger desk rejection |
| Resumable sweep | Database/SQLite | Set of (task, strategy, budget) read from existing summary.jsonl | No new dep needed; JSONL is already the output format |

**Key insight:** The existing JSONL logging infrastructure is sufficient for both resumability and aggregation — there is no need to add a new database or tracking system.

---

## Common Pitfalls

### Pitfall 1: format_message() Signature Change Breaks Tests

**What goes wrong:** Adding `budget` parameter to `format_message()` without a default value breaks all existing test calls that omit the argument.
**Why it happens:** Tests in `test_tasks_wave1.py` call `task.format_message(item)` without a budget argument.
**How to avoid:** Use `budget: int = 8192` as the default. Verify with `python -m pytest tests/test_tasks_wave1.py -v` before running the sweep.
**Warning signs:** `TypeError: format_message() missing 1 required positional argument: 'budget'` in test output.

### Pitfall 2: RAGStrategy Indexes the Question as Part of History

**What goes wrong:** If the question_msg is placed at index [1] instead of [-1], RAGStrategy.__call__() treats it as indexable history (messages[1:-1]) and indexes the question itself — then the retrieval query misses the actual chunks.
**Why it happens:** Message ordering matters: [system, chunk_1, ..., chunk_N, question] is the required shape. The question must always be last.
**How to avoid:** Verify the output of format_message() has `messages[-1]["content"]` containing the question text and `messages[1:-1]` containing the context chunks.
**Warning signs:** Violation rate drops to 0% but accuracy stays at 0% even with correct model — means strategy passes budget but context is wrong.

### Pitfall 3: Interrupting the Sweep Corrupts summary.jsonl

**What goes wrong:** A ^C during the `with open(summary_file, "a") as f: f.write(...)` call can leave a partial JSON line, breaking the resume parser.
**Why it happens:** File write is not atomic. A partial write leaves a malformed line.
**How to avoid:** The resume loader must use try/except per line: `try: json.loads(line); except json.JSONDecodeError: pass`. This silently skips any truncated final line.
**Warning signs:** `json.JSONDecodeError` on resume startup.

### Pitfall 4: Chunk Character Approximation Drifts from Token Count

**What goes wrong:** Using `chunk_chars = chunk_size * 4` (chars per token heuristic) on non-ASCII LongBench items (Chinese, Arabic, etc.) significantly overestimates tokens, so chunks may exceed the budget tier.
**Why it happens:** cl100k_base tokenizer encodes CJK characters as 3-4 bytes each but often 1 token — heuristic breaks down.
**How to avoid:** For Phase 4, LongBench v2 is English-primary. If items with non-ASCII context are encountered, the enforce_budget() step will catch violations and log them. The chunk formula is an approximation — RAGStrategy's post-retrieval token-aware filtering (step 5 in rag.py) provides the real budget gate.
**Warning signs:** Elevated violation rates specifically on LongBench items after the fix. Monitor violation_rate in summary.jsonl after the first smoke test run.

### Pitfall 5: LongBenchV2Task Loads Full Dataset on Every run() Call

**What goes wrong:** If `get_dataset()` re-downloads or reprocesses the HuggingFace dataset for each (strategy, budget) combination, it adds minutes of overhead per combination.
**Why it happens:** LongBenchV2Task uses a lazy `@property` for the dataset, but TaskRunner calls `self.task.get_dataset()` on every `run_evaluation()` call.
**How to avoid:** The `@property dataset` already caches `self._dataset` after first load — this is correct. Ensure the task instance is reused across budget tiers (not re-instantiated per combination). The current pilot runner instantiates tasks once per task name — verify this is preserved in the full study extension.
**Warning signs:** Console shows "Downloading dataset" messages at the start of each combination.

### Pitfall 6: summary.jsonl Lacks Model Field for Multi-Model Aggregation

**What goes wrong:** Running three models produces three separate summary.jsonl files with identical schemas, but no way to distinguish which row came from which model when aggregated.
**Why it happens:** Current runner doesn't record args.model in summary rows.
**How to avoid:** Add `"model": args.model or "unknown"` to every summary row in the runner. This is required before any multi-model analysis.
**Warning signs:** Aggregated CSV has duplicate (task, strategy, budget) combinations with no way to differentiate.

### Pitfall 7: Per-Combination JSONL Has No model Field for Violation Rate Computation

**What goes wrong:** The per-combination JSONL (e.g., swe_truncation_2048.jsonl) contains per-turn metrics including violation_rate per turn, but the summary.jsonl only has accuracy. When aggregating violation_rate across combinations for the paper figure, the per-combination files must also be parsed.
**Why it happens:** JSONLMetricsLogger writes per-turn rows; the summary writer only writes the combination-level accuracy. Violation rate per combination must be computed from the per-combination file.
**How to avoid:** In `analyze_results.py`, parse both summary.jsonl (for accuracy) and per-combination JSONL files (for mean violation_rate per combination). The per-combination file naming convention `{task}_{strategy}_{budget}.jsonl` is already established.

---

## Duration Estimates

### Qwen2.5-14B (primary, EVAL-02)

Based on pilot durations (qwen2.5:1.5b via Ollama on Apple Silicon) scaled by model size:

| Component | Pilot (1.5B, 3 items) | Scaling Factor | Full Study Estimate |
|-----------|----------------------|----------------|---------------------|
| SWE-bench per item | ~11s (averaged) | ~3-4x for 14B | ~40s/item |
| LongBench truncation/rag per item | ~2s | ~2-3x | ~5s/item |
| LongBench summary per item | ~34s | ~3-4x | ~120s/item |

**Full sweep calculation (EVAL-02):**
- SWE: 20 items × 6 strategies × 5 tiers × 40s = **6.7 hours**
- LongBench: 50 items × 5 tiers × [1 strategy × 120s + 5 strategies × 5s] = **10.4 hours**
- Total per model: **~17 hours** (plus overhead)

**For EVAL-03 (32B and 30B-A3B):** Expect 1.5-2x longer for 32B (9.0 GB → 19 GB, ~25-35 hours per model).

**Total compute budget for all 3 models:** 50-80 hours. Run sequentially, unattended overnight. Resume support is critical.

[ASSUMED: Scaling factors are based on typical GPU/MLX throughput ratios for model size. Actual timing will depend on hardware load, KV-cache eviction, and prompt length variance.]

---

## Reproducibility Checklist (for Paper)

Per NeurIPS D&B track requirements [CITED: neurips.cc/Conferences/2026/EvaluationsDatasetsFAQ]:

| Item | Value / Action |
|------|---------------|
| Random seed | 42 (set in run_pilot.py, propagate to full runner with `random.seed(args.seed)`) |
| Model digest | Capture with `ollama show qwen2.5:14b --format json` at run time; log to run metadata file |
| HF dataset version | `datasets.load_dataset("THUDM/LongBench-v2", revision="main")` — pin commit hash at run start |
| HF SWE dataset version | Same pinning pattern for SWE-bench Verified subset |
| Hardware | Document: Mac M4 Pro 64GB RAM or RTX 5060 Ti 16GB VRAM |
| Inference stack | Ollama 0.23.1 (confirmed installed), API: localhost:11434/v1/chat/completions |
| Temperature | 0.0 (set in get_llm_client, line 47 of run_pilot.py) |
| Code availability | GitHub repo (anonymized for double-blind; use anonymous.4open.science for submission) |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `conftest.py` (root) + `tests/conftest.py` (fixtures) |
| Quick run command | `python -m pytest tests/test_tasks_wave1.py tests/test_rag.py -v` |
| Full suite command | `python -m pytest tests/ -v` |

**Current baseline:** 38 tests pass. [VERIFIED: `python -m pytest tests/ -v` 2026-05-07]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RAG-FIX | format_message() chunks context at correct sizes | unit | `python -m pytest tests/test_tasks_wave1.py::test_longbench_chunking -x` | ❌ Wave 0 |
| RAG-FIX | RAGStrategy retrieves from chunks (not full context blob) | unit | `python -m pytest tests/test_rag.py::test_rag_longbench_chunked -x` | ❌ Wave 0 |
| RAG-FIX | Violation rate is 0% for LongBench+RAG with chunked messages | smoke | `python scripts/run_pilot.py --limit-tasks 2 --strategies rag --model qwen2.5:14b --limit-budgets 2` | depends on runner |
| EVAL-02 | Full study runner respects --full-study flag (5 tiers, correct items) | unit | `python -m pytest tests/test_runner_full_study.py -x` | ❌ Wave 0 |
| EVAL-02 | Resume skips completed (task, strategy, budget) combinations | unit | `python -m pytest tests/test_runner_full_study.py::test_resume_skip -x` | ❌ Wave 0 |
| EVAL-02 | summary.jsonl includes model field | unit | `python -m pytest tests/test_runner_full_study.py::test_summary_schema -x` | ❌ Wave 0 |
| DOCS-01 | analyze_results.py produces valid CSV from summary.jsonl input | unit | `python -m pytest tests/test_analysis.py -x` | ❌ Wave 0 |
| DOCS-01 | plot_tradeoffs.py generates PNG without error on test data | unit | `python -m pytest tests/test_visualization.py -x` | ❌ Wave 0 |
| DOCS-01 | paper/ directory contains compilable LaTeX (pdflatex smoke test) | manual | `cd paper && pdflatex main.tex` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -v` (full 38-test suite, runs in < 30s)
- **Per wave merge:** Full suite green
- **Phase gate:** Full suite green + 3-item smoke test with Qwen2.5-14B before EVAL-02 sweep starts

### Wave 0 Gaps

- [ ] `tests/test_tasks_wave1.py` — add `test_longbench_chunking` for format_message() chunk count and sizes
- [ ] `tests/test_rag.py` — add `test_rag_longbench_chunked` for end-to-end chunked retrieval
- [ ] `tests/test_runner_full_study.py` — covers --full-study flag, resume logic, summary schema
- [ ] `tests/test_analysis.py` — covers analyze_results.py with fixture JSONL files
- [ ] `tests/test_visualization.py` — covers plot_tradeoffs.py (uses matplotlib non-interactive backend: `matplotlib.use('Agg')`)

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Ollama | EVAL-02, EVAL-03 | ✓ | 0.23.1 | — |
| qwen2.5:14b | EVAL-02 | ✓ | 9.0 GB | — |
| qwen2.5:32b | EVAL-03 | ✓ | 19 GB | — |
| qwen3-coder:30b | EVAL-03 | ✓ | 18 GB | — |
| matplotlib | DOCS-01 | ✓ | 3.10.9 | — |
| pandas | DOCS-01 | ✓ | 2.3.0 | — |
| numpy | DOCS-01 | ✓ | 2.4.4 | — |
| pytest | validation | ✓ | 9.0.3 | — |
| tiktoken | RAG chunking | ✓ | 0.12.0 | 4-char/token heuristic (already in codebase) |
| pdflatex / LaTeX | DOCS-01 paper compile | not checked | — | arXiv accepts .tex source directly; compile not required locally |
| seaborn | visualization style | ✗ | — | matplotlib rcParams style sufficient |

**Missing dependencies with no fallback:** None — all execution and analysis dependencies are confirmed present.

**Missing dependencies with fallback:** seaborn (optional style), pdflatex (arXiv handles compilation).

---

## Security Domain

Security enforcement is not applicable to this phase. BudgetBench is a local research benchmark with no web-facing components, authentication, or user data. All LLM inference runs on localhost via Ollama. Input data is academic datasets (LongBench v2, SWE-bench) with no PII.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Qwen2.5-14B on Apple Silicon (Ollama) runs at ~3-4x slower than 1.5B for inference | Duration Estimates | Run time off by ±50%; could be 8h or 30h. Actual timing from smoke test before full sweep launch. |
| A2 | Chunk char approximation (4 chars/token) is sufficient for English-primary LongBench v2 | Pattern 1 | May produce oversized chunks for rare non-ASCII items; enforce_budget() catches violations anyway |
| A3 | NeurIPS 2026 D&B submission deadline (May 6, 2026) has passed; arXiv preprint is the immediate target | Paper scaffold | If wrong, paper timeline is unaffected (arXiv first regardless) |
| A4 | `ollama show qwen2.5:14b --format json` captures model digest for reproducibility | Reproducibility | Digest capture method may differ across Ollama versions; verify with `ollama show` before run |

---

## Open Questions

1. **LongBench violation rate post-fix verification**
   - What we know: fix is a 1-function change; chunk formula is correct per analysis
   - What's unclear: actual violation rate after fix — could have residual violations if chunk_chars overestimates tokens for specific items
   - Recommendation: Run 3-item smoke test with `--strategies rag --limit-tasks 3 --limit-budgets 2` on Qwen2.5-14B immediately after fix; inspect summary.jsonl for violation_rate = 0% before launching full sweep

2. **τ²-bench full sweep feasibility (deferred)**
   - What we know: integration is wired but tau2-bench not installed; Phase 4 lists it as "if feasible"
   - What's unclear: how long τ²-bench items take with Qwen2.5-14B; whether the 30-day timeline allows it
   - Recommendation: Confirm after EVAL-02 data is collected — if time remains and hardware is available, attempt the sweep; include in paper if complete; note as future work if not

3. **SWE-bench container-based grading vs simplified diff check**
   - What we know: current grader uses simplified diff-presence check; full container-based grading requires Docker + repo checkout per item
   - What's unclear: whether the paper reviewer will accept diff-presence as sufficient for a benchmark paper
   - Recommendation: Use diff-presence for Phase 4 (practical constraint on a 30-day timeline). Disclose clearly in paper as a known limitation; note SWE-bench oracle container grading as future work. [ASSUMED]

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-turn QA benchmarks | Multi-step agentic task suites (SWE-bench, τ²-bench) | 2023-2024 | BudgetBench must use multi-step tasks to be relevant |
| Fixed context window evaluation | Budget-tier sweep (2K/4K/8K/16K/32K) | BudgetBench introduces this | Core contribution |
| LLM-as-judge grading | Deterministic grading (MCQ match, diff presence) | 2024 community push | Enforced by CLAUDE.md constraint |
| NeurIPS D&B single-blind | NeurIPS 2026 D&B now defaults to double-blind | 2026 | Must anonymize submission; use anonymous.4open.science |

**Deprecated/outdated:**
- vLLM as inference backend: explicitly excluded (CLAUDE.md) due to high memory overhead on consumer hardware
- ToolBench for task grading: excluded (LLM-as-judge, violates determinism constraint)

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: codebase] `src/budgetbench/strategies/rag.py` — RAGStrategy.__call__() indexes messages[1:-1]; confirmed root cause of violation
- [VERIFIED: codebase] `src/budgetbench/tasks/long.py` — format_message() returns single user message with full context; confirmed fix target
- [VERIFIED: codebase] `scripts/run_pilot.py` — BUDGET_TIERS, JSONL logging schema, build_strategies() pattern
- [VERIFIED: `ollama list`] All three target models confirmed present: qwen2.5:14b (9.0 GB), qwen2.5:32b (19 GB), qwen3-coder:30b (18 GB)
- [VERIFIED: `python -m pytest tests/ -v`] 38 tests pass; current baseline confirmed 2026-05-07
- [VERIFIED: `pip show matplotlib pandas`] matplotlib 3.10.9, pandas 2.3.0 confirmed installed
- [VERIFIED: pilot JSONL] Log schema confirmed from logs/pilot/20260429_004124/
- [CITED: neurips.cc/Conferences/2026/MainTrackHandbook] 9-page limit, single PDF requirement
- [CITED: neurips.cc/Conferences/2026/EvaluationsDatasetsFAQ] eandd LaTeX option, double-blind default, Croissant metadata, HuggingFace hosting

### Secondary (MEDIUM confidence)

- [CITED: neurips.cc/Conferences/2026/CallForEvaluationsDatasets] Dataset sharing, code requirements, deadline (May 6, 2026)
- [CITED: ollama.com/library/qwen2.5:14b] Tag name and 9.0 GB size confirmed

### Tertiary (LOW confidence)

- Duration scaling factors (3-4x for 14B vs 1.5B) — [ASSUMED] based on model parameter scaling; actual timing from smoke test
- SWE-bench diff-presence acceptability for publication — [ASSUMED] based on practical constraint; disclose as limitation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all deps verified via pip and ollama
- RAG fix pattern: HIGH — root cause confirmed in source, fix logic follows directly
- Architecture: HIGH — all patterns derived from verified codebase
- Duration estimates: MEDIUM — scaling factors assumed; smoke test will confirm
- NeurIPS requirements: MEDIUM — from live official docs, but submission deadline already passed
- Pitfalls: HIGH — most derived from direct code inspection

**Research date:** 2026-05-07
**Valid until:** 2026-06-07 (stable stack; matplotlib/pandas APIs are stable; Ollama model availability may change)
