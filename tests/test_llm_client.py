import json

import pytest

from trendminer.config import ProviderConfig, Settings
from trendminer.llm import client as client_mod
from trendminer.llm.client import LLMClient, LLMError


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    @property
    def text(self):
        return json.dumps(self._payload, ensure_ascii=False)


def _ok(content: str) -> FakeResponse:
    return FakeResponse(200, {"choices": [{"message": {"content": content}}]})


@pytest.fixture
def provider():
    return ProviderConfig(
        base_url="https://example.com/v1",
        model="test-model",
        api_key_env="LLM_API_KEY",
        supports_json_object=True,
    )


def test_retry_then_success(monkeypatch, provider):
    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeResponse(500, {"error": "boom"})
        return _ok('{"ok": true}')

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    settings = Settings()
    settings.retry_backoff_seconds = 0.0
    out = LLMClient(provider, settings).chat([{"role": "user", "content": "hi"}])
    assert out == '{"ok": true}'
    assert calls["n"] == 2


def test_client_error_not_retried(monkeypatch, provider):
    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        return FakeResponse(400, {"error": "bad request"})

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    with pytest.raises(LLMError):
        LLMClient(provider, Settings()).chat([{"role": "user", "content": "hi"}])
    assert calls["n"] == 1
