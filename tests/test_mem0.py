import pytest
from unittest.mock import MagicMock, patch
from src.budgetbench.strategies.mem0 import Mem0Strategy

def test_mem0_strategy_initialization():
    with patch("src.budgetbench.strategies.mem0.Memory") as mock_memory:
        mock_instance = MagicMock()
        mock_memory.from_config.return_value = mock_instance
        strategy = Mem0Strategy()
        assert strategy is not None
        mock_memory.from_config.assert_called_once()

def test_mem0_strategy_reset():
    with patch("src.budgetbench.strategies.mem0.Memory") as mock_memory:
        mock_instance = MagicMock()
        mock_memory.from_config.return_value = mock_instance
        strategy = Mem0Strategy()
        strategy.reset()
        mock_instance.reset.assert_called_once()

def test_mem0_strategy_call():
    with patch("src.budgetbench.strategies.mem0.Memory") as mock_memory:
        mock_instance = MagicMock()
        mock_memory.from_config.return_value = mock_instance
        # Mock search results
        mock_instance.search.return_value = [
            {"memory": "User's favorite color is blue."},
            {"memory": "User likes pizza."}
        ]
        
        strategy = Mem0Strategy()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is my favorite color?"}
        ]
        
        result = strategy(messages, active_budget=100)
        
        # Check if memories were injected
        # The strategy should inject memories into the system prompt or as a new message
        content_blob = " ".join([m["content"] for m in result])
        assert "favorite color is blue" in content_blob
        
        # Check if original messages are preserved
        assert result[-1]["content"] == "What is my favorite color?"
        assert result[0]["role"] == "system"
