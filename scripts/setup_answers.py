"""
Setup script: chạy Day 18 pipeline trên 50 câu hỏi → lưu artifacts/answers_50q.json

Chạy TRƯỚC khi bắt đầu Phase A:
    python scripts/setup_answers.py --live

Yêu cầu:
    1. Có 5 module m1-m5 với giao diện trong doc/PIPELINE_INTERFACE.md
       Script tự lắp module; không gọi src/pipeline.py.
    2. docker compose -f infra/docker-compose.yml up -d  (Qdrant đang chạy trên port 6333)
    3. .env có OPENAI_API_KEY
"""
from __future__ import annotations

import json
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ROOT_DIR, TEST_SET_PATH, ANSWERS_PATH, GENERATION_MODEL


def check_day18_files() -> bool:
    required = [
        "src/m1_chunking.py", "src/m2_search.py", "src/m3_rerank.py",
        "src/m4_eval.py",     "src/m5_enrichment.py",
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(ROOT_DIR, f))]
    if missing:
        print("\n❌ Thiếu files từ Day 18. Copy chúng vào src/ trước:\n")
        for f in missing:
            print(f"   cp <Day18>/src/{os.path.basename(f)} src/")
        return False
    print(f"✓ Day 18 source files: {len(required)}/{len(required)} found")
    return True


def build_pipeline():
    # This assembler calls m1/m2/m3/m5 directly, NOT src.pipeline.py.
    from src.m1_chunking import load_documents, chunk_hierarchical
    from src.m2_search import HybridSearch
    from src.m3_rerank import CrossEncoderReranker
    from src.m5_enrichment import enrich_chunks
    from config import RERANK_TOP_K

    print("\n[1/3] Chunking + enriching documents...")
    t0 = time.time()
    docs = load_documents()
    all_chunks = []
    for doc in docs:
        parents, children = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
        for child in children:
            all_chunks.append({
                "text": child.text,
                "metadata": {**child.metadata, "parent_id": child.parent_id},
            })

    enriched = enrich_chunks(all_chunks)
    if enriched:
        if len(enriched) != len(all_chunks):
            raise ValueError("enrich_chunks must preserve chunk count/order; see doc/PIPELINE_INTERFACE.md")
        all_chunks = [{"text": e.enriched_text,
                       "metadata": {**original["metadata"], **e.auto_metadata}}
                      for original, e in zip(all_chunks, enriched)]
        print(f"  ✓ Enriched {len(enriched)} chunks ({time.time()-t0:.1f}s)")
    else:
        print(f"  ✓ Using {len(all_chunks)} raw chunks (M5 not implemented or no API key)")

    print("\n[2/3] Indexing (BM25 + Dense)...")
    t0 = time.time()
    search = HybridSearch()
    search.index(all_chunks)
    print(f"  ✓ Indexed {len(all_chunks)} chunks ({time.time()-t0:.1f}s)")

    print("\n[3/3] Loading reranker...")
    t0 = time.time()
    reranker = CrossEncoderReranker()
    print(f"  ✓ Reranker ready ({time.time()-t0:.1f}s)")

    return search, reranker, RERANK_TOP_K


GENERATION_SYSTEM_PROMPT = (
    "Trả lời CHỈ dựa trên context. Viết câu trả lời bằng tiếng Việt dưới dạng câu hoàn chỉnh "
    "(một hoặc vài câu, luôn kết thúc bằng dấu chấm), nêu rõ số liệu, điều kiện và phạm vi áp dụng "
    "có trong context. Không trả lời bằng cụm từ rời hay chỉ một con số. "
    "Nếu context không có thông tin → trả lời đúng câu: 'Không tìm thấy thông tin.'"
)


GENERATION_MAX_TOKENS = int(os.getenv("GENERATION_MAX_TOKENS", "4096"))
# Ladder thử lại khi model chính trả content rỗng (reasoning ăn hết token):
# model dự phòng trước, rồi tới model mạnh hơn. Đã gặp thật: câu multi-hop id 27 trả rỗng ở 1024/2048 token.
GENERATION_RETRY_MODELS = [name.strip() for name in os.getenv(
    "GENERATION_RETRY_MODELS", "glm-5.3-flash,qwen3.8-max").split(",") if name.strip()]


def _sentence_ok(text: str) -> bool:
    """Câu trả lời phải là câu hoàn chỉnh, có dấu kết câu.

    RAGAS faithfulness tách 'sentences from the answer' rồi mới sinh statements; một cụm rời
    như '1.000.000 VNĐ/tháng' (không có dấu chấm) làm RAGAS không sinh được statement nào và
    trả về NaN cho metric đó — đã gặp thật với câu id 3.
    """
    stripped = (text or "").strip()
    return len(stripped) > 3 and stripped[-1] in ".!?…"


def run_query(q: str, search, reranker, top_k: int, client=None) -> tuple[str, list[str], str, str | None]:
    from config import OPENAI_API_KEY

    results = search.search(q)
    docs    = [{"text": r.text, "score": r.score, "metadata": r.metadata} for r in results]
    reranked = reranker.rerank(q, docs, top_k=top_k)
    contexts = [r.text for r in reranked] if reranked else [r.text for r in results[:3]]

    if (OPENAI_API_KEY or client is not None) and contexts:
        try:
            if client is None:
                # llm_client gắn header x-opencode-session (bắt buộc với OpenCode Go):
                # SDK pin trong lab (openai==1.109.1) KHÔNG đọc OPENAI_CUSTOM_HEADERS.
                from src import llm_client
                client = llm_client.chat_client()
            ctx = "\n\n".join(contexts)
            messages = [{"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                        {"role": "user",   "content": f"Context:\n{ctx}\n\nCâu hỏi: {q}"}]
            resp = client.chat.completions.create(
                model=GENERATION_MODEL,
                max_tokens=GENERATION_MAX_TOKENS,
                messages=messages,
            )
            # Log RAW (ngoài bài nộp): .hermes/llm_raw/ — xem src/llm_log.py
            from src import llm_log
            llm_log.log_chat(caller="setup_answers.generation", model=GENERATION_MODEL,
                             messages=messages, max_tokens=GENERATION_MAX_TOKENS,
                             response_format=None, response=resp,
                             extra={"question": q, "n_contexts": len(contexts)})
            reported_model = getattr(resp, "model", None)
            used_model = reported_model if isinstance(reported_model, str) and reported_model.strip() else GENERATION_MODEL
            content = resp.choices[0].message.content
            if not (isinstance(content, str) and content.strip()):
                # content rỗng = reasoning model tiêu hết max_tokens trước khi sinh câu trả lời
                # (đã gặp thật ở 4/50 câu và ở 1/8 câu của batch thử). Thử lần lượt các model trong
                # GENERATION_RETRY_MODELS với ngân sách token lớn hơn; hết cách mới chịu fallback extractive.
                from src import llm_client
                print(f"  ⚠️  content rỗng với {used_model} → thử lại lần lượt {GENERATION_RETRY_MODELS}")
                for retry_model in GENERATION_RETRY_MODELS:
                    try:
                        content = llm_client.chat(messages, model=retry_model,
                                                  max_tokens=GENERATION_MAX_TOKENS,
                                                  caller="setup_answers.generation_retry")
                        used_model = retry_model
                        break
                    except Exception as retry_error:    # noqa: BLE001 - thử model kế tiếp
                        print(f"     ✗ {retry_model}: {retry_error}")
                else:
                    raise ValueError(
                        f"mọi model thử lại đều trả content rỗng: {GENERATION_RETRY_MODELS}")
            if not _sentence_ok(content):
                # Không sửa câu trả lời của model, chỉ ghi lại: RAGAS faithfulness sẽ không tách
                # được statement từ cụm rời và metric đó sẽ NaN — đây là rủi ro đã biết.
                print(f"  ⚠️  câu trả lời không phải câu hoàn chỉnh: {content[:60]!r}")
                llm_log.log_chat(caller="setup_answers.short_answer", model=used_model,
                                 messages=messages, max_tokens=2048, response_format=None,
                                 extra={"question": q, "answer": content})
            return content, contexts, "llm", used_model
        except Exception as e:
            print(f"  ⚠️  LLM generation failed: {e}")

    return (contexts[0] if contexts else "Không tìm thấy thông tin."), contexts, "extractive_fallback", None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Assemble previous modules and generate 50 answers (API cost).")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("Generation/enrichment may call APIs. Pass --live after completing pre-class setup.")
    print("=" * 60)
    print("K4 / TRACK 3A SETUP — Generating answers for 50 questions")
    print("=" * 60)

    if not check_day18_files():
        sys.exit(1)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)
    print(f"✓ Loaded {len(test_set)} questions (factual/multi_hop/adversarial)")

    try:
        search, reranker, top_k = build_pipeline()
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("→ Đảm bảo bạn đã copy src/ từ Day 18 và đã pip install -r requirements/requirements.txt")
        sys.exit(1)

    print(f"\nRunning {len(test_set)} queries...")
    answers = []
    from config import OPENAI_API_KEY
    client = None
    if OPENAI_API_KEY:
        from src import llm_client
        client = llm_client.chat_client()
    t_start = time.time()

    for i, item in enumerate(test_set):
        answer, contexts, generation_mode, generation_model = run_query(item["question"], search, reranker, top_k, client)
        answers.append({
            "id":           item["id"],
            "distribution": item["distribution"],
            "question":     item["question"],
            "answer":       answer,
            "contexts":     contexts,
            "ground_truth": item["ground_truth"],
            "generation_mode": generation_mode,
            "generation_model": generation_model,
        })
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(test_set)}] done ({time.time()-t_start:.0f}s elapsed)")

    os.makedirs(os.path.dirname(ANSWERS_PATH), exist_ok=True)
    with open(ANSWERS_PATH, "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved {len(answers)} answers → artifacts/answers_50q.json")
    print(f"  Total time: {time.time()-t_start:.1f}s")
    print("\n→ Bây giờ bắt đầu Phase A:")
    print("     python scripts/run_experiments.py --phase a --live")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
