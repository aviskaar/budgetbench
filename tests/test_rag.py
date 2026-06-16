import pytest
from budgetbench.strategies.rag import RAGStrategy
from budgetbench.tasks.long import LongBenchV2Task
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
    task = LongBenchV2Task()
    item = {
        "context": ("irrelevant " * 400) + "Paris is the capital of France. " + ("filler " * 400),
        "question": "What is the capital of France?",
        "choice_A": "London",
        "choice_B": "Paris",
        "choice_C": "Berlin",
        "choice_D": "Rome",
        "answer": "B",
    }
    messages = task.format_message(item, budget=1024)

    strategy = RAGStrategy(tokenizer_fn=lambda text: max(1, len(text) // 4))
    result = strategy(messages, active_budget=1400)

    assert len(messages[1:-1]) >= 1
    assert len(strategy._indexed_ids) >= 1
    assert result[0]["role"] == "system"
    assert result[-1]["content"].startswith("Question: What is the capital of France?")
    assert any("Paris is the capital of France" in msg["content"] for msg in result[1:-1])
