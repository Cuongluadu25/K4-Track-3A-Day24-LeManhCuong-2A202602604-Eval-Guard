"""OpenAI-compatible NeMo provider configuration for OpenCode Go."""
from __future__ import annotations

from typing import Any

ENGINE_NAME = "compat"
_provider_registered = False


def register_provider() -> None:
    """Register ChatOpenAI directly so chat-only model IDs use chat completions."""
    global _provider_registered
    if _provider_registered:
        return

    from langchain_core.pydantic_v1 import Field
    from langchain_openai import ChatOpenAI
    from src.llm_client import headers, settings
    from nemoguardrails.llm.providers import register_llm_provider

    provider_settings = settings()

    class OpenCodeChatOpenAI(ChatOpenAI):
        model_name: str = Field(default=provider_settings["primary"], alias="model")
        openai_api_base: str = Field(default=provider_settings["base_url"], alias="base_url")
        default_headers: dict[str, str] = Field(default_factory=headers)

    register_llm_provider(ENGINE_NAME, OpenCodeChatOpenAI)
    _provider_registered = True


def configure_model(config: Any) -> None:
    """Set the declared model and API parameters to the actual live provider values."""
    from src.llm_client import DEFAULT_MAX_TOKENS, settings

    provider_settings = settings()
    if not provider_settings["api_key"]:
        raise ValueError("Thiếu OPENAI_API_KEY trong .env để chạy NeMo Guardrails.")

    main_models = [model for model in config.models if model.type == "main"]
    if len(main_models) != 1:
        raise ValueError("NeMo Guardrails phải khai báo đúng một model type 'main'.")

    main_model = main_models[0]
    main_model.engine = ENGINE_NAME
    main_model.model = provider_settings["primary"]
    main_model.parameters = {
        **main_model.parameters,
        "max_tokens": DEFAULT_MAX_TOKENS,
    }
