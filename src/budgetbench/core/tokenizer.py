from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import tiktoken

try:
    from transformers import AutoTokenizer
except ImportError:  # pragma: no cover - optional at runtime
    AutoTokenizer = None


def _normalize_model_name(model_name: Optional[str]) -> str:
    return (model_name or "").strip().lower()


def _infer_hf_tokenizer_id(model_name: Optional[str]) -> Optional[str]:
    normalized = _normalize_model_name(model_name)
    if not normalized:
        return None

    if normalized.startswith("qwen2.5:1.5b"):
        return "Qwen/Qwen2.5-1.5B-Instruct"
    if normalized.startswith("qwen2.5:7b"):
        return "Qwen/Qwen2.5-7B-Instruct"
    if normalized.startswith("qwen2.5:14b"):
        return "Qwen/Qwen2.5-14B-Instruct"
    if normalized.startswith("qwen2.5:32b"):
        return "Qwen/Qwen2.5-32B-Instruct"
    if normalized.startswith("qwen2.5:72b"):
        return "Qwen/Qwen2.5-72B-Instruct"
    if normalized.startswith("qwen3-vl:2b"):
        return "Qwen/Qwen2.5-VL-3B-Instruct"
    return None


@dataclass
class TokenCounter:
    tokenizer_id: str
    backend: str
    is_approximate: bool
    source: str
    model_name: Optional[str] = None
    _tokenizer: Any = None

    def __call__(self, text: str) -> int:
        text = text or ""
        if self.backend == "huggingface":
            return len(self._tokenizer.encode(text, add_special_tokens=False))
        if self.backend == "tiktoken":
            return len(self._tokenizer.encode(text, disallowed_special=()))
        return len(text) // 4

    def metadata(self) -> Dict[str, Any]:
        return {
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_backend": self.backend,
            "tokenizer_source": self.source,
            "tokenizer_is_approximate": self.is_approximate,
            "tokenizer_model_name": self.model_name,
        }


def build_token_counter(
    model_name: Optional[str] = None,
    tokenizer_name: Optional[str] = None,
) -> TokenCounter:
    explicit_name = (tokenizer_name or "").strip()
    if explicit_name and explicit_name.lower() != "auto":
        if explicit_name.startswith("tiktoken:"):
            encoding_name = explicit_name.split(":", 1)[1] or "cl100k_base"
            encoding = tiktoken.get_encoding(encoding_name)
            return TokenCounter(
                tokenizer_id=encoding_name,
                backend="tiktoken",
                is_approximate=True,
                source="explicit_tiktoken",
                model_name=model_name,
                _tokenizer=encoding,
            )
        if AutoTokenizer is not None:
            tokenizer = AutoTokenizer.from_pretrained(explicit_name, trust_remote_code=True)
            return TokenCounter(
                tokenizer_id=explicit_name,
                backend="huggingface",
                is_approximate=False,
                source="explicit_huggingface",
                model_name=model_name,
                _tokenizer=tokenizer,
            )

    inferred_name = _infer_hf_tokenizer_id(model_name)
    if inferred_name and AutoTokenizer is not None:
        tokenizer = AutoTokenizer.from_pretrained(inferred_name, trust_remote_code=True)
        return TokenCounter(
            tokenizer_id=inferred_name,
            backend="huggingface",
            is_approximate=False,
            source="model_inferred_huggingface",
            model_name=model_name,
            _tokenizer=tokenizer,
        )

    encoding = tiktoken.get_encoding("cl100k_base")
    return TokenCounter(
        tokenizer_id="cl100k_base",
        backend="tiktoken",
        is_approximate=True,
        source="fallback_tiktoken",
        model_name=model_name,
        _tokenizer=encoding,
    )
