# Phase 4: Full Execution & Publication - Pattern Map

**Mapped:** 2026-05-07
**Files analyzed:** 11 (7 code files + 1 LaTeX scaffold + 1 results dir + 2 implied)
**Analogs found:** 9 / 11

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/budgetbench/tasks/long.py` | task (modify) | transform | `src/budgetbench/tasks/long.py` (self) | exact |
| `scripts/run_pilot.py` | script (modify) | batch | `scripts/run_pilot.py` (self) | exact |
| `scripts/analyze_results.py` | utility (new) | batch/transform | `scripts/run_pilot.py` (JSONL reading/writing) | role-match |
| `scripts/plot_tradeoffs.py` | utility (new) | transform | none — matplotlib with no existing viz script | partial |
| `tests/test_tasks_wave1.py` | test (modify) | — | `tests/test_tasks_wave1.py` (self) | exact |
| `tests/test_rag.py` | test (modify) | — | `tests/test_rag.py` (self) | exact |
| `tests/test_runner_full_study.py` | test (new) | — | `tests/test_tasks_wave1.py` | role-match |
| `tests/test_analysis.py` | test (new) | — | `tests/test_metrics.py` (tmp_path fixture + JSONL) | role-match |
| `tests/test_visualization.py` | test (new) | — | `tests/test_metrics.py` (tmp_path fixture pattern) | partial |
| `paper/main.tex` | LaTeX scaffold (new) | — | none | no analog |
| `results/` | output directory | — | `logs/pilot/` (naming/JSONL conventions) | partial |

---

## Pattern Assignments

### `src/budgetbench/tasks/long.py` — modify `format_message()` (task, transform)

**Analog:** `src/budgetbench/tasks/long.py` (self — targeted single-function change)

**Current signature** (line 28):
```python
def format_message(self, item: Dict[str, Any]) -> List[OpenAIMessage]:
```

**New signature** — add `budget` with default to preserve backward compatibility:
```python
def format_message(self, item: Dict[str, Any], budget: int = 8192) -> List[OpenAIMessage]:
```

**Current imports pattern** (lines 1-8) — no changes needed:
```python
import datasets
import re
from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask
```

**Current single-message body** (lines 28-45) — replace with chunking logic:
```python
# CURRENT (lines 41-45):
messages: List[OpenAIMessage] = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}{choices_text}"}
]
return messages
```

**New chunking body** — replace lines 41-45 only:
```python
chunk_size = min(budget // 4, 512)   # tokens; 512 for all budgets >= 2K
chunk_chars = chunk_size * 4         # ~4 chars/token heuristic (matches run_pilot.py fallback)

if len(context) <= chunk_chars:
    # Small context — single message, no overhead
    context_messages: List[OpenAIMessage] = [
        {"role": "user", "content": f"Context:\n{context}"}
    ]
else:
    context_messages = []
    for i in range(0, len(context), chunk_chars):
        chunk_text = context[i : i + chunk_chars]
        context_messages.append({
            "role": "user",
            "content": f"Context part {i // chunk_chars + 1}:\n{chunk_text}"
        })

system_msg: OpenAIMessage = {"role": "system", "content": system_prompt}
question_msg: OpenAIMessage = {"role": "user", "content": f"Question: {question}{choices_text}"}
return [system_msg] + context_messages + [question_msg]
```

**Caller update** in `run()` (line 56) — pass budget through:
```python
# CURRENT (line 56):
messages = self.format_message(item)

# NEW:
messages = self.format_message(item, budget=max_tokens)
```

**Critical invariant** — `messages[-1]` must always be the question, and `messages[1:-1]` must be the context chunks. RAGStrategy indexes `messages[1:-1]` (verified in `src/budgetbench/strategies/rag.py` lines 68-79). The new message shape `[system, chunk_1, ..., chunk_N, question]` satisfies this.

---

### `scripts/run_pilot.py` — add `--full-study` flag (script, batch)

**Analog:** `scripts/run_pilot.py` (self — additive extension)

**Existing constants pattern** (lines 21-22):
```python
# Default Budget Tiers (tokens)
BUDGET_TIERS = [2048, 8192, 32768]
```

**Add alongside existing constant:**
```python
FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]
```

**Existing argparse block** (lines 241-277) — add two new flags after `--dry-run`:
```python
parser.add_argument(
    "--full-study",
    action="store_true",
    help="Run full parameter sweep: all 5 budget tiers, all strategies, with checkpoint/resume",
)
parser.add_argument(
    "--seed",
    type=int,
    default=42,
    help="Random seed for reproducibility (default: 42)",
)
```

**Existing budget selection** (lines 121-123):
```python
budgets = BUDGET_TIERS
if args.limit_budgets:
    budgets = budgets[: args.limit_budgets]
```

**New budget selection** — prepend full-study check:
```python
if args.full_study:
    budgets = FULL_STUDY_BUDGET_TIERS
else:
    budgets = BUDGET_TIERS
    if args.limit_budgets:
        budgets = budgets[: args.limit_budgets]
```

**Existing log_dir** (line 111):
```python
log_dir = os.path.join("logs", "pilot", timestamp)
```

**New conditional log_dir:**
```python
run_type = "full_study" if args.full_study else "pilot"
log_dir = os.path.join("logs", run_type, timestamp)
```

**Existing random seed** (line 143):
```python
random.seed(42)
```

**New (use arg):**
```python
random.seed(args.seed)
```

**Add resume loader function** — before `run_pilot()`:
```python
def load_completed_combinations(summary_file: str) -> set:
    """Returns set of (task, strategy, budget) tuples already logged in summary.jsonl."""
    completed = set()
    if not os.path.exists(summary_file):
        return completed
    with open(summary_file) as f:
        for line in f:
            try:
                row = json.loads(line)
                completed.add((row["task"], row["strategy"], row["budget"]))
            except (json.JSONDecodeError, KeyError):
                pass  # Silently skip truncated/malformed lines from interrupted runs
    return completed
```

**Existing inner loop** (lines 167-169):
```python
for strategy_name, strategy in selected_strategies.items():
    for budget in budgets:
        print(...)
```

**New resume check** — insert inside inner loop before `if args.dry_run`:
```python
if args.full_study:
    completed = load_completed_combinations(summary_file)
    key = (task_name, strategy_name, budget)
    if key in completed:
        print(f"  > [SKIP] {task_name} | {strategy_name} | {budget} — already done")
        continue
```

**Existing summary dict** (lines 202-211):
```python
summary = {
    "timestamp": timestamp,
    "task": task_name,
    "strategy": strategy_name,
    "budget": budget,
    "accuracy": accuracy,
    "total": total_count,
    "success": success_count,
    "duration_sec": duration,
}
```

**New summary dict** — add `model` field:
```python
summary = {
    "timestamp": timestamp,
    "model": args.model or "unknown",   # ADD: required for multi-model aggregation
    "task": task_name,
    "strategy": strategy_name,
    "budget": budget,
    "accuracy": accuracy,
    "total": total_count,
    "success": success_count,
    "duration_sec": duration,
}
```

**Error summary dict** (lines 223-231) — add same `"model"` field to keep schema consistent.

---

### `scripts/analyze_results.py` — new (utility, batch/transform)

**Analog:** `scripts/run_pilot.py` — JSONL reading pattern (lines 215-214, 218-231)

**Imports pattern** — modeled on run_pilot.py's `json`, `os`, `argparse` usage:
```python
import argparse
import glob
import json
import os
import sys
from typing import List

import pandas as pd
```

**JSONL reading core pattern** — copied from run_pilot.py's per-line `json.loads()` with `try/except`:
```python
def load_summary_files(log_dirs: List[str]) -> pd.DataFrame:
    """Load all summary.jsonl files from given log directories into a DataFrame."""
    rows = []
    for log_dir in log_dirs:
        summary_path = os.path.join(log_dir, "summary.jsonl")
        if not os.path.exists(summary_path):
            print(f"  [warn] No summary.jsonl in {log_dir}", file=sys.stderr)
            continue
        with open(summary_path) as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # Skip truncated lines from interrupted runs (Pitfall 3)
    return pd.DataFrame(rows)
```

**Per-combination JSONL violation_rate extraction pattern** — mirrors per-combination file naming `{task}_{strategy}_{budget}.jsonl` (verified from `logs/pilot/20260429_004124/`):
```python
def compute_violation_rates(log_dir: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Annotate df rows with mean violation_rate from per-combination JSONL files.
    Per-combination file schema (verified from pilot logs):
      {"quality": 0.0, "used_budget": 0, "peak_budget": 275460,
       "violation_rate": 1.0, "tokens_per_task": 0, ...}
    """
    violation_rates = []
    for _, row in df.iterrows():
        combo_file = os.path.join(
            log_dir,
            f"{row['task']}_{row['strategy']}_{row['budget']}.jsonl"
        )
        rates = []
        if os.path.exists(combo_file):
            with open(combo_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if "violation_rate" in entry:
                            rates.append(entry["violation_rate"])
                    except json.JSONDecodeError:
                        pass
        violation_rates.append(sum(rates) / len(rates) if rates else None)
    df = df.copy()
    df["violation_rate"] = violation_rates
    return df
```

**Output writing pattern** — mirrors run_pilot.py's `os.makedirs` + file write pattern:
```python
def write_csv(df: pd.DataFrame, out_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
```

**Argparse pattern** — mirrors run_pilot.py's argparse block:
```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate BudgetBench JSONL logs into CSV")
    parser.add_argument("log_dirs", nargs="+", help="One or more log directories (each containing summary.jsonl)")
    parser.add_argument("--out", default="results/full_study.csv", help="Output CSV path")
    args = parser.parse_args()
    df = load_summary_files(args.log_dirs)
    # Attempt violation_rate annotation for single-dir runs
    if len(args.log_dirs) == 1:
        df = compute_violation_rates(args.log_dirs[0], df)
    write_csv(df, args.out)
```

---

### `scripts/plot_tradeoffs.py` — new (utility, transform)

**Analog:** None in codebase. Follows RESEARCH.md Pattern 4 (matplotlib 3.10.9).

**Imports pattern** — no existing analog; use RESEARCH.md pattern:
```python
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")   # Non-interactive backend — must be set BEFORE pyplot import
import matplotlib.pyplot as plt
import pandas as pd
```

**Constants** — strategy rendering config (no existing analog):
```python
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
    "mem0": "D", "letta": "v", "llmlingua": "P",
}
```

**Figure layout** — 2×2 panel, log2 x-axis, one line per strategy:
```python
def plot_tradeoff_curves(df: pd.DataFrame, model: str, out_path: str) -> None:
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
        for strategy in sorted(df["strategy"].unique()):
            s_data = sub[sub["strategy"] == strategy].sort_values("budget")
            x = s_data["budget"].tolist()
            y_acc = s_data["accuracy"].tolist()
            y_viol = s_data.get("violation_rate", s_data["accuracy"] * 0).tolist()
            color = STRATEGY_COLORS.get(strategy)
            marker = STRATEGY_MARKERS.get(strategy, "o")
            axes[0][col].plot(x, y_acc, label=strategy, color=color, marker=marker)
            axes[1][col].plot(x, y_viol, label=strategy, color=color, marker=marker)

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
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close()
```

---

### `tests/test_tasks_wave1.py` — add `test_longbench_chunking` (test, modify)

**Analog:** `tests/test_tasks_wave1.py` (self) — follow `test_longbench_wrapper` structure exactly

**Existing test structure** (lines 1-5, 7-10):
```python
import pytest
import json
from unittest.mock import MagicMock, patch
from budgetbench.tasks.long import LongBenchV2Task
from budgetbench.tasks.swe import SWEBenchTask

@pytest.fixture
def mock_datasets():
    with patch("datasets.load_dataset") as mock:
        yield mock
```

**New test to append** — follows exact fixture-usage and assertion style:
```python
def test_longbench_chunking(mock_datasets):
    """format_message() with budget param produces multiple context chunk messages."""
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = []
    mock_ds.__len__.return_value = 0
    mock_datasets.return_value = mock_ds

    task = LongBenchV2Task()
    # Build an item where context is large enough to force chunking at budget=2048
    # chunk_chars = min(2048//4, 512) * 4 = 512 * 4 = 2048 chars
    # Context of 5000 chars should produce ceil(5000/2048) = 3 chunks
    item = {
        "context": "X" * 5000,
        "question": "What is the answer?",
        "choice_A": "A", "choice_B": "B", "choice_C": "C", "choice_D": "D",
        "answer": "A",
    }

    messages = task.format_message(item, budget=2048)

    # Structure: [system, chunk_1, chunk_2, ..., chunk_N, question]
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert "Question:" in messages[-1]["content"]

    # The middle messages are all context chunks
    context_chunks = messages[1:-1]
    assert len(context_chunks) >= 2, "Context should be split into multiple chunks"

    # Each chunk should start with "Context part"
    for chunk in context_chunks:
        assert chunk["role"] == "user"
        assert chunk["content"].startswith("Context part")

def test_longbench_no_chunking_small_context(mock_datasets):
    """format_message() with small context passes it as a single message."""
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = []
    mock_ds.__len__.return_value = 0
    mock_datasets.return_value = mock_ds

    task = LongBenchV2Task()
    item = {
        "context": "Short context.",
        "question": "What?",
        "choice_A": "A", "choice_B": "B", "choice_C": "C", "choice_D": "D",
        "answer": "A",
    }

    messages = task.format_message(item, budget=8192)
    # Single context message — no chunking overhead
    assert len(messages) == 3   # system + 1 context + question
    assert messages[1]["content"].startswith("Context:")

def test_longbench_format_message_backward_compat(mock_datasets):
    """Calling format_message(item) without budget arg still works (default=8192)."""
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = []
    mock_ds.__len__.return_value = 0
    mock_datasets.return_value = mock_ds

    task = LongBenchV2Task()
    item = {
        "context": "Some context.", "question": "Q?",
        "choice_A": "A", "choice_B": "B", "choice_C": "C", "choice_D": "D",
        "answer": "A",
    }
    # Must not raise TypeError
    messages = task.format_message(item)
    assert messages[0]["role"] == "system"
```

---

### `tests/test_rag.py` — add `test_rag_longbench_chunked` (test, modify)

**Analog:** `tests/test_rag.py` (self) — follow `test_rag_strategy_retrieval` structure

**Existing test structure** (lines 1-3):
```python
import pytest
from budgetbench.strategies.rag import RAGStrategy
from budgetbench.utils.types import OpenAIMessage
```

**New test to append** — same RAGStrategy instantiation and assertion style:
```python
def test_rag_longbench_chunked():
    """RAGStrategy retrieves from chunked context messages produced by format_message()."""
    strategy = RAGStrategy()

    # Simulate messages shaped as [system, chunk_1, chunk_2, ..., chunk_N, question]
    # This is the shape that LongBenchV2Task.format_message(item, budget=2048) produces
    messages = [
        {"role": "system", "content": "Answer based on the provided context."},
        {"role": "user", "content": "Context part 1:\nThe Eiffel Tower is in Paris, France."},
        {"role": "user", "content": "Context part 2:\nThe Great Wall is in China."},
        {"role": "user", "content": "Context part 3:\nMt. Fuji is in Japan."},
        {"role": "user", "content": "Question: Where is the Eiffel Tower?"},
    ]

    # Budget tight enough to force retrieval but wide enough to fit system+question+1 chunk
    result = strategy(messages, active_budget=100)

    # Invariants: system first, question last
    assert result[0]["role"] == "system"
    assert result[-1]["content"] == "Question: Where is the Eiffel Tower?"

    # The relevant chunk (Paris) should be retrieved
    content_blob = " ".join(m["content"] for m in result)
    assert "Paris" in content_blob
```

---

### `tests/test_runner_full_study.py` — new (test, role-match)

**Analog:** `tests/test_tasks_wave1.py` — MagicMock + patch pattern; `tests/test_harness.py` — error path patterns

**File header pattern** — mirrors test_tasks_wave1.py structure:
```python
import json
import os
import pytest
from unittest.mock import MagicMock, patch
```

**Import under test** — the functions added to run_pilot.py:
```python
# Import the two new functions from run_pilot
import importlib, sys

def _load_run_pilot():
    # Reload to pick up any in-process changes
    if "scripts.run_pilot" in sys.modules:
        del sys.modules["scripts.run_pilot"]
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_pilot", os.path.join(os.path.dirname(__file__), "../scripts/run_pilot.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
```

**Test stubs** — follow conftest fixture pattern (`tmp_path` from pytest):
```python
def test_load_completed_combinations_empty(tmp_path):
    """Returns empty set when summary.jsonl does not exist."""
    mod = _load_run_pilot()
    result = mod.load_completed_combinations(str(tmp_path / "summary.jsonl"))
    assert result == set()

def test_load_completed_combinations_skips_malformed(tmp_path):
    """Skips truncated/malformed JSON lines (Pitfall 3 guard)."""
    summary = tmp_path / "summary.jsonl"
    summary.write_text(
        '{"task":"swe","strategy":"rag","budget":2048}\n'
        'TRUNCATED_LINE\n'
    )
    mod = _load_run_pilot()
    result = mod.load_completed_combinations(str(summary))
    assert ("swe", "rag", 2048) in result
    assert len(result) == 1

def test_summary_schema_includes_model(tmp_path):
    """Full-study summary rows contain 'model' field (Pitfall 6 guard)."""
    # Write a fake summary.jsonl with model field and verify load reads it
    summary = tmp_path / "summary.jsonl"
    row = {
        "timestamp": "20260507_000000",
        "model": "qwen2.5:14b",
        "task": "long",
        "strategy": "truncation",
        "budget": 4096,
        "accuracy": 0.5,
        "total": 10,
        "success": 5,
        "duration_sec": 120.0,
    }
    summary.write_text(json.dumps(row) + "\n")
    mod = _load_run_pilot()
    result = mod.load_completed_combinations(str(summary))
    assert ("long", "truncation", 4096) in result
```

**Full-study flag test** — integration-level, uses `subprocess` to avoid LLM call:
```python
def test_full_study_flag_sets_5_tiers():
    """--full-study flag sets FULL_STUDY_BUDGET_TIERS (5 entries)."""
    mod = _load_run_pilot()
    assert len(mod.FULL_STUDY_BUDGET_TIERS) == 5
    assert mod.FULL_STUDY_BUDGET_TIERS == [2048, 4096, 8192, 16384, 32768]
```

---

### `tests/test_analysis.py` — new (test, role-match)

**Analog:** `tests/test_metrics.py` — `tmp_path` fixture + JSONL file write + read-back assertions

**Existing test_metrics.py pattern** (lines 1-5, 6-10):
```python
import os
import json
import pytest
from budgetbench.evaluation.metrics import MetricsLogger

def test_metrics_logger_appends_jsonl(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    ...
    with open(log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
```

**New test file** — same `tmp_path` + JSONL fixture approach:
```python
import json
import os
import pytest
import pandas as pd

# Load analyze_results module from scripts/
import importlib.util, sys

def _load_analyze():
    spec = importlib.util.spec_from_file_location(
        "analyze_results",
        os.path.join(os.path.dirname(__file__), "../scripts/analyze_results.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture
def pilot_summary(tmp_path):
    """Creates a minimal summary.jsonl fixture matching the verified pilot schema."""
    rows = [
        {"timestamp": "20260507", "model": "qwen2.5:14b", "task": "swe",
         "strategy": "truncation", "budget": 2048, "accuracy": 0.0,
         "total": 3, "success": 0, "duration_sec": 34.5},
        {"timestamp": "20260507", "model": "qwen2.5:14b", "task": "long",
         "strategy": "rag", "budget": 4096, "accuracy": 0.33,
         "total": 3, "success": 1, "duration_sec": 5.0},
    ]
    log_dir = tmp_path / "pilot"
    log_dir.mkdir()
    summary = log_dir / "summary.jsonl"
    with open(summary, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return str(log_dir)

def test_load_summary_files_returns_dataframe(pilot_summary):
    mod = _load_analyze()
    df = mod.load_summary_files([pilot_summary])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "accuracy" in df.columns
    assert "model" in df.columns

def test_load_summary_skips_malformed_lines(tmp_path):
    """Malformed JSONL lines are silently skipped (Pitfall 3 guard)."""
    log_dir = tmp_path / "run"
    log_dir.mkdir()
    summary = log_dir / "summary.jsonl"
    summary.write_text('{"task":"swe","strategy":"rag","budget":2048,"model":"x","accuracy":0.0,"total":1,"success":0,"duration_sec":1.0}\nBAD_LINE\n')
    mod = _load_analyze()
    df = mod.load_summary_files([str(log_dir)])
    assert len(df) == 1

def test_write_csv_creates_file(tmp_path, pilot_summary):
    mod = _load_analyze()
    df = mod.load_summary_files([pilot_summary])
    out = str(tmp_path / "results" / "test.csv")
    mod.write_csv(df, out)
    assert os.path.exists(out)
    import pandas as pd
    df2 = pd.read_csv(out)
    assert len(df2) == 2
```

---

### `tests/test_visualization.py` — new (test, partial-match)

**Analog:** `tests/test_metrics.py` — `tmp_path` pattern for file output assertion

**Critical setup** — `matplotlib.use("Agg")` before pyplot import (non-interactive CI):
```python
import os
import json
import pytest
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # MUST be before pyplot import; same requirement as plot_tradeoffs.py

import importlib.util

def _load_plot():
    spec = importlib.util.spec_from_file_location(
        "plot_tradeoffs",
        os.path.join(os.path.dirname(__file__), "../scripts/plot_tradeoffs.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture
def minimal_tradeoff_df():
    """Minimal DataFrame matching analyze_results.py output schema."""
    import pandas as pd
    rows = []
    for task in ["swe", "long"]:
        for strategy in ["truncation", "rag"]:
            for budget in [2048, 8192, 32768]:
                rows.append({
                    "model": "qwen2.5:14b", "task": task,
                    "strategy": strategy, "budget": budget,
                    "accuracy": 0.5, "violation_rate": 0.1,
                })
    return pd.DataFrame(rows)

def test_plot_generates_png(tmp_path, minimal_tradeoff_df):
    """plot_tradeoff_curves() produces a PNG file without error."""
    mod = _load_plot()
    out_path = str(tmp_path / "figures" / "tradeoffs.png")
    mod.plot_tradeoff_curves(minimal_tradeoff_df, model="qwen2.5:14b", out_path=out_path)
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

def test_plot_handles_missing_violation_rate(tmp_path, minimal_tradeoff_df):
    """plot_tradeoff_curves() runs even if violation_rate column is absent."""
    mod = _load_plot()
    df = minimal_tradeoff_df.drop(columns=["violation_rate"])
    out_path = str(tmp_path / "figures" / "tradeoffs_no_viol.png")
    mod.plot_tradeoff_curves(df, model="qwen2.5:14b", out_path=out_path)
    assert os.path.exists(out_path)
```

---

### `paper/main.tex` — new NeurIPS 2026 scaffold (LaTeX, no analog)

**No codebase analog.** Use RESEARCH.md Pattern 5 directly.

**Required preamble:**
```latex
\documentclass{article}
\usepackage[eandd]{neurips_2026}   % NeurIPS D&B track option
\usepackage{amsmath, amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{natbib}
```

**Section scaffold** — 7 required sections per NeurIPS D&B requirements:
1. `\section{Introduction}` — problem, gap, contribution, teaser result
2. `\section{Related Work}` — LLMLingua, MemGPT/Letta, Mem0, SWE-bench, LongBench v2
3. `\section{BudgetBench Framework}` — task suite, strategy interface, budget enforcement
4. `\section{Experiments}` — pilot table (Phase 3) + full study (EVAL-02/03)
5. `\section{Results and Analysis}` — tradeoff curve figure + findings
6. `\section{Conclusion}` — contribution summary + future work
7. `\appendix` — reproducibility details, strategy descriptions

**Figure inclusion pattern:**
```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/tradeoff_curves_qwen2514b}
  \caption{BudgetBench tradeoff curves for Qwen2.5-14B across all 5 budget tiers.
           Top row: accuracy vs. budget. Bottom row: violation rate vs. budget.}
  \label{fig:tradeoff}
\end{figure}
```

**Reproducibility appendix required fields** (NeurIPS D&B requirement):
- Random seed: 42
- Model digest: from `ollama show qwen2.5:14b --format json`
- HuggingFace dataset version: pinned revision hash
- Hardware: Mac M4 Pro 64GB / RTX 5060 Ti 16GB
- Inference stack: Ollama 0.23.1, `localhost:11434/v1/chat/completions`
- Temperature: 0.0

---

### `results/` — output directory (no file, just conventions)

**Analog:** `logs/pilot/` directory structure (naming conventions verified from codebase)

**Naming conventions:**
```
results/
├── full_study_qwen2514b_YYYYMMDD_HHMMSS.csv   # from analyze_results.py
└── figures/
    └── tradeoff_curves_qwen2514b_YYYYMMDD.png  # from plot_tradeoffs.py
```

**CSV column schema** (derived from summary.jsonl + violation_rate annotation):
```
model, task, strategy, budget, accuracy, violation_rate, total, success, duration_sec, timestamp
```

---

## Shared Patterns

### JSONL-per-line with try/except guard (Pitfall 3 guard)

**Source:** `scripts/run_pilot.py` lines 215-214 (write) and confirmed from pilot log `logs/pilot/20260429_004124/long_rag_2048.jsonl`
**Apply to:** `analyze_results.py` `load_summary_files()`, `load_completed_combinations()`, `test_analysis.py`

```python
# Write (run_pilot.py lines 213-214):
with open(summary_file, "a") as f:
    f.write(json.dumps(summary) + "\n")

# Read — always wrap per-line parse:
with open(path) as f:
    for line in f:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            pass   # Silently skip truncated last line from interrupted run
```

### Optional import / graceful skip

**Source:** `scripts/run_pilot.py` lines 76-93 (`build_strategies()`)
**Apply to:** `analyze_results.py` and `plot_tradeoffs.py` optional deps (pandas, matplotlib)

```python
try:
    from budgetbench.strategies import Mem0Strategy
    strategies["mem0"] = Mem0Strategy()
except (ImportError, Exception) as e:
    print(f"  [skip] Mem0Strategy not available: {e}")
```

### `os.makedirs` before file write

**Source:** `scripts/run_pilot.py` line 100 (`JSONLMetricsLogger.__init__`):
```python
os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
```

**Apply to:** `analyze_results.py` `write_csv()`, `plot_tradeoffs.py` `plot_tradeoff_curves()`

### Tokenizer with tiktoken fallback

**Source:** `scripts/run_pilot.py` lines 24-31:
```python
def get_tokenizer_fn():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return lambda x: len(enc.encode(x))
    except ImportError:
        return lambda x: len(x) // 4   # 4-char/token heuristic
```

**Apply to:** `long.py` chunking — uses same 4-char/token heuristic (`chunk_chars = chunk_size * 4`)

### `unittest.mock.MagicMock` + `patch` test structure

**Source:** `tests/test_tasks_wave1.py` lines 1-3, 7-10:
```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_datasets():
    with patch("datasets.load_dataset") as mock:
        yield mock
```

**Apply to:** `test_runner_full_study.py`, `test_analysis.py`, `test_visualization.py`

### `tmp_path` fixture for file I/O tests

**Source:** `tests/test_metrics.py` line 6:
```python
def test_metrics_logger_appends_jsonl(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
```

**Apply to:** All three new test files — use `tmp_path` for all output file assertions

### `matplotlib.use("Agg")` before pyplot import

**Source:** No codebase precedent — derived from RESEARCH.md validation architecture (test_visualization.py note)
**Apply to:** `plot_tradeoffs.py` (top of file) and `test_visualization.py` (before `import matplotlib.pyplot`)

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `paper/main.tex` | LaTeX document | — | No LaTeX files exist in the codebase; use NeurIPS 2026 template per RESEARCH.md Pattern 5 |
| `scripts/plot_tradeoffs.py` | visualization utility | transform | No existing visualization scripts; matplotlib pattern from RESEARCH.md Pattern 4 |

---

## Metadata

**Analog search scope:** `scripts/`, `src/budgetbench/tasks/`, `src/budgetbench/strategies/`, `tests/`, `logs/pilot/`
**Files read for pattern extraction:** 9 source files + 2 JSONL log files
**Pattern extraction date:** 2026-05-07
