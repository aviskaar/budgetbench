import re
from typing import Any, Callable, Dict, List, Optional

from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask
from budgetbench.utils.types import OpenAIMessage


class MemoryUpdateTask(BaseTask):
    """
    Deterministic synthetic memory task with updates, temporal queries, and abstention.

    This is a pilot memory-agent task, not a public benchmark replacement.  It
    gives the harness a controlled exact-match memory family while LongMemEval
    or LoCoMo wiring is pending.
    """

    _NAMES = [
        "Alex",
        "Blair",
        "Casey",
        "Devon",
        "Emery",
        "Finley",
        "Gray",
        "Harper",
        "Indigo",
        "Jordan",
    ]
    _COLORS = ["blue", "green", "violet", "yellow", "red", "teal"]
    _SNACKS = ["pretzels", "mango", "crackers", "almonds", "yogurt", "berries"]
    _CITIES = ["Austin", "Denver", "Boston", "Seattle", "Chicago", "Phoenix"]
    _PROJECTS = ["Atlas", "Beacon", "Cinder", "Delta", "Echo", "Fjord"]

    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        builders = [
            self._build_single_fact,
            self._build_update,
            self._build_temporal_before,
            self._build_preference,
            self._build_abstention,
        ]
        for index in range(30):
            builder = builders[index % len(builders)]
            items.append(builder(index))
        if limit:
            return items[:limit]
        return items

    def _distractors(self, index: int, count: int = 80) -> List[str]:
        rows = []
        for offset in range(count):
            name = self._NAMES[(index + offset) % len(self._NAMES)]
            project = self._PROJECTS[(index + offset) % len(self._PROJECTS)]
            city = self._CITIES[(index + offset) % len(self._CITIES)]
            rows.append(
                f"Distractor memory {offset:02d}: {name} filed project {project} "
                f"from {city} with ticket code T{index:02d}-{offset:02d}."
            )
        return rows

    def _with_id(
        self,
        index: int,
        category: str,
        events: List[str],
        question: str,
        answer: str,
    ) -> Dict[str, Any]:
        return {
            "id": f"memory-{index:03d}",
            "category": category,
            "events": events,
            "question": question,
            "answer": answer,
        }

    def _build_single_fact(self, index: int) -> Dict[str, Any]:
        name = self._NAMES[index % len(self._NAMES)]
        color = self._COLORS[index % len(self._COLORS)]
        events = self._distractors(index, 40)
        events.insert(5, f"Canonical memory: {name}'s favorite color is {color}.")
        events.extend(self._distractors(index + 7, 40))
        return self._with_id(
            index,
            "single_session_fact",
            events,
            f"What is {name}'s favorite color?",
            color,
        )

    def _build_update(self, index: int) -> Dict[str, Any]:
        name = self._NAMES[index % len(self._NAMES)]
        old_city = self._CITIES[index % len(self._CITIES)]
        new_city = self._CITIES[(index + 2) % len(self._CITIES)]
        events = self._distractors(index, 35)
        events.insert(8, f"Profile memory: {name} lives in {old_city}.")
        events.extend(self._distractors(index + 11, 35))
        events.append(f"Update memory: {name} moved to {new_city}; this supersedes prior city records.")
        return self._with_id(
            index,
            "knowledge_update",
            events,
            f"What city does {name} currently live in?",
            new_city,
        )

    def _build_temporal_before(self, index: int) -> Dict[str, Any]:
        name = self._NAMES[index % len(self._NAMES)]
        old_snack = self._SNACKS[index % len(self._SNACKS)]
        new_snack = self._SNACKS[(index + 3) % len(self._SNACKS)]
        events = self._distractors(index, 30)
        events.append(f"January memory: {name}'s preferred snack was {old_snack}.")
        events.extend(self._distractors(index + 17, 30))
        events.append(f"March update: {name}'s preferred snack became {new_snack}.")
        events.extend(self._distractors(index + 23, 20))
        return self._with_id(
            index,
            "temporal_reasoning",
            events,
            f"Before the March update, what snack did {name} prefer?",
            old_snack,
        )

    def _build_preference(self, index: int) -> Dict[str, Any]:
        name = self._NAMES[index % len(self._NAMES)]
        project = self._PROJECTS[index % len(self._PROJECTS)]
        events = self._distractors(index, 45)
        events.insert(20, f"Preference memory: when choosing dashboards, {name} prefers project {project}.")
        events.extend(self._distractors(index + 29, 35))
        return self._with_id(
            index,
            "preference",
            events,
            f"Which project does {name} prefer for dashboards?",
            project,
        )

    def _build_abstention(self, index: int) -> Dict[str, Any]:
        name = self._NAMES[index % len(self._NAMES)]
        events = self._distractors(index, 90)
        return self._with_id(
            index,
            "abstention",
            events,
            f"What is {name}'s private passphrase?",
            "UNKNOWN",
        )

    def format_message(self, item: Dict[str, Any]) -> List[OpenAIMessage]:
        system_prompt = (
            "You answer memory questions from the provided event log. "
            "Use updates when they supersede earlier facts. For questions about "
            "a past time, answer the value at that time. If the event log does "
            "not contain the answer, respond exactly with UNKNOWN. Respond with "
            "only the answer string."
        )
        messages: List[OpenAIMessage] = [{"role": "system", "content": system_prompt}]
        for event in item["events"]:
            messages.append({"role": "user", "content": event})
        messages.append({"role": "user", "content": f"Question: {item['question']}\nAnswer:"})
        return messages

    def natural_prompt_token_count(
        self,
        item: Dict[str, Any],
        tokenizer_fn: Callable[[str], int],
    ) -> int:
        return sum(tokenizer_fn(m.get("content", "")) for m in self.format_message(item))

    def metric_context(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {"memory_category": item["category"]}

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

    def grade(self, prediction: Any, item: Dict[str, Any]) -> bool:
        expected = str(item.get("answer", "")).strip().lower()
        text = str(prediction).strip()
        match = re.search(r"answer\s*:\s*([A-Za-z0-9_-]+)", text, re.IGNORECASE)
        if match:
            text = match.group(1)
        else:
            token_match = re.search(r"[A-Za-z0-9_-]+", text)
            text = token_match.group(0) if token_match else ""
        return text.strip().lower() == expected
