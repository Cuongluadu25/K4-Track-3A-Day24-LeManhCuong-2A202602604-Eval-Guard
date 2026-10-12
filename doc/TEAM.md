# Nhóm thực hiện K4 Track 3A

Tên nhóm: AI_Pro

Repo chung: https://github.com/Cuongluadu25/K4-Track-3A-Day24-LeManhCuong-2A202602604-Eval-Guard

Trưởng nhóm/người nộp: Lê Mạnh Cường - 2A202602604

Ngày lab/deadline áp dụng: 23:59 ngày diễn ra lab — Asia/Ho_Chi_Minh (UTC+07:00);
ngày cụ thể xác nhận theo thông báo của lớp.

Commit dùng để chấm: 5edca10 (cập nhật lại bằng SHA của commit cuối cùng trước khi nộp).

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Lê Mạnh Cường | 2A202602604 | Member A — nhóm trưởng: CP0 (môi trường, m1–m5, Qdrant, `artifacts/answers_50q.json`), provider NeMo `guardrails/config.py`, Task 13 `doc/reports/blueprint.md`, `doc/TEAM.md`, tích hợp và nộp bài | nhánh `feat/cp0-pipeline-deepseek` (commit `272af3c`, `33a2d55`, `9db80ec`); merge PR #1 `bc52c99`; `doc/TEAM.md`, `doc/reports/blueprint.md` |
| 2 | Nguyễn Trọng Minh | 2A202602496 | Member B — Phase A: `src/phase_a_ragas.py` (Task 1–4 `group_by_distribution` / `run_ragas_50q` / `bottom_10` / `cluster_analysis`), adapter `src/m4_eval.py` (`metadata.evaluator_models`, NaN⇒raise), hạ tầng dùng chung `src/llm_client.py` + `scripts/preflight.py`, `doc/reports/failure_clusters.md` | commit `0b814ea` (Task 1–4), `251e5d6` (adapter m4 + llm_client), `b22671a` (ép n≤1 cho evaluator), `e7f8ea7` (guard content rỗng khi generation); artifact `artifacts/ragas_50q.json`; báo cáo `doc/reports/failure_clusters.md`; log RAW `.hermes/llm_raw/` |
| 3 | Vũ Duy Điệp | 2A202602703 | Member C — Phase B: `src/phase_b_judge.py` (Task 5–8 `pairwise_judge` / `swap_and_average` / `cohen_kappa` / `bias_report`), `doc/reports/bias_report.md`, `artifacts/judge_results.json` | commit `5bf18c7` và `0aeaae1` (bản hoàn chỉnh sau khi revert `08d8060`); PR #1 `bc52c99`; `artifacts/judge_results.json`, `doc/reports/bias_report.md` |
| 4 | Nguyễn Mạnh Tiến | 2A202602506 | Member D — Phase C: `src/phase_c_guard.py` (Task 9a–12 `pii_scan` / `check_input_rail` / `run_adversarial_suite` / `check_output_rail` / `measure_p95_latency`), `guardrails/config.yml`, `artifacts/guard_results.json` | cập nhật sau khi thành viên hoàn thành và commit Phase C |

Người tích hợp/chạy batch/nộp link: Lê Mạnh Cường — kiểm tra `scripts/check_lab.py`
về 0 lỗi, rà secrets trước khi push, giữ `main` là bản chấm, và gửi một link repo
qua vlearn trước deadline. Bằng chứng là commit `doc/TEAM.md` và `doc/reports/blueprint.md`
trên `main`.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 Home Single Language (build 10.0.26200), Python 3.11.9.
Microsoft Visual Studio Community 2022, catalog 17.13.3, dùng để build `annoy`
(`annoy` được `nemoguardrails` kéo vào).

Virtualenv/dependencies/imports: `.venv` tạo bằng `py -3.11 -m venv .venv`; cài
`requirements/requirements.txt` kèm `requirements/constraints-core.txt`.
`.venv/Scripts/python.exe -m pip check` → "No broken requirements found."
Import `ragas`, `nemoguardrails`, `presidio_analyzer`, `spacy`, `annoy` đều thành công.

Models/Qdrant/50 answers đã chuẩn bị: Qdrant `qdrant/qdrant:v1.9.7` chạy ở port 6333;
embedding `BAAI/bge-m3` phục vụ qua LM Studio (`LOCAL_EMBED_BASE_URL=http://127.0.0.1:1234/v1`).
`artifacts/answers_50q.json` đủ 50 câu, phân bố 20 factual / 20 multi_hop / 10 adversarial,
`generation_mode = "llm"` cho cả 50 câu, không câu nào rỗng.

Lưu ý về provider: nhóm không dùng OpenAI mà dùng endpoint OpenAI-compatible
(`OPENAI_BASE_URL`) vì tài khoản cá nhân hết credit — API trả `429 insufficient_quota`,
`code: credit_balance_exhausted`. Vì vậy `config.py` cho phép đổi `LLM_MODEL` và
`OPENAI_BASE_URL` qua biến môi trường, và `guardrails/config.yml` giữ `model:` khớp
đúng model thật đang gọi.

## INDIVIDUAL

Mỗi thành viên thêm một heading `### HoTenKhongDau-MSSV` khớp đúng MSSV trong bảng phía trên, kèm 6 dòng như mẫu bên dưới.

### LeManhCuong-2A202602604

- Phần được giao và phần thực tế đã làm: Member A — nhóm trưởng, phụ trách CP0, Task 13 blueprint và khâu tích hợp/nộp bài. Dựng môi trường Python 3.11 + MSVC, chép năm module m1–m5 từ repo RAG buổi trước vào `src/`, dựng Qdrant v1.9.7, chạy `scripts/setup_answers.py --live` để sinh `artifacts/answers_50q.json`. Viết `guardrails/config.py` đăng ký engine `compat` vì NeMo Guardrails 0.10.0 chỉ chọn `ChatOpenAI` khi tên model chứa `gpt-3.5`/`gpt-4` (`providers.py:217-221`), nên không thể đổi provider chỉ bằng biến môi trường. Trên `main`: điền `doc/TEAM.md`, viết `doc/reports/blueprint.md`, chạy checker và nộp bài.
- Bằng chứng: nhánh `feat/cp0-pipeline-deepseek` gồm commit `272af3c` (m1–m5 + provider), `33a2d55` (`doc/TEAM.md`), `9db80ec` (`artifacts/answers_50q.json`); merge commit `bc52c99` (PR #1); các commit `doc/TEAM.md` và `doc/reports/blueprint.md` trên `main`. Kiểm chứng chéo bằng `git log --format='%h %an %s'`.
- Cách kiểm tra: `.venv/Scripts/python.exe -m pip check` → không lỗi; `docker ps` thấy `qdrant/qdrant:v1.9.7` ở port 6333; `python scripts/check_lab.py` để đối chiếu artifact; `git log --oneline` để truy vết commit.
- Điều đã học: phân biệt lỗi cài đặt với lỗi cấu hình provider; `model:` trong `guardrails/config.yml` được `guard_models()` ghi thẳng vào metadata kết quả nên không được khai một đằng chạy một nẻo; model dạng reasoning đốt hết `max_tokens` vào phần suy luận rồi trả `content` rỗng, khiến lỗi xảy ra âm thầm.
- Giới hạn/cách xử lý: nhánh CP0 `feat/cp0-pipeline-deepseek` dựng từ `main` cũ nên bị thành viên khác làm trước và vượt qua — nhóm đã có bản tốt hơn, nên nhánh đó được giữ làm bản lưu và **không merge** (merge sẽ kéo lùi `artifacts/answers_50q.json` và m1–m5). Task 13 blueprint chỉ viết được sau khi Phase C có `artifacts/guard_results.json` vì bảng latency phải lấy số thật.
- Nguồn/AI hỗ trợ nếu có: dùng Claude Code để tra lỗi build `annoy`/MSVC, dò chuỗi phụ thuộc `annoy` ← `nemoguardrails`, và đối chiếu giao diện m1–m5 với `doc/PIPELINE_INTERFACE.md`. Mọi kết luận đều kiểm chứng lại bằng lệnh chạy thật (`vswhere`, `pip check`, `docker ps`, `git log`); không dùng số liệu do AI sinh ra làm kết quả bài lab.

### NguyenTrongMinh-2A202602496

- Phần được giao và phần thực tế đã làm: Member B — Phase A (RAGAS & phân tích lỗi). Hoàn thiện 4 hàm TODO trong `src/phase_a_ragas.py`: `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis`. Sửa adapter `src/m4_eval.py` để m4 khai `metadata.evaluator_models` (Task 2 bắt buộc) và biến NaN thành lỗi thật thay vì ghi 0.0. Viết `src/llm_client.py` (client dùng chung: header `x-opencode-session`, model dự phòng, `max_tokens` cho reasoning model) và `scripts/preflight.py` (kiểm tra provider/embedding/corpus trước khi chạy `--live`). Điền `doc/reports/failure_clusters.md` từ `artifacts/ragas_50q.json`.
- Bằng chứng: commit `0b814ea` (Task 1–4), `251e5d6` (cắm m1–m5 + adapter m4 + llm_client), `b22671a` (ép `n≤1` cho evaluator), `e7f8ea7` (guard content rỗng khi generation); artifacts `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`; báo cáo `doc/reports/failure_clusters.md`.
- Cách kiểm tra: `python -m pytest tests/test_phase_a.py -q` → 6 passed; `python -m pytest tests/ -m support -q` → 67 passed; `python scripts/preflight.py` → 0 FAIL; `python scripts/run_experiments.py --phase a --live` → sinh `artifacts/ragas_50q.json` (50 per_question, 10 bottom rows, matrix 4×3) và `python scripts/check_lab.py` → pass artifact Phase A.
- Điều đã học: RAGAS trả NaN khi request bị provider từ chối (ví dụ tham số `n=3`), nên phải đọc RAW request/response mới thấy nguyên nhân — unit test offline không bắt được lớp lỗi này; và tự điền 0.0 cho NaN còn tệ hơn một lỗi đỏ vì nó lặng lẽ làm sai toàn bộ phân tích.
- Giới hạn/cách xử lý: evaluator là model miễn phí dạng preview, và `strictness` của `answer_relevancy` bị hạ về 1 do provider giới hạn `n≤1` (đã ghi rõ trong `failure_clusters.md`); m5 enrichment tắt ở lượt chạy answers đầu tiên nên retrieval dùng chunk gốc.
- Nguồn/AI hỗ trợ nếu có: dùng trợ lý AI để dựng môi trường, viết adapter và chạy lệnh; mọi số liệu trong báo cáo đến từ lượt chạy thật, tự kiểm chứng bằng pytest offline, `scripts/preflight.py` và log RAW `.hermes/llm_raw/`.

### VuDuyDiep-2A202602703

- Phần được giao và phần thực tế đã làm: Member C — Phase B, Tasks 5–8. Hoàn thiện pairwise_judge, swap_and_average, cohen_kappa và bias_report trong src/phase_b_judge.py; kiểm tra JSON, đảo winner/scores về candidate gốc; tích hợp client provider cho pairwise và binary. Viết doc/reports/bias_report.md từ kết quả thật.
- Bằng chứng: src/phase_b_judge.py, tests/test_phase_b.py, artifacts/judge_results.json, doc/reports/bias_report.md. Commit `5bf18c7` và `0aeaae1` (bản hoàn chỉnh sau khi revert `08d8060`); merge vào `main` qua PR #1 `bc52c99`.
- Cách kiểm tra: 88 tests offline pass (Phase B, support, report contracts, llm_client). Chạy một batch --phase b --live bằng deepseek-flash: đủ 5 cặp × 2 lượt và 10 binary judgments, κ=1.0, position inconsistency=0/5, longer-answer win rate=4/5. Runner validate schema và nguồn trước khi lưu.
- Điều đã học: Pairwise A/B/tie khác calibration 0/1. Swap cần đảo cả scores lẫn winner; κ điều chỉnh đồng thuận ngẫu nhiên. Tỷ lệ câu dài thắng không tự chứng minh bias vì chất lượng và độ dài có thể cùng thay đổi.
- Giới hạn/cách xử lý: Chỉ 5 cặp và 10 nhãn; không suy rộng κ=1.0 sang production. Case 21 cho thấy answer ngắn nhưng đầy đủ thắng answer dài thiếu lương. Cần mở rộng tập nhãn và thiết kế candidates cùng nội dung khác độ dài; giữ human review cho quyết định quan trọng.
- Nguồn/AI hỗ trợ nếu có: Codex hỗ trợ implement, tích hợp provider, viết tests, chạy API được cho phép và soạn báo cáo từ artifact thật. Không đưa human_label/human_note vào prompt; không sửa dữ liệu hoặc chạy lại để tăng điểm. Học viên cần tự đọc và kiểm chứng trước khi nộp.

### NguyenManhTien-2A202602506

- Phần được giao và phần thực tế đã làm: Member D — Phase C (guardrails). Thành viên tự khai báo sau khi hoàn thành 5 hàm trong `src/phase_c_guard.py` và sinh `artifacts/guard_results.json`.
- Bằng chứng: thành viên tự điền commit và artifact sau khi hoàn thành Phase C.
- Cách kiểm tra: thành viên tự ghi lệnh đã chạy và kết quả, gồm `python -m pytest tests/test_phase_c.py -q` và `python scripts/run_experiments.py --phase c --live --latency-samples 20`.
- Điều đã học: thành viên tự khai báo.
- Giới hạn/cách xử lý: thành viên tự khai báo.
- Nguồn/AI hỗ trợ nếu có: thành viên tự khai báo.

## Cập nhật sau khi nộp

Chưa có cập nhật sau khi nộp. Nếu phải sửa sau deadline, ghi rõ commit, thời điểm và
lý do, kèm xác nhận cho phép của coach trước khi áp dụng bản cập nhật.
