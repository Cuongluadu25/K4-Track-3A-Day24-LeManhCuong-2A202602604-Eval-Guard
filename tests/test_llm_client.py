"""Test offline cho src/llm_client.py — fallback model và guard content rỗng.

Không gọi mạng: `chat_client` và `settings` đều được patch. Lý do tồn tại của
những test này là hai ràng buộc của provider đã kiểm chứng thật: (1) reasoning model
có thể trả `content = null` khi max_tokens nhỏ; (2) free server có thể chết giữa batch,
cần chuyển sang FALLBACK_MODEL thay vì bỏ cả lượt chạy.
"""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src import llm_client

pytestmark = pytest.mark.support

BASE_SETTINGS = {
    "base_url": "https://example.invalid/v1",
    "api_key": "test-key",
    "session": "test-session",
    "primary": "primary-model",
    "fallback": "fallback-model",
    "embed_base_url": "http://127.0.0.1:1234/v1",
    "embed_api_key": "lm-studio",
    "embed_model": "text-embedding-bge-m3",
}


def _reply(text, finish="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(
        finish_reason=finish, message=SimpleNamespace(content=text))])


def _client_that_fails_for(failing_model, text="done"):
    def create(**kwargs):
        if failing_model is not None and kwargs["model"] == failing_model:
            raise RuntimeError("429 rate limited")
        return _reply(text)

    client = Mock()
    client.chat.completions.create = Mock(side_effect=create)
    return client


def test_headers_carry_session_header(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(
        BASE_SETTINGS, base_url="https://opencode.ai/zen/go/v1"))
    assert llm_client.headers()["x-opencode-session"] == "test-session"


def test_headers_omit_opencode_session_for_other_providers(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(BASE_SETTINGS))
    assert "x-opencode-session" not in llm_client.headers()


def test_provider_pacing_waits_for_reserved_request_slot(monkeypatch):
    import asyncio as asyncio_module

    monkeypatch.setenv("LLM_MIN_REQUEST_INTERVAL_SECONDS", "0.25")
    monkeypatch.setattr(llm_client, "_next_request_slot", time.monotonic() + 0.25)
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio_module, "sleep", sleep)

    asyncio.run(llm_client.pace_llm_request())

    sleep.assert_awaited_once()
    assert sleep.await_args.args[0] == pytest.approx(0.25, abs=0.01)


def test_default_pacing_is_gemini_specific(monkeypatch):
    monkeypatch.delenv("LLM_MIN_REQUEST_INTERVAL_SECONDS", raising=False)
    monkeypatch.setattr(llm_client, "settings", lambda: dict(
        BASE_SETTINGS, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"))
    assert llm_client._request_min_interval() == 15
    monkeypatch.setattr(llm_client, "settings", lambda: dict(
        BASE_SETTINGS, base_url="https://opencode.ai/zen/go/v1"))
    assert llm_client._request_min_interval() == 0


def test_chat_uses_primary_when_it_works(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(BASE_SETTINGS))
    client = _client_that_fails_for(None)
    monkeypatch.setattr(llm_client, "chat_client", lambda **_: client)

    assert llm_client.chat([{"role": "user", "content": "hi"}]) == "done"
    assert client.chat.completions.create.call_args.kwargs["model"] == "primary-model"


def test_chat_falls_back_to_fallback_model(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(BASE_SETTINGS))
    client = _client_that_fails_for("primary-model", text="from-fallback")
    monkeypatch.setattr(llm_client, "chat_client", lambda **_: client)

    assert llm_client.chat([{"role": "user", "content": "hi"}]) == "from-fallback"
    models = [call.kwargs["model"] for call in client.chat.completions.create.call_args_list]
    assert models == ["primary-model", "fallback-model"]


def test_chat_raises_when_every_model_fails(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(BASE_SETTINGS))
    client = Mock()
    client.chat.completions.create = Mock(side_effect=RuntimeError("503 upstream"))
    monkeypatch.setattr(llm_client, "chat_client", lambda **_: client)

    with pytest.raises(RuntimeError, match="Tất cả model đều lỗi"):
        llm_client.chat([{"role": "user", "content": "hi"}])


def test_empty_content_raises_with_max_tokens_hint(monkeypatch):
    monkeypatch.setattr(llm_client, "settings",
                        lambda: dict(BASE_SETTINGS, fallback="primary-model"))
    client = Mock()
    client.chat.completions.create = Mock(return_value=_reply(None, finish="length"))
    monkeypatch.setattr(llm_client, "chat_client", lambda **_: client)

    # Một model duy nhất -> lỗi được gói lại trong RuntimeError, nhưng thông điệp
    # phải nói rõ nguyên nhân (content rỗng vì reasoning model) để người chạy sửa được.
    with pytest.raises(RuntimeError, match="max_tokens"):
        llm_client.chat([{"role": "user", "content": "hi"}])


def test_run_with_model_fallback_reruns_whole_batch(monkeypatch):
    monkeypatch.setattr(llm_client, "settings", lambda: dict(BASE_SETTINGS))
    calls = []

    def run(model):
        calls.append(model)
        if model == "primary-model":
            raise ValueError("m4: faithfulness=nan cho câu 3")
        return f"ok::{model}"

    result, model_used = llm_client.run_with_model_fallback(run)

    assert result == "ok::fallback-model"
    assert model_used == "fallback-model"
    assert calls == ["primary-model", "fallback-model"]


def test_run_without_distinct_fallback_propagates(monkeypatch):
    monkeypatch.setattr(llm_client, "settings",
                        lambda: dict(BASE_SETTINGS, fallback="primary-model"))

    def run(model):
        raise ValueError("lỗi dữ liệu, không phải lỗi provider")

    with pytest.raises(ValueError, match="lỗi dữ liệu"):
        llm_client.run_with_model_fallback(run)
