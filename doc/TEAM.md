# Nhóm thực hiện K4 Track 3A

Tên nhóm: AI_Pro

Repo chung: https://github.com/Cuongluadu25/K4-Track-3A-Day24-LeManhCuong-2A202602604-Eval-Guard

Trưởng nhóm/người nộp: Lê Mạnh Cường - 2A202602604

Ngày lab/deadline áp dụng: 23:59 ngày làm lab — Asia/Ho_Chi_Minh (UTC+07:00);
ngày cụ thể xác nhận theo thông báo của lớp.

Commit dùng để chấm: cập nhật sau khi push bản cuối cùng.

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Lê Mạnh Cường | 2A202602604 | CP0 (môi trường, m1–m5, Qdrant, .env) + Task 13 blueprint + doc/TEAM.md + tích hợp và nộp bài | cập nhật sau khi push |
| 2 | Nguyễn Trọng Minh | 2A202602496 | Phase A — src/phase_a_ragas.py Tasks 1–4, doc/reports/failure_clusters.md, artifacts/ragas_50q.json | cập nhật sau khi push |
| 3 | Vũ Duy Điệp | 2A202602703 | Phase B — src/phase_b_judge.py Tasks 5–8, doc/reports/bias_report.md, artifacts/judge_results.json | cập nhật sau khi push |
| 4 | Nguyễn Mạnh Tiến | 2A202602506 | Phase C — src/phase_c_guard.py Tasks 9a–12, artifacts/guard_results.json, guardrails/config.yml | cập nhật sau khi push |

Người tích hợp/chạy batch/nộp link: Lê Mạnh Cường — chạy scripts/setup_answers.py --live,
chạy scripts/run_experiments.py cho cả ba phase, chạy scripts/check_lab.py, kiểm tra
secrets, push và gửi một link repo qua vlearn.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 Home Single Language (build 10.0.26200), Python 3.11.9,
Microsoft Visual Studio Community 2022 với workload Desktop development with C++
(MSVC 14.43.34808 và Windows SDK 10.0.22621.0).

Virtualenv/dependencies/imports: `.venv` tạo bằng `py -3.11 -m venv .venv`; cài
`requirements/requirements.txt` kèm `requirements/constraints-core.txt`. `pip check`
báo "No broken requirements found"; import `ragas`, `nemoguardrails`,
`presidio_analyzer`, `spacy`, `annoy` đều thành công.

Models/Qdrant/50 answers đã chuẩn bị: Qdrant `qdrant/qdrant:v1.9.7` chạy ở port 6333;
spaCy `en_core_web_lg` đã tải xong; năm module m1–m5 đã có trong `src/`.
`artifacts/answers_50q.json` **đã sinh xong**: 50 câu đúng 20 factual / 20 multi_hop /
10 adversarial, `generation_mode = "llm"`, `generation_model = "deepseek-flash"`,
`contexts` và `answer` tách riêng khỏi `ground_truth`.

Ba lỗi thực tế gặp phải khi chạy `scripts/setup_answers.py --live`, theo thứ tự:

1. `pyarrow 26.0.0` xung đột với `numpy 1.26.4` mà `constraints-core.txt` ghim
   (`pyarrow requires NumPy 2.0 or newer`). Đã xử lý bằng cách hạ về `pyarrow 16.1.0`
   và `pandas 2.2.3`, giữ nguyên `numpy 1.26.4` theo bộ phiên bản lõi của starter.
2. Tài khoản OpenAI không còn credit — API trả `429 insufficient_quota`,
   `code: credit_balance_exhausted`; cả 102/102 lời gọi enrichment đều thất bại.
   Nhóm không nạp credit mà chuyển sang DeepSeek — endpoint OpenAI-compatible, có
   bản miễn phí. Việc này đòi hỏi đăng ký engine `compat` trong `guardrails/config.py`
   cho Phase C (NeMo 0.10.0 chỉ chọn `ChatOpenAI` khi tên model chứa `gpt-3.5`/`gpt-4`).
3. `deepseek-flash` là model reasoning: nó đốt hết `max_tokens` vào `reasoning_content`
   rồi trả `content` rỗng, khiến enrichment và generation hỏng âm thầm. Đã tắt bằng
   `reasoning_effort: none` và nâng `max_tokens` của enrichment từ 400 lên 1200 để
   JSON tiếng Việt không bị cắt mất dấu `}` cuối.

Không dùng extractive fallback để tạo answers thay cho chạy thật.
`generation_mode` và `generation_model` trong `artifacts/answers_50q.json` phản ánh
đúng cấu hình đã chạy, khớp với `model:` trong `guardrails/config.yml`.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### LeManhCuong-2A202602604

- Phần được giao và phần thực tế đã làm: Nhóm trưởng, phụ trách CP0 và Task 13.
  Đã tạo virtualenv Python 3.11, cài MSVC và toàn bộ dependencies, chép năm module
  m1–m5 từ repo RAG buổi trước vào `src/` rồi đối chiếu từng chữ ký với
  `doc/PIPELINE_INTERFACE.md`, khởi động Qdrant v1.9.7, tải model spaCy, tạo `.env`
  và kiểm tra key. Phát hiện và xử lý ba lỗi chặn setup: xung đột pyarrow/numpy, tình
  trạng hết credit của API, và model reasoning trả `content` rỗng. Sau khi chuyển sang
  DeepSeek đã chạy thành công `scripts/setup_answers.py --live`, sinh
  `artifacts/answers_50q.json` đủ 50 câu với `generation_mode = "llm"`.
- Bằng chứng: commit cho `doc/TEAM.md`, `PHAN_CONG.md`, `src/m1_chunking.py` … `m5_enrichment.py`;
  kết quả `pip check`; log chạy `scripts/setup_answers.py --live`.
- Cách kiểm tra: `.venv/Scripts/python.exe -m pip check`; `docker ps` thấy container
  `qdrant/qdrant:v1.9.7` ở port 6333; chạy `scripts/setup_answers.py --live` và đọc log
  để phân biệt lỗi môi trường với lỗi API.
- Điều đã học: phân biệt lỗi cài đặt với lỗi cấu hình provider; cách đọc file constraint
  để hiểu vì sao pip chọn phiên bản gây xung đột; NeMo Guardrails 0.10.0 chỉ chọn
  `ChatOpenAI` khi tên model chứa `gpt-3.5` hoặc `gpt-4` (`providers.py:217-221`), nên
  không thể đổi provider chỉ bằng biến môi trường — phải đăng ký engine riêng
  (`guardrails/config.py`) để điều kiện đó không được thoả và NeMo dùng thẳng class đã
  đăng ký. Cũng học được rằng `model:` trong `guardrails/config.yml` được
  `guard_models()` ghi thẳng vào metadata kết quả, nên không được khai một đằng chạy
  một nẻo.
- Giới hạn/cách xử lý: chưa đo được P95 latency của Phase C vì phần đó thuộc Task 12 của
  thành viên khác. Task 13 blueprint chưa viết vì blueprint phải dựa trên kết quả thật
  của ba phase, hiện chưa có artifacts. Chất lượng 50 câu trả lời còn hạn chế: 12/50 câu
  trả lời "Không tìm thấy", tập trung ở nhóm multi_hop (9/20) — đây là dữ liệu thật để
  Phase A phân tích thành failure cluster, không được che đi.
- Nguồn/AI hỗ trợ nếu có: có dùng Claude Code để tra lỗi build `annoy`/MSVC, dò chuỗi
  phụ thuộc `annoy` ← `nemoguardrails`, và đối chiếu giao diện m1–m5 với
  `doc/PIPELINE_INTERFACE.md`. Mọi kết luận đều kiểm chứng lại bằng lệnh chạy thật trên
  máy (`vswhere`, `pip check`, `docker ps`, log setup); không dùng số liệu do AI sinh ra
  làm kết quả bài lab.

### NguyenTrongMinh-2A202602496

- Phần được giao và phần thực tế đã làm: thành viên phụ trách Phase A khai báo tại đây.
- Bằng chứng: cập nhật sau khi push.
- Cách kiểm tra: thành viên tự khai báo lệnh đã chạy và kết quả.
- Điều đã học: thành viên tự khai báo.
- Giới hạn/cách xử lý: thành viên tự khai báo.
- Nguồn/AI hỗ trợ nếu có: thành viên tự khai báo.

### VuDuyDiep-2A202602703

- Phần được giao và phần thực tế đã làm: thành viên phụ trách Phase B khai báo tại đây.
- Bằng chứng: cập nhật sau khi push.
- Cách kiểm tra: thành viên tự khai báo lệnh đã chạy và kết quả.
- Điều đã học: thành viên tự khai báo.
- Giới hạn/cách xử lý: thành viên tự khai báo.
- Nguồn/AI hỗ trợ nếu có: thành viên tự khai báo.

### NguyenManhTien-2A202602506

- Phần được giao và phần thực tế đã làm: thành viên phụ trách Phase C khai báo tại đây.
- Bằng chứng: cập nhật sau khi push.
- Cách kiểm tra: thành viên tự khai báo lệnh đã chạy và kết quả.
- Điều đã học: thành viên tự khai báo.
- Giới hạn/cách xử lý: thành viên tự khai báo.
- Nguồn/AI hỗ trợ nếu có: thành viên tự khai báo.

## Cập nhật sau khi nộp

Chưa nộp. Phiên bản nộp và commit SHA sẽ được ghi vào đây sau khi push bản cuối.
Nếu có sửa sau deadline, ghi rõ commit, thời điểm và lý do theo doc/RULES.md.
