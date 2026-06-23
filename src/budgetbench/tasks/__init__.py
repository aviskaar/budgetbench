from importlib import import_module
from typing import Dict, Tuple, Type

from budgetbench.tasks.base import BaseTask


_REGISTRY: Dict[str, Tuple[str, str]] = {
    "long": ("budgetbench.tasks.long", "LongBenchV2Task"),
    "swe": ("budgetbench.tasks.swe", "SWEBenchTask"),
    "tau": ("budgetbench.tasks.tau", "TauBenchTask"),
    "memory": ("budgetbench.tasks.memory", "MemoryUpdateTask"),
    "longmem": ("budgetbench.tasks.longmem", "LongMemEvalTask"),
}


def get_task_class(name: str) -> Type[BaseTask]:
    if name not in _REGISTRY:
        raise ValueError(f"Task '{name}' not found. Available tasks: {list(_REGISTRY.keys())}")

    module_name, class_name = _REGISTRY[name]
    module = import_module(module_name)
    return getattr(module, class_name)


def get_task(name: str, **kwargs) -> BaseTask:
    """
    Returns an instance of a task by name.
    """
    task_class = get_task_class(name)
    return task_class(**kwargs)


__all__ = ["get_task", "get_task_class"]
