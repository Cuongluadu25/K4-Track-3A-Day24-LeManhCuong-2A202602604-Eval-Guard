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


def _extract_content(response, model: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    choice = response.choices[0]
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            f"{model}: content rỗng (finish_reason={choice.finish_reason!r}). "
            f"Reasoning model cần max_tokens lớn hơn (lời gọi này đặt {max_tokens})."
        )
    return content


def chat(messages: list[dict], *, model: str | None = None,
         max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = 0,
         response_format: dict | None = None, client=None, caller: str = "llm_client") -> str:
    """Gọi chat completion; tự chuyển sang FALLBACK_MODEL nếu model chính lỗi.

    Mọi lượt gọi (kể cả lượt lỗi) được ghi RAW vào `.hermes/llm_raw/` qua src/llm_log.py.
    """
    import time

    from src import llm_log

    config = settings()
    primary = model or config["primary"]
    order = [primary] + ([config["fallback"]] if config["fallback"] != primary else [])
    active = client if client is not None else chat_client()
    errors: list[str] = []
    for candidate in order:
        started = time.perf_counter()
        kwargs = {"model": candidate, "messages": messages,
                  "max_tokens": max_tokens, "temperature": temperature}
        if response_format is not None:
            kwargs["response_format"] = response_format
        try:
            response = active.chat.completions.create(**kwargs)
        except Exception as error:                      # noqa: BLE001 - muốn bắt mọi lỗi provider
            llm_log.log_chat(caller=caller, model=candidate, messages=messages,
                             max_tokens=max_tokens, response_format=response_format,
                             error=error, latency_ms=(time.perf_counter() - started) * 1000)
            errors.append(f"{candidate}: {error}")
            if candidate != order[-1]:
                print(f"⚠️  LLM {candidate} lỗi ({error}) → thử {order[-1]}")
            continue
        # Log cả khi content rỗng: đó là dữ liệu cần để debug reasoning model.
        llm_log.log_chat(caller=caller, model=candidate, messages=messages,
                         max_tokens=max_tokens, response_format=response_format,
                         response=response, latency_ms=(time.perf_counter() - started) * 1000)
        try:
            return _extract_content(response, candidate, max_tokens)
        except ValueError as content_error:
            # Reasoning model hết max_tokens trước khi sinh content -> thử model dự phòng.
            errors.append(f"{candidate}: {content_error}")
            if candidate != order[-1]:
                print(f"⚠️  LLM {candidate} trả content rỗng ({content_error}) → thử {order[-1]}")
            continue
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


def _capped_chat_class():
    """Trả về ChatOpenAI nhưng ép tham số `n` <= 1.

    OpenCode Go TỪ CHỐI n > 1 — đã kiểm chứng bằng request thật:
        n=1 -> HTTP 200; n=2/n=3 -> HTTP 400
        {"error":{"type":"invalid_request_error","message":"Upstream request failed:
          [invalid_parameter] 参数校验失败: /n: 3 is not less or equal to 1"}}
    RAGAS `answer_relevancy` mặc định `strictness = 3` nên gọi n=3; nếu không ép lại thì
    metric trả NaN cho mọi câu (đúng lỗi làm hỏng lượt smoke đầu tiên của Phase A).

    Hệ quả phải ghi trong báo cáo: answer_relevancy chỉ có MỘT lượt sinh câu hỏi cho mỗi
    lời gọi (prompt vẫn yêu cầu nhiều câu hỏi trong cùng một response), tức strictness bị
    hạ xuống 1 so với mặc định 3 của RAGAS.
    """
    from langchain_openai import ChatOpenAI

    class _CappedChatOpenAI(ChatOpenAI):
        def _get_request_payload(self, *args, **kwargs):
            payload = super()._get_request_payload(*args, **kwargs)
            if payload.get("n") not in (None, 1):
                global _N_CAPPED_LOGGED
                if not _N_CAPPED_LOGGED:
                    _N_CAPPED_LOGGED = True
                    from src import llm_log
                    llm_log.write({"caller": "llm_client.n_capped",
                                   "request": {"n_requested": payload["n"], "n_sent": 1},
                                   "note": "provider giới hạn n<=1 (RAGAS answer_relevancy strictness=3)"})
                payload["n"] = 1
            return payload

    return _CappedChatOpenAI


_N_CAPPED_LOGGED = False


def langchain_llm(model: str, *, max_tokens: int = 2048, caller: str = "ragas"):
    """ChatOpenAI cho RAGAS (import lazy để test offline chạy được).

    - Ép `n` <= 1 vì provider từ chối n>1 (xem `_capped_chat_class`).
    - `max_tokens` mặc định 2048: reasoning model tiêu token cho reasoning trước khi sinh
      content, để thấp quá thì RAGAS nhận câu trả lời rỗng.
    - Gắn callback của src/llm_log để ghi RAW từng lượt chấm điểm vào `.hermes/llm_raw/`.
    """
    from src import llm_log

    config = settings()
    handler = llm_log.callback_handler(caller)
    return _capped_chat_class()(
        model=model, api_key=config["api_key"], base_url=config["base_url"],
        default_headers=headers(), temperature=0, max_tokens=max_tokens,
        max_retries=3, timeout=180,
        **({"callbacks": [handler]} if handler is not None else {}))


EMBED_TIMEOUT_S = float(os.getenv("EMBED_TIMEOUT_S", "60"))
EMBED_MAX_RETRIES = int(os.getenv("EMBED_MAX_RETRIES", "1"))


def langchain_embeddings():
    """OpenAIEmbeddings trỏ LM Studio local.

    `check_embedding_ctx_length=False` là BẮT BUỘC: mặc định True khiến LangChain gửi
    mảng token id, LM Studio trả 400 ("'input' field must be a string or an array of strings").

    `timeout` ngắn + ít retry là CỐ Ý (đã trả giá thật): LM Studio từng kẹt ở
    /v1/embeddings (model ở trạng thái COMPUTINGEMBEDDING) trong khi /v1/models vẫn trả lời
    trong 22ms; mặc định của LangChain chờ rất lâu nên cả lượt chạy 200 bước đứng im ~70 phút.
    Với timeout 60s, sự cố kiểu đó lộ ra trong ~2 phút thay vì treo im lặng.
    """
    from langchain_openai import OpenAIEmbeddings

    config = settings()
    return OpenAIEmbeddings(model=config["embed_model"], api_key=config["embed_api_key"],
                            base_url=config["embed_base_url"],
                            check_embedding_ctx_length=False,
                            timeout=EMBED_TIMEOUT_S, max_retries=EMBED_MAX_RETRIES)


def probe(model: str) -> dict:
    """Gọi 1 request nhỏ để biết model còn phục vụ được không (dùng cho pre-flight).

    `ok` chỉ True khi có `content` thật: reasoning model có thể trả HTTP 200 mà `content`
    rỗng nếu `max_tokens` không đủ — model như vậy không dùng được cho judge/RAGAS.
    """
    import json
    import urllib.error
    import urllib.request

    config = settings()
    body = json.dumps({"model": model, "max_tokens": 512,
                       "messages": [{"role": "user", "content": "Reply with exactly: OK"}]}).encode()
    request = urllib.request.Request(
        config["base_url"].rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + config["api_key"],
                 "Content-Type": "application/json",
                 "User-Agent": USER_AGENT,
                 "x-opencode-session": config["session"]})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        choice = payload["choices"][0]
        content = (choice.get("message") or {}).get("content")
        has_content = isinstance(content, str) and bool(content.strip())
        return {"model": model, "ok": has_content, "http": response.status,
                "finish_reason": choice.get("finish_reason"),
                "content": (content or "")[:40],
                "detail": "" if has_content else "HTTP 200 nhưng content rỗng (chỉ có reasoning)"}
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
