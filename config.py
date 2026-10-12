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
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

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

# --- LLM Judge ---
# Model dùng cho cả generation (setup_answers, m5 enrichment) lẫn judge (Phase B).
# Mặc định giữ nguyên gpt-4o-mini nên chạy với OpenAI thật không đổi hành vi.
# Khi trỏ vào endpoint OpenAI-compatible khác thì đặt LAB_LLM_MODEL trong .env.
# LƯU Ý: phải đổi `model:` trong guardrails/config.yml cho khớp, vì giá trị đó
# được guard_models() ghi thẳng vào metadata của artifacts/guard_results.json.
LLM_MODEL = os.getenv("LAB_LLM_MODEL", "gpt-4o-mini")
GENERATION_MODEL = LLM_MODEL
JUDGE_MODEL = LLM_MODEL

# --- Guardrail latency budget ---
LATENCY_BUDGET_P95_MS = 500  # Full guard target; Task 12 currently measures input guards only.
PRESIDIO_LANGUAGE = "en"    # Presidio base language; custom VN recognizers added via PatternRecognizer
