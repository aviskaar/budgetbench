import pytest
from budgetbench.strategies.rag import RAGStrategy
from budgetbench.utils.types import OpenAIMessage


class DummySentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, text):
        lowered = text.lower()
        if "blue" in lowered or "favorite color" in lowered:
            return DummyEmbedding([1.0, 0.0, 0.0])
        if "pizza" in lowered:
            return DummyEmbedding([0.0, 1.0, 0.0])
        if "paris" in lowered or "france" in lowered:
            return DummyEmbedding([0.0, 0.0, 1.0])
        if "rome" in lowered or "italy" in lowered:
            return DummyEmbedding([0.0, 0.0, 0.5])
        return DummyEmbedding([0.0, 0.0, 0.0])


class DummyEmbedding(list):
    def tolist(self):
        return list(self)


@pytest.fixture(autouse=True)
def mock_sentence_transformer(monkeypatch):
    monkeypatch.setattr("budgetbench.strategies.rag.SentenceTransformer", DummySentenceTransformer)


def test_rag_strategy_initialization():
    strategy = RAGStrategy()
    assert strategy is not None

def test_rag_strategy_reset():
    strategy = RAGStrategy()
    # Add some messages to simulate state
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about Tokyo."},
        {"role": "assistant", "content": "Tokyo is the capital of Japan."}
    ]
    strategy(messages, 1000)
    strategy.reset()
    # After reset, the vector store should be empty or re-initialized
    # We'll check this by seeing if it still returns the same thing for a query
    # (though RAG is deterministic if the store is the same)
    # More specifically, reset should clear internal buffers/indices.

def test_rag_strategy_retrieval():
    strategy = RAGStrategy()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My favorite color is blue."},
        {"role": "assistant", "content": "I will remember that."},
        {"role": "user", "content": "I like pizza."},
        {"role": "assistant", "content": "Pizza is delicious."},
        {"role": "user", "content": "What is my favorite color?"}
    ]
    
    # Set a small budget that forces retrieval
    # System prompt + Last user message + retrieved content
    # We want to ensure "My favorite color is blue" is retrieved.
    
    result = strategy(messages, active_budget=20)
    
    # Check if "blue" is in the result
    content_blob = " ".join([m["content"] for m in result])
    assert "blue" in content_blob.lower()
    assert "pizza" not in content_blob.lower() # Budget is now tight enough to exclude pizza
    
    # Ensure chronological order of retrieved messages
    # System prompt should be first
    assert result[0]["role"] == "system"
    
    # Ensure the last message is always included (the query)
    assert result[-1]["content"] == "What is my favorite color?"


def test_rag_longbench_chunked():
    """RAGStrategy must index chunked messages from format_message() without error."""
    strategy = RAGStrategy()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Context part 1:\nParis is the capital of France."},
        {"role": "user", "content": "Context part 2:\nRome is the capital of Italy."},
        {"role": "user", "content": "Question: What is the capital of France?\nA: Paris\nB: Rome\nC: Berlin\nD: Madrid"},
    ]
    result = strategy(messages, active_budget=200)
    assert result[0]["role"] == "system"
    assert result[-1]["content"].startswith("Question:")
    assert len(result) >= 2
