# Provider LLM/embedding cho Lab 24 (đã kiểm chứng, không phải suy đoán)

Tài liệu này ghi lại cấu hình provider mà nhóm dùng để chạy Phase A/B/C, kèm bằng chứng
từ các request thật. Mọi thành viên cần đọc trước khi tự chạy `--live`.

## 1. LLM: OpenCode Go (OpenAI-compatible)

| Hạng mục | Giá trị |
|---|---|
| Base URL | `https://opencode.ai/zen/go/v1` |
| Endpoint | `/chat/completions` (OpenAI-compatible) |
| Danh sách model | `GET /v1/models` → 38 model |
| Auth | `Authorization: Bearer $OPENCODE_GO_API_KEY` |
| Header **bắt buộc** | `x-opencode-session: <chuỗi ổn định>` |
| User-Agent | Nên khai báo riêng (ví dụ `lab24-ragas-eval/1.0`); UA mặc định của thư viện HTTP dễ bị Cloudflare chặn 403 |

**Bằng chứng (request thật):**

- Thiếu `x-opencode-session` với model hợp lệ → `HTTP 400`
  `{"type":"MissingSessionID","message":"Request is missing x-opencode-session..."}`.
- Có header, gọi `deepseek-v4.1-flash` → `HTTP 200`, trả `OK`.
- 4 request song song vào `longcat-2.5-preview-free` → cả 4 đều `HTTP 200` (4.98–14.6 giây/request).
- Gọi bằng `urllib` (UA mặc định của Python) → `HTTP 403 error code: 1010` (Cloudflare) dù
  key đúng; cùng request đó bằng `curl` → `200`. Vì vậy `src/llm_client.py` khai báo User-Agent riêng.

### 1.1 Model: chọn gì, và điều đã kiểm chứng

| Model | Trạng thái | Ghi chú |
|---|---|---|
| `longcat-2.5-preview-free` | **Dùng làm model chính** — HTTP 200 | Miễn phí (bản preview có thời hạn) |
| `glm-5.3-flash` | **Model dự phòng** — HTTP 200, trả `OK` | Nằm trong gói Go |
| `qwen3.8-max` | HTTP 200 (docs ghi endpoint `/messages` nhưng `/chat/completions` vẫn chạy) | Mạnh hơn, dùng khi cần chất lượng |
| `step-5-preview-free` | **Không dùng được**: `HTTP 429 Upstream request failed: Endpoint is unavailable.` | Có trong `/v1/models` nhưng upstream chết |
| `gpt-5-nano` | **Không tồn tại**: `HTTP 400 Model is unavailable` | Không có id nào chứa "nano"; họ GPT chỉ có `gpt-5.6-luna`, `gpt-6-luna` |
| `deepseek-v4.1-flash` | HTTP 200 | Mặc định của Hermes |

**LƯU Ý QUAN TRỌNG — reasoning model và `max_tokens`:** mọi model trên đều sinh
`reasoning_content` trước `content`. Khi `max_tokens` nhỏ, `content` trả về `null`
(`finish_reason = "length"`) — đã thấy ở `max_tokens` 20 và 50. Vì vậy:

- `max_tokens` **≥ 500** cho mỗi lời gọi (JSON của judge/RAGAS cần 500–1024).
- `src/llm_client.py` đặt mặc định 1024 và `_extract_content()` báo lỗi rõ ràng nếu
  `content` rỗng, thay vì trả chuỗi rỗng âm thầm.
- `response_format={"type":"json_object"}` **chạy được** (đã xác nhận trả về JSON sạch khi
  `max_tokens` đủ lớn) → dùng được cho `judge_binary` và `pairwise_judge`.

### 1.2 Fallback tự động

`.env`: `LLM_MODEL=longcat-2.5-preview-free`, `FALLBACK_MODEL=glm-5.3-flash`.

- `llm_client.chat()` đổi model **trong cùng một lời gọi** nếu model chính lỗi.
- `llm_client.run_with_model_fallback(run)` chạy lại **cả batch** (dùng cho RAGAS, vì một
  metric hỏng là hỏng cả lượt) và trả về model thực sự đã dùng → ghi vào
  `metadata.evaluator_models`, không khai khống.

## 2. Embedding: LM Studio local (OpenCode Go KHÔNG có embedding)

- `POST https://opencode.ai/zen/go/v1/embeddings` → trả về **trang HTML** (không phải JSON):
  provider này không phục vụ embedding. Vì vậy embedding phải lấy từ máy local.
- LM Studio đang chạy ở `http://127.0.0.1:1234/v1`, hiện chỉ nạp **`text-embedding-bge-m3`**.
- Đã kiểm chứng: `GET /v1/models` → 200 với token; `POST /v1/embeddings` cho
  `"nghi phep nam 12 ngay"` → 200, vector **1024 chiều** (khớp `EMBEDDING_DIM = 1024`).
- Server yêu cầu `Authorization: Bearer <token>`; thiếu token → `HTTP 401`.

Ràng buộc khi dùng:

1. LM Studio phải **đang bật** trong suốt lượt chạy cần embedding (index/query và metric
   `answer_relevancy` của RAGAS). Tắt giữa lượt → metric NaN → `m4_eval` raise
   (cố ý: thà đỏ còn hơn ghi 0.0 giả).
2. `check_embedding_ctx_length=False` là **bắt buộc** với `OpenAIEmbeddings`; mặc định `True`
   khiến LangChain gửi mảng token id và LM Studio trả 400.
3. Chỉ dùng được từ chính máy này (loopback). Chạy trong WSL/Docker/máy khác sẽ không tới được.
4. Embedding ở local, nhưng nội dung câu hỏi/answer/contexts/ground_truth vẫn được gửi lên
   LLM cloud để chấm điểm — cần biết khi viết phần privacy trong `blueprint.md`.

## 3. Cách khai `.env` (không commit file này)

```dotenv
OPENAI_API_KEY=<key OpenCode Go>          # lấy ở opencode.ai (auth), KHÔNG commit
OPENAI_BASE_URL=https://opencode.ai/zen/go/v1
OPENAI_CUSTOM_HEADERS=x-opencode-session: lab24-ragas   # SDK >= 2.x đọc biến này
LLM_MODEL=longcat-2.5-preview-free
FALLBACK_MODEL=glm-5.3-flash

EMBED_BACKEND=lmstudio
EMBEDDING_MODEL=text-embedding-bge-m3
RAGAS_EMBEDDING_MODEL=text-embedding-bge-m3
LOCAL_EMBED_BASE_URL=http://127.0.0.1:1234/v1
LOCAL_EMBED_API_KEY=<token LM Studio>
```

`OPENAI_CUSTOM_HEADERS` là biến của chính SDK openai (định dạng `Tên: giá trị`, nhiều dòng
cách nhau bằng `\n`). **Phải kiểm tra lại trong venv của lab**: `constraints-core.txt` pin
`openai==1.109.1`, và biến này chỉ chắc chắn có ở SDK bản mới hơn. Kiểm tra nhanh:

```bash
".venv/Scripts/python.exe" -c "import inspect, openai; from openai import OpenAI; print(openai.__version__); print('default_headers' in inspect.signature(OpenAI.__init__).parameters)"
```

Nếu bản trong venv không hỗ trợ `OPENAI_CUSTOM_HEADERS`, các client do **code của nhóm** tạo
vẫn OK vì `src/llm_client.py` truyền `default_headers=` trực tiếp. Chỉ còn 2 chỗ do đề bài
cung cấp là tạo client trần: `src/experiment_support.judge_binary()` (Phase B) và
`src/experiment_runners.run_phase_b()` — hai file **dùng chung**, sửa phải báo cả nhóm.

## 4. Ảnh hưởng theo từng phase

| Phase | Việc phải làm với provider |
|---|---|
| **A (RAGAS)** | Xong: `src/m4_eval.py` dùng `llm_client.langchain_llm(model)` + `langchain_embeddings()`, tự fallback model, khai `metadata.evaluator_models` |
| **A (setup answers)** | `scripts/setup_answers.py` gọi `OpenAI()` trần cho generation → cần `OPENAI_CUSTOM_HEADERS` hoặc sửa script (dùng chung) để dùng `llm_client` |
| **B (judge)** | `run_phase_b` và `judge_binary` tạo client trần → cùng vấn đề header như trên |
| **C (guardrails)** | `guardrails/config.yml` đang là `engine: openai / model: gpt-4o-mini`; cần `base_url` + headers cho NeMo 0.10.0 → Member D |
| **Retrieval** | `m2_search.py` đã hỗ trợ `EMBED_BACKEND=lmstudio`, không cần torch nếu dùng đường này |

## 5. Cảnh báo sử dụng

OpenCode Go được thiết kế cho traffic của coding agent và có theo dõi lạm dụng. Batch RAGAS
(200–350 lời gọi cho 50 câu) là traffic khác thường: nên để `RAGAS_MAX_WORKERS=4` (đã thử 4
song song OK), không tăng lên 16, và không chạy lại cùng một batch nhiều lần cho "đẹp số".
Free preview model có thể biến mất giữa chừng — đó là lý do có `FALLBACK_MODEL`.
