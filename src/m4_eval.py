from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from math import isfinite
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _metric(value, name: str, question: str) -> float:
    """Chuyển metric RAGAS thành float. NaN/inf là LỖI THẬT, không được thay bằng 0.0.

    Day 18 từng map NaN -> 0.0; doc/PIPELINE_INTERFACE.md cấm "tự thay NaN bằng điểm giả".
    Raise ở đây cũng là tín hiệu để tầng trên chạy lại bằng FALLBACK_MODEL.
    """
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"m4: {name} không phải số cho câu {question!r}: {value!r}") from error
    if not isfinite(number):
        raise ValueError(
            f"m4: {name}={number} cho câu {question!r}. Kiểm tra lại evaluator "
            "(max_tokens, model, endpoint embedding) rồi chạy lại — không ghi 0.0."
        )
    return number


def _ragas_llm_and_embeddings(model: str):
    """Build RAGAS evaluator: LLM qua OpenCode Go, embeddings qua LM Studio local.

    LUY Y 1: khong dung llm_factory()/embedding_factory() mac dinh cua RAGAS --
    chung hard-code `gpt-4o-mini` va `text-embedding-ada-002`, khong dung provider
    cua lab. Moi client di qua src/llm_client.py de co header x-opencode-session.

    LUY Y 2: check_embedding_ctx_length=False la BAT BUOC (xem llm_client.langchain_embeddings).
    Mac dinh True khien langchain tokenize roi gui mang int len /v1/embeddings;
    LM Studio tra 400 "'input' field must be a string or an array of strings",
    khien answer_relevancy = nan.
    """
    from src import llm_client

    return llm_client.langchain_llm(model), llm_client.langchain_embeddings()


def _evaluate_once(model: str, dataset) -> list[EvalResult]:
    """Chạy 4 metric bằng một model. NaN ở bất kỳ câu nào -> raise để tầng trên đổi model."""
    from ragas import RunConfig, evaluate
    from ragas.metrics import (answer_relevancy, context_precision,
                               context_recall, faithfulness)

    llm, embeddings = _ragas_llm_and_embeddings(model)
    # max_workers: OpenCode Go chịu được vài request song song (đã thử 4 -> 200 OK).
    # Đặt 1 nếu evaluator là LM Studio local (một request một lượt trên GPU).
    run_config = RunConfig(max_workers=int(os.getenv("RAGAS_MAX_WORKERS", "4")),
                           timeout=int(os.getenv("RAGAS_TIMEOUT", "300")), max_retries=3)
    result = evaluate(dataset,
                      metrics=[faithfulness, answer_relevancy,
                               context_precision, context_recall],
                      llm=llm, embeddings=embeddings,
                      run_config=run_config, raise_exceptions=False)

    frame = result.to_pandas()
    return [
        EvalResult(
            question=row["question"], answer=row["answer"],
            contexts=row["contexts"], ground_truth=row["ground_truth"],
            faithfulness=_metric(row.get("faithfulness"), "faithfulness", row["question"]),
            answer_relevancy=_metric(row.get("answer_relevancy"), "answer_relevancy", row["question"]),
            context_precision=_metric(row.get("context_precision"), "context_precision", row["question"]),
            context_recall=_metric(row.get("context_recall"), "context_recall", row["question"]),
        )
        for _, row in frame.iterrows()
    ]


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Chạy RAGAS 4 metric; tự động đổi sang FALLBACK_MODEL nếu model chính lỗi/cho NaN.

    Trả dict có `per_question` và `metadata.evaluator_models`. Task 2 bắt buộc lấy
    model evaluator từ đây (doc/PIPELINE_INTERFACE.md), không đoán JUDGE_MODEL,
    nên metadata phải ghi model THẬT SỰ đã chạy (kể cả khi đã fallback).
    """
    from datasets import Dataset

    from config import RAGAS_EMBEDDING_MODEL
    from src import llm_client

    lengths = {len(questions), len(answers), len(contexts), len(ground_truths)}
    if len(lengths) != 1:
        raise ValueError("m4: questions/answers/contexts/ground_truths phải cùng độ dài.")

    dataset = Dataset.from_dict({
        "question": questions, "answer": answers,
        "contexts": contexts, "ground_truth": ground_truths,
    })
    # Lỗi giữa chừng (429, timeout, content rỗng vì reasoning model) -> chạy lại
    # toàn bộ batch bằng FALLBACK_MODEL; trả về model thực sự dùng để ghi metadata.
    per_question, model_used = llm_client.run_with_model_fallback(
        lambda model: _evaluate_once(model, dataset))
    if not per_question:
        raise ValueError("m4: RAGAS không trả dòng nào.")

    def avg(attr: str) -> float:
        return round(sum(getattr(r, attr) for r in per_question) / len(per_question), 4)

    return {"faithfulness": avg("faithfulness"),
            "answer_relevancy": avg("answer_relevancy"),
            "context_precision": avg("context_precision"),
            "context_recall": avg("context_recall"),
            "per_question": per_question,
            "metadata": {"evaluator_models": sorted({model_used, RAGAS_EMBEDDING_MODEL}),
                         "model_used": model_used}}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM đang hallucinate — câu trả lời có thông tin không có trong context",
                         "Siết prompt, hạ temperature xuống 0, ép trích dẫn nguồn"),
        "context_recall": ("Thiếu chunk chứa đáp án trong context đã truy xuất",
                           "Cải thiện chunking, thêm BM25 vào hybrid, nới top_k khi truy xuất"),
        "context_precision": ("Quá nhiều chunk không liên quan lọt vào top-k",
                              "Thêm reranking, lọc theo metadata, giảm top_k xuống 3"),
        "answer_relevancy": ("Câu trả lời không khớp câu hỏi",
                             "Cải thiện prompt template, ép trả lời đúng 1 ý chính"),
    }

    scored = []
    for result in eval_results:
        metrics = {
            "faithfulness": result.faithfulness,
            "answer_relevancy": result.answer_relevancy,
            "context_precision": result.context_precision,
            "context_recall": result.context_recall,
        }
        worst_metric = min(metrics, key=lambda k: metrics[k])
        avg_score = sum(metrics.values()) / 4
        scored.append((avg_score, result, worst_metric))

    # Sắp xếp tăng dần theo điểm trung bình → lấy bottom_n câu hỏi tệ nhất.
    scored.sort(key=lambda item: item[0])

    failures = []
    for avg_score, result, worst_metric in scored[:bottom_n]:
        diagnosis, suggested_fix = diagnostic_tree[worst_metric]
        failures.append({
            "question": result.question,
            "worst_metric": worst_metric,
            "score": round(avg_score, 4),
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
        })
    return failures


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
