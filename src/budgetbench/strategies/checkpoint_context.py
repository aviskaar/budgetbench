from typing import Callable, Dict, List, Optional

import tiktoken

from ..core.strategy import MemoryStrategy
from ..utils.types import OpenAIMessage


class CheckpointContextStrategy(MemoryStrategy):
    """
    Hybrid checkpoint baseline.

    Keeps a compact extractive checkpoint for early turns, a recent tail for
    recency-sensitive information, and a small set of retrieved evidence turns
    selected by lexical overlap with the current query.
    """

    def __init__(
        self,
        tokenizer_fn: Optional[Callable[[str], int]] = None,
        checkpoint_fraction: float = 0.25,
        recent_fraction: float = 0.35,
    ):
        self.tokenizer_fn = tokenizer_fn or self._default_tokenizer
        self.checkpoint_fraction = checkpoint_fraction
        self.recent_fraction = recent_fraction

    def _default_tokenizer(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))

    def reset(self) -> None:
        pass

    def _terms(self, text: str) -> List[str]:
        return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token]

    def _compact_snippet(self, message: OpenAIMessage, max_words: int = 20) -> str:
        content = str(message.get("content", "")).strip().replace("\n", " ")
        words = content.split()
        if len(words) > max_words:
            content = " ".join(words[:max_words]) + " ..."
        return f"{message.get('role', 'user')}: {content}"

    def _score_message(self, query_terms: List[str], message: OpenAIMessage, position: int, max_position: int) -> float:
        text = str(message.get("content", "")).lower()
        tokens = self._terms(text)
        if not tokens:
            return 0.0
        overlap = len(set(query_terms) & set(tokens)) / max(1, len(set(query_terms)))
        has_number = 1.0 if any(ch.isdigit() for ch in text) else 0.0
        recency = position / max(1, max_position)
        return 0.65 * overlap + 0.2 * recency + 0.15 * has_number

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
        if system_tokens + query_tokens >= active_budget:
            return [system_prompt, query_msg]

        candidate_messages = messages[1:-1]
        if not candidate_messages:
            return [system_prompt, query_msg]

        query_terms = self._terms(str(query_msg.get("content", "")))
        max_position = len(candidate_messages)

        recent_budget = max(8, int(active_budget * self.recent_fraction))
        checkpoint_budget = max(8, int(active_budget * self.checkpoint_fraction))
        evidence_budget = max(8, active_budget - system_tokens - query_tokens - recent_budget - checkpoint_budget)

        recent_messages: List[OpenAIMessage] = []
        used_recent = 0
        for message, tokens in zip(reversed(candidate_messages), reversed(token_counts[1:-1])):
            if used_recent + tokens > recent_budget:
                continue
            recent_messages.append(message)
            used_recent += tokens
        recent_messages.reverse()
        recent_ids = {id(message) for message in recent_messages}

        remaining_messages = [
            (index, message, token_counts[index])
            for index, message in enumerate(candidate_messages, start=1)
            if id(message) not in recent_ids
        ]
        checkpoint_source = remaining_messages[: max(1, len(remaining_messages) // 2)]
        evidence_source = remaining_messages[len(checkpoint_source):]

        checkpoint_lines = []
        checkpoint_tokens = 0
        for index, message, tokens in checkpoint_source:
            snippet = self._compact_snippet(message, max_words=18)
            snippet_tokens = self.tokenizer_fn(snippet) + 2
            if checkpoint_tokens + snippet_tokens > checkpoint_budget:
                break
            checkpoint_lines.append(snippet)
            checkpoint_tokens += snippet_tokens

        checkpoint_message: Optional[OpenAIMessage] = None
        if checkpoint_lines:
            checkpoint_message = {
                "role": "system",
                "content": "Checkpoint:\n" + "\n".join(checkpoint_lines),
            }

        scored_evidence = []
        for index, message, tokens in evidence_source:
            score = self._score_message(query_terms, message, index, max_position)
            scored_evidence.append((score, index, message, tokens))

        scored_evidence.sort(key=lambda item: (-item[0], -item[1]))
        selected_evidence: List[OpenAIMessage] = []
        used_evidence = 0
        for score, index, message, tokens in scored_evidence:
            if used_evidence + tokens > evidence_budget:
                continue
            selected_evidence.append(message)
            used_evidence += tokens

        selected_evidence.sort(key=lambda message: candidate_messages.index(message) + 1)

        output: List[OpenAIMessage] = [system_prompt]
        if checkpoint_message:
            output.append(checkpoint_message)
        output.extend(recent_messages)
        output.extend(selected_evidence)
        output.append(query_msg)
        return output
