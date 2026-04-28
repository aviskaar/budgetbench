import pytest
from budgetbench.utils.types import OpenAIMessage, BUDGET_TIERS
from budgetbench.core.exceptions import BudgetExceededError

def test_types_and_tiers_exist():
    assert BUDGET_TIERS == [2048, 4096, 8192, 16384, 32768]
    
    # Check OpenAIMessage structure (via typing hints if possible or just usage)
    msg: OpenAIMessage = {"role": "user", "content": "hello"}
    assert msg["role"] == "user"

def test_exception_exists():
    with pytest.raises(BudgetExceededError):
        raise BudgetExceededError("test")
