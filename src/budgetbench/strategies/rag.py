import uuid
from typing import List, Optional, Callable
import tiktoken
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage

class RAGStrategy(MemoryStrategy):
    """
    Episodic RAG Strategy (BASE-03).
    Stores message history in a vector store and retrieves relevant context.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", tokenizer_fn: Optional[Callable[[str], int]] = None):
        # We use a persistent=False client for in-memory operation
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.Client(Settings(allow_reset=True))
        self.collection_name = f"history_{uuid.uuid4().hex}"
        self.collection = self.client.create_collection(name=self.collection_name)
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self._indexed_ids = set()

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))

    def reset(self) -> None:
        """
        Clears the vector index.
        """
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection_name = f"history_{uuid.uuid4().hex}"
        self.collection = self.client.create_collection(name=self.collection_name)
        self._indexed_ids = set()

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        # 1. Calculate total tokens
        token_counts = [self.tokenizer_fn(m.get("content", "")) for m in messages]
        total_tokens = sum(token_counts)

        if total_tokens <= active_budget:
            return messages

        # 2. Identify System Prompt and Query
        # We assume messages[0] is system and messages[-1] is query
        system_prompt = messages[0]
        query_msg = messages[-1]
        
        system_tokens = token_counts[0]
        query_tokens = token_counts[-1]
        
        # If even system and query exceed budget, return them anyway as a baseline
        # (The enforcer will catch it if needed, but we provide the minimal context)
        if system_tokens + query_tokens > active_budget:
            return [system_prompt, query_msg]

        # 3. Index intermediate messages (if not already indexed)
        # We index messages[1:-1]
        # In a real scenario, we might want to avoid re-embedding everything if called multiple times.
        # But for the benchmark, we can afford it or use a simple cache.
        for i in range(1, len(messages) - 1):
            msg = messages[i]
            # Use a deterministic ID based on content and index to avoid duplicates
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

        # 4. Retrieve relevant messages
        remaining_budget = active_budget - system_tokens - query_tokens
        
        query_embedding = self.model.encode(query_msg["content"]).tolist()
        
        # Retrieve all indexed messages, then filter by budget
        all_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=len(self._indexed_ids)
        )
        
        # 5. Select based on relevance (descending) until budget is hit
        selected_metadatas = []
        current_tokens = 0
        
        if all_results["metadatas"] and all_results["metadatas"][0]:
            metadatas = all_results["metadatas"][0]
            documents = all_results["documents"][0]
            
            for i in range(len(metadatas)):
                doc = documents[i]
                msg_tokens = self.tokenizer_fn(doc)
                if current_tokens + msg_tokens <= remaining_budget:
                    meta = metadatas[i].copy()
                    meta["content"] = doc
                    selected_metadatas.append(meta)
                    current_tokens += msg_tokens
                # Continue trying to fit smaller relevant messages if current one is too big
        
        # 6. Re-order chronologically to maintain coherence
        selected_metadatas.sort(key=lambda x: x["index"])
        
        retrieved_messages = [{"role": m["role"], "content": m["content"]} for m in selected_metadatas]

        return [system_prompt] + retrieved_messages + [query_msg]
