"""LLM provider abstraction.

A thin, provider-agnostic interface so the rest of the engine never knows which
model or vendor is answering. Today the only implementation talks to OpenRouter's
OpenAI-compatible API; a future ``OllamaProvider`` (self-hosted, zero per-token
cost) is a drop-in because it speaks the same wire format.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx

from app.core.config import Settings, get_settings

# OpenRouter asks integrators to identify their app via these headers; harmless
# elsewhere and useful for their dashboards/rate-limit attribution.
_REFERER = "https://intimateai.chat"
_TITLE = "IntimateAI"


class LLMProvider(ABC):
    """Streams assistant text for a list of chat messages."""

    @abstractmethod
    async def stream(
        self, messages: list[dict], **overrides
    ) -> AsyncIterator[str]:
        """Yield content deltas (token chunks) as they arrive."""
        raise NotImplementedError
        yield ""  # pragma: no cover - marks this an async generator

    async def complete(self, messages: list[dict], **overrides) -> str:
        """Convenience: collect a full (non-streamed) response."""
        parts = [chunk async for chunk in self.stream(messages, **overrides)]
        return "".join(parts)


class OpenRouterProvider(LLMProvider):
    """Talks to OpenRouter's OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def model(self) -> str:
        return self._settings.active_model

    async def stream(
        self, messages: list[dict], **overrides
    ) -> AsyncIterator[str]:
        s = self._settings
        payload = {
            "model": overrides.get("model", s.active_model),
            "messages": messages,
            "temperature": overrides.get("temperature", s.LLM_TEMPERATURE),
            "max_tokens": overrides.get("max_tokens", s.LLM_MAX_TOKENS),
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {s.OPENROUTER_API_KEY}",
            "HTTP-Referer": _REFERER,
            "X-Title": _TITLE,
            "Content-Type": "application/json",
        }
        url = f"{s.OPENROUTER_BASE_URL}/chat/completions"

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if delta:
                        yield delta


def get_provider() -> LLMProvider:
    """Factory: returns the configured provider.

    Swapping vendors later (e.g. self-hosted Ollama) happens here and in config,
    not in the engine or routers.
    """
    return OpenRouterProvider()
