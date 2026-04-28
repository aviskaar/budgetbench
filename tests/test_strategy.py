import pytest
from typing import List
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.utils.types import OpenAIMessage

class DummyStrategy(MemoryStrategy):
    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        # Simple dummy: return all messages if under budget, else empty (just for test)
        return messages

def test_memory_strategy_abc():
    strategy = DummyStrategy()
    messages: List[OpenAIMessage] = [{"role": "user", "content": "hello"}]
    result = strategy(messages, 2048)
    assert result == messages

def test_cannot_instantiate_abc():
    with pytest.raises(TypeError):
        MemoryStrategy()
