import math
import re
from typing import Callable, List, Optional

import tiktoken
from sentence_transformers import SentenceTransformer

from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage


class LeanRetrievalStrategy(MemoryStrategy):
    """
    Hybrid retrieval baseline using dense, lexical, recency, and salience scores.

    Unlike the Chroma-backed RAG baseline, this strategy is stateless within an
    item and ranks the formatted message list directly.  It is intended as a
    lightweight "lean context" selector for active-budget comparisons.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        tokenizer_fn: Optional[Callable[[str], int]] = None,
        dense_weight: float = 0.45,
        lexical_weight: float = 0.35,
        recency_weight: float = 0.10,
        salience_weight: float = 0.10,
    ):
        self.model = SentenceTransformer(model_name)
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight
        self.recency_weight = recency_weight
        self.salience_weight = salience_weight

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))

    def reset(self) -> None:
        pass

    def _terms(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-z0-9_]+", text.lower())

    def _as_vector(self, value) -> List[float]:
        if hasattr(value, "tolist"):
            value = value.tolist()
        return [float(x) for x in value]

    def _cosine(self, left: List[float], right: List[float]) -> float:
        if not left or not right:
            return 0.0
        limit = min(len(left), len(right))
        numerator = sum(left[i] * right[i] for i in range(limit))
        left_norm = math.sqrt(sum(x * x for x in left[:limit]))
        right_norm = math.sqrt(sum(x * x for x in right[:limit]))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _lexical_scores(self, query_terms: List[str], doc_terms: List[List[str]]) -> List[float]:
        query_set = set(query_terms)
        if not query_set or not doc_terms:
            return [0.0 for _ in doc_terms]

        doc_sets = [set(terms) for terms in doc_terms]
        document_count = len(doc_sets)
        dfs = {
            term: sum(1 for terms in doc_sets if term in terms)
            for term in query_set
        }
        idfs = {
            term: math.log((document_count + 1.0) / (dfs[term] + 0.5))
            for term in query_set
        }
        denominator = sum(idfs.values()) or 1.0
        return [
            sum(idfs[term] for term in query_set if term in terms) / denominator
            for terms in doc_sets
        ]

    def _salience_score(self, content: str, terms: List[str]) -> float:
        if not terms:
            return 0.0
        unique_ratio = len(set(terms)) / max(1, len(terms))
        has_numbers = 1.0 if re.search(r"\d", content) else 0.0
        has_named_markers = 1.0 if re.search(r"\b[A-Z][a-z]{2,}\b", content) else 0.0
        return min(1.0, 0.6 * unique_ratio + 0.2 * has_numbers + 0.2 * has_named_markers)

    def __call__(self, messages: List[OpenAIMessage], active_budget: int) -> List[OpenAIMessage]:
        if not messages:
            return []

        token_counts = [self.tokenizer_fn(m.get("content", "")) for m in messages]
        if sum(token_counts) <= active_budget:
            return messages

        system_prompt = messages[0]
        query_msg = messages[-1]
        system_tokens = token_counts[0]
        query_tokens = token_counts[-1]

        if system_tokens + query_tokens > active_budget:
            return [system_prompt, query_msg]

        candidates = []
        for index in range(1, len(messages) - 1):
            content = messages[index].get("content", "")
            candidates.append(
                {
                    "index": index,
                    "role": messages[index].get("role", "user"),
                    "content": content,
                    "tokens": token_counts[index],
                    "terms": self._terms(content),
                }
            )

        if not candidates:
            return [system_prompt, query_msg]

        query_terms = self._terms(query_msg.get("content", ""))
        lexical_scores = self._lexical_scores(query_terms, [c["terms"] for c in candidates])
        query_vector = self._as_vector(self.model.encode(query_msg.get("content", "")))

        max_index = max(c["index"] for c in candidates) or 1
        for position, candidate in enumerate(candidates):
            dense_vector = self._as_vector(self.model.encode(candidate["content"]))
            dense_score = (self._cosine(query_vector, dense_vector) + 1.0) / 2.0
            recency_score = candidate["index"] / max_index
            salience_score = self._salience_score(candidate["content"], candidate["terms"])
            candidate["score"] = (
                self.dense_weight * dense_score
                + self.lexical_weight * lexical_scores[position]
                + self.recency_weight * recency_score
                + self.salience_weight * salience_score
            )

        remaining_budget = active_budget - system_tokens - query_tokens
        selected = []
        used_tokens = 0
        for candidate in sorted(candidates, key=lambda c: c["score"], reverse=True):
            if used_tokens + candidate["tokens"] <= remaining_budget:
                selected.append(candidate)
                used_tokens += candidate["tokens"]

        selected.sort(key=lambda c: c["index"])
        retrieved_messages = [
            {"role": c["role"], "content": c["content"]}
            for c in selected
        ]
        return [system_prompt] + retrieved_messages + [query_msg]
