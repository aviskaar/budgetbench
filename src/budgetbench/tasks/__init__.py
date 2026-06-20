from typing import Dict, Type
from budgetbench.tasks.base import BaseTask
from budgetbench.tasks.long import LongBenchV2Task
from budgetbench.tasks.swe import SWEBenchTask
from budgetbench.tasks.tau import TauBenchTask
from budgetbench.tasks.memory import MemoryUpdateTask
from budgetbench.tasks.longmem import LongMemEvalTask

_REGISTRY: Dict[str, Type[BaseTask]] = {
    "long": LongBenchV2Task,
    "swe": SWEBenchTask,
    "tau": TauBenchTask,
    "memory": MemoryUpdateTask,
    "longmem": LongMemEvalTask,
}

def get_task(name: str, **kwargs) -> BaseTask:
    """
    Returns an instance of a task by name.
    """
    if name not in _REGISTRY:
        raise ValueError(f"Task '{name}' not found. Available tasks: {list(_REGISTRY.keys())}")
    
    task_class = _REGISTRY[name]
    return task_class(**kwargs)
