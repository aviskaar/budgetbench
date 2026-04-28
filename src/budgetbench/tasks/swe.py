import docker
import json
import re
import os
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
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None

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
            "You are a skilled software engineer. You are given a problem statement and access to a bash shell. "
            "Your goal is to fix the issue by exploring the repository and applying a patch. "
            "Available commands: ls, cat, grep, python, pytest, sed, and 'submit' to finish. "
            "Format your response as a JSON object with two fields: 'thought' (your reasoning) and 'command' (the bash command to execute). "
            "Example: {\"thought\": \"I will list the files.\", \"command\": \"ls -R\"}"
        )

    def _execute_command(self, container: Any, command: str) -> str:
        if container is None:
            return f"Mocked output for: {command}"
        
        try:
            exit_code, output = container.exec_run(f"bash -c {json.dumps(command)}")
            return output.decode("utf-8")
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def run(
        self,
        item: Dict[str, Any],
        strategy: MemoryStrategy,
        llm_client: Callable[[List[OpenAIMessage]], Any],
        tokenizer_fn: Callable[[str], int],
        max_tokens: int,
        logger: MetricsLogger,
        max_turns: int = 10,
        use_docker: bool = False
    ) -> str:
        instance_id = item["instance_id"]
        problem_statement = item["problem_statement"]
        
        container = None
        if use_docker and self.docker_client:
            # Placeholder for actual container setup logic
            # In a real scenario, we'd use a specific image for the repo/version
            # image_name = f"swe-bench-{item['repo'].replace('/', '-')}-{item['version']}"
            try:
                container = self.docker_client.containers.run(
                    "python:3.12-slim", # Placeholder image
                    command="tail -f /dev/null",
                    detach=True,
                    # network_mode="none" # Security: mitigate T-03-01-01
                )
                # Clone repo and setup env... (Omitted for brevity in pilot)
            except Exception as e:
                logger.log_metrics({"error": f"Failed to start container: {str(e)}"})
                container = None

        history: List[OpenAIMessage] = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Problem Statement:\n{problem_statement}\n\nYou are in the root of the repository. What is your first command?"}
        ]
        
        submitted_patch = ""
        
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
                
                # Parse command
                command = ""
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        action = json.loads(json_match.group())
                        command = action.get("command", "")
                    else:
                        # Fallback: try to find something that looks like a command if JSON fails
                        pass
                except:
                    pass

                if not command:
                    history.append({"role": "user", "content": "Error: Could not parse command. Please provide a JSON object with 'thought' and 'command'."})
                    continue

                if command.strip() == "submit":
                    # In real SWE-bench, we would generate a patch
                    # For pilot, we take the last 'write' command or just return a dummy
                    submitted_patch = "diff --git a/file.py b/file.py\n..." 
                    break
                
                observation = self._execute_command(container, command)
                history.append({"role": "user", "content": f"Observation:\n{observation}"})
        finally:
            if container:
                container.stop()
                container.remove()
            
        return submitted_patch

    def grade(self, patch: str, item: Dict[str, Any]) -> bool:
        """
        Grades the patch. In pilot, we check if it's non-empty and has basic diff format.
        """
        if not patch:
            return False
        return "diff --git" in patch or patch == "SIMULATED_PATCH"
