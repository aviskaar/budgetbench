import pytest
from budgetbench.strategies.letta import LettaStrategy

def test_letta_strategy_init():
    strategy = LettaStrategy()
    assert strategy is not None

def test_letta_strategy_call():
    strategy = LettaStrategy()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My name is Alice."},
        {"role": "assistant", "content": "Nice to meet you, Alice!"},
        {"role": "user", "content": "What is my name?"}
    ]
    # Small budget
    processed = strategy(messages, active_budget=200)
    assert len(processed) >= 2
    assert processed[0]["role"] == "system"
    assert processed[-1]["role"] == "user"
    assert "Alice" in str(processed)

def test_letta_strategy_reset():
    strategy = LettaStrategy()
    strategy.reset()
    # verify it doesn't crash
