from __future__ import annotations

"""
Module 5: Enrichment Pipeline
==============================
Làm giàu chunks TRƯỚC khi embed: Summarize, HyQA, Contextual Prepend, Auto Metadata.

Test: pytest tests/test_m5.py
"""

import os, sys
import json
import re
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GENERATION_MODEL, OPENAI_API_KEY


def _chat_completion(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    from openai import OpenAI

    response = OpenAI().chat.completions.create(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        # `deepseek-flash` là model reasoning: nó đốt hết `max_tokens` vào
        # `reasoning_content` rồi trả `content` rỗng. Với max_tokens 80-200 ở
        # các hàm dưới, enrichment sẽ hỏng âm thầm. Tắt reasoning để lấy thẳng
        # câu trả lời. Endpoint không hỗ trợ tham số này sẽ bỏ qua nó.
        reasoning_effort="none",
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty enrichment response")
    return content.strip()


def _fallback_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text.strip())
        if sentence.strip()
    ]


def _fallback_questions(text: str, n_questions: int = 3) -> list[str]:
    sentences = [sentence for sentence in _fallback_sentences(text) if len(sentence) > 10]
    return [
        f"Nội dung quy định gì về {sentence.rstrip('.!?')}?"
        for sentence in sentences[:max(n_questions, 0)]
    ]


def _fallback_metadata(text: str) -> dict:
    sentences = _fallback_sentences(text)
    first_sentence = sentences[0] if sentences else ""
    folded_text = text.casefold()
    if any(word in folded_text for word in ("mật khẩu", "máy chủ", "phần mềm", "vpn", "hệ thống")):
        category = "it"
    elif any(word in folded_text for word in ("chi phí", "ngân sách", "tài chính", "lương", "thuế")):
        category = "finance"
    elif any(word in folded_text for word in ("nhân viên", "nghỉ phép", "thử việc", "tuyển dụng")):
        category = "hr"
    else:
        category = "policy"

    capitalized = re.findall(
        r"\b[A-ZÀ-Ỵ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỵ][a-zà-ỹ]+)*\b",
        text,
    )
    first_word = first_sentence.split(maxsplit=1)[0] if first_sentence.split() else ""
    entities = list(dict.fromkeys(entity for entity in capitalized if entity != first_word))
    has_vietnamese_diacritics = bool(re.search(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", folded_text))
    return {
        "topic": first_sentence[:120],
        "entities": entities,
        "category": category,
        "language": "vi" if has_vietnamese_diacritics else "en",
    }


def _parse_json_object(content: str) -> dict:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content, flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Enrichment response did not contain a JSON object")
    result = json.loads(cleaned[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError("Enrichment response JSON must be an object")
    return result


@dataclass
class EnrichedChunk:
    """Chunk đã được làm giàu."""
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str  # "contextual", "summary", "hyqa", "full"


# ─── Technique 1: Chunk Summarization ────────────────────


def summarize_chunk(text: str) -> str:
    """
    Tạo summary ngắn cho chunk.
    Embed summary thay vì (hoặc cùng với) raw chunk → giảm noise.
    """
    if not text.strip():
        return ""
    if OPENAI_API_KEY:
        try:
            return _chat_completion(
                "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn bằng tiếng Việt.",
                text,
                max_tokens=150,
            )
        except Exception as error:
            print(f"  ⚠️  OpenAI summarize failed: {error}")

    return " ".join(_fallback_sentences(text)[:2]) or text.strip()


# ─── Technique 2: Hypothesis Question-Answer (HyQA) ─────


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    """
    Generate câu hỏi mà chunk có thể trả lời.
    Index cả questions lẫn chunk → query match tốt hơn (bridge vocabulary gap).
    """
    if n_questions <= 0 or not text.strip():
        return []
    if OPENAI_API_KEY:
        try:
            content = _chat_completion(
                f"Dựa trên đoạn văn, tạo {n_questions} câu hỏi mà đoạn văn có thể trả lời. "
                "Trả về mỗi câu hỏi trên một dòng.",
                text,
                max_tokens=200,
            )
            questions = [
                re.sub(r"^\s*\d+[\s.)-]*", "", line).strip()
                for line in content.splitlines()
                if line.strip()
            ]
            questions = [question for question in questions if question]
            if questions:
                return questions[:n_questions]
        except Exception as error:
            print(f"  ⚠️  OpenAI HyQA failed: {error}")

    return _fallback_questions(text, n_questions)


# ─── Technique 3: Contextual Prepend (Anthropic style) ──


def contextual_prepend(text: str, document_title: str = "") -> str:
    """
    Prepend context giải thích chunk nằm ở đâu trong document.
    Anthropic benchmark: giảm 49% retrieval failure (alone).
    """
    if OPENAI_API_KEY:
        try:
            context = _chat_completion(
                "Viết 1 câu ngắn mô tả đoạn văn này nằm ở đâu trong tài liệu và nói về chủ đề gì. "
                "Chỉ trả về 1 câu.",
                f"Tài liệu: {document_title}\n\nĐoạn văn:\n{text}",
                max_tokens=80,
            )
            return f"{context}\n\n{text}"
        except Exception as error:
            print(f"  ⚠️  OpenAI contextual failed: {error}")

    prefix = f"Trích từ {document_title}. " if document_title else "Nội dung tài liệu. "
    return f"{prefix}{text}"


# ─── Technique 4: Auto Metadata Extraction ──────────────


def extract_metadata(text: str) -> dict:
    """
    LLM extract metadata tự động: topic, entities, date_range, category.
    """
    if OPENAI_API_KEY:
        try:
            content = _chat_completion(
                'Trích xuất metadata từ đoạn văn. Trả về JSON: '
                '{"topic": "...", "entities": ["..."], '
                '"category": "policy|hr|it|finance", "language": "vi|en"}.',
                text,
                max_tokens=150,
            )
            result = _parse_json_object(content)
            fallback = _fallback_metadata(text)
            return {
                **fallback,
                **result,
                "entities": result.get("entities", fallback["entities"]),
            }
        except Exception as error:
            print(f"  ⚠️  OpenAI metadata failed: {error}")

    return _fallback_metadata(text)


# ─── Combined Single-Call Mode ───────────────────────────


def _enrich_single_call(text: str, source: str) -> dict:
    """Single LLM call to get summary + questions + context + metadata.

    ⚠️ Cost optimization: 1 API call thay vì 4 calls riêng lẻ.
    """
    if OPENAI_API_KEY:
        try:
            content = _chat_completion(
                'Phân tích đoạn văn và trả về JSON: {"summary": "...", '
                '"questions": ["..."], "context": "...", '
                '"metadata": {"topic": "...", "entities": [], '
                '"category": "policy|hr|it|finance", "language": "vi|en"}}',
                f"Tài liệu: {source}\n\nĐoạn văn:\n{text}",
                # JSON gồm summary + 3 câu hỏi + context + metadata, viết bằng
                # tiếng Việt. Ở 400 token model bị cắt giữa chừng (finish_reason
                # = "length"), mất dấu `}` cuối nên _parse_json_object báo
                # "did not contain a JSON object" và enrichment hỏng âm thầm.
                max_tokens=1200,
            )
            result = _parse_json_object(content)
            if not isinstance(result.get("questions", []), list):
                raise ValueError("Enrichment questions must be a JSON list")
            if not isinstance(result.get("metadata", {}), dict):
                raise ValueError("Enrichment metadata must be a JSON object")
            return result
        except Exception as error:
            print(f"  ⚠️  Enrichment API failed: {error}")

    sentences = _fallback_sentences(text)
    return {
        "summary": " ".join(sentences[:2]) or text.strip(),
        "questions": _fallback_questions(text),
        "context": f"Trích từ {source}." if source else "Nội dung tài liệu.",
        "metadata": _fallback_metadata(text),
    }


# ─── Full Enrichment Pipeline ────────────────────────────


def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:
    """
    Chạy enrichment pipeline trên danh sách chunks. (Đã implement sẵn — dùng functions ở trên)

    Có 2 chế độ:
    - methods cụ thể (["summary"], ["contextual"]...): gọi từng function riêng (tốt cho học/debug)
    - methods=["combined"] hoặc None: 1 API call duy nhất cho tất cả (tốt cho production)

    Args:
        chunks: List of {"text": str, "metadata": dict}
        methods: Default None → combined mode (1 call/chunk).
                 Options: "summary", "hyqa", "contextual", "metadata", "combined"
    """
    if methods is None:
        methods = ["combined"]

    supported_methods = {"summary", "hyqa", "contextual", "metadata", "combined"}
    unknown_methods = set(methods) - supported_methods
    if unknown_methods:
        raise ValueError(f"Unsupported enrichment method(s): {', '.join(sorted(unknown_methods))}")

    use_combined = "combined" in methods

    enriched = []
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        source = chunk.get("metadata", {}).get("source", "")

        if use_combined:
            result = _enrich_single_call(text, source)
            summary = result.get("summary", "")
            questions = result.get("questions", [])
            context_line = result.get("context", "")
            enriched_text = f"{context_line}\n\n{text}" if context_line else text
            auto_meta = result.get("metadata", {})
        else:
            summary = summarize_chunk(text) if "summary" in methods else ""
            questions = generate_hypothesis_questions(text) if "hyqa" in methods else []
            enriched_text = contextual_prepend(text, source) if "contextual" in methods else text
            auto_meta = extract_metadata(text) if "metadata" in methods else {}

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**chunk.get("metadata", {}), **auto_meta},
            method="+".join(methods),
        ))

        if (i + 1) % 10 == 0 or (i + 1) == len(chunks):
            print(f"  Enriched {i + 1}/{len(chunks)} chunks...", flush=True)

    return enriched


# ─── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    sample = "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm. Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác."

    print("=== Enrichment Pipeline Demo ===\n")
    print(f"Original: {sample}\n")

    s = summarize_chunk(sample)
    print(f"Summary: {s}\n")

    qs = generate_hypothesis_questions(sample)
    print(f"HyQA questions: {qs}\n")

    ctx = contextual_prepend(sample, "Sổ tay nhân viên VinUni 2024")
    print(f"Contextual: {ctx}\n")

    meta = extract_metadata(sample)
    print(f"Auto metadata: {meta}")
