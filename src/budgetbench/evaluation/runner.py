from typing import List, Callable, Any, Dict, Optional
from budgetbench.tasks.base import BaseTask
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.utils.types import OpenAIMessage

class TaskRunner:
    def __init__(
        self,
        task: BaseTask,
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        logger: MetricsLogger
    ):
        self.task = task
        self.strategy = strategy
        self.llm_client = llm_client
        self.tokenizer_fn = tokenizer_fn
        self.logger = logger

    def run_evaluation(self, max_tokens: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs the evaluation for the configured task and strategy.
        """
        items = self.task.get_dataset(limit=limit)
        results = []

        for item in items:
            try:
                prediction = self.task.run(
                    item=item,
                    strategy=self.strategy,
                    llm_client=self.llm_client,
                    tokenizer_fn=self.tokenizer_fn,
                    max_tokens=max_tokens,
                    logger=self.logger
                )
                
                is_correct = self.task.grade(prediction, item)
                
                results.append({
                    "item_id": item.get("id") or item.get("instance_id") or "unknown",
                    "prediction": prediction,
                    "is_correct": is_correct
                })
                
                self.logger.log_metrics({
                    "quality": float(is_correct),
                    "task_success": float(is_correct)
                })
                
            except Exception as e:
                self.logger.log_metrics({"error": f"Evaluation error on item: {str(e)}"})
                results.append({
                    "item_id": item.get("id") or item.get("instance_id") or "unknown",
                    "error": str(e),
                    "is_correct": False
                })

        return results
