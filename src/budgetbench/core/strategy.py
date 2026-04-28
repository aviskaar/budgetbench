from abc import ABC, abstractmethod
from typing import List
from ..utils.types import OpenAIMessage

class MemoryStrategy(ABC):
    """
    Abstract base class for memory strategies.
    Takes an OpenAI-formatted message list and returns a budget-compliant list.
    """
    @abstractmethod
    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        """
        Process messages to fit within the active_budget.
        """
        pass
