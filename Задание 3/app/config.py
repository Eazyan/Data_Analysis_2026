from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def load_config() -> LLMConfig:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    if provider == "ollama":
        return LLMConfig(
            provider="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        )

    return LLMConfig(
        provider="openrouter",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "qwen/qwen3.6-plus"),
    )
