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
| 2 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 3 | Nguyễn Mạnh Tiến | 2A202602506 | Phase C: Tasks 9a–12 trong src/phase_c_guard.py, tests/test_phase_c.py, guardrails/config.yml, guardrails/rails.co | commit feat(phase-c),artifacts/guard_results.json |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: {{Phiên bản thực tế}}.
Virtualenv/dependencies/imports: {{Lệnh và kết quả}}.
Models/Qdrant/50 answers đã chuẩn bị: {{Bằng chứng và giới hạn/fallback}}.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

### NguyenManhTien-2A202602506
Phần được giao và phần thực tế đã làm: Phase C (35 điểm). Implement 5 hàm trong src/phase_c_guard.py: Task 9a pii_scan (Presidio, nhận diện CCCD/CMND, SĐT VN, email, trả vị trí start/end và bản anonymized); Task 9b check_input_rail (NeMo input rail, quyết định dựa trên rail.stop trong activated_rails, không dò từ khóa); Task 10 run_adversarial_suite (Presidio trước, NeMo input sau, một lần asyncio.run, giữ nguyên input, expected chỉ để đối chiếu); Task 11 check_output_rail (output rail trên cặp question/answer có sẵn); Task 12 measure_p95_latency (2 lượt warm-up thật loại khỏi mẫu, ít nhất 20 mẫu timed, luôn đo cả Presidio và NeMo, input_guard_ms là tổng hai tầng). Chỉnh prompt self_check_input và self_check_output trong guardrails/config.yml.
Bằng chứng: commit feat(phase-c) [ĐIỀN: SHA]; artifacts/guard_results.json gồm 20 attack, 8 clean, 4 output và latency raw samples.
Cách kiểm tra: unit test offline với engine/rails giả, lệnh python -m pytest tests/test_phase_c.py -q, kết quả 12 passed. Live experiment: python scripts/run_experiments.py --phase c --live --latency-samples 20, kết quả [ĐIỀN: attack passed /20, clean allowed /8, false_positive_rate, output cases đúng /4, p95 input_guard_ms so với budget 500ms].
Điều đã học: guard nhiều tầng (Presidio bắt PII có cấu trúc, NeMo self-check bắt jailbreak/off-topic/prompt injection); chặn tất cả sẽ đạt attack nhưng hỏng clean nên phải đo cả false positive; quyết định block phải lấy từ rail chứ không từ nội dung câu trả lời; latency cần warm-up và percentile nội suy tuyến tính, số vượt budget vẫn ghi số thật.
Giới hạn/cách xử lý: Presidio mặc định dùng spaCy tiếng Anh nên có thể báo nhầm PERSON/DATE_TIME trên câu tiếng Việt, vì vậy chỉ giữ các loại VN_CCCD, VN_PHONE, EMAIL_ADDRESS, PHONE_NUMBER; mẫu CMND 9 chữ số có thể trùng số bất kỳ. NeMo self-check phụ thuộc LLM nên kết quả có thể dao động giữa các lần chạy; đã siết prompt trong config.yml và kiểm chứng bằng kết quả live ở mục trên. Phần ngoài phạm vi (RAG, output rail, total guard) ghi "chưa đo".
Nguồn/AI hỗ trợ nếu có: dùng Claude để viết code 5 hàm và gợi ý chỉnh prompt trong config.yml; tự kiểm chứng bằng cách chạy test offline, đọc lại code đối chiếu hợp đồng trong doc/REPORT_SCHEMAS.md và chạy live experiment. [ĐIỀN: bổ sung nếu dùng thêm công cụ khác]

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
