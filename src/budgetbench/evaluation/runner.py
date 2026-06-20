from typing import List, Callable, Any, Dict, Optional
from budgetbench.tasks.base import BaseTask
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.utils.types import OpenAIMessage


class _ContextMetricsLogger:
    def __init__(self, logger: MetricsLogger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context

    def log_metrics(self, metrics: Dict[str, Any]):
        merged = {**self.context, **metrics}
        self.logger.log_metrics(merged)


class TaskRunner:
    def __init__(
        self,
        task: BaseTask,
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        logger: MetricsLogger,
        max_natural_tokens: Optional[int] = None,
    ):
        self.task = task
        self.strategy = strategy
        self.llm_client = llm_client
        self.tokenizer_fn = tokenizer_fn
        self.logger = logger
        self.max_natural_tokens = max_natural_tokens

    def _item_id(self, item: Dict[str, Any]) -> str:
        return (
            item.get("_budgetbench_item_id")
            or item.get("item_id")
            or item.get("id")
            or item.get("question_id")
            or item.get("instance_id")
            or "unknown"
        )

    def _supports_natural_prompt_tokens(self) -> bool:
        return callable(getattr(type(self.task), "natural_prompt_token_count", None))

    def _natural_prompt_tokens(self, item: Dict[str, Any]) -> Optional[int]:
        if not self._supports_natural_prompt_tokens():
            return item.get("_budgetbench_natural_tokens")
        return int(self.task.natural_prompt_token_count(item, self.tokenizer_fn))

    def _metric_context(self, item: Dict[str, Any]) -> Dict[str, Any]:
        hook = getattr(self.task, "metric_context", None)
        if not callable(hook):
            return {}
        context = hook(item)
        return dict(context) if context else {}

    def _loggable_prediction(self, prediction: Any) -> Any:
        if isinstance(prediction, (str, int, float, bool)) or prediction is None:
            return prediction
        if isinstance(prediction, (list, tuple)):
            return [self._loggable_prediction(value) for value in prediction]
        if isinstance(prediction, dict):
            return {
                str(key): self._loggable_prediction(value)
                for key, value in prediction.items()
            }
        return str(prediction)

    def _load_items(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        if self.max_natural_tokens is None:
            return self.task.get_dataset(limit=limit)

        if not self._supports_natural_prompt_tokens():
            raise ValueError(
                f"{self.task.__class__.__name__} does not support "
                "--max-natural-tokens filtering"
            )

        filtered = []
        for item in self.task.get_dataset(limit=None):
            natural_tokens = self._natural_prompt_tokens(item)
            if natural_tokens is None or natural_tokens > self.max_natural_tokens:
                continue

            item_with_tokens = dict(item)
            item_with_tokens["_budgetbench_natural_tokens"] = natural_tokens
            filtered.append(item_with_tokens)
            if limit and len(filtered) >= limit:
                break

        return filtered

    def run_evaluation(self, max_tokens: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs the evaluation for the configured task and strategy.
        """
        items = self._load_items(limit=limit)
        results = []

        for item in items:
            item_id = self._item_id(item)
            natural_tokens = item.get("_budgetbench_natural_tokens")
            if natural_tokens is None:
                natural_tokens = self._natural_prompt_tokens(item)
            context = {"item_id": item_id, **self._metric_context(item)}
            if natural_tokens is not None:
                context["natural_prompt_tokens"] = natural_tokens
            item_logger = _ContextMetricsLogger(self.logger, context)

            try:
                prediction = self.task.run(
                    item=item,
                    strategy=self.strategy,
                    llm_client=self.llm_client,
                    tokenizer_fn=self.tokenizer_fn,
                    max_tokens=max_tokens,
                    logger=item_logger
                )
                
                is_correct = self.task.grade(prediction, item)
                
                results.append({
                    "item_id": item_id,
                    "prediction": prediction,
                    "is_correct": is_correct
                })
                
                item_logger.log_metrics({
                    "quality": float(is_correct),
                    "task_success": float(is_correct),
                    "prediction": self._loggable_prediction(prediction),
                })
                
            except Exception as e:
                item_logger.log_metrics({
                    "error": f"Evaluation error on item: {str(e)}",
                })
                results.append({
                    "item_id": item_id,
                    "error": str(e),
                    "is_correct": False
                })

        return results
