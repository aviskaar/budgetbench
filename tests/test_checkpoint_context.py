from budgetbench.strategies.checkpoint_context import CheckpointContextStrategy


def _word_count(text: str) -> int:
    return len(text.split())


def test_checkpoint_context_builds_hybrid_view():
    strategy = CheckpointContextStrategy(tokenizer_fn=_word_count, checkpoint_fraction=0.5, recent_fraction=0.2)
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "alpha beta gamma delta epsilon"},
        {"role": "assistant", "content": "irrelevant filler one two three"},
        {"role": "user", "content": "checkpoint candidate with important name and date"},
        {"role": "assistant", "content": "more filler content"},
        {"role": "user", "content": "query wants important name and date"},
    ]

    result = strategy(messages, active_budget=24)

    assert result[0]["role"] == "system"
    assert result[-1]["content"] == "query wants important name and date"
    assert any(msg["content"].startswith("Checkpoint:") for msg in result)
    assert any("important name and date" in msg["content"] for msg in result)


def test_checkpoint_context_returns_input_when_within_budget():
    strategy = CheckpointContextStrategy(tokenizer_fn=_word_count)
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "short history"},
        {"role": "assistant", "content": "short reply"},
        {"role": "user", "content": "final query"},
    ]

    result = strategy(messages, active_budget=20)

    assert result == messages
