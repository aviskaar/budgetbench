from typing import Callable, List
from budgetbench.utils.types import OpenAIMessage
from budgetbench.core.exceptions import BudgetExceededError


def enforce_budget(messages: List[OpenAIMessage], tokenizer_fn: Callable[[str], int], max_tokens: int) -> int:
    """
    Counts tokens in messages and raises BudgetExceededError if limit is hit.
    
    Args:
        messages: List of OpenAI-format messages.
        tokenizer_fn: Function that takes a string and returns token count.
        max_tokens: Maximum allowed tokens.
        
    Returns:
        Total token count.
        
    Raises:
        BudgetExceededError: If total tokens exceed max_tokens.
    """
    total_tokens = sum(tokenizer_fn(m.get("content", "")) for m in messages)
    
    if total_tokens > max_tokens:
        raise BudgetExceededError(f"Budget exceeded: {total_tokens} > {max_tokens}")
        
    return total_tokens
