from typing import List, Optional, Callable
import tiktoken
from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class TruncationStrategy(MemoryStrategy):
    """
    FIFO Truncation Strategy.
    Keeps the first message (system prompt) and as many recent messages as possible.
    """
    def __init__(self, tokenizer_fn: Optional[Callable[[str], int]] = None):
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        # Calculate total tokens
        token_counts = [self.tokenizer_fn(m.get("content", "")) for m in messages]
        total_tokens = sum(token_counts)

        if total_tokens <= active_budget:
            return messages

        # Budget exceeded. 
        # Always keep the first message (assuming system prompt)
        system_prompt = messages[0]
        system_tokens = token_counts[0]
        
        if system_tokens > active_budget:
            # Even system prompt is too big. 
            # In a real scenario we might want to truncate it too, but per requirements 
            # we keep it. If it's over budget, return just it (enforcement will still fail later).
            return [system_prompt]

        remaining_budget = active_budget - system_tokens
        
        # Take messages from newest to oldest (skipping the first one which is already handled)
        result_messages = []
        current_tokens = 0
        
        for i in range(len(messages) - 1, 0, -1):
            msg_tokens = token_counts[i]
            if current_tokens + msg_tokens <= remaining_budget:
                result_messages.insert(0, messages[i])
                current_tokens += msg_tokens
            else:
                break
                
        return [system_prompt] + result_messages

    def reset(self) -> None:
        pass
