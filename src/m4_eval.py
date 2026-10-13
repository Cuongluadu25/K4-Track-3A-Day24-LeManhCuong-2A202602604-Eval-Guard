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


def _metric_value(value) -> float:
    """Chuyển metric RAGAS thành float; NaN/inf được GIỮ NGUYÊN để tầng trên xử lý.

    Tầng trên (`evaluate_ragas`) mới là nơi quyết định: chạy lại đúng những câu bị NaN
    bằng model khác, và chỉ raise khi vẫn không lấy được số thật. Tuyệt đối không thay
    NaN bằng 0.0 (doc/PIPELINE_INTERFACE.md dòng 34 cấm "tự thay NaN bằng điểm giả").
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


METRIC_NAMES = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
RAGAS_MAX_TOKENS = int(os.getenv("RAGAS_MAX_TOKENS", "3072"))
# Model dùng để chạy lại RIÊNG các câu bị NaN (chỉ một số ít câu, không chạy lại cả batch).
REPAIR_MODELS = [name.strip() for name in
                 os.getenv("RAGAS_REPAIR_MODELS", "qwen3.8-max,glm-5.3-flash").split(",")
                 if name.strip()]


def _ragas_llm_and_embeddings(model: str, *, max_tokens: int = RAGAS_MAX_TOKENS):
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

    return llm_client.langchain_llm(model, max_tokens=max_tokens), llm_client.langchain_embeddings()


def _evaluate_once(model: str, dataset, *, max_tokens: int = RAGAS_MAX_TOKENS) -> list[dict]:
    """Chạy 4 metric bằng MỘT model; trả list dict theo đúng thứ tự của dataset.

    KHÔNG raise khi metric là NaN: đó là việc của `evaluate_ragas` (chạy lại đúng những
    câu hỏng bằng model khác). Giữ nguyên NaN để không giấu việc chấm điểm thất bại.
    """
    from ragas import RunConfig, evaluate
    from ragas.metrics import (answer_relevancy, context_precision,
                               context_recall, faithfulness)

    llm, embeddings = _ragas_llm_and_embeddings(model, max_tokens=max_tokens)
    # max_workers: OpenCode Go chịu được vài request song song (đã thử 4 -> 200 OK).
    run_config = RunConfig(max_workers=int(os.getenv("RAGAS_MAX_WORKERS", "4")),
                           timeout=int(os.getenv("RAGAS_TIMEOUT", "300")), max_retries=3)
    result = evaluate(dataset,
                      metrics=[faithfulness, answer_relevancy,
                               context_precision, context_recall],
                      llm=llm, embeddings=embeddings,
                      run_config=run_config, raise_exceptions=False)

    frame = result.to_pandas()
    return [{"question": row["question"],
             **{name: _metric_value(row.get(name)) for name in METRIC_NAMES}}
            for _, row in frame.iterrows()]


def _nan_rows(rows: list[dict]) -> list[dict]:
    """Các dòng còn thiếu ít nhất một metric hữu hạn."""
    return [row for row in rows
            if any(not isfinite(row.get(name, float("nan"))) for name in METRIC_NAMES)]


def _dataset_of(rows: list[dict]):
    """Dataset nhỏ chỉ gồm các dòng cần chạy lại (chỉ 1 lời gọi cho mỗi dòng)."""
    from datasets import Dataset

    return Dataset.from_dict({"question": [row["question"] for row in rows],
                              "answer": [row["answer"] for row in rows],
                              "contexts": [row["contexts"] for row in rows],
                              "ground_truth": [row["ground_truth"] for row in rows]})


def _merge_repaired(rows: list[dict], repaired: list[dict]) -> int:
    """Ghép kết quả chạy lại vào dòng gốc theo `question`; CHỈ nhận giá trị hữu hạn."""
    by_question = {row["question"]: row for row in repaired}
    applied = 0
    for row in rows:
        patch = by_question.get(row["question"])
        if patch is None:
            continue
        for name in METRIC_NAMES:
            value = patch.get(name, float("nan"))
            if isfinite(value):
                row[name] = value
        if all(isfinite(row[name]) for name in METRIC_NAMES):
            applied += 1
    return applied


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Chạy RAGAS 4 metric; sửa đúng những câu bị NaN; không bao giờ ghi điểm giả.

    Quy trình:
      1. Một lượt đầy đủ bằng LLM_MODEL. Lỗi transport (429/timeout) -> chạy lại cả batch
         bằng FALLBACK_MODEL (`llm_client.run_with_model_fallback`).
      2. Câu nào có metric NaN (model không trả về đúng định dạng RAGAS yêu cầu - thực tế
         đã gặp với model free) -> chạy lại DUY NHẤT những câu đó theo REPAIR_MODELS
         (mặc định `qwen3.8-max` rồi `glm-5.3-flash`): vài lời gọi, không chạy lại 200 bước.
      3. Vẫn còn NaN -> raise kèm tên câu. Không thay NaN bằng 0.0.

    Trả dict có `per_question` và `metadata.evaluator_models` = mọi model thật sự đã tạo ra
    số (model lượt chính + model dùng để sửa) cùng model embedding - Task 2 lấy từ đây.
    """
    from config import RAGAS_EMBEDDING_MODEL
    from src import llm_client

    lengths = {len(questions), len(answers), len(contexts), len(ground_truths)}
    if len(lengths) != 1:
        raise ValueError("m4: questions/answers/contexts/ground_truths phải cùng độ dài.")

    source_rows = [{"question": q, "answer": a, "contexts": c, "ground_truth": g}
                   for q, a, c, g in zip(questions, answers, contexts, ground_truths)]
    raw_rows, model_used = llm_client.run_with_model_fallback(
        lambda model: _evaluate_once(model, _dataset_of(source_rows)))
    models_used = {model_used}

    bad = _nan_rows(raw_rows)
    print(f"  RAGAS: {len(raw_rows) - len(bad)}/{len(raw_rows)} câu đủ 4 metric; "
          f"{len(bad)} câu bị NaN (model không parse được output)")
    source_by_question = {row["question"]: row for row in source_rows}
    for repair_model in REPAIR_MODELS:
        if not bad:
            break
        print(f"  ↻ chạy lại {len(bad)} câu bằng {repair_model}: "
              f"{[row['question'][:40] for row in bad[:3]]}")
        try:
            # `bad` chỉ có question + metric: phải lấy lại answer/contexts/ground_truth gốc.
            repaired = _evaluate_once(
                repair_model,
                _dataset_of([source_by_question[row["question"]] for row in bad]))
        except Exception as error:                      # noqa: BLE001 - sửa được thì sửa
            print(f"  ⚠️  sửa bằng {repair_model} lỗi: {error}")
            continue
        applied = _merge_repaired(raw_rows, repaired)
        if applied:
            models_used.add(repair_model)
        print(f"     → {applied}/{len(bad)} câu đã đủ 4 metric")
        bad = _nan_rows(raw_rows)

    if bad:
        detail = "; ".join(
            f"'{row['question'][:60]}' thiếu "
            f"{[name for name in METRIC_NAMES if not isfinite(row[name])]}"
            for row in bad[:5])
        raise ValueError(f"m4: còn {len(bad)} câu NaN sau khi chạy lại: {detail}")

    per_question = [
        EvalResult(question=source["question"], answer=source["answer"],
                   contexts=source["contexts"], ground_truth=source["ground_truth"],
                   **{name: raw[name] for name in METRIC_NAMES})
        for source, raw in zip(source_rows, raw_rows)
    ]

    def avg(attr: str) -> float:
        return round(sum(getattr(item, attr) for item in per_question) / len(per_question), 4)

    return {"faithfulness": avg("faithfulness"),
            "answer_relevancy": avg("answer_relevancy"),
            "context_precision": avg("context_precision"),
            "context_recall": avg("context_recall"),
            "per_question": per_question,
            "metadata": {"evaluator_models": sorted(models_used | {RAGAS_EMBEDDING_MODEL}),
                         "model_used": model_used,
                         "repair_models": sorted(models_used - {model_used})}}


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
