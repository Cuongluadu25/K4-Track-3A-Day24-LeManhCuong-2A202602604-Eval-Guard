"""LLM/embedding client dùng chung cho cả lab 24 (OpenCode Go + LM Studio local).

Vì sao cần module này (3 ràng buộc đã kiểm chứng thật, xem doc/LLM_PROVIDER_SETUP.md):

1. OpenCode Go yêu cầu header `x-opencode-session`; thiếu header này trả HTTP 400
   `MissingSessionID` dù model hợp lệ. Vì vậy mọi client phải đi qua đây.
2. Các model của Go là reasoning model: nếu `max_tokens` nhỏ thì `content` trả về
   `null` và chỉ có `reasoning_content` (đã thấy ở 20 và 50 token). Vì vậy mặc định
   `max_tokens` lớn và `chat()` báo lỗi rõ ràng khi `content` rỗng.
3. KHÔNG có `/v1/embeddings` trên OpenCode Go, nên embedding phải lấy từ LM Studio
   local (`LOCAL_EMBED_BASE_URL`) — xem `embedding_client()`.

Fallback model: `LLM_MODEL` là model chính, `FALLBACK_MODEL` dùng khi model chính lỗi.
`chat()` tự chuyển ngay trong một call; `run_with_model_fallback()` chuyển cả một batch
(ví dụ RAGAS) và trả về model thực sự đã dùng để ghi vào metadata.
"""
from __future__ import annotations

import os
from typing import Callable

from dotenv import load_dotenv

load_dotenv()

USER_AGENT = "lab24-ragas-eval/1.0"
DEFAULT_MAX_TOKENS = 1024      # reasoning model cần đủ chỗ, nếu không content = null
DEFAULT_BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_PRIMARY = "longcat-2.5-preview-free"
DEFAULT_FALLBACK = "glm-5.3-flash"


def settings() -> dict:
    """Đọc cấu hình provider từ .env (không chứa giá trị secret trong log)."""
    return {
        "base_url": os.getenv("OPENAI_BASE_URL") or DEFAULT_BASE_URL,
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "session": os.getenv("OPENCODE_SESSION", "lab24-ragas"),
        "primary": os.getenv("LLM_MODEL") or DEFAULT_PRIMARY,
        "fallback": os.getenv("FALLBACK_MODEL") or DEFAULT_FALLBACK,
        "embed_base_url": os.getenv("LOCAL_EMBED_BASE_URL", "http://127.0.0.1:1234/v1"),
        "embed_api_key": os.getenv("LOCAL_EMBED_API_KEY", "lm-studio"),
        "embed_model": os.getenv("EMBEDDING_MODEL", "text-embedding-bge-m3"),
    }


def headers() -> dict:
    config = settings()
    return {"x-opencode-session": config["session"], "User-Agent": USER_AGENT}


def chat_client(*, timeout: float = 180.0, max_retries: int = 2):
    """OpenAI client trỏ vào OpenCode Go, đã kèm header session."""
    from openai import OpenAI

    config = settings()
    if not config["api_key"]:
        raise ValueError("Thiếu OPENAI_API_KEY trong .env (không được hardcode trong source).")
    return OpenAI(base_url=config["base_url"], api_key=config["api_key"],
                  default_headers=headers(), timeout=timeout, max_retries=max_retries)


def embedding_client():
    """OpenAI client trỏ vào LM Studio local (endpoint embeddings, 1024-dim)."""
    from openai import OpenAI

    config = settings()
    return OpenAI(base_url=config["embed_base_url"], api_key=config["embed_api_key"],
                  timeout=180.0, max_retries=2)


def _extract_content(response, model: str) -> str:
    choice = response.choices[0]
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            f"{model}: content rỗng (finish_reason={choice.finish_reason!r}). "
            f"Reasoning model cần max_tokens lớn hơn (đang là {DEFAULT_MAX_TOKENS})."
        )
    return content


def chat(messages: list[dict], *, model: str | None = None,
         max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = 0,
         response_format: dict | None = None, client=None) -> str:
    """Gọi chat completion; tự chuyển sang FALLBACK_MODEL nếu model chính lỗi."""
    config = settings()
    primary = model or config["primary"]
    order = [primary] + ([config["fallback"]] if config["fallback"] != primary else [])
    active = client if client is not None else chat_client()
    errors: list[str] = []
    for candidate in order:
        try:
            kwargs = {"model": candidate, "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature}
            if response_format is not None:
                kwargs["response_format"] = response_format
            return _extract_content(active.chat.completions.create(**kwargs), candidate)
        except Exception as error:                      # noqa: BLE001 - muốn bắt mọi lỗi provider
            errors.append(f"{candidate}: {error}")
            if candidate != order[-1]:
                print(f"⚠️  LLM {candidate} lỗi ({error}) → thử {order[-1]}")
    raise RuntimeError("Tất cả model đều lỗi:\n  " + "\n  ".join(errors))


def run_with_model_fallback(run: Callable[[str], object], *,
                            primary: str | None = None,
                            fallback: str | None = None) -> tuple[object, str]:
    """Chạy một batch bằng model chính; lỗi giữa chừng thì chạy lại bằng model dự phòng.

    Returns:
        (kết quả, model ID thực sự dùng) — trả model ID để ghi metadata trung thực.
    """
    config = settings()
    primary = primary or config["primary"]
    fallback = fallback or config["fallback"]
    try:
        return run(primary), primary
    except Exception as error:                          # noqa: BLE001
        if fallback == primary:
            raise
        print(f"⚠️  Batch lỗi với {primary}: {error}\n   → chạy lại toàn bộ bằng {fallback}")
        return run(fallback), fallback


def langchain_llm(model: str, *, max_tokens: int = DEFAULT_MAX_TOKENS):
    """ChatOpenAI cho RAGAS (cần langchain-openai; import lazy để test offline chạy được)."""
    from langchain_openai import ChatOpenAI

    config = settings()
    return ChatOpenAI(model=model, api_key=config["api_key"], base_url=config["base_url"],
                      default_headers=headers(), temperature=0, max_tokens=max_tokens,
                      max_retries=3, timeout=180)


def langchain_embeddings():
    """OpenAIEmbeddings trỏ LM Studio local.

    `check_embedding_ctx_length=False` là BẮT BUỘC: mặc định True khiến LangChain gửi
    mảng token id, LM Studio trả 400 ("'input' field must be a string or an array of strings").
    """
    from langchain_openai import OpenAIEmbeddings

    config = settings()
    return OpenAIEmbeddings(model=config["embed_model"], api_key=config["embed_api_key"],
                            base_url=config["embed_base_url"],
                            check_embedding_ctx_length=False)


def probe(model: str) -> dict:
    """Gọi 1 request nhỏ để biết model còn phục vụ được không (dùng cho pre-flight)."""
    import json
    import urllib.error
    import urllib.request

    config = settings()
    body = json.dumps({"model": model, "max_tokens": 64,
                       "messages": [{"role": "user", "content": "Reply: OK"}]}).encode()
    request = urllib.request.Request(
        config["base_url"].rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + config["api_key"],
                 "Content-Type": "application/json",
                 "User-Agent": USER_AGENT,
                 "x-opencode-session": config["session"]})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        choice = payload["choices"][0]
        return {"model": model, "ok": True, "http": response.status,
                "finish_reason": choice.get("finish_reason")}
    except urllib.error.HTTPError as error:
        return {"model": model, "ok": False, "http": error.code,
                "detail": error.read().decode("utf-8", "replace")[:200]}
    except Exception as error:                          # noqa: BLE001
        return {"model": model, "ok": False, "http": None, "detail": repr(error)[:200]}


def pick_model() -> str:
    """Trả model sẽ dùng cho batch: model chính nếu còn sống, ngược lại là model dự phòng."""
    config = settings()
    result = probe(config["primary"])
    if result["ok"]:
        return config["primary"]
    print(f"⚠️  {config['primary']} không dùng được ({result}) → dùng {config['fallback']}")
    return config["fallback"]


if __name__ == "__main__":
    config = settings()
    print("primary :", config["primary"])
    print("fallback:", config["fallback"])
    print("base_url:", config["base_url"], "| embed:", config["embed_base_url"], config["embed_model"])
    for name in (config["primary"], config["fallback"]):
        print(probe(name))
