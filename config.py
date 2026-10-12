"""Shared configuration for K4 / Track 3A: Eval + Guardrail Stack."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Optional: for HuggingFace models

# --- Qdrant (same as Day 18) ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "lab24_production"
NAIVE_COLLECTION = "lab24_naive"

# --- Embedding (same as Day 18) ---
# Plan 24 dùng LM Studio local cho embedding (OpenCode Go KHÔNG có /v1/embeddings).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "sentence_transformers")  # "lmstudio" | "sentence_transformers"
LOCAL_EMBED_BASE_URL = os.getenv("LOCAL_EMBED_BASE_URL", "http://127.0.0.1:1234/v1")
LOCAL_EMBED_API_KEY = os.getenv("LOCAL_EMBED_API_KEY", "lm-studio")

# --- Chunking (same as Day 18) ---
HIERARCHICAL_PARENT_SIZE = 2048
HIERARCHICAL_CHILD_SIZE = 256
SEMANTIC_THRESHOLD = 0.85

# --- Search (same as Day 18) ---
BM25_TOP_K = 20
DENSE_TOP_K = 20
HYBRID_TOP_K = 20
RERANK_TOP_K = 3

# --- Paths ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
FIXTURES_DIR = os.path.join(ROOT_DIR, "fixtures")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts")
TEST_SET_PATH = os.path.join(FIXTURES_DIR, "test_set_50q.json")
ANSWERS_PATH = os.path.join(ARTIFACTS_DIR, "answers_50q.json")
HUMAN_LABELS_PATH = os.path.join(FIXTURES_DIR, "human_labels_10q.json")
ADVERSARIAL_SET_PATH = os.path.join(FIXTURES_DIR, "adversarial_set_20.json")
CLEAN_SET_PATH = os.path.join(FIXTURES_DIR, "clean_set_8.json")
OUTPUT_SET_PATH = os.path.join(FIXTURES_DIR, "output_set_4.json")
GUARDRAILS_CONFIG_DIR = os.path.join(ROOT_DIR, "guardrails")
PAIR_QUESTION_IDS = (1, 5, 12, 21, 41)

# --- LLM Judge / provider ---
# Day 24 chạy trên OpenCode Go (OpenAI-compatible). GENERATION_MODEL/JUDGE_MODEL vẫn giữ
# giá trị mặc định của đề bài khi .env không khai gì, nhưng đọc .env trước để metadata
# trong artifacts ghi ĐÚNG model thực sự được gọi (không khai gpt-4o-mini khi gọi model khác).
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://opencode.ai/zen/go/v1")
OPENCODE_SESSION = os.getenv("OPENCODE_SESSION", "lab24-ragas")
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("GENERATION_MODEL") or "gpt-4o-mini"
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "glm-5.3-flash")
GENERATION_MODEL = os.getenv("GENERATION_MODEL") or LLM_MODEL
JUDGE_MODEL = os.getenv("JUDGE_MODEL") or LLM_MODEL
# Embedding cho RAGAS (LM Studio local; phải khác endpoint với LLM).
RAGAS_EMBEDDING_MODEL = os.getenv("RAGAS_EMBEDDING_MODEL", EMBEDDING_MODEL)

# --- Guardrail latency budget ---
LATENCY_BUDGET_P95_MS = 500  # Full guard target; Task 12 currently measures input guards only.
PRESIDIO_LANGUAGE = "en"    # Presidio base language; custom VN recognizers added via PatternRecognizer
