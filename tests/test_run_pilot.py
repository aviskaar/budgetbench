import pytest

from scripts import run_pilot


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


def test_llm_client_sends_configured_api_key(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return _Response()

    monkeypatch.setenv("TEST_API_KEY", "test-secret")
    monkeypatch.setattr(run_pilot.requests, "post", fake_post)

    client = run_pilot.get_llm_client(
        "https://example.test/chat/completions",
        model="test-model",
        api_key_env="TEST_API_KEY",
    )

    assert client([{"role": "user", "content": "hello"}]) == "ok"
    assert captured["headers"] == {"Authorization": "Bearer test-secret"}
    assert captured["json"]["model"] == "test-model"


def test_llm_client_rejects_missing_configured_api_key(monkeypatch):
    monkeypatch.delenv("MISSING_API_KEY", raising=False)
    client = run_pilot.get_llm_client(api_key_env="MISSING_API_KEY")

    with pytest.raises(RuntimeError, match="MISSING_API_KEY is not set"):
        client([{"role": "user", "content": "hello"}])
