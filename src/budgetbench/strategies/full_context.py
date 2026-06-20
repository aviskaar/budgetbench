from typing import List

from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage


class FullContextStrategy(MemoryStrategy):
    """
    Baseline that passes the task's natural formatted prompt through unchanged.

    Budget enforcement stays in the runner.  This makes infeasible full-context
    prompts visible as ordinary budget violations instead of hiding them behind
    strategy-specific truncation.
    """

    def __call__(
        self,
        messages: List[OpenAIMessage],
        active_budget: int,
    ) -> List[OpenAIMessage]:
        return list(messages)

    def reset(self) -> None:
        pass
