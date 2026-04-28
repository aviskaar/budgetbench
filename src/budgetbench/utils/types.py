from typing import TypedDict, List, Optional

class OpenAIMessage(TypedDict, total=False):
    role: str
    content: str
    name: Optional[str]

BUDGET_TIERS: List[int] = [2048, 4096, 8192, 16384, 32768]
