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
from budgetbench.core.tokenizer import build_token_counter
from budgetbench.tasks import get_task
from budgetbench.evaluation.runner import TaskRunner
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.utils.types import OpenAIMessage

# Default Budget Tiers (tokens)
BUDGET_TIERS = [2048, 8192, 32768]
FULL_STUDY_BUDGET_TIERS = [2048, 4096, 8192, 16384, 32768]
DEFAULT_TASKS_CONFIG = [
    {"name": "swe", "default_limit": 100},
    {"name": "long", "default_limit": 100},
    {"name": "memory", "default_limit": 30},
    {"name": "tau", "default_limit": 200},
    {"name": "longmem", "default_limit": 20, "enabled_by_default": False},
]


def resolve_budget_tiers(
    full_study: bool = False,
    limit_budgets: int = 0,
    selected_budgets: Optional[List[int]] = None,
) -> List[int]:
    """Resolve the budget tier list for a run."""
    if selected_budgets:
        budgets = list(selected_budgets)
    else:
        budgets = list(FULL_STUDY_BUDGET_TIERS if full_study else BUDGET_TIERS)

    if any(budget <= 0 for budget in budgets):
        raise ValueError(f"Budgets must be positive integers: {budgets}")

    if limit_budgets:
        budgets = budgets[:limit_budgets]

    return budgets


def get_tokenizer_fn(model: Optional[str] = None, tokenizer_name: Optional[str] = None):
    return build_token_counter(model_name=model, tokenizer_name=tokenizer_name)


def get_llm_client(
    url: str = "http://localhost:11434/v1/chat/completions",
    model: Optional[str] = None,
    max_output_tokens: int = 512,
    api_key_env: Optional[str] = None,
):
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
            "max_tokens": max_output_tokens,
        }
        if model:
            payload["model"] = model
        headers = {}
        if api_key_env:
            api_key = os.environ.get(api_key_env)
            if not api_key:
                raise RuntimeError(f"{api_key_env} is not set")
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if "Connection refused" in str(e):
                return f"SIMULATED_RESPONSE_DUE_TO_NO_SERVER: {str(e)}"
            raise e

    return llm_client


def load_completed_combinations(summary_file: str) -> set:
    """Return set of (task, strategy, budget, repeat_index) tuples already logged in summary_file."""
    completed = set()
    if not os.path.exists(summary_file):
        return completed
    with open(summary_file) as f:
        for line in f:
            try:
                row = json.loads(line)
                key = (row["task"], row["strategy"], row["budget"], int(row.get("repeat_index", 0)))
                completed.add(key)
            except (json.JSONDecodeError, KeyError):
                pass
    return completed


def build_strategies(
    llm_client,
    tokenizer_fn,
    retrieval_model_name: str,
    selected_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build all strategy instances.  Strategies that depend on optional
    third-party packages (mem0, llmlingua, letta) are skipped gracefully
    if their dependencies are not installed.
    """
    requested = set(selected_names) if selected_names else None
    strategies: Dict[str, Any] = {}

    if requested is None or "truncation" in requested:
        from budgetbench.strategies.truncation import TruncationStrategy
        strategies["truncation"] = TruncationStrategy(tokenizer_fn=tokenizer_fn)
    if requested is None or "full_context" in requested:
        from budgetbench.strategies.full_context import FullContextStrategy
        strategies["full_context"] = FullContextStrategy()
    if requested is None or "summary" in requested:
        from budgetbench.strategies.summary import SummaryBufferStrategy
        strategies["summary"] = SummaryBufferStrategy(
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
        )

    if requested is None or "rag" in requested:
        try:
            from budgetbench.strategies.rag import RAGStrategy
            strategies["rag"] = RAGStrategy(
                model_name=retrieval_model_name,
                tokenizer_fn=tokenizer_fn,
            )
        except Exception as e:
            print(f"  [skip] RAGStrategy not available: {e}")

    if requested is None or "lean_retrieval" in requested:
        try:
            from budgetbench.strategies.lean_retrieval import LeanRetrievalStrategy
            strategies["lean_retrieval"] = LeanRetrievalStrategy(
                model_name=retrieval_model_name,
                tokenizer_fn=tokenizer_fn,
            )
        except Exception as e:
            print(f"  [skip] LeanRetrievalStrategy not available: {e}")

    if requested is None or "checkpoint_context" in requested:
        try:
            from budgetbench.strategies.checkpoint_context import CheckpointContextStrategy
            strategies["checkpoint_context"] = CheckpointContextStrategy(tokenizer_fn=tokenizer_fn)
        except Exception as e:
            print(f"  [skip] CheckpointContextStrategy not available: {e}")

    if requested is None or "mem0" in requested:
        try:
            from budgetbench.strategies import Mem0Strategy
            strategies["mem0"] = Mem0Strategy(tokenizer_fn=tokenizer_fn)
        except (ImportError, Exception) as e:
            print(f"  [skip] Mem0Strategy not available: {e}")

    if requested is None or "letta" in requested:
        try:
            from budgetbench.strategies import LettaStrategy
            strategies["letta"] = LettaStrategy(
                model_name=retrieval_model_name,
                tokenizer_fn=tokenizer_fn,
            )
        except (ImportError, Exception) as e:
            print(f"  [skip] LettaStrategy not available: {e}")

    if requested is None or "llmlingua" in requested:
        try:
            from budgetbench.strategies import LLMLinguaStrategy
            strategies["llmlingua"] = LLMLinguaStrategy(tokenizer_fn=tokenizer_fn)
        except (ImportError, Exception) as e:
            print(f"  [skip] LLMLinguaStrategy not available: {e}")

    return strategies


def build_task_kwargs(args) -> Dict[str, Dict[str, Any]]:
    kwargs: Dict[str, Dict[str, Any]] = {}
    long_kwargs: Dict[str, Any] = {}
    if args.longbench_chunk_tokens is not None:
        long_kwargs["context_chunk_tokens"] = args.longbench_chunk_tokens
    if args.longbench_char_per_token is not None:
        long_kwargs["context_char_per_token"] = args.longbench_char_per_token
    if long_kwargs:
        kwargs["long"] = long_kwargs
    return kwargs


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

    tokenizer_fn = get_tokenizer_fn(model=args.model, tokenizer_name=args.tokenizer)
    llm_client = get_llm_client(
        args.llm_url,
        model=args.model,
        max_output_tokens=args.max_output_tokens,
        api_key_env=args.api_key_env,
    )

    budgets = resolve_budget_tiers(
        full_study=args.full_study,
        limit_budgets=args.limit_budgets,
        selected_budgets=args.budgets,
    )

    all_strategies = build_strategies(
        llm_client,
        tokenizer_fn=tokenizer_fn,
        retrieval_model_name=args.retrieval_embedding_model,
        selected_names=args.strategies,
    )
    selected_strategies = (
        {k: all_strategies[k] for k in args.strategies if k in all_strategies}
        if args.strategies
        else all_strategies
    )

    # Fixed seed for reproducibility
    random.seed(42)

    tasks_config = [
        cfg for cfg in DEFAULT_TASKS_CONFIG
        if cfg.get("enabled_by_default", True)
    ]
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
    task_kwargs_by_name = build_task_kwargs(args)

    execution_plan = []
    for task_cfg in tasks_config:
        task_name = task_cfg["name"]
        limit = args.limit_tasks or task_cfg["default_limit"]
        for strategy_name, strategy in selected_strategies.items():
            for budget in budgets:
                for repeat_index in range(args.repeat_cells):
                    execution_plan.append(
                        {
                            "task_name": task_name,
                            "limit": limit,
                            "strategy_name": strategy_name,
                            "strategy": strategy,
                            "budget": budget,
                            "repeat_index": repeat_index,
                        }
                    )

    if args.shuffle_cells:
        random.shuffle(execution_plan)

    loaded_tasks = {}
    announced_tasks = set()
    for plan in execution_plan:
        task_name = plan["task_name"]
        limit = plan["limit"]
        strategy_name = plan["strategy_name"]
        strategy = plan["strategy"]
        budget = plan["budget"]
        repeat_index = plan["repeat_index"]

        if task_name not in announced_tasks:
            print(f"\nProcessing Task: {task_name} (Limit: {limit})")
            announced_tasks.add(task_name)

        if task_name not in loaded_tasks:
            try:
                loaded_tasks[task_name] = get_task(
                    task_name,
                    **task_kwargs_by_name.get(task_name, {}),
                )
            except Exception as e:
                print(f"  Error loading task '{task_name}': {e}")
                loaded_tasks[task_name] = None

        task = loaded_tasks[task_name]
        if task is None:
            continue

        print(
            f"  > Strategy: {strategy_name:10} | Budget: {budget:5} | Repeat: {repeat_index + 1}/{args.repeat_cells} | ",
            end="",
            flush=True,
        )

        if (task_name, strategy_name, budget, repeat_index) in completed:
            print("SKIP (already done)")
            continue

        if args.dry_run:
            print("DRY RUN")
            continue

        log_suffix = f"_r{repeat_index + 1}" if args.repeat_cells > 1 else ""
        log_file = os.path.join(
            log_dir, f"{task_name}_{strategy_name}_{budget}{log_suffix}.jsonl"
        )
        logger = JSONLMetricsLogger(log_file)

        runner = TaskRunner(
            task=task,
            strategy=strategy,
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
            logger=logger,
            max_natural_tokens=args.max_natural_tokens,
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
                "repeat_index": repeat_index,
                "combo_log_file": log_file,
                "retrieval_embedding_model": args.retrieval_embedding_model,
                "longbench_chunk_tokens": args.longbench_chunk_tokens,
                "longbench_char_per_token": args.longbench_char_per_token,
                **tokenizer_fn.metadata(),
            }
            if args.max_natural_tokens:
                summary["max_natural_tokens"] = args.max_natural_tokens
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
                            "repeat_index": repeat_index,
                            "combo_log_file": log_file,
                            "retrieval_embedding_model": args.retrieval_embedding_model,
                            "longbench_chunk_tokens": args.longbench_chunk_tokens,
                            "longbench_char_per_token": args.longbench_char_per_token,
                            **tokenizer_fn.metadata(),
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
        help="Limit number of items per task (0 = use task defaults)",
    )
    parser.add_argument(
        "--limit-budgets",
        type=int,
        default=0,
        help="Limit number of budget tiers to evaluate (0 = all 3)",
    )
    parser.add_argument(
        "--budgets",
        nargs="+",
        type=int,
        default=None,
        help="Explicit active-context budgets to evaluate, e.g. --budgets 2048 8192 32768",
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
        help="Specific task names to run (default: swe long memory tau; longmem is opt-in)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to pass in the API payload (required for Ollama; omit for llama.cpp)",
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default=None,
        help="Environment variable containing the API key for the LLM endpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="auto",
        help="Explicit tokenizer ID for budget enforcement, e.g. Qwen/Qwen2.5-1.5B-Instruct or tiktoken:cl100k_base",
    )
    parser.add_argument(
        "--retrieval-embedding-model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Embedding model name for RAG/lean_retrieval/Letta ablations",
    )
    parser.add_argument(
        "--longbench-chunk-tokens",
        type=int,
        default=None,
        help="Override LongBench context chunk size in tokens for chunking ablations",
    )
    parser.add_argument(
        "--longbench-char-per-token",
        type=int,
        default=4,
        help="Character-per-token heuristic used when chunking LongBench context",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=512,
        help="Maximum generated tokens for each LLM call",
    )
    parser.add_argument(
        "--max-natural-tokens",
        type=int,
        default=None,
        help="Filter to items whose uncompressed natural prompt is at or below this token count",
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
    parser.add_argument(
        "--repeat-cells",
        type=int,
        default=1,
        help="Number of repeated runs per task/strategy/budget cell for latency and stability measurement",
    )
    parser.add_argument(
        "--shuffle-cells",
        action="store_true",
        help="Shuffle task/strategy/budget execution order to reduce warmup and ordering bias",
    )

    args = parser.parse_args()
    run_pilot(args)
