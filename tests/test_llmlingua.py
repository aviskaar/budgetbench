import pytest
from budgetbench.strategies.llmlingua import LLMLinguaStrategy

def test_llmlingua_strategy_init():
    strategy = LLMLinguaStrategy()
    assert strategy is not None

def test_llmlingua_strategy_call():
    strategy = LLMLinguaStrategy()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "The quick brown fox jumps over the lazy dog. " * 10},
        {"role": "user", "content": "What was that about a fox?"}
    ]
    # Huge input, small budget
    processed = strategy(messages, active_budget=50)
    assert len(processed) >= 2
    # Check that some compression happened or at least it returned something
    assert processed[0]["role"] == "system"
    assert processed[-1]["role"] == "user"

def test_llmlingua_strategy_reset():
    strategy = LLMLinguaStrategy()
    strategy.reset()
