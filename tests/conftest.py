import pytest
from typing import List, Dict, Any

@pytest.fixture
def tokenizer_fn():
    """A simple function that returns the number of words in a string (proxy for tokens)."""
    def _tokenizer(text: str) -> int:
        return len(text.split())
    return _tokenizer

@pytest.fixture
def llm_client():
    """A dummy LLM client that returns a fixed response."""
    def _client(messages: List[Dict[str, Any]]) -> str:
        return "Dummy response"
    return _client
