import pytest
from budgetbench.strategies.llmlingua import LLMLinguaStrategy


class DummyPromptCompressor:
    def __init__(self, model_name, use_llmlingua2=True, device_map="cpu"):
        self.model_name = model_name
        self.use_llmlingua2 = use_llmlingua2
        self.device_map = device_map

    def compress_prompt(self, text, rate, force_tokens=None, chunk_end_tokens=None):
        keep_chars = max(1, int(len(text) * rate))
        return {"compressed_prompt": text[:keep_chars]}


@pytest.fixture(autouse=True)
def mock_prompt_compressor(monkeypatch):
    monkeypatch.setattr("budgetbench.strategies.llmlingua.PromptCompressor", DummyPromptCompressor)


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
