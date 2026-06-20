from abc import ABC, abstractmethod
from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger

class BaseTask(ABC):
    @abstractmethod
    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns a list of task items to evaluate."""
        pass

    @abstractmethod
    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger
    ) -> Any:
        """Executes the task for a single item."""
        pass

    @abstractmethod
    def grade(self, prediction: Any, item: Dict[str, Any]) -> bool:
        """Grades the prediction against the item's ground truth."""
        pass

    def metric_context(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Optional per-item metadata to attach to raw metric rows."""
        return {}
