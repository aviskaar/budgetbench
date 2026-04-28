import pytest
from budgetbench.strategies.truncation import TruncationStrategy
from budgetbench.utils.types import OpenAIMessage
import tiktoken

def mock_tokenizer(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def test_truncation_under_budget():
    strategy = TruncationStrategy(tokenizer_fn=mock_tokenizer)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
    # Small budget but enough
    result = strategy(messages, 100)
    assert result == messages

def test_truncation_over_budget():
    strategy = TruncationStrategy(tokenizer_fn=mock_tokenizer)
    messages = [
        {"role": "system", "content": "System prompt."},
        {"role": "user", "content": "Message 1 (oldest)."},
        {"role": "user", "content": "Message 2."},
        {"role": "user", "content": "Message 3 (newest)."}
    ]
    
    # Calculate tokens
    tokens = [mock_tokenizer(m["content"]) for m in messages]
    print(f"DEBUG: tokens={tokens}")
    # [3, 6, 3, 6] -> Total 18
    
    # Tokens are [3, 7, 4, 7]
    # To keep System (3) + M3 (7) + M2 (4) = 14 tokens
    result = strategy(messages, 14)
    assert len(result) == 3
    assert result[0] == messages[0] # System
    assert result[1] == messages[2] # M2
    assert result[2] == messages[3] # M3

def test_truncation_preserves_system_even_if_over_budget():
    strategy = TruncationStrategy(tokenizer_fn=mock_tokenizer)
    messages = [
        {"role": "system", "content": "Very long system prompt that takes most of the budget."},
        {"role": "user", "content": "Hello"}
    ]
    # System prompt tokens
    sys_tokens = mock_tokenizer(messages[0]["content"])
    
    # Budget only enough for system prompt
    result = strategy(messages, sys_tokens + 1)
    assert len(result) == 2 # System + Hello (if Hello is 1 token)
    
    result = strategy(messages, sys_tokens)
    assert len(result) == 1
    assert result[0] == messages[0]

def test_truncation_reset():
    strategy = TruncationStrategy()
    strategy.reset() # Should not raise
