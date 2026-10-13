"""Ghi log RAW request/response của mọi lời gọi LLM (JSONL) — để nhóm tự kiểm tra.

TÁCH BIỆT HOÀN TOÀN với bằng chứng mà đề bài yêu cầu:
- Đề bài chỉ cần `artifacts/*.json` và `doc/reports/*.md` (do runner/setup tạo).
- Log ở đây ghi vào `.hermes/llm_raw/*.jsonl` — `.hermes/` đã bị `.gitignore`, nên
  không bao giờ lọt vào bài nộp. Không dùng log này làm số liệu báo cáo.

Mỗi dòng là một JSON object:
    {"ts","caller","model","endpoint","request":{"messages","max_tokens","response_format"},
     "response":{"content","finish_reason","usage"} | "error","latency_ms"}

Bật/tắt: `LLM_LOG=off` trong .env. Đổi chỗ ghi: `LLM_LOG_DIR=<path>`.
An toàn khi lỗi: mọi lỗi ghi log đều bị nuốt (không được làm hỏng lượt chạy thật).
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()
_OFF = {"off", "0", "false", "no", "none"}


def enabled() -> bool:
    # Không ghi log trong lúc chạy unit test: tránh tạo file trong tests, và test
    # không được phụ thuộc vào side effect của logging.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return os.getenv("LLM_LOG", "on").strip().lower() not in _OFF


def log_dir() -> Path:
    root = os.getenv("LLM_LOG_DIR")
    if not root:
        repo_root = Path(__file__).resolve().parents[1]
        root = str(repo_root / ".hermes" / "llm_raw")
    return Path(root)


def _path(name: str | None = None) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return log_dir() / f"{name or os.getenv('LLM_LOG_NAME', 'llm')}-{stamp}.jsonl"


def write(record: dict, *, name: str | None = None) -> None:
    """Ghi một dòng JSONL. Không bao giờ raise ra ngoài."""
    if not enabled():
        return
    try:
        path = _path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        record.setdefault("ts", datetime.now(timezone.utc).isoformat())
        line = json.dumps(record, ensure_ascii=False, default=str)
        with _LOCK:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except Exception:                                   # noqa: BLE001 - logging không được phá lượt chạy
        pass


def log_chat(*, caller: str, model: str, messages, max_tokens, response_format,
             response=None, error: Exception | None = None, latency_ms: float | None = None,
             extra: dict | None = None) -> None:
    """Log một lời gọi chat completion (đã thành công hoặc lỗi)."""
    record: dict = {
        "caller": caller,
        "model": model,
        "request": {"messages": messages, "max_tokens": max_tokens,
                    "response_format": response_format},
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
    }
    if callers_endpoint := os.getenv("OPENAI_BASE_URL"):
        record["endpoint"] = callers_endpoint
    if extra:
        record.update(extra)
    if error is not None:
        record["error"] = f"{type(error).__name__}: {error}"
    if response is not None:
        try:
            choice = response.choices[0]
            usage = getattr(response, "usage", None)
            record["response"] = {
                "content": choice.message.content,
                "reasoning_content": getattr(choice.message, "reasoning_content", None),
                "finish_reason": getattr(choice, "finish_reason", None),
                "usage": usage.model_dump() if hasattr(usage, "model_dump") else (
                    dict(usage) if isinstance(usage, dict) else None),
            }
            record["response_model"] = getattr(response, "model", None)
        except Exception as extract_error:              # noqa: BLE001
            record["response_extract_error"] = repr(extract_error)
    write(record)


def callback_handler(caller: str = "langchain"):
    """CallbackHandler cho LangChain (RAGAS dùng ChatOpenAI) để log từng lượt chấm điểm.

    Trả None nếu langchain-core không có (ví dụ môi trường test offline tối giản).
    """
    if not enabled():
        return None
    try:
        from langchain_core.callbacks import BaseCallbackHandler
    except Exception:                                   # noqa: BLE001
        return None

    class _RawLLMLogger(BaseCallbackHandler):
        def __init__(self) -> None:
            self._pending: dict[str, dict] = {}

        def _key(self, kwargs) -> str:
            return str(kwargs.get("run_id") or id(kwargs))

        def on_chat_model_start(self, serialized, messages, **kwargs):   # noqa: D102
            self._pending[self._key(kwargs)] = {
                "messages": [[getattr(m, "type", "?"), getattr(m, "content", str(m))]
                             for group in messages for m in group],
                "started": time.perf_counter(),
            }

        def on_llm_start(self, serialized, prompts, **kwargs):           # noqa: D102
            self._pending[self._key(kwargs)] = {
                "prompts": list(prompts), "started": time.perf_counter()}

        def on_llm_end(self, response, **kwargs):                        # noqa: D102
            state = self._pending.pop(self._key(kwargs), {})
            generations = []
            try:
                for group in response.generations:
                    for gen in group:
                        text = getattr(gen, "text", None)
                        if not text and getattr(gen, "message", None) is not None:
                            text = getattr(gen.message, "content", None)
                        generations.append(text)
            except Exception:                           # noqa: BLE001
                generations = ["<unparsed>"]
            write({
                "caller": caller,
                "model": (response.llm_output or {}).get("model_name") if response.llm_output else None,
                "request": {"messages": state.get("messages"), "prompts": state.get("prompts")},
                "response": {"generations": generations,
                             "llm_output": response.llm_output},
                "latency_ms": round((time.perf_counter() - state["started"]) * 1000, 1)
                             if "started" in state else None,
            })

        def on_llm_error(self, error, **kwargs):                         # noqa: D102
            state = self._pending.pop(self._key(kwargs), {})
            write({"caller": caller, "request": {"messages": state.get("messages")},
                   "error": f"{type(error).__name__}: {error}"})

    return _RawLLMLogger()
