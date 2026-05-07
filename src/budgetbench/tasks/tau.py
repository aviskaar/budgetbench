import json
from typing import List, Callable, Any, Dict, Optional
from budgetbench.utils.types import OpenAIMessage
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger
from budgetbench.tasks.base import BaseTask

try:
    from tau2.envs import get_env as _tau2_get_env
    TAU2_AVAILABLE = True
except ImportError:
    _tau2_get_env = None
    TAU2_AVAILABLE = False


class TauBenchTask(BaseTask):
    def __init__(self, domain: str = "retail", split: str = "test"):
        self.domain = domain
        self.split = split
        self.env = None
        if TAU2_AVAILABLE:
            try:
                self.env = _tau2_get_env(domain)
            except Exception:
                self.env = None

    def get_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if not TAU2_AVAILABLE:
            raise ImportError(
                "tau2-bench is not installed. Install it with: pip install tau2-bench. "
                "τ²-bench full sweep is scoped to Phase 4."
            )
        env = _tau2_get_env(self.domain)
        items = env.get_dataset()  # Returns List[Dict] with "goal" and "id"
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
                "tau2-bench is not installed. τ²-bench integration requires tau2-bench. "
                "Install with: pip install tau2-bench"
            )

        obs, info = self.env.reset()
        user_goal = item.get("goal", "Help the user.")

        # Extract tool definitions if available in info
        tools = info.get("tools", [])
        tools_str = json.dumps(tools, indent=2) if tools else "No tools available."

        history: List[OpenAIMessage] = [
            {"role": "system", "content": f"{self._get_system_prompt()}\n\nAvailable Tools:\n{tools_str}"},
            {"role": "user", "content": f"User Goal: {user_goal}\nInitial Observation: {obs}"}
        ]

        success = False
        turn = 0
        try:
            for turn in range(max_turns):
                response = run_evaluation_task(
                    messages=history,
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

                history.append({"role": "assistant", "content": content})

                # For tau-bench, the 'action' can be the full assistant message dict
                action = {"role": "assistant", "content": content}

                # Try to extract structured tool calls if available
                try:
                    data = json.loads(content)
                    if "tool_calls" in data:
                        action["tool_calls"] = data["tool_calls"]
                except Exception:
                    pass

                obs, reward, done, truncated, info = self.env.step(action)

                if done:
                    success = info.get('success', False)
                    break

                history.append({"role": "user", "content": f"Observation: {obs}"})
        except Exception as e:
            logger.log_metrics({"error": f"TauBench execution error: {str(e)}"})

        return {"success": success, "turns": turn + 1}

    def grade(self, prediction: Any, item: Dict[str, Any]) -> bool:
        if isinstance(prediction, dict):
            return prediction.get("success", False)
        return False
