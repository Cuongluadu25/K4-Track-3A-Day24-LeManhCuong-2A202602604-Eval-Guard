# Nhóm thực hiện K4 Track 3A

Tên nhóm: {{Tên nhóm}}

Repo chung: {{Link repo}}

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 2 | Nguyễn Trọng Minh | 2A202602496 | Member B — Phase A: `src/phase_a_ragas.py` (Task 1–4 `group_by_distribution` / `run_ragas_50q` / `bottom_10` / `cluster_analysis`), adapter `src/m4_eval.py` (`metadata.evaluator_models`, NaN⇒raise), hạ tầng dùng chung `src/llm_client.py` + `scripts/preflight.py`, `doc/reports/failure_clusters.md` | commit `0b814ea` (Task 1–4), `251e5d6` (adapter m4 + llm_client), `b22671a` (ép n≤1 cho evaluator), `e7f8ea7` (guard content rỗng khi generation); artifact `artifacts/ragas_50q.json`; báo cáo `doc/reports/failure_clusters.md`; log RAW `.hermes/llm_raw/` |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: {{Phiên bản thực tế}}.
Virtualenv/dependencies/imports: {{Lệnh và kết quả}}.
Models/Qdrant/50 answers đã chuẩn bị: {{Bằng chứng và giới hạn/fallback}}.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

Mỗi thành viên thêm một heading `### HoTenKhongDau-MSSV` khớp đúng MSSV trong bảng phía trên, kèm 6 dòng như mẫu bên dưới.

### NguyenTrongMinh-2A202602496

- Phần được giao và phần thực tế đã làm: Member B — Phase A (RAGAS & phân tích lỗi). Hoàn thiện 4 hàm TODO trong `src/phase_a_ragas.py`: `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis`. Sửa adapter `src/m4_eval.py` để m4 khai `metadata.evaluator_models` (Task 2 bắt buộc) và biến NaN thành lỗi thật thay vì ghi 0.0. Viết `src/llm_client.py` (client dùng chung: header `x-opencode-session`, model dự phòng, `max_tokens` cho reasoning model) và `scripts/preflight.py` (kiểm tra provider/embedding/corpus trước khi chạy `--live`). Điền `doc/reports/failure_clusters.md` từ `artifacts/ragas_50q.json`.
- Bằng chứng: commit `0b814ea` (Task 1–4), `251e5d6` (cắm m1–m5 + adapter m4 + llm_client), `b22671a` (ép `n≤1` cho evaluator), `e7f8ea7` (guard content rỗng khi generation); artifacts `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`; báo cáo `doc/reports/failure_clusters.md`.
- Cách kiểm tra: `python -m pytest tests/test_phase_a.py -q` → 6 passed; `python -m pytest tests/ -m support -q` → 67 passed; `python scripts/preflight.py` → 0 FAIL; `python scripts/run_experiments.py --phase a --live` → sinh `artifacts/ragas_50q.json` (50 per_question, 10 bottom rows, matrix 4×3) và `python scripts/check_lab.py` → pass artifact Phase A.
- Điều đã học: RAGAS trả NaN khi request bị provider từ chối (ví dụ tham số `n=3`), nên phải đọc RAW request/response mới thấy nguyên nhân — unit test offline không bắt được lớp lỗi này; và tự điền 0.0 cho NaN còn tệ hơn một lỗi đỏ vì nó lặng lẽ làm sai toàn bộ phân tích.
- Giới hạn/cách xử lý: evaluator là model miễn phí dạng preview, và `strictness` của `answer_relevancy` bị hạ về 1 do provider giới hạn `n≤1` (đã ghi rõ trong `failure_clusters.md`); m5 enrichment tắt ở lượt chạy answers đầu tiên nên retrieval dùng chunk gốc.
- Nguồn/AI hỗ trợ nếu có: dùng trợ lý AI để dựng môi trường, viết adapter và chạy lệnh; mọi số liệu trong báo cáo đến từ lượt chạy thật, tự kiểm chứng bằng pytest offline, `scripts/preflight.py` và log RAW `.hermes/llm_raw/`.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
