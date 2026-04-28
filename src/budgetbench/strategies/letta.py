import uuid
import os
from typing import List, Optional, Callable, Dict
import tiktoken
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class LettaStrategy(MemoryStrategy):
    """
    Letta (MemGPT) Strategy (BASE-04).
    Simulates agentic memory with Core Memory, Recall Memory (FIFO), and Archival Memory (RAG).
    """
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        tokenizer_fn: Optional[Callable[[str], int]] = None,
        core_memory_ratio: float = 0.2,
        recall_memory_ratio: float = 0.4
    ):
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.Client(Settings(allow_reset=True))
        self.collection_name = f"archival_{uuid.uuid4().hex}"
        self.collection = self.client.create_collection(name=self.collection_name)
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self._indexed_ids = set()
        
        self.core_memory_ratio = core_memory_ratio
        self.recall_memory_ratio = recall_memory_ratio
        
        # State for Core Memory (simulated)
        self.core_memory = {"persona": "", "human": ""}

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def reset(self) -> None:
        """
        Clears the archival index and core memory.
        """
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection_name = f"archival_{uuid.uuid4().hex}"
        self.collection = self.client.create_collection(name=self.collection_name)
        self._indexed_ids = set()
        self.core_memory = {"persona": "", "human": ""}

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        # 1. Identify components
        system_prompt = messages[0].copy()
        query_msg = messages[-1]
        history = messages[1:-1]
        
        # 2. Update Core Memory (Simple heuristic: first user message often contains persona info)
        if not self.core_memory["human"] and len(history) > 0:
            for msg in history:
                if msg["role"] == "user":
                    self.core_memory["human"] = msg["content"][:200] # Cap core memory
                    break

        # 3. Index new history into Archival Memory
        for i, msg in enumerate(history):
            msg_id = f"msg_{i}_{hash(msg['content'])}"
            if msg_id not in self._indexed_ids:
                embedding = self.model.encode(msg["content"]).tolist()
                self.collection.add(
                    embeddings=[embedding],
                    documents=[msg["content"]],
                    metadatas=[{"role": msg["role"], "index": i}],
                    ids=[msg_id]
                )
                self._indexed_ids.add(msg_id)

        # 4. Budget Allocation
        core_budget = int(active_budget * self.core_memory_ratio)
        recall_budget = int(active_budget * self.recall_memory_ratio)
        
        # Fixed costs
        system_tokens = self.tokenizer_fn(system_prompt["content"])
        query_tokens = self.tokenizer_fn(query_msg["content"])
        
        # 5. Build Core Memory Block
        core_text = f"\nCORE MEMORY:\n<persona>{self.core_memory['persona']}</persona>\n<human>{self.core_memory['human']}</human>\n"
        core_tokens = self.tokenizer_fn(core_text)
        
        # Integrate Core Memory into System Prompt
        system_prompt["content"] += core_text
        total_fixed = system_tokens + core_tokens + query_tokens
        
        if total_fixed > active_budget:
            # Fallback if even fixed content exceeds budget
            return [system_prompt, query_msg]

        available_budget = active_budget - total_fixed
        
        # 6. Retrieve from Archival Memory (RAG)
        archival_budget = available_budget - recall_budget
        if archival_budget < 0:
            archival_budget = 0
            recall_budget = available_budget
            
        retrieved_msgs = []
        if archival_budget > 0 and self._indexed_ids:
            query_embedding = self.model.encode(query_msg["content"]).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(10, len(self._indexed_ids))
            )
            
            current_archival_tokens = 0
            if results["metadatas"] and results["metadatas"][0]:
                for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                    tokens = self.tokenizer_fn(doc)
                    if current_archival_tokens + tokens <= archival_budget:
                        retrieved_msgs.append({
                            "role": meta["role"],
                            "content": f"[Archival] {doc}",
                            "index": meta["index"]
                        })
                        current_archival_tokens += tokens

        # 7. Fill Recall Memory (FIFO)
        # Last N messages that fit in recall_budget
        recall_msgs = []
        current_recall_tokens = 0
        for msg in reversed(history):
            tokens = self.tokenizer_fn(msg["content"])
            if current_recall_tokens + tokens <= recall_budget:
                recall_msgs.insert(0, msg)
                current_recall_tokens += tokens
            else:
                break
        
        # 8. Combine and return
        # Combine retrieved and recall, avoiding duplicates if possible
        # For simplicity, we just concatenate and let the LLM handle it, 
        # but we'll sort them to maintain some order.
        
        # Note: Letta usually has a clear separation between 'context' (FIFO) and 'archival results'.
        # We'll put archival results before the FIFO recall.
        
        final_history = retrieved_msgs + recall_msgs
        # Remove metadata 'index' if present from sorting/filtering
        cleaned_history = []
        for m in final_history:
            cleaned_history.append({"role": m["role"], "content": m["content"]})
            
        return [system_prompt] + cleaned_history + [query_msg]
