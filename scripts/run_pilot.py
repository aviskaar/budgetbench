import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests
from budgetbench.tasks import get_task
from budgetbench.strategies import (
    TruncationStrategy,
    SummaryBufferStrategy,
    RAGStrategy,
)
from budgetbench.evaluation.runner import TaskRunner
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.utils.types import OpenAIMessage

# Default Budget Tiers (tokens)
BUDGET_TIERS = [2048, 8192, 32768]
FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]
DEFAULT_TASKS_CONFIG = [
    {"name": "swe", "default_limit": 20},
    {"name": "long", "default_limit": 50},
    {"name": "tau", "default_limit": 200},
]


def get_tokenizer_fn():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return lambda x: len(enc.encode(x))
    except ImportError:
        # Fallback to simple 4-char-per-token approximation
        return lambda x: len(x) // 4


def get_llm_client(url: str = "http://localhost:11434/v1/chat/completions", model: Optional[str] = None):
    def llm_client(messages: List[OpenAIMessage]) -> str:
        formatted_messages = []
        for m in messages:
            msg = {"role": m["role"], "content": m["content"]}
            if "name" in m:
                msg["name"] = m["name"]
            formatted_messages.append(msg)

        payload = {
            "messages": formatted_messages,
            "temperature": 0.0,
            "max_tokens": 512,
        }
        if model:
            payload["model"] = model
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if "Connection refused" in str(e):
                return f"SIMULATED_RESPONSE_DUE_TO_NO_SERVER: {str(e)}"
            raise e

    return llm_client


def load_completed_combinations(summary_file: str) -> set:
    """Return set of (task, strategy, budget) tuples already logged in summary_file."""
    completed = set()
    if not os.path.exists(summary_file):
        return completed
    with open(summary_file) as f:
        for line in f:
            try:
                row = json.loads(line)
                key = (row["task"], row["strategy"], row["budget"])
                completed.add(key)
            except (json.JSONDecodeError, KeyError):
                pass
    return completed


def build_strategies(llm_client, selected_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Build all strategy instances.  Strategies that depend on optional
    third-party packages (mem0, llmlingua, letta) are skipped gracefully
    if their dependencies are not installed.
    """
    requested = set(selected_names) if selected_names else None
    strategies: Dict[str, Any] = {}

    if requested is None or "truncation" in requested:
        strategies["truncation"] = TruncationStrategy()
    if requested is None or "summary" in requested:
        strategies["summary"] = SummaryBufferStrategy(llm_client=llm_client)

    if requested is None or "rag" in requested:
        try:
            strategies["rag"] = RAGStrategy()
        except Exception as e:
            print(f"  [skip] RAGStrategy not available: {e}")

    if requested is None or "letta" in requested:
        try:
            from budgetbench.strategies import LettaStrategy
            strategies["letta"] = LettaStrategy()
        except (ImportError, Exception) as e:
            print(f"  [skip] LettaStrategy not available: {e}")

    if requested is None or "llmlingua" in requested:
        try:
            from budgetbench.strategies import LLMLinguaStrategy
            strategies["llmlingua"] = LLMLinguaStrategy()
        except (ImportError, Exception) as e:
            print(f"  [skip] LLMLinguaStrategy not available: {e}")

    return strategies


class JSONLMetricsLogger(MetricsLogger):
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)

    def log_metrics(self, metrics: Dict[str, Any]):
        metrics_to_log = metrics.copy()
        metrics_to_log["log_time"] = datetime.now().isoformat()
        with open(self.log_path, "a") as f:
            f.write(json.dumps(metrics_to_log) + "\n")


def run_pilot(args):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.full_study and args.run_id:
        log_dir = os.path.join("logs", "full_study", args.run_id)
    elif args.full_study:
        log_dir = os.path.join("logs", "full_study", timestamp)
    else:
        log_dir = os.path.join("logs", "pilot", timestamp)
    os.makedirs(log_dir, exist_ok=True)

    print("--- BudgetBench Full Study Execution ---" if args.full_study else "--- BudgetBench Pilot Execution ---")
    print(f"Logs will be saved to: {log_dir}")

    tokenizer_fn = get_tokenizer_fn()
    llm_client = get_llm_client(args.llm_url, model=args.model)

    # Determine which budget tiers to run
    if args.full_study:
        budgets = FULL_STUDY_BUDGET_TIERS
    elif args.limit_budgets:
        budgets = BUDGET_TIERS[: args.limit_budgets]
    else:
        budgets = BUDGET_TIERS

    # Determine which strategies to run
    if args.limit_budgets:
        budgets = budgets[: args.limit_budgets]

    all_strategies = build_strategies(llm_client, selected_names=args.strategies)
    selected_strategies = (
        {k: all_strategies[k] for k in args.strategies if k in all_strategies}
        if args.strategies
        else all_strategies
    )

    # Fixed seed for reproducibility
    random.seed(42)

    tasks_config = DEFAULT_TASKS_CONFIG
    if args.tasks:
        task_names = set(args.tasks)
        tasks_config = [cfg for cfg in DEFAULT_TASKS_CONFIG if cfg["name"] in task_names]
        unknown_tasks = task_names - {cfg["name"] for cfg in DEFAULT_TASKS_CONFIG}
        if unknown_tasks:
            raise ValueError(
                f"Unknown task(s): {sorted(unknown_tasks)}. "
                f"Available tasks: {[cfg['name'] for cfg in DEFAULT_TASKS_CONFIG]}"
            )

    summary_file = os.path.join(log_dir, "summary.jsonl")
    completed = load_completed_combinations(summary_file)

    for task_cfg in tasks_config:
        task_name = task_cfg["name"]
        limit = task_cfg["default_limit"]
        if args.limit_tasks:
            limit = args.limit_tasks

        print(f"\nProcessing Task: {task_name} (Limit: {limit})")

        try:
            task = get_task(task_name)
        except Exception as e:
            print(f"  Error loading task '{task_name}': {e}")
            continue

        for strategy_name, strategy in selected_strategies.items():
            for budget in budgets:
                print(
                    f"  > Strategy: {strategy_name:10} | Budget: {budget:5} | ",
                    end="",
                    flush=True,
                )

                if (task_name, strategy_name, budget) in completed:
                    print("SKIP (already done)")
                    continue

                if args.dry_run:
                    print("DRY RUN")
                    continue

                log_file = os.path.join(
                    log_dir, f"{task_name}_{strategy_name}_{budget}.jsonl"
                )
                logger = JSONLMetricsLogger(log_file)

                runner = TaskRunner(
                    task=task,
                    strategy=strategy,
                    llm_client=llm_client,
                    tokenizer_fn=tokenizer_fn,
                    logger=logger,
                )

                start_time = time.time()
                try:
                    results = runner.run_evaluation(max_tokens=budget, limit=limit)
                    duration = time.time() - start_time

                    success_count = sum(float(r.get("is_correct", 0)) for r in results)
                    total_count = len(results)
                    accuracy = success_count / total_count if total_count > 0 else 0

                    print(f"Acc: {accuracy:.2f} | Time: {duration:.1f}s")

                    summary = {
                        "timestamp": timestamp,
                        "model": args.model or "unknown",
                        "task": task_name,
                        "strategy": strategy_name,
                        "budget": budget,
                        "accuracy": accuracy,
                        "total": total_count,
                        "success": success_count,
                        "duration_sec": duration,
                    }
                    with open(summary_file, "a") as f:
                        f.write(json.dumps(summary) + "\n")

                except Exception as e:
                    duration = time.time() - start_time
                    print(f"FAILED: {e}")
                    with open(summary_file, "a") as f:
                        f.write(
                            json.dumps(
                                {
                                    "timestamp": timestamp,
                                    "model": args.model or "unknown",
                                    "task": task_name,
                                    "strategy": strategy_name,
                                    "budget": budget,
                                    "error": str(e),
                                    "duration_sec": duration,
                                }
                            )
                            + "\n"
                        )

    print("\n--- Pilot Execution Finished ---")
    if not args.dry_run:
        print(f"Summary available at: {summary_file}")
    else:
        print("Dry run complete. No LLM calls were made.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BudgetBench Pilot Study")
    parser.add_argument(
        "--llm-url",
        type=str,
        default="http://localhost:11434/v1/chat/completions",
        help="Ollama, llama.cpp, or compatible OpenAI-style API URL",
    )
    parser.add_argument(
        "--limit-tasks",
        type=int,
        default=0,
        help="Limit number of items per task (0 = use defaults: 20 SWE / 50 LongBench)",
    )
    parser.add_argument(
        "--limit-budgets",
        type=int,
        default=0,
        help="Limit number of budget tiers to evaluate (0 = all 3)",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        help="Specific strategy names to run (default: all available)",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=[cfg["name"] for cfg in DEFAULT_TASKS_CONFIG],
        help="Specific task names to run (default: swe long tau)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to pass in the API payload (required for Ollama; omit for llama.cpp)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the setup without calling the LLM",
    )
    parser.add_argument(
        "--full-study",
        action="store_true",
        help="Run full 5-tier study (all 5 budget tiers, logs to logs/full_study/)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Resume a previous run by its timestamp string (e.g. 20260508_120000)",
    )

    args = parser.parse_args()
    run_pilot(args)
