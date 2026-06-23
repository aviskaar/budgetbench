from importlib import import_module
from typing import Dict, Tuple


_REGISTRY: Dict[str, Tuple[str, str]] = {
    "TruncationStrategy": ("budgetbench.strategies.truncation", "TruncationStrategy"),
    "FullContextStrategy": ("budgetbench.strategies.full_context", "FullContextStrategy"),
    "SummaryBufferStrategy": ("budgetbench.strategies.summary", "SummaryBufferStrategy"),
    "RAGStrategy": ("budgetbench.strategies.rag", "RAGStrategy"),
    "LeanRetrievalStrategy": ("budgetbench.strategies.lean_retrieval", "LeanRetrievalStrategy"),
    "CheckpointContextStrategy": ("budgetbench.strategies.checkpoint_context", "CheckpointContextStrategy"),
    "Mem0Strategy": ("budgetbench.strategies.mem0", "Mem0Strategy"),
    "LettaStrategy": ("budgetbench.strategies.letta", "LettaStrategy"),
    "LLMLinguaStrategy": ("budgetbench.strategies.llmlingua", "LLMLinguaStrategy"),
}


def __getattr__(name: str):
    if name not in _REGISTRY:
        raise AttributeError(name)
    module_name, class_name = _REGISTRY[name]
    module = import_module(module_name)
    return getattr(module, class_name)


__all__ = list(_REGISTRY.keys())
