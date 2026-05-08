import tiktoken
from typing import List, Optional, Callable
try:
    from llmlingua import PromptCompressor
except ImportError:
    PromptCompressor = None

from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class LLMLinguaStrategy(MemoryStrategy):
    """
    LLMLingua-2 Strategy (BASE-06).
    Uses token-level pruning to compress prompts into a target budget.
    """
    def __init__(
        self, 
        model_name: str = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
        device: str = "cpu",
        tokenizer_fn: Optional[Callable[[str], int]] = None
    ):
        if PromptCompressor is None:
            raise ImportError("llmlingua is not installed. Please install it with 'pip install llmlingua'.")
            
        self.compressor = PromptCompressor(
            model_name=model_name, 
            use_llmlingua2=True, 
            device_map=device
        )
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def reset(self) -> None:
        """
        LLMLingua is mostly stateless, but we provide reset for consistency.
        """
        pass

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        if len(messages) == 1:
            return messages

        # 1. Identify components
        system_prompt = messages[0]
        query_msg = messages[-1]
        history = messages[1:-1]
        
        system_tokens = self.tokenizer_fn(system_prompt["content"])
        query_tokens = self.tokenizer_fn(query_msg["content"])
        
        fixed_tokens = system_tokens + query_tokens
        
        if fixed_tokens >= active_budget:
            # If fixed tokens already exceed budget, we can't do much history compression
            # return just them (or just the query if even that is too much)
            return [system_prompt, query_msg]

        target_history_tokens = active_budget - fixed_tokens
        
        # 2. Combine history into a single string for compression
        # We include role markers to help the compressor understand the structure
        context_parts = []
        for msg in history:
            context_parts.append(f"{msg['role'].upper()}: {msg['content']}")
        
        context_text = "\n".join(context_parts)
        history_tokens = self.tokenizer_fn(context_text)
        
        if history_tokens <= target_history_tokens:
            return messages

        # 3. Compress History
        # Calculate compression rate
        rate = target_history_tokens / history_tokens
        # LLMLingua-2 uses 'rate' or 'target_token'
        
        try:
            result = self.compressor.compress_prompt(
                context_text,
                rate=rate,
                force_tokens=['\n', 'USER:', 'ASSISTANT:', 'SYSTEM:'],
                chunk_end_tokens=['.', '?', '!', '\n'],
            )
            compressed_history_text = result.get("compressed_prompt", "")
        except Exception as e:
            # Fallback to simple truncation if compression fails
            compressed_history_text = context_text[:target_history_tokens * 4] # very rough
            
        # 4. Wrap back into messages
        # Since LLMLingua-2 smashes everything together, we return it as a single "user" message 
        # or try to split it. For benchmarking, a single compressed context message is often used.
        compressed_msg = {
            "role": "user",
            "content": f"[Compressed Context]\n{compressed_history_text}"
        }
        
        return [system_prompt, compressed_msg, query_msg]
