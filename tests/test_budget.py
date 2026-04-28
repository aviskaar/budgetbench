import pytest
from budgetbench.utils.types import OpenAIMessage, BUDGET_TIERS
from budgetbench.core.exceptions import BudgetExceededError
from budgetbench.core.budget import enforce_budget

def test_types_and_tiers_exist():
    assert BUDGET_TIERS == [2048, 4096, 8192, 16384, 32768]
    
    # Check OpenAIMessage structure (via typing hints if possible or just usage)
    msg: OpenAIMessage = {"role": "user", "content": "hello"}
    assert msg["role"] == "user"

def test_exception_exists():
    with pytest.raises(BudgetExceededError):
        raise BudgetExceededError("test")

def test_enforce_budget_success():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"}
    ]
    # Dummy tokenizer: length of content
    def tokenizer(text): return len(text)
    
    total = enforce_budget(messages, tokenizer, 100)
    assert total == 5 + 8

def test_enforce_budget_failure():
    messages = [
        {"role": "user", "content": "a" * 50},
        {"role": "assistant", "content": "b" * 60}
    ]
    def tokenizer(text): return len(text)
    
    with pytest.raises(BudgetExceededError) as excinfo:
        enforce_budget(messages, tokenizer, 100)
    assert "Budget exceeded" in str(excinfo.value)
    assert "110 > 100" in str(excinfo.value)
