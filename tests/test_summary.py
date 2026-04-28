import pytest
from budgetbench.strategies.summary import SummaryBufferStrategy
from budgetbench.utils.types import OpenAIMessage
import tiktoken

def mock_tokenizer(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def mock_llm_client(messages: list) -> dict:
    # Very simple mock summarizer: just returns "Summary: " + first 10 chars of content of user messages
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    summary = "Summary: " + "; ".join(user_msgs)
    return {"choices": [{"message": {"content": summary}}]}

def test_summary_buffer_under_budget():
    strategy = SummaryBufferStrategy(llm_client=mock_llm_client, tokenizer_fn=mock_tokenizer)
    messages = [
        {"role": "system", "content": "System prompt."},
        {"role": "user", "content": "Hello!"}
    ]
    result = strategy(messages, 100)
    # When under budget, it might still prepend an empty summary if not handled carefully, 
    # but ideally it should just return the messages if no summary exists.
    assert len(result) == 2
    assert result == messages

def test_summary_buffer_over_budget():
    strategy = SummaryBufferStrategy(llm_client=mock_llm_client, tokenizer_fn=mock_tokenizer)
    messages = [
        {"role": "system", "content": "System."}, # 1 token
        {"role": "user", "content": "Message 1."}, # 3 tokens
        {"role": "user", "content": "Message 2."}, # 3 tokens
        {"role": "user", "content": "Message 3."}  # 3 tokens
    ]
    # Total ~10 tokens
    
    # Set budget to 8. 
    # System(1) + Newest(3) = 4. 
    # We need to summarize M1 and M2.
    
    result = strategy(messages, 8)
    
    # Expected result:
    # 1. System Prompt
    # 2. Summary of M1, M2
    # 3. M3
    
    assert len(result) == 3
    assert result[0] == messages[0] # System
    assert "Summary:" in result[1]["content"]
    assert result[2] == messages[3] # M3

def test_summary_buffer_reset():
    strategy = SummaryBufferStrategy(llm_client=mock_llm_client, tokenizer_fn=mock_tokenizer)
    strategy.summary = "Existing summary"
    strategy.reset()
    assert strategy.summary == ""
