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
            return self._sanitize_patch(content[idx:].strip())

        return ""

    def _sanitize_patch(self, patch: str) -> str:
        """
        Keep only complete diff sections with valid headers.

        This avoids exporting markdown fences, truncated prose tails, or
        half-finished diff fragments that the official SWE harness rejects
        immediately as malformed patches.
        """
        patch = patch.replace("\r\n", "\n").strip()
        if not patch.startswith("diff --git "):
            return ""

        lines = patch.splitlines()
        sections: List[List[str]] = []
        current: List[str] = []

        for line in lines:
            if line.startswith("```"):
                break
            if line.startswith("diff --git "):
                if current:
                    sections.append(current)
                current = [line]
            elif current:
                current.append(line)
        if current:
            sections.append(current)

        kept_sections: List[str] = []
        seen_files = set()
        for section in sections:
            if len(section) < 3:
                continue
            diff_parts = section[0].split()
            if len(diff_parts) < 4:
                continue
            diff_a = diff_parts[2]
            diff_b = diff_parts[3]
            header_start = 1
            if section[1].startswith("index "):
                header_start = 2
            if len(section) <= header_start + 1:
                continue
            minus_line = section[header_start]
            plus_line = section[header_start + 1]
            if not minus_line.startswith("--- "):
                continue
            if not plus_line.startswith("+++ "):
                continue
            if minus_line.split(maxsplit=1)[1] != diff_a:
                continue
            if plus_line.split(maxsplit=1)[1] != diff_b:
                continue
            file_key = diff_b[2:] if diff_b.startswith("b/") else diff_b
            if file_key in seen_files:
                continue

            last_safe_idx = header_start + 1
            saw_hunk = False
            for idx, line in enumerate(section[header_start + 2 :], start=header_start + 2):
                if line.startswith("@@ " ) or line == "@@":
                    saw_hunk = True
                    last_safe_idx = idx
                    continue
                if not saw_hunk:
                    # Allow metadata lines between file headers and first hunk.
                    if line.startswith(("new file mode ", "deleted file mode ", "similarity index ", "rename from ", "rename to ")):
                        last_safe_idx = idx
                        continue
                    continue
                if (
                    line.startswith((" ", "+", "-", "\\"))
                    or line == ""
                ):
                    last_safe_idx = idx
                    continue
                # Stop at the first clearly invalid tail line.
                break

            trimmed = section[: last_safe_idx + 1]
            if any(line.startswith("@@") for line in trimmed):
                kept_sections.append("\n".join(trimmed).rstrip())
                seen_files.add(file_key)

        if not kept_sections:
            return ""
        return "\n".join(kept_sections).strip() + "\n"

    def _fit_user_content(
        self,
        system_prompt: str,
        user_content: str,
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
    ) -> str:
        system_tokens = tokenizer_fn(system_prompt)
        if system_tokens >= max_tokens:
            return ""

        available = max_tokens - system_tokens
        if tokenizer_fn(user_content) <= available:
            return user_content

        prefix = "Bug report:\n"
        if user_content.startswith(prefix):
            body = user_content[len(prefix):]
            reserved = tokenizer_fn(prefix)
            if reserved < available:
                available_for_body = max(1, available - reserved)
                lo, hi = 0, len(body)
                best = ""
                while lo <= hi:
                    mid = (lo + hi) // 2
                    candidate_body = body[:mid].rstrip()
                    candidate = prefix + candidate_body
                    if tokenizer_fn(candidate) <= available:
                        best = candidate
                        lo = mid + 1
                    else:
                        hi = mid - 1
                if best:
                    return best

        lo, hi = 0, len(user_content)
        best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = user_content[:mid].rstrip()
            if tokenizer_fn(candidate) <= available:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        return best

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

        system_prompt = self._get_system_prompt()
        user_content = self._fit_user_content(
            system_prompt=system_prompt,
            user_content=user_content,
            tokenizer_fn=tokenizer_fn,
            max_tokens=max_tokens,
        )

        messages: List[OpenAIMessage] = [
            {"role": "system", "content": system_prompt},
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
