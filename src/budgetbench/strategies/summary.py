from typing import List, Optional, Callable, Any
import tiktoken
from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class SummaryBufferStrategy(MemoryStrategy):
    """
    Summary-Buffer Strategy.
    Summarizes evicted context using an LLM and prepends it to the messages.
    """
    def __init__(
        self, 
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Optional[Callable[[str], int]] = None,
        summary_prompt: str = "Summarize the following conversation history concisely:"
    ):
        self.llm_client = llm_client
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self.summary_prompt = summary_prompt
        self.summary = ""

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def reset(self) -> None:
        self.summary = ""

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        # Current messages including summary if it exists
        working_messages = list(messages)
        if self.summary:
            # Prepend summary after system prompt (or at the beginning if no system prompt)
            summary_msg: OpenAIMessage = {
                "role": "system", 
                "content": f"Context Summary: {self.summary}"
            }
            if working_messages[0].get("role") == "system":
                working_messages.insert(1, summary_msg)
            else:
                working_messages.insert(0, summary_msg)

        # Calculate total tokens
        token_counts = [self.tokenizer_fn(m.get("content", "")) for m in working_messages]
        total_tokens = sum(token_counts)

        if total_tokens <= active_budget:
            return working_messages

        # Over budget. Need to evict and summarize.
        # Always keep the first message (System Prompt)
        system_prompt = working_messages[0]
        system_tokens = token_counts[0]
        
        # We also want to keep the N newest messages that fit in the budget
        # and summarize EVERYTHING else (including previous summary if it exists).
        
        # Let's find how many newest messages we can keep.
        keep_indices = []
        current_tokens = system_tokens
        
        # We need to leave some room for the summary itself. 
        # For simplicity, let's assume summary takes ~10% of budget or at least 100 tokens.
        summary_reserve = min(active_budget // 10, 200)
        usable_budget = active_budget - summary_reserve
        
        if usable_budget < system_tokens:
            usable_budget = system_tokens # Minimum is system prompt
            
        for i in range(len(working_messages) - 1, 0, -1):
            msg_tokens = token_counts[i]
            if current_tokens + msg_tokens <= usable_budget:
                keep_indices.append(i)
                current_tokens += msg_tokens
            else:
                break
        
        keep_indices.sort()
        
        # Messages to evict and summarize are those NOT in keep_indices and NOT the system prompt
        evict_indices = [i for i in range(1, len(working_messages)) if i not in keep_indices]
        
        if not evict_indices:
            # Should not happen if total_tokens > active_budget, but safety first
            return working_messages[:1] + [working_messages[i] for i in keep_indices]

        to_summarize = [working_messages[i] for i in evict_indices]
        
        # Call LLM to summarize
        summary_request_messages = [
            {"role": "system", "content": self.summary_prompt},
            {"role": "user", "content": "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])}
        ]
        
        response = self.llm_client(summary_request_messages)
        
        # Extract summary from response
        if isinstance(response, dict) and "choices" in response:
            new_summary_content = response["choices"][0]["message"]["content"]
        else:
            # Handle other client response formats if needed
            new_summary_content = str(response)
            
        self.summary = new_summary_content
        
        # Construct final message list
        summary_msg = {
            "role": "system",
            "content": f"Context Summary: {self.summary}"
        }
        
        return [system_prompt, summary_msg] + [working_messages[i] for i in keep_indices]
