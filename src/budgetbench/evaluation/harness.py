import time
import hashlib
import json
from typing import List, Callable, Any, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.core.budget import enforce_budget
from budgetbench.core.exceptions import BudgetExceededError
from budgetbench.evaluation.metrics import MetricsLogger


def _tokenizer_metadata(tokenizer_fn: Callable[[str], int]) -> dict:
    metadata = getattr(tokenizer_fn, "metadata", None)
    if callable(metadata):
        return dict(metadata())
    return {}


def _prompt_hash(messages: List[OpenAIMessage]) -> str:
    payload = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_evaluation_task(
    messages: List[OpenAIMessage],
    strategy: MemoryStrategy,
    llm_client: Callable[[List[OpenAIMessage]], Any],
    tokenizer_fn: Callable[[str], int],
    max_tokens: int,
    logger: MetricsLogger,
    max_retries: int = 3
) -> Any:
    """
    Orchestrates a single evaluation task with budget enforcement and retries.
    """
    strategy.reset()
    violations = 0
    start_time = time.time()
    last_error = None
    peak_budget = 0
    last_prompt_hash = None
    last_token_count = None
    tokenizer_metadata = _tokenizer_metadata(tokenizer_fn)
    
    for attempt in range(max_retries):
        try:
            # 1. Apply memory strategy
            processed_messages = strategy(messages, max_tokens)
            prompt_hash = _prompt_hash(processed_messages)
            token_count = sum(tokenizer_fn(m.get("content", "")) for m in processed_messages)
            last_prompt_hash = prompt_hash
            last_token_count = token_count
            logger.log_metrics(
                {
                    "event": "prompt_audit",
                    "attempt": attempt,
                    "budget": max_tokens,
                    "processed_prompt_hash": prompt_hash,
                    "processed_prompt_messages": processed_messages,
                    "processed_prompt_token_count": token_count,
                    "processed_prompt_within_budget": token_count <= max_tokens,
                    **tokenizer_metadata,
                }
            )
            
            # 2. Enforce budget
            token_count = enforce_budget(processed_messages, tokenizer_fn, max_tokens)
            peak_budget = max(peak_budget, token_count)
            
            # 3. Call LLM
            response = llm_client(processed_messages)
            
            # 4. Record budget/latency metrics (quality logged by caller after grading)
            duration = time.time() - start_time
            metrics = {
                "used_budget": token_count,
                "peak_budget": peak_budget,
                "violation_rate": violations / (attempt + 1),
                "tokens_per_task": token_count,
                "duration": duration,
                "retries": attempt,
                "processed_prompt_hash": prompt_hash,
                "processed_prompt_token_count": token_count,
                **tokenizer_metadata,
            }
            logger.log_metrics(metrics)
            
            return response
            
        except BudgetExceededError as e:
            violations += 1
            last_error = e
            # Logic for peak budget even on failure
            try:
                # We can't use processed_messages here if it wasn't returned, but strategy should return it.
                # If enforce_budget failed, it means processed_messages exists.
                # Let's re-calculate tokens without raising error to get peak.
                token_count = sum(tokenizer_fn(m.get("content", "")) for m in processed_messages)
                peak_budget = max(peak_budget, token_count)
            except:
                pass
            continue
            
    # If we reached here, all retries failed
    duration = time.time() - start_time
    metrics = {
        "quality": 0.0,
        "used_budget": 0,
        "peak_budget": peak_budget,
        "violation_rate": 1.0,
        "tokens_per_task": 0,
        "duration": duration,
        "retries": max_retries,
        "status": "failed",
        "processed_prompt_hash": last_prompt_hash,
        "processed_prompt_token_count": last_token_count,
        **tokenizer_metadata,
    }
    logger.log_metrics(metrics)
    
    if last_error:
        raise last_error
    raise BudgetExceededError(f"Task failed after {max_retries} retries")
