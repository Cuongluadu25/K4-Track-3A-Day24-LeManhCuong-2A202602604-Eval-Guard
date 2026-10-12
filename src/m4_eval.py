from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass
from math import isfinite

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH
from config import OPENAI_API_KEY
from config import EMBEDDING_MODEL, GENERATION_MODEL


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


def evaluator_models() -> list[str]:
    """Model IDs thật mà evaluator dùng; Phase A ghi giá trị này vào metadata."""
    return [GENERATION_MODEL, EMBEDDING_MODEL]


def build_evaluator_components():
    """Khởi tạo LLM + embeddings để truyền tường minh vào RAGAS.

    Không thể để RAGAS dùng mặc định: nó gọi `gpt-3.5-turbo` và
    `text-embedding-ada-002`, mà các endpoint OpenAI-compatible không có
    (DeepSeek không có endpoint embeddings) → Phase A chết.

    - LLM: `ChatOpenAI` đọc `OPENAI_API_BASE` từ env, model lấy từ config.
    - Embeddings: `BAAI/bge-m3` chạy local, đã cache sẵn từ module m2, không tốn phí.
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_openai import ChatOpenAI

    # RAGAS gọi LLM hàng trăm lần cho 50 câu; để model reasoning chạy mặc định
    # sẽ vừa chậm vừa tốn token gấp nhiều lần.
    llm = ChatOpenAI(model=GENERATION_MODEL, model_kwargs={"reasoning_effort": "none"})
    return llm, HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    metric_names = (
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    )
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("questions, answers, contexts, and ground_truths must have equal lengths")
    if not questions:
        return {
            **dict.fromkeys(metric_names, 0.0),
            "input_question_count": 0,
            "per_question": [],
            "metadata": {"evaluator_models": evaluator_models()},
        }

    if not OPENAI_API_KEY:
        error = "OPENAI_API_KEY is not configured; RAGAS evaluation was skipped."
        print(f"  ⚠️  {error}")
        return {
            **dict.fromkeys(metric_names, 0.0),
            "input_question_count": len(questions),
            "per_question": [],
            "evaluation_error": error,
            "metadata": {"evaluator_models": evaluator_models()},
        }

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        llm, embeddings = build_evaluator_components()
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=llm,
            embeddings=embeddings,
        )
        dataframe = result.to_pandas()

        def metric_value(value) -> float:
            try:
                score = float(value)
            except (TypeError, ValueError):
                return 0.0
            return score if isfinite(score) else 0.0

        per_question = [
            EvalResult(
                question=row["question"],
                answer=row["answer"],
                contexts=list(row["contexts"]),
                ground_truth=row["ground_truth"],
                faithfulness=metric_value(row.get("faithfulness", 0.0)),
                answer_relevancy=metric_value(row.get("answer_relevancy", 0.0)),
                context_precision=metric_value(row.get("context_precision", 0.0)),
                context_recall=metric_value(row.get("context_recall", 0.0)),
            )
            for _, row in dataframe.iterrows()
        ]
        return {
            **{
                name: metric_value(dataframe[name].mean()) if name in dataframe else 0.0
                for name in metric_names
            },
            "input_question_count": len(questions),
            "per_question": per_question,
            "metadata": {"evaluator_models": evaluator_models()},
        }
    except Exception as error:
        message = f"RAGAS evaluation failed: {error}"
        print(f"  ⚠️  {message}")
        return {
            **dict.fromkeys(metric_names, 0.0),
            "input_question_count": len(questions),
            "per_question": [],
            "evaluation_error": message,
            "metadata": {"evaluator_models": evaluator_models()},
        }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    if bottom_n < 0:
        raise ValueError("bottom_n must be non-negative")

    diagnostic_tree = {
        "faithfulness": (
            "The answer may contain claims unsupported by the retrieved context.",
            "Tighten the grounding prompt, reduce generation temperature, and verify citations.",
        ),
        "context_recall": (
            "The retrieved context may be missing information needed to answer the question.",
            "Improve chunking and query coverage, or add complementary BM25 retrieval.",
        ),
        "context_precision": (
            "The retrieved context may contain too many irrelevant chunks.",
            "Improve reranking and apply appropriate metadata filters.",
        ),
        "answer_relevancy": (
            "The answer may not directly address the user's question.",
            "Improve the answer prompt and require a concise, question-focused response.",
        ),
    }

    failures = []
    for result in eval_results:
        metric_scores = {
            name: float(getattr(result, name))
            for name in diagnostic_tree
        }
        worst_metric = min(metric_scores, key=metric_scores.__getitem__)
        diagnosis, suggested_fix = diagnostic_tree[worst_metric]
        failures.append({
            "question": result.question,
            "answer": result.answer,
            "ground_truth": result.ground_truth,
            "contexts": result.contexts,
            "average_score": sum(metric_scores.values()) / len(metric_scores),
            "worst_metric": worst_metric,
            "score": metric_scores[worst_metric],
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
            "error_tree": (
                f"Output quality → {worst_metric} is lowest "
                f"({metric_scores[worst_metric]:.3f}) → {diagnosis}"
            ),
        })

    failures.sort(key=lambda item: item["average_score"])
    return failures[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {
            k: v for k, v in results.items()
            if k not in {"per_question", "input_question_count"}
        },
        "input_question_count": results.get(
            "input_question_count",
            len(results.get("per_question", [])),
        ),
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
