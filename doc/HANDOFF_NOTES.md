# Ghi chú bàn giao giữa các thành viên (làm việc, không phải báo cáo nộp bài)

Tài liệu này để cả nhóm biết **ai đang chờ ai**. Không phải một phần của rubric; có thể xoá trước khi nộp
nếu nhóm thấy không cần.

## 1. Trạng thái hiện tại

| Hạng mục | Trạng thái |
|---|---|
| `src/m1..m5*.py` | ✅ có trong repo (copy từ Day 18) + adapter cho provider mới |
| `src/phase_a_ragas.py` (Task 1–4) | ✅ xong, `# TODO` = 0, `pytest tests/test_phase_a.py -q` → 6 passed |
| `src/phase_b_judge.py`, `src/phase_c_guard.py` | ⏳ còn TODO (Member C và D) |
| `artifacts/answers_50q.json` | ✅ có, 50 câu, 20/20/10, mode=llm, đã validate schema |
| `artifacts/ragas_50q.json` | ✅ **ĐÃ CÓ** (12/10/2026 21:44, `run_kind=live`): 50 dòng `per_question`, đủ 4 metric hữu hạn 50/50 sau khi chạy lại 13 câu NaN bằng `qwen3.8-max` (8 câu) và `glm-5.3-flash` (5 câu) |
| `artifacts/judge_results.json` | ✅ C đã đẩy lên `main` (`bc52c99`); `guard_results.json` ⏳ của D |
| `doc/reports/failure_clusters.md` | ✅ **đã điền** bằng số thật; `validate_markdown` PASS |
| `doc/TEAM.md` | 🔶 đã có dòng + mục INDIVIDUAL của **Nguyễn Trọng Minh (2A202602496)**; còn `{{...}}` ở dòng 3, 5, 7, 9, 11, 20, 22, 24, 28, 29, 30, 49 (A điền: tên nhóm, link repo, người nộp, deadline, commit chấm, dòng thành viên 1 và 3, người tích hợp, môi trường) |
| `doc/reports/bias_report.md`, `blueprint.md` | 🔶 C đã điền bias_report; `blueprint.md` của A còn `{{...}}` |

## 2. Ai có thể làm ngay, ai phải chờ (trả lời câu hỏi "có cần đợi 200 bước của B không?")

| Thành viên | Có cần chờ lượt RAGAS 50 câu của B không? | Ghi chú |
|---|---|---|
| **Member C — Phase B** | ❌ **KHÔNG** | Phase B dùng A = `answer` trong `artifacts/answers_50q.json` (đã có) và B = `model_answer` trong `fixtures/human_labels_10q.json`; không đọc `ragas_50q.json`. Làm được ngay. |
| **Member D — Phase C** | ❌ **KHÔNG** | Chỉ dùng fixtures guard + NeMo; nhưng đang bị chặn bởi `annoy` (xem mục 4). |
| **Member A — Task 13 blueprint** | 🔶 **một phần** | Blueprint cần số của cả 3 phase (RAGAS mean/worst distribution của B, κ của C, attacks/clean của D). A có thể viết phần kiến trúc, CI gates, monitoring, môi trường, TEAM trước; chỉ phần số liệu Phase A mới phải chờ B chạy xong. |

**Kết luận:** chỉ **A (phần số liệu) và chính B** phải chờ lượt chạy đầy đủ; C và D không nên ngồi đợi.

## 3. Vì sao B vẫn cần lượt chạy đầy đủ 50 câu

`src/report_contracts.py::validate_phase_a` (và `check_lab.py`) **bắt buộc** `total_questions == 50`,
`per_question` đúng 50 dòng theo id, cộng matrix và bottom-10. Một batch nhỏ chỉ dùng để **kiểm tra đường ống**,
không thể trở thành artifact nộp bài. Vì vậy:

- Batch nhỏ (3–10 câu) = kiểm chứng code chạy đúng (đã làm).
- Lượt đầy đủ 200 bước = bắt buộc để có `artifacts/ragas_50q.json`. Thời gian đo thật ngày 12/10/2026: **43:31 cho lượt chính** (13.1 s/bước) + **~15 phút cho lượt chạy lại các câu NaN** = khoảng **60 phút**, không tốn tiền (model free + embedding local). Ước lượng "12 phút" ở bản trước là sai vì lúc đó câu trả lời còn rất ngắn.

## 4. Việc cụ thể cho từng người

### Member C — Phase B (`src/phase_b_judge.py`, `tests/test_phase_b.py`, `doc/reports/bias_report.md`)
1. Hoàn thành Task 5–8 theo `PHAN_CONG.md`. Test offline: `python -m pytest tests/test_phase_b.py -q` → phải `8 passed`.
2. ⚠️ **Bắt buộc biết:** `scripts/run_experiments.py`/`src/experiment_runners.py` gọi `judge_binary()` trong
   `src/experiment_support.py` và tự tạo `OpenAI()` **trần**. Với OpenCode Go, client trần sẽ lỗi
   `400 MissingSessionID` vì thiếu header `x-opencode-session`, và SDK pin của đề bài (`openai==1.109.1`)
   **không** đọc biến `OPENAI_CUSTOM_HEADERS`. Cách xử lý (đã có sẵn trong repo):
   ```python
   from src import llm_client
   client = llm_client.chat_client()        # hoặc llm_client.chat(..., caller="phase_b")
   ```
   `src/experiment_support.py` và `src/experiment_runners.py` là **file dùng chung** → sửa thì báo cả nhóm.
3. ⚠️ Provider **từ chối tham số `n > 1`** (`n=3` → HTTP 400). Nếu chỗ nào cần nhiều mẫu, hãy gọi nhiều lần
   thay vì truyền `n`.
4. ⚠️ Model là reasoning model: luôn đặt `max_tokens ≥ 512` cho mỗi lời gọi, nếu không `content` trả về `null`.
5. Chạy live **một lần**: `python scripts/run_experiments.py --phase b --live`.

### Member D — Phase C (`src/phase_c_guard.py`, `guardrails/*`, `artifacts/guard_results.json`)
1. ⚠️ **Chặn cài đặt:** `nemoguardrails 0.10.0` yêu cầu `annoy>=1.17.3`, mà PyPI **không có wheel cho Windows**
   (chỉ có sdist) → cần **Microsoft C++ Build Tools** (workload *Desktop development with C++*), hoặc lấy
   `annoy` từ conda-forge rồi cài vào môi trường. Chưa cài được `nemoguardrails` thì Phase C chưa chạy được.
2. `python -m spacy download en_core_web_lg` là bắt buộc cho Presidio.
3. ⚠️ `guardrails/config.yml` đang là `engine: openai / model: gpt-4o-mini`. Trỏ vào OpenCode Go cần
   `base_url` + header `x-opencode-session` (NeMo 0.10.0 dùng langchain-openai bên dưới) — phải thử và ghi lại.
4. `pii_scan`, `check_input_rail`, `check_output_rail`, `run_adversarial_suite`, `measure_p95_latency` theo
   `PHAN_CONG.md`; test offline: `python -m pytest tests/test_phase_c.py -q` → `12 passed`.

### Member A — Setup & Task 13
1. `doc/TEAM.md`: thêm dòng + mục `INDIVIDUAL` cho các thành viên còn lại (mẫu đã có trong file; MSSV phải
   khác nhau và heading đúng dạng `HoVaTen-MSSV`).
2. `doc/reports/blueprint.md`: bảng latency lấy từ `artifacts/guard_results.json` của D; phần RAG/NeMo output/
   full guard ghi **"chưa đo"**; số RAGAS lấy từ `artifacts/ragas_50q.json` của B (chờ B chạy xong).
3. `python scripts/check_lab.py` là cổng cuối: hiện còn `FAIL` ở TEAM (thiếu thành viên), 2 report của C/A,
   và 2 file `phase_*.py` còn TODO — đúng như mong đợi.

## 5. Môi trường chung (để cả nhóm dùng lại, không phải dò lại)

- Python 3.11 tạo bằng conda: `conda create -p D:/py311-lab24 python=3.11 pip`, rồi `D:/py311-lab24/python.exe -m venv .venv`.
- Phase A đã cài đủ (ragas 0.1.22, langchain-openai 0.1.25, datasets 2.21, sentence-transformers, torch, underthesea, pypdf, qdrant-client 1.9.2).
  **Chưa** cài `nemoguardrails`/`presidio` vì lý do `annoy` ở mục 4.
- Ghim thêm: `requirements/constraints-local.txt` (`pyarrow==16.1.0`) vì pyarrow 26 đòi numpy≥2 trong khi đề bài pin numpy 1.26.4.
- `.env` (không commit) chứa key OpenCode Go + token LM Studio; xem `doc/LLM_PROVIDER_SETUP.md` để biết cách khai.
- Kiểm tra trước khi chạy `--live`: `python scripts/preflight.py` (kiểm tra provider, embedding local, corpus, answers).
- Log RAW mọi lời gọi LLM nằm ở `.hermes/llm_raw/` (đã bị gitignore): `python scripts/llm_log_summary.py`.
