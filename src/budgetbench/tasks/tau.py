from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask

try:
    import tau2.registry as _tau2_registry
    TAU2_AVAILABLE = True
except ImportError:
    _tau2_registry = None
    TAU2_AVAILABLE = False


class TauBenchTask(BaseTask):
    def __init__(self, domain: str = "all", split: str = "test"):
        self.domain = domain
        self.split = split

    def _domains(self) -> List[str]:
        if self.domain == "all":
            return ["retail", "airline"]
        return [self.domain]

    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if not TAU2_AVAILABLE:
            raise ImportError(
                "tau2-bench is not installed. Install from "
                "git+https://github.com/sierra-research/tau2-bench@v0.2.0 and set "
                "TAU2_DATA_DIR to the checkout data directory."
            )
        items: List[Dict[str, Any]] = []
        for domain in self._domains():
            try:
                loader = _tau2_registry.registry.get_tasks_loader(domain)
                tasks = loader()
            except FileNotFoundError as e:
                raise ImportError(
                    "tau2-bench data files are not available. Set TAU2_DATA_DIR "
                    "to the tau2-bench checkout data directory."
                ) from e
            for task in tasks:
                items.append({
                    "id": f"{domain}:{task.id}",
                    "domain": domain,
                    "scenario": str(task.user_scenario),
                    "evaluation_criteria": (
                        str(task.evaluation_criteria)
                        if task.evaluation_criteria is not None
                        else ""
                    ),
                })
        if limit:
            items = items[:limit]
        return items

    def _get_system_prompt(self) -> str:
        return (
            f"You are a helpful assistant for the {self.domain} domain. "
            "You have access to tools to help the user. "
            "Always respond with a JSON object containing 'thought' and 'tool_calls' if you want to use a tool, "
            "or 'thought' and 'response' if you want to answer the user."
        )

    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger,
        max_turns: int = 15
    ) -> Dict[str, Any]:
        if not TAU2_AVAILABLE:
            raise ImportError(
                "tau2-bench is not installed. Install from "
                "git+https://github.com/sierra-research/tau2-bench@v0.2.0 and set TAU2_DATA_DIR."
            )

        history: List[OpenAIMessage] = [
            {"role": "system", "content": self._get_system_prompt()},
            {
                "role": "user",
                "content": (
                    f"Domain: {item.get('domain', self.domain)}\n\n"
                    f"User Scenario:\n{item.get('scenario', '')}\n\n"
                    "Respond with the next assistant message for this customer-service task."
                ),
            },
        ]

        try:
            response = run_evaluation_task(
                messages=history,
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
        except Exception as e:
            logger.log_metrics({"error": f"TauBench execution error: {str(e)}"})
            return {"success": False, "response": "", "error": str(e)}

        return {"success": bool(content.strip()), "response": content, "turns": 1}

    def grade(self, prediction: Any, item: Dict[str, Any]) -> bool:
        if isinstance(prediction, dict):
            return prediction.get("success", False)
        return False
