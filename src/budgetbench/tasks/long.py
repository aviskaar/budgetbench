import datasets
import re
from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask

class LongBenchV2Task(BaseTask):
    NATURAL_PROMPT_BUDGET = 32768

    def __init__(self, dataset_name: str = "THUDM/LongBench-v2", split: str = "train"):
        self.dataset_name = dataset_name
        self.split = split
        self._dataset = None

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = datasets.load_dataset(self.dataset_name, split=self.split)
        return self._dataset
    
    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        ds = self.dataset
        if limit:
            ds = ds.select(range(min(limit, len(ds))))
        items = []
        for index, item in enumerate(ds):
            row = dict(item)
            row.setdefault(
                "_budgetbench_item_id",
                f"{self.dataset_name}:{self.split}:{index}",
            )
            items.append(row)
        return items

    def format_message(self, item: Dict[str, Any], budget: int = 8192) -> List[OpenAIMessage]:
        context = item.get("context", "")
        question = item.get("question", "")
        
        # LongBench v2 schema: context, question, choice_A, choice_B, choice_C, choice_D, answer
        choices_text = ""
        for char in ['A', 'B', 'C', 'D']:
            val = item.get(f"choice_{char}")
            if val:
                choices_text += f"\n{char}: {val}"
        
        system_prompt = "You are a helpful assistant. Answer the following multiple choice question based on the provided context. Respond only with the letter of the correct answer (A, B, C, or D)."
        question_msg: OpenAIMessage = {"role": "user", "content": f"Question: {question}{choices_text}"}

        chunk_size = min(budget // 4, 512)  # tokens
        chunk_chars = chunk_size * 4  # chars (4-char/token heuristic)

        if len(context) <= chunk_chars:
            context_messages: List[OpenAIMessage] = [
                {"role": "user", "content": f"Context:\n{context}"}
            ]
        else:
            context_messages = []
            for i in range(0, len(context), chunk_chars):
                chunk_text = context[i : i + chunk_chars]
                context_messages.append({
                    "role": "user",
                    "content": f"Context part {i // chunk_chars + 1}:\n{chunk_text}"
                })

        return [{"role": "system", "content": system_prompt}] + context_messages + [question_msg]

    def natural_prompt_token_count(
        self,
        item: Dict[str, Any],
        tokenizer_fn: Callable[[str], int],
    ) -> int:
        messages = self.format_message(item, budget=self.NATURAL_PROMPT_BUDGET)
        return sum(tokenizer_fn(m.get("content", "")) for m in messages)

    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger
    ) -> str:
        messages = self.format_message(item, budget=max_tokens)
        response = run_evaluation_task(
            messages=messages,
            strategy=strategy,
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
            max_tokens=max_tokens,
            logger=logger
        )
        
        if isinstance(response, dict):
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif hasattr(response, "choices"):
            content = response.choices[0].message.content
        else:
            content = str(response)
            
        return content.strip()

    def grade(self, prediction: str, item: Any) -> bool:
        """
        Performs deterministic MCQ matching (ignoring case/whitespace).
        """
        if isinstance(item, dict):
            ground_truth = item.get("answer", "")
        else:
            ground_truth = str(item)
        
        pred = prediction.strip().upper()
        if len(pred) > 1:
            match = re.search(r'\b[A-D]\b', pred)
            if match:
                pred = match.group()
            else:
                # Try first character if no word boundary match
                pred = pred[0]
        
        return pred == ground_truth.strip().upper()
