import pytest
from typing import List
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.utils.types import OpenAIMessage

class DummyStrategy(MemoryStrategy):
    def __init__(self):
        self.reset_called = False

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        # Simple dummy: return all messages if under budget, else empty (just for test)
        return messages

    def reset(self):
        self.reset_called = True

def test_memory_strategy_abc():
    strategy = DummyStrategy()
    messages: List[OpenAIMessage] = [{"role": "user", "content": "hello"}]
    result = strategy(messages, 2048)
    assert result == messages
    
    strategy.reset()
    assert strategy.reset_called is True

def test_cannot_instantiate_abc():
    with pytest.raises(TypeError):
        MemoryStrategy()
