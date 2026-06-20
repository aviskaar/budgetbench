import pytest

from budgetbench.strategies.lean_retrieval import LeanRetrievalStrategy
from budgetbench.tasks.long import LongBenchV2Task


class DummyEmbedding(list):
    def tolist(self):
        return list(self)


class DummySentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, text):
        lowered = text.lower()
        if "favorite color" in lowered or "blue" in lowered:
            return DummyEmbedding([1.0, 0.0, 0.0])
        if "pizza" in lowered:
            return DummyEmbedding([0.0, 1.0, 0.0])
        if "paris" in lowered or "france" in lowered:
            return DummyEmbedding([0.0, 0.0, 1.0])
        if "rome" in lowered or "italy" in lowered:
            return DummyEmbedding([0.0, 0.0, 0.5])
        return DummyEmbedding([0.0, 0.0, 0.0])


@pytest.fixture(autouse=True)
def mock_sentence_transformer(monkeypatch):
    monkeypatch.setattr(
        "budgetbench.strategies.lean_retrieval.SentenceTransformer",
        DummySentenceTransformer,
    )


def test_lean_retrieval_initialization():
    strategy = LeanRetrievalStrategy()
    assert strategy is not None


def test_lean_retrieval_selects_relevant_memory_under_budget():
    strategy = LeanRetrievalStrategy(tokenizer_fn=lambda text: max(1, len(text.split())))
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My favorite color is blue."},
        {"role": "assistant", "content": "I will remember that."},
        {"role": "user", "content": "I like pizza."},
        {"role": "assistant", "content": "Pizza is delicious."},
        {"role": "user", "content": "What is my favorite color?"},
    ]

    result = strategy(messages, active_budget=18)

    content_blob = " ".join(m["content"] for m in result).lower()
    assert "blue" in content_blob
    assert "what is my favorite color" in content_blob
    assert result[0]["role"] == "system"
    assert result[-1]["content"] == "What is my favorite color?"


def test_lean_retrieval_preserves_chronological_order():
    strategy = LeanRetrievalStrategy(
        tokenizer_fn=lambda text: max(1, len(text.split())),
        recency_weight=0.0,
        salience_weight=0.0,
    )
    messages = [
        {"role": "system", "content": "System."},
        {"role": "user", "content": "Paris is in France."},
        {"role": "assistant", "content": "Rome is in Italy."},
        {"role": "user", "content": "France has Paris as capital."},
        {"role": "user", "content": "What is the capital of France?"},
    ]

    result = strategy(messages, active_budget=18)
    selected = [m["content"] for m in result[1:-1]]

    assert selected == sorted(
        selected,
        key=lambda content: [m["content"] for m in messages].index(content),
    )


def test_lean_retrieval_longbench_chunked():
    task = LongBenchV2Task()
    item = {
        "context": ("irrelevant " * 400)
        + "Paris is the capital of France. "
        + ("filler " * 400),
        "question": "What is the capital of France?",
        "choice_A": "London",
        "choice_B": "Paris",
        "choice_C": "Berlin",
        "choice_D": "Rome",
        "answer": "B",
    }
    messages = task.format_message(item, budget=1024)
    strategy = LeanRetrievalStrategy(tokenizer_fn=lambda text: max(1, len(text) // 4))

    result = strategy(messages, active_budget=1400)

    assert result[0]["role"] == "system"
    assert result[-1]["content"].startswith("Question: What is the capital of France?")
    assert any("Paris is the capital of France" in msg["content"] for msg in result[1:-1])
