import json
import os
import re
import string
from typing import Any, Callable, Dict, List, Optional

from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask
from budgetbench.utils.types import OpenAIMessage


class LongMemEvalTask(BaseTask):
    """
    Adapter for the official LongMemEval JSON format.

    LongMemEval's official QA scoring uses an LLM judge.  This adapter provides
    a deterministic normalized-containment pilot scorer so BudgetBench can run
    budget-strategy sweeps without a remote judge.  Paper claims using this
    task must label the scorer as approximate unless official evaluation logs
    are added.
    """

    DEFAULT_PATH = os.path.join("data", "longmemeval_oracle.json")
    ENV_PATH = "BUDGETBENCH_LONGMEMEVAL_PATH"

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.environ.get(self.ENV_PATH) or self.DEFAULT_PATH
        self._dataset: Optional[List[Dict[str, Any]]] = None

    def _load_dataset(self) -> List[Dict[str, Any]]:
        if self._dataset is not None:
            return self._dataset
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(
                f"LongMemEval data not found at {self.data_path}. "
                f"Set {self.ENV_PATH} or download longmemeval_oracle.json from "
                "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned"
            )
        with open(self.data_path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("LongMemEval data must be a JSON list")
        self._dataset = data
        return data

    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self._load_dataset()
        if not limit:
            return items

        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            by_category.setdefault(self._category(item), []).append(item)

        sampled: List[Dict[str, Any]] = []
        category_names = sorted(by_category)
        while len(sampled) < limit and any(by_category.values()):
            for category in category_names:
                if not by_category[category]:
                    continue
                sampled.append(by_category[category].pop(0))
                if len(sampled) >= limit:
                    break
        return sampled

    def _category(self, item: Dict[str, Any]) -> str:
        question_id = str(item.get("question_id", ""))
        if question_id.endswith("_abs"):
            return "abstention"
        return str(item.get("question_type", "unknown")).replace("-", "_")

    def format_message(self, item: Dict[str, Any]) -> List[OpenAIMessage]:
        system_prompt = (
            "You answer LongMemEval memory questions from timestamped chat "
            "history. Use the provided dates when reasoning about updates or "
            "temporal order. Answer with only the shortest correct phrase."
        )
        messages: List[OpenAIMessage] = [{"role": "system", "content": system_prompt}]

        dates = item.get("haystack_dates") or []
        session_ids = item.get("haystack_session_ids") or []
        sessions = item.get("haystack_sessions") or []
        for session_index, session in enumerate(sessions):
            date = dates[session_index] if session_index < len(dates) else "unknown-date"
            session_id = (
                session_ids[session_index]
                if session_index < len(session_ids)
                else f"session-{session_index}"
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"[Session {session_index + 1} | {date} | {session_id}]",
                }
            )
            for turn in session:
                role = turn.get("role", "user")
                if role not in {"system", "user", "assistant"}:
                    role = "user"
                content = str(turn.get("content", ""))
                messages.append({"role": role, "content": f"[{date}] {content}"})

        question_date = item.get("question_date", "unknown-date")
        messages.append(
            {
                "role": "user",
                "content": (
                    f"[Question date: {question_date}]\n"
                    f"Question: {item.get('question', '')}\nAnswer:"
                ),
            }
        )
        return messages

    def natural_prompt_token_count(
        self,
        item: Dict[str, Any],
        tokenizer_fn: Callable[[str], int],
    ) -> int:
        return sum(tokenizer_fn(m.get("content", "")) for m in self.format_message(item))

    def metric_context(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "memory_category": self._category(item),
            "longmem_question_id": item.get("question_id"),
            "longmem_grader": "normalized_contains",
        }

    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger,
    ) -> str:
        response = run_evaluation_task(
            messages=self.format_message(item),
            strategy=strategy,
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
            max_tokens=max_tokens,
            logger=logger,
        )
        if isinstance(response, dict):
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif hasattr(response, "choices"):
            content = response.choices[0].message.content
        else:
            content = str(response)
        return content.strip()

    def _normalize(self, text: Any) -> str:
        text = str(text).lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text.translate(str.maketrans("", "", string.punctuation)).strip()

    def grade(self, prediction: Any, item: Dict[str, Any]) -> bool:
        expected = self._normalize(item.get("answer", ""))
        predicted = self._normalize(prediction)
        if not expected:
            return False
        return expected in predicted or predicted in expected
