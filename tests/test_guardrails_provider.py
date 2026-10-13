import sys
from types import ModuleType, SimpleNamespace

import pytest

from guardrails import config as provider_config


def test_opencode_provider_uses_chat_api_and_live_model(monkeypatch):
    registered = {}
    provider_settings = {
        "api_key": "offline-test-key",
        "base_url": "https://example.invalid/v1",
        "primary": "longcat-test-model",
    }
    session_headers = {"x-opencode-session": "test-session"}

    import src.llm_client as llm_client

    monkeypatch.setattr(llm_client, "settings", lambda: provider_settings)
    monkeypatch.setattr(llm_client, "headers", lambda: session_headers)
    monkeypatch.setattr(provider_config, "_provider_registered", False)

    langchain_core = ModuleType("langchain_core")
    pydantic_v1 = ModuleType("langchain_core.pydantic_v1")
    pydantic_v1.Field = lambda default=None, alias=None, default_factory=None: (
        default_factory() if default_factory is not None else default
    )
    langchain_core.pydantic_v1 = pydantic_v1
    langchain_openai = ModuleType("langchain_openai")
    langchain_openai.ChatOpenAI = type("ChatOpenAI", (), {})

    nemo = ModuleType("nemoguardrails")
    nemo_llm = ModuleType("nemoguardrails.llm")
    nemo_providers = ModuleType("nemoguardrails.llm.providers")
    nemo_providers.register_llm_provider = lambda name, cls: registered.update(
        {name: cls}
    )

    for name, module in (
        ("langchain_core", langchain_core),
        ("langchain_core.pydantic_v1", pydantic_v1),
        ("langchain_openai", langchain_openai),
        ("nemoguardrails", nemo),
        ("nemoguardrails.llm", nemo_llm),
        ("nemoguardrails.llm.providers", nemo_providers),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    provider_config.register_provider()
    model = SimpleNamespace(type="main", engine="compat", model="stale-model", parameters={})
    provider_config.configure_model(SimpleNamespace(models=[model]))

    provider = registered["compat"]
    assert model.engine == "compat"
    assert provider.model_name == "longcat-test-model"
    assert provider.openai_api_base == "https://example.invalid/v1"
    assert provider.default_headers == session_headers
    assert model.model == "longcat-test-model"
    assert model.parameters["max_tokens"] == 1024


def test_opencode_provider_requires_api_key(monkeypatch):
    import src.llm_client as llm_client

    monkeypatch.setattr(
        llm_client,
        "settings",
        lambda: {"api_key": "", "base_url": "https://example.invalid/v1", "primary": "model"},
    )
    model = SimpleNamespace(type="main", engine="compat", model="model", parameters={})

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        provider_config.configure_model(SimpleNamespace(models=[model]))
