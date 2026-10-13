"""Pre-flight trước khi chạy `--live`: kiểm tra mọi thứ cần có, không tốn quota LLM.

Mục đích: nhóm chỉ được chạy mỗi batch `--live` MỘT lần (tránh trả phí/lượt dùng 2 lần),
nên phải biết chắc provider, embedding, corpus và artifact đã sẵn sàng.

Chạy từ gốc repo:
    python scripts/preflight.py            # chỉ đọc, không tạo file
    python scripts/preflight.py --answers  # thêm kiểm tra artifacts/answers_50q.json

Exit code 0 = không có mục FAIL (WARN vẫn có thể còn).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402  (đảm bảo .env đã được load)
from src import llm_client  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []


def record(level: str, name: str, detail: str) -> None:
    RESULTS.append((level, name, detail))
    print(f"{level:4} {name}: {detail}")


def check_files() -> None:
    modules = ["m1_chunking.py", "m2_search.py", "m3_rerank.py", "m4_eval.py", "m5_enrichment.py"]
    missing = [name for name in modules if not (Path(config.ROOT_DIR) / "src" / name).is_file()]
    if missing:
        record("FAIL", "src/m1-m5", f"thiếu {missing} — copy từ Day 18 (xem doc/PIPELINE_INTERFACE.md)")
    else:
        record("OK", "src/m1-m5", "đủ 5 module")

    todos = [name for name in ("phase_a_ragas.py", "phase_b_judge.py", "phase_c_guard.py")
             if "# TODO" in (Path(config.ROOT_DIR) / "src" / name).read_text(encoding="utf-8")]
    record("WARN" if todos else "OK", "TODO",
           f"còn # TODO trong {todos} (mỗi file còn TODO = -5 điểm, runner cũng chặn --live)"
           if todos else "không còn # TODO trong phase_*.py")


def check_secrets() -> None:
    key = os.getenv("OPENAI_API_KEY", "")
    record("OK" if key else "FAIL", "OPENAI_API_KEY",
           f"đã set (dài {len(key)} ký tự, không in giá trị)" if key else "thiếu trong .env")
    record("OK", "base_url", os.getenv("OPENAI_BASE_URL") or "(mặc định api.openai.com)")
    record("OK", "session header", os.getenv("OPENCODE_SESSION") or "lab24-ragas (mặc định)")


def check_provider() -> None:
    settings = llm_client.settings()
    if not settings["api_key"]:
        record("FAIL", "provider", "không probe được vì thiếu key")
        return
    for role, model in (("primary", settings["primary"]), ("fallback", settings["fallback"])):
        result = llm_client.probe(model)
        if result.get("ok"):
            record("OK", f"LLM {role}", f"{model} → HTTP {result['http']} (finish={result['finish_reason']})")
        else:
            level = "FAIL" if role == "primary" else "WARN"
            detail = f"{model} → HTTP {result.get('http')} {result.get('detail', '')}".strip()
            record(level, f"LLM {role}", detail + (" (sẽ dùng fallback)" if role == "primary" else ""))


def check_embeddings() -> None:
    settings = llm_client.settings()
    url = settings["embed_base_url"].rstrip("/") + "/embeddings"
    body = json.dumps({"model": settings["embed_model"], "input": ["nghỉ phép năm"]}).encode()
    request = urllib.request.Request(
        url, data=body, headers={"Authorization": "Bearer " + settings["embed_api_key"],
                                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        dim = len(payload["data"][0]["embedding"])
        if dim == config.EMBEDDING_DIM:
            record("OK", "embedding local", f"{settings['embed_model']} trả vector {dim}-dim (khớp EMBEDDING_DIM)")
        else:
            record("FAIL", "embedding local",
                   f"{settings['embed_model']} trả {dim}-dim nhưng EMBEDDING_DIM={config.EMBEDDING_DIM}")
    except urllib.error.HTTPError as error:
        record("FAIL", "embedding local", f"HTTP {error.code} — LM Studio đang chạy? token đúng?")
    except Exception as error:  # noqa: BLE001
        record("FAIL", "embedding local", f"{type(error).__name__}: {error} — bật LM Studio server")


def check_qdrant() -> None:
    try:
        with urllib.request.urlopen(f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}/collections",
                                    timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        names = [item["name"] for item in payload["result"]["collections"]]
        record("OK", "qdrant", f"đang chạy; collections={names}")
    except Exception:  # noqa: BLE001
        record("WARN", "qdrant",
               "không kết nối được localhost:6333 — sẽ dùng QdrantClient(':memory:') như Day 18")


def check_answers() -> None:
    path = Path(config.ANSWERS_PATH)
    if not path.is_file():
        record("FAIL", "answers_50q.json",
               "chưa có — chạy: python scripts/setup_answers.py --live (Phase A cần file này)")
        return
    rows = json.loads(path.read_text(encoding="utf-8"))
    distributions: dict[str, int] = {}
    modes: dict[str, int] = {}
    for row in rows:
        distributions[row["distribution"]] = distributions.get(row["distribution"], 0) + 1
        modes[row["generation_mode"]] = modes.get(row["generation_mode"], 0) + 1
    expected = {"factual": 20, "multi_hop": 20, "adversarial": 10}
    ids = {row["id"] for row in rows}
    if len(rows) == 50 and len(ids) == 50 and distributions == expected:
        record("OK", "answers_50q.json", f"50 id, distribution {distributions}, mode {modes}")
    else:
        record("FAIL", "answers_50q.json",
               f"n={len(rows)} ids={len(ids)} distribution={distributions} (cần 20/20/10)")
    same = [row["id"] for row in rows if row["answer"] == row["ground_truth"]]
    if same:
        record("FAIL", "answer vs ground_truth", f"trùng nhau ở id {same[:5]} — cấm lấy ground_truth làm answer")
    else:
        record("OK", "answer vs ground_truth", "không có dòng nào trùng")
    if modes.get("extractive_fallback"):
        record("WARN", "generation_mode", f"{modes['extractive_fallback']} câu dùng extractive_fallback — phải ghi rõ trong báo cáo")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Pre-flight cho lab 24 (không gọi LLM tốn phí).")
    parser.add_argument("--answers", action="store_true", help="kiểm tra artifacts/answers_50q.json")
    args = parser.parse_args(argv)

    print("=" * 70)
    print("PRE-FLIGHT — Lab 24 (Track 3A)")
    print("=" * 70)
    check_secrets()
    check_files()
    check_provider()
    check_embeddings()
    check_qdrant()
    if args.answers:
        check_answers()

    failures = [item for item in RESULTS if item[0] == "FAIL"]
    warnings = [item for item in RESULTS if item[0] == "WARN"]
    print("-" * 70)
    print(f"{len(failures)} FAIL, {len(warnings)} WARN")
    for level, name, detail in RESULTS:
        if level == "FAIL":
            print(f"  FAIL {name}: {detail}")
    return int(bool(failures))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
