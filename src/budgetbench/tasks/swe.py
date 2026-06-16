import re
from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask


class SWEBenchTask(BaseTask):
    def __init__(self, dataset_name: str = "princeton-nlp/SWE-bench_Verified", split: str = "test"):
        self.dataset_name = dataset_name
        self.split = split
        self._dataset = None

    @property
    def dataset(self):
        import datasets
        if self._dataset is None:
            self._dataset = datasets.load_dataset(self.dataset_name, split=self.split)
        return self._dataset

    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        ds = self.dataset
        if limit:
            ds = ds.select(range(min(limit, len(ds))))
        return list(ds)

    def _get_system_prompt(self) -> str:
        return (
            "You are an expert software engineer. You will be given a bug report and any available hints. "
            "Your task is to produce a minimal unified diff patch that fixes the bug. "
            "Output ONLY the patch in unified diff format, starting with 'diff --git'. "
            "Do not include any explanation or prose outside the diff block."
        )

    def _extract_patch(self, content: str) -> str:
        """Extract the unified diff block from the model's response."""
        # Try a fenced code block first
        fenced = re.search(r'```(?:diff|patch)?\s*\n(.*?)```', content, re.DOTALL)
        if fenced:
            block = fenced.group(1)
            if 'diff --git' in block:
                return block.strip()

        # Fall back to finding "diff --git" and taking everything from there
        idx = content.find('diff --git')
        if idx != -1:
            return content[idx:].strip()

        return ""

    def _parse_patch(self, patch: str) -> Dict[str, List[str]]:
        """Return {filename: [changed_lines]} parsed from a unified diff."""
        files: Dict[str, List[str]] = {}
        current_file = None
        for line in patch.splitlines():
            if line.startswith('diff --git '):
                parts = line.split()
                if len(parts) >= 4:
                    current_file = parts[3].lstrip('b/')
                    files[current_file] = []
            elif current_file is not None:
                if line.startswith('+++ ') or line.startswith('--- '):
                    continue
                if line.startswith('+') or line.startswith('-'):
                    files[current_file].append(line)
        return files

    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger,
    ) -> str:
        problem_statement = item.get("problem_statement", "")
        hints = item.get("hints_text", "").strip()

        user_content = f"Bug report:\n{problem_statement}"
        if hints:
            user_content += f"\n\nHints:\n{hints}"
        user_content += "\n\nProduce the patch now."

        messages: List[OpenAIMessage] = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": user_content},
        ]

        response = run_evaluation_task(
            messages=messages,
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

        return self._extract_patch(content)

    def grade(self, patch: str, item: Dict[str, Any]) -> float:
        """
        Deterministic patch similarity against the gold patch.

        Scores file-level recall (40%) + changed-line overlap (60%).
        Returns 0.0–1.0.
        """
        gold_patch = item.get("patch", "")
        if not gold_patch:
            return 0.0
        if not patch or not patch.strip():
            return 0.0

        gold_files = self._parse_patch(gold_patch)
        pred_files = self._parse_patch(patch)

        if not gold_files:
            return 0.0

        gold_file_set = set(gold_files)
        pred_file_set = set(pred_files)
        matched_files = gold_file_set & pred_file_set

        file_recall = len(matched_files) / len(gold_file_set)
        if file_recall == 0.0:
            return 0.0

        # Line overlap on matched files only
        total_gold_lines = sum(len(gold_files[f]) for f in matched_files)
        if total_gold_lines == 0:
            return 0.4 * file_recall

        matched_lines = sum(
            len(set(gold_files[f]) & set(pred_files[f]))
            for f in matched_files
        )
        line_score = matched_lines / total_gold_lines

        return 0.4 * file_recall + 0.6 * line_score
