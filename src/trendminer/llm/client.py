"""LLM 客户端：通过 requests 调用 OpenAI 兼容的 /chat/completions。"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

from trendminer.config import ProviderConfig, Settings


class LLMError(RuntimeError):
    """LLM 调用失败（不可重试或重试耗尽）。"""


class LLMClient:
    def __init__(self, provider: ProviderConfig, settings: Settings):
        self.provider = provider
        self.settings = settings

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        stage: Optional[str] = None,
        response_format_json: bool = True,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> str:
        url = self.provider.base_url.rstrip("/") + "/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.provider.model,
            "messages": messages,
            "temperature": (
                temperature if temperature is not None else self.provider.default_temperature
            ),
            "max_tokens": self.settings.max_tokens,
        }
        if response_format_json and self.provider.supports_json_object:
            payload["response_format"] = {"type": "json_object"}
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Bearer {self.provider.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.settings.request_timeout,
                )
            except requests.RequestException as exc:
                last_error = exc
            else:
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                if resp.status_code in (429, 500, 502, 503, 504):
                    last_error = LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                else:
                    raise LLMError(f"HTTP {resp.status_code}: {resp.text[:300]}")

            if attempt < self.settings.max_retries:
                time.sleep(self.settings.retry_backoff_seconds * (2 ** attempt))

        raise LLMError(f"重试 {self.settings.max_retries} 次后仍失败: {last_error}")
