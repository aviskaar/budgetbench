from budgetbench.strategies.full_context import FullContextStrategy


def test_full_context_returns_prompt_unchanged():
    strategy = FullContextStrategy()
    messages = [
        {"role": "system", "content": "System prompt."},
        {"role": "user", "content": "Natural task prompt."},
    ]

    result = strategy(messages, active_budget=1)

    assert result == messages
    assert result is not messages


def test_full_context_reset_is_noop():
    strategy = FullContextStrategy()
    strategy.reset()
