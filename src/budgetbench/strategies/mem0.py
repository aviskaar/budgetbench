import os
import uuid
from typing import List, Optional, Callable
import tiktoken
try:
    from mem0 import Memory
except ImportError:
    # Fallback for environments where mem0 is not installed during build/test collection
    Memory = None

from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class Mem0Strategy(MemoryStrategy):
    """
    Mem0 Strategy (BASE-05).
    Integrates mem0ai to extract and store persistent, graph-based memories.
    """
    def __init__(self, config: Optional[dict] = None, tokenizer_fn: Optional[Callable[[str], int]] = None):
        if Memory is None:
            raise ImportError("mem0ai is not installed. Please install it with 'pip install mem0ai'.")
            
        if config is None:
            # Default local-first config
            config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": f"bb_mem_{uuid.uuid4().hex[:8]}",
                        "path": os.path.join(os.getcwd(), ".mem0_db"),
                    },
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "all-MiniLM-L6-v2",
                    }
                },
                "llm": {
                    "provider": "ollama",
                    "config": {
                        "model": os.environ.get("BUDGETBENCH_MEM0_MODEL", "qwen2.5:14b"),
                        "temperature": 0.0,
                    },
                },
            }
        
        self.memory = Memory.from_config(config)
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self._processed_messages_count = 0
        self.user_id = "benchmark_user"

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def reset(self) -> None:
        """
        Clears the Mem0 memory store.
        """
        try:
            self.memory.reset()
        except Exception:
            # Some versions might not support reset() or it might fail if uninitialized
            pass
        self._processed_messages_count = 0

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        # 1. Add new messages to memory
        # We skip the system prompt (index 0) and the last message (query)
        # We only process messages that haven't been seen yet.
        for i in range(max(1, self._processed_messages_count), len(messages) - 1):
            msg = messages[i]
            try:
                # mem0.add performs extraction using an LLM
                self.memory.add(msg["content"], user_id=self.user_id)
            except Exception as e:
                # Extraction might fail if no LLM is configured or API key is missing.
                # In benchmark mode, we might want to log this but continue.
                pass
        
        self._processed_messages_count = max(0, len(messages) - 1)

        # 2. Search for relevant memories based on the current query
        query_msg = messages[-1]
        try:
            memories = self.memory.search(query_msg["content"], user_id=self.user_id)
        except Exception:
            memories = []

        # 3. Inject memories into system prompt while respecting budget
        system_prompt = messages[0].copy()
        
        # Base tokens: System + Query
        system_tokens = self.tokenizer_fn(system_prompt["content"])
        query_tokens = self.tokenizer_fn(query_msg["content"])
        
        current_tokens = system_tokens + query_tokens
        
        # If even base messages exceed budget, return them as is
        if current_tokens > active_budget:
            return [system_prompt, query_msg]

        # 4. Filter and format memories
        injected_memories = []
        for m in memories:
            # mem0 search results can vary in structure depending on version/provider
            mem_text = m.get("memory", m.get("text", ""))
            if not mem_text:
                continue
                
            formatted_mem = f"- {mem_text}"
            mem_tokens = self.tokenizer_fn(formatted_mem)
            
            # Check if it fits (with a small buffer for the header)
            if current_tokens + mem_tokens + 10 <= active_budget:
                injected_memories.append(formatted_mem)
                current_tokens += mem_tokens
            else:
                break
        
        if injected_memories:
            header = "\n\nRelevant Memories:\n"
            system_prompt["content"] += header + "\n".join(injected_memories)

        return [system_prompt, query_msg]
