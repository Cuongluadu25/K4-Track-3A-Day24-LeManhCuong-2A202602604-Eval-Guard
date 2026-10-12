# PHÂN CÔNG CÔNG VIỆC — Nhóm 4 người

**Bài lab:** K4 Track 3A — Production Eval + Guardrail Stack (Day 24)
**Repo đề bài:** [K4-Track-3A-Day24-Eval-Guard](https://github.com/VinUni-AI20k/K4-Track-3A-Day24-Eval-Guard)
**Repo nộp nhóm:** `K4-L3-DAY24-TenNhom-Eval-Guard`
**Deadline:** **23:59 ngày diễn ra lab** (Asia/Ho_Chi_Minh, UTC+07:00)
**Hình thức nộp:** Trưởng nhóm gửi **một link repo GitHub chung** qua vlearn.

> **Quy ước bắt buộc:** Mỗi người tự commit phần mình làm trên máy mình — **không commit hộ**.
> README ghi rõ: *"Ai cũng phải có commit, dùng để chấm sau này."* Rubric cũng nêu
> *"TEAM và lịch sử Git là bằng chứng đóng góp cá nhân."*

---

## 1. Bảng điền tên thành viên

> ⚠️ **Nhóm tự điền bảng này trước khi bắt đầu.** Các chỗ `Member A/B/C/D` ở phần
> dưới là placeholder, thay bằng tên thật sau khi điền.

**Tên nhóm:** `__________________`
**Người nộp bài (trưởng nhóm):** `__________________`
**Link repo nộp:** `__________________`

| Mã | Vai trò | Họ và tên | MSSV | GitHub username | Email |
|---|---|---|---|---|---|
| Member A | Nhóm trưởng — Setup & Đóng gói | | | | |
| Member B | Phase A — RAGAS & phân tích lỗi | | | | |
| Member C | Phase B — Pairwise judge & calibration | | | | |
| Member D | Phase C — Guardrails & latency | | | | |

> Lưu ý: `doc/TEAM.md` yêu cầu **MSSV khác nhau** cho từng người và **mỗi thành viên
> phải có một heading `### Họ-Tên-MSSV`** khớp với bảng.

---

## 2. Bảng tổng quan phân công

| Mã | Phạm vi phụ trách | File sở hữu (không ai khác sửa) | Điểm rubric | Deliverable chính |
|---|---|---|---:|---|
| **A** | CP0 + Task 13 + đóng gói | `src/m1_*.py` … `m5_*.py`, `doc/TEAM.md`, `doc/reports/blueprint.md` | CP0 (chặn Phase A) + blueprint (−10 nếu trống) | `artifacts/answers_50q.json`, `blueprint.md`, `TEAM.md` |
| **B** | Phase A — Tasks 1–4 | `src/phase_a_ragas.py`, `tests/test_phase_a.py`, `doc/reports/failure_clusters.md` | **30** | `artifacts/ragas_50q.json`, `failure_clusters.md` |
| **C** | Phase B — Tasks 5–8 | `src/phase_b_judge.py`, `tests/test_phase_b.py`, `doc/reports/bias_report.md` | **35** | `artifacts/judge_results.json`, `bias_report.md` |
| **D** | Phase C — Tasks 9a–12 | `src/phase_c_guard.py`, `tests/test_phase_c.py`, `guardrails/*` | **35** | `artifacts/guard_results.json` |

**Tổng điểm bắt buộc: 30 + 35 + 35 = 100 điểm** (+ tối đa 10 bonus).

---

## 3. Timeline

| Mốc | Thời lượng | Nội dung | Phụ trách |
|---|---|---|---|
| **CP0** — Trước lớp | Trước buổi lab | Môi trường Python 3.11, copy m1–m5, Qdrant, sinh 50 answers | **A** |
| Kiểm tra sẵn sàng | 15 phút | Xác nhận venv/Qdrant/module/50 answers; chốt phân công | Cả nhóm |
| **CP1** — Phase A | 30 phút | Tasks 1–4 → chạy runner A | **B** |
| **CP2** — Phase B | 30 phút | Tasks 5–8 → chạy runner B | **C** |
| **CP3** — Phase C | 30 phút | Tasks 9a–12 → chạy runner C | **D** |
| **CP4** — Tổng hợp | Sau lớp | 3 báo cáo + TEAM + `check_lab.py` + push + nộp link | **A** + cả nhóm |

> Trong 15 phút đầu buổi: chỉ kiểm tra những gì **đã chuẩn bị trước** — không tải
> model, không indexing, không generation tại lớp.

---

## 4. Chi tiết theo từng thành viên

### Member A — Nhóm trưởng / Setup & Đóng gói (critical path)

**Vai trò:** Chặn toàn bộ nhóm — 3 phase không chạy được nếu CP0 chưa xong.

**CP0 — Chuẩn bị trước lớp**

| Việc | Chi tiết |
|---|---|
| Môi trường | Python **3.11**; cài theo [doc/ENVIRONMENT.md](doc/ENVIRONMENT.md) |
| Dependencies | `requirements/requirements.txt` + `requirements/constraints-core.txt` (full runtime); `requirements/requirements-test.lock.txt` cho unit tests offline |
| **Copy m1–m5** | 🚧 **Blocker lớn nhất:** `src/` **chưa có** `m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`, `m5_enrichment.py`. Phải mang từ repo RAG buổi trước vào `src/`, đối chiếu [doc/PIPELINE_INTERFACE.md](doc/PIPELINE_INTERFACE.md). `scripts/setup_answers.py` sẽ **lỗi ngay** nếu thiếu. `pipeline.py` chỉ để tham khảo — setup **không gọi** file này. |
| Qdrant | Khởi động `qdrant/qdrant:v1.9.7` qua [infra/docker-compose.yml](infra/docker-compose.yml) |
| Model | Tải spaCy + embedding `BAAI/bge-m3` + rerank **trước lớp** (không tải tại lớp) |
| Secrets | Kiểm key trong `.env` (tạo từ `.env.example`) |
| Sinh answers | `python scripts/setup_answers.py --live` |

**Tiêu chí hoàn thành CP0:**
- `artifacts/answers_50q.json` đủ **50 id**, đúng **20 factual / 20 multi_hop / 10 adversarial**.
- Mỗi bản ghi có `answer`, `contexts`, `ground_truth` **tách biệt**.
- `generation_mode` ghi rõ `llm` hay extractive fallback; `generation_model` là ID model hoặc `null` với fallback.
- **Không lấy `ground_truth` làm `answer`.** Giữ nguyên question/distribution/ground_truth gốc.
- ⚠️ Nếu thiếu `artifacts/answers_50q.json` → **Phase A = 0 điểm** (rubric).

**Task 13 — Blueprint & đóng gói**

- Điền [doc/reports/blueprint.md](doc/reports/blueprint.md) từ bằng chứng A/B/C: kiến trúc, failure actions, CI gates, monitoring, latency input-layer đã đo, đề xuất cải tiến.
- Đây là **đề xuất**, không mặc nhiên là workflow đã chạy. Ngưỡng **18/20** là bonus/CI gate đề xuất; ngưỡng lab bắt buộc vẫn **15/20**.
- Phần ngoài phạm vi Task 12 (RAG/output/full guard latency) ghi **"chưa đo"** + kế hoạch. **Không** dùng `input_guard_ms` làm full-guard latency.
- ❌ Không để `{{placeholder}}`, dấu `?` hay bảng rỗng → **trừ 10 điểm**.

**`doc/TEAM.md`**
- Bảng thành viên (họ tên, MSSV, vai trò, việc làm, bằng chứng) — MSSV **khác nhau**.
- Dòng khai **integrator / batch-runner / submitter**.
- Ghi chú môi trường.
- Mỗi thành viên một mục `INDIVIDUAL`: việc đã làm, bằng chứng, cách kiểm chứng, điều học được, hạn chế, **khai báo phần dùng AI**.
- Ghi **commit SHA đã nộp**.
- *Mỗi người tự viết phần INDIVIDUAL của mình, A tổng hợp lại.*

**Đóng gói & nộp**
```bash
python scripts/check_lab.py          # hoặc --with-tests nếu muốn gộp unit tests
```
- Kiểm secrets trước khi commit `artifacts/*.json`.
- Push lên repo chung, gửi **một link** qua vlearn trước deadline.
- ❌ Không commit `.env`, API key, virtualenv, cache model.

**Bằng chứng commit:** các commit `chore(cp0):`, `docs(team):`, `docs(blueprint):`.

---

### Member B — Phase A: RAGAS & phân tích lỗi (30 điểm)

**File sở hữu:** [src/phase_a_ragas.py](src/phase_a_ragas.py), [tests/test_phase_a.py](tests/test_phase_a.py), [doc/reports/failure_clusters.md](doc/reports/failure_clusters.md)

| Task | Hàm | Điểm | Hợp đồng bắt buộc |
|---|---|---:|---|
| 1 | `group_by_distribution` | 5 | Trả **3 keys**, đúng số câu **20 factual / 20 multi_hop / 10 adversarial** |
| 2 | `run_ragas_50q` | 10 | Gọi `m4.evaluate_ragas`; trả `RagasEvaluation` chứa **50 `RagasResult`**; `evaluator_models` lấy từ `metadata["evaluator_models"]` của m4; đủ **4 metric hữu hạn trong [0,1]** |
| 3 | `bottom_10` | 7 | **10 câu**, tăng dần theo `avg_score`; đủ `rank/id/question/distribution/worst_metric/diagnosis/suggested_fix` |
| 4 | `cluster_analysis` | 8 | Matrix `worst_metric × distribution`; insight; nhóm yếu nhất theo `avg_score` trung bình **thấp nhất** |

**Chi tiết cần hiểu (dễ mất điểm):**

- **Task 2 — model ID:** metadata Phase A phải giữ **model ID thực tế của evaluator**, tách khỏi generation/judge/guard. Thiếu thông tin model thì **sửa adapter m4**, ❌ **không** dùng `JUDGE_MODEL` điền thay.
- **Task 3 — exporter:** runner truyền đúng kết quả Task 3 vào exporter; exporter **giữ nguyên** `diagnosis`/`suggested_fix` của bạn, **không tính lại để ghi đè**.
- **Task 4 — matrix đếm MỌI câu**, theo `worst_metric` của từng câu, **không** định nghĩa tất cả là failures. Tổng mỗi cột = 20/20/10 (đây là **số câu**, không phải chất lượng).
- **Task 4 — chọn nhóm yếu:** dùng **điểm trung bình thấp nhất**, ❌ **không** chọn `max tổng` (làm vậy chỉ chọn ra nhóm lớn nhất). Nhóm rỗng phải **bỏ khỏi phép chia** — không tự gán 0 chất lượng cho nhóm không có dữ liệu.
- ❌ Không chấp nhận list rỗng, `NaN`, missing rows.

**Chạy:**
```bash
python -m pytest tests/test_phase_a.py -q
python scripts/run_experiments.py --phase a --live
```

**Bẫy trong corpus (cố ý, không được xóa):** có bản policy **cũ/mới** — `nghi_phep_nam_v2023.md` vs `nghi_phep_nam_v2024.md`, `mat_khau_v1.md` vs `mat_khau_v2.md`. Đây là bẫy version conflict; **không xóa bản cũ để làm eval dễ hơn**.

**Deliverable:** `artifacts/ragas_50q.json` (50 per_question, 10 bottom rows, matrix/mean/insight) + `doc/reports/failure_clusters.md` giải thích lỗi retrieval vs generation.

**Bonus Phase A (+4):** `adversarial mean < factual mean`, kèm phân tích bẫy. Lưu ý: adversarial thấp hơn **chỉ cho thấy nhóm đó khó hơn**, không tự chứng minh pipeline nhận ra version conflict.

**Bằng chứng commit:** `feat(phase-a): ...`, `docs(failure-clusters): ...`.

---

### Member C — Phase B: Pairwise judge & calibration (35 điểm)

**File sở hữu:** [src/phase_b_judge.py](src/phase_b_judge.py), [tests/test_phase_b.py](tests/test_phase_b.py), [doc/reports/bias_report.md](doc/reports/bias_report.md)

| Task | Hàm | Điểm | Hợp đồng bắt buộc |
|---|---|---:|---|
| 5 | `pairwise_judge(q, A, B, reference="")` | 10 | JSON `winner` = A/B/tie, `reasoning`, `scores` A/B trong [0,1]; dùng `reference` để chấm accuracy |
| 6 | `swap_and_average(q, A, B, reference="")` | 10 | **2 lượt** A/B rồi B/A; **convert winner/scores về A/B ban đầu**; đồng thuận hoặc tie |
| 7 | `cohen_kappa(judge_labels, human_labels)` | 10 | κ từ **10 nhãn đúng thứ tự**; mixed perfect agreement = 1; giá trị trong **[-1, 1]** |
| 8 | `bias_report` | 5 | Đếm **position inconsistency**; tỷ lệ winner **dài hơn** trong các case decisive; có diễn giải |

**Nguồn 5 cặp A/B — id `1, 5, 12, 21, 41`:**

| Thành phần | Nguồn |
|---|---|
| **A** | `answer` đã lưu trong `artifacts/answers_50q.json` |
| **B** | `model_answer` cùng id trong [fixtures/human_labels_10q.json](fixtures/human_labels_10q.json) |
| question / reference | [fixtures/test_set_50q.json](fixtures/test_set_50q.json) |

- Ghi rõ `pair_sources` trong JSON.
- ❌ Không tự đổi B thành ground truth; ❌ không sửa candidate sau khi xem judge để tăng điểm.
- Hai lượt swap nhận **cùng** question/reference.

**10 nhãn binary — dùng helper có sẵn:**
```python
from src.experiment_support import judge_binary
judge_binary(question, answer, reference)
```

| Quy tắc | |
|---|---|
| Gửi gì | **Đúng `question` và `model_answer` đang có trong file**, reference = `ground_truth` cùng `question_id` |
| ❌ Cấm | Gửi `human_label` hoặc `human_note` vào prompt |
| ❌ Cấm | Thay bằng `answer` mới của pipeline |
| Định dạng | JSON `label` **integer 0/1** + `reasoning` — không nhận bool/string hay winner A/B |
| Thứ tự | Giữ `ids` và thứ tự đồng bộ cho `judge_labels`/`human_labels` rồi mới gọi Task 7 |
| ⚠️ | Dataset có **6 nhãn human=1, 4 nhãn human=0** — **không** đưa tỉ lệ này vào prompt |

**Phân biệt hai loại kết quả (điểm hay nhầm nhất):**
- **A/B/tie** = chọn giữa **hai** candidate.
- **Nhãn 0/1** = đánh giá **một** answer cụ thể so với reference.
- ❌ Không chuyển A/B thắng sang 1/0 một cách máy móc.

**Chạy:**
```bash
python -m pytest tests/test_phase_b.py -q
python scripts/run_experiments.py --phase b --live
```

**Deliverable:** `artifacts/judge_results.json` (5 cặp × 2 lượt, 10 binary judgments, calibration/κ, bias report) + `doc/reports/bias_report.md`.

**Bonus Phase B (+3):** κ > 0.6 trên **đúng 10 supplied `model_answer`**.

**Lưu ý kết luận:** position inconsistency **không tự chứng minh** nguyên nhân là bias; verbosity win rate **chỉ là dấu hiệu** — phải đọc nội dung trước khi kết luận.

**Bằng chứng commit:** `feat(phase-b): ...`, `docs(bias-report): ...`.

---

### Member D — Phase C: Guardrails & latency (35 điểm)

**File sở hữu:** [src/phase_c_guard.py](src/phase_c_guard.py), [tests/test_phase_c.py](tests/test_phase_c.py), `artifacts/guard_results.json`, [guardrails/config.yml](guardrails/config.yml), [guardrails/rails.co](guardrails/rails.co)

| Task | Hàm | Điểm | Hợp đồng bắt buộc |
|---|---|---:|---|
| 9a | `pii_scan` | 10 | Presidio detect/anonymize **CCCD/CMND, VN phone, email**; trả `entities` kèm **vị trí** |
| 9b | `check_input_rail` (async) | 5 | Chỉ chạy **input rail**; `allowed`/`blocked_reason`/`response` phản ánh **quyết định của rail** |
| 10 | `run_adversarial_suite` | 10 | Nhận list inputs bất kỳ; **giữ nguyên input**; `expected` **chỉ dùng đối chiếu**; trả đủ các rows |
| 11 | `check_output_rail` (async) | 5 | Kiểm answer có sẵn bằng output rail; `safe`/`final_answer`/`flagged_reason` |
| 12 | `measure_p95_latency` | 5 | Warm-up thật **2 lượt**, **≥20 samples** timed, raw samples + percentile cho input layers |

**Ngưỡng đạt (Task 10):**

| Chỉ số | Ngưỡng |
|---|---|
| Attacks đạt | **≥ 15/20** (bonus nếu **≥ 18/20**) |
| Clean controls allowed | **8/8** — bắt buộc kể cả khi đạt bonus |
| `false_positive_rate` | = clean bị blocked / 8 |

- Runner gọi Task 10 cho **28 inputs trong một batch**: **20 attacks** từ [fixtures/adversarial_set_20.json](fixtures/adversarial_set_20.json) + **8 clean** từ [fixtures/clean_set_8.json](fixtures/clean_set_8.json), tách theo id.
- ⚠️ **Always-block đạt 20/20 attacks nhưng FAIL clean controls** → không được điểm Task 10. Bộ clean set có chủ ý để phát hiện false positives (nghỉ phép, khung lương, VPN, mật khẩu).
- ❌ **Không** xác định block bằng từ "xin lỗi/không thể" — các từ này **có thể xuất hiện trong câu sạch**.

**Task 11 — 4 output cases** từ [fixtures/output_set_4.json](fixtures/output_set_4.json) (2 sạch, 2 nhạy cảm): output sạch **giữ nguyên** answer; output nhạy cảm **thay/redact**.

**Task 12 — latency (nhiều ràng buộc nhỏ, dễ sai):**
- `scope` bắt buộc = **`input_layers_sequential`**.
- Luôn đo **Presidio rồi NeMo input**, ❌ **không short-circuit**.
- **Tạo engine trước khi đo.**
- Warm-up **thật 2 lượt**, **bị loại khỏi samples**.
- **≥ 20 timed samples**, `input_guard_ms` = **tổng từng sample**.
- Percentile **nội suy tuyến tính**.
- Phần ngoài phạm vi (request thật, RAG/output rail, total guard) ghi **"chưa đo"**.
- ⚠️ Số đo **vượt budget 500ms vẫn ghi số thật** và phân tích — ❌ **không** sửa số cho đạt. (Xem [doc/REPORT_SCHEMAS.md](doc/REPORT_SCHEMAS.md).)

**NeMo Guardrails 0.10.0 / Colang 1.0:**
- Dùng built-in self-check và policy prompts trong [guardrails/config.yml](guardrails/config.yml); [guardrails/rails.co](guardrails/rails.co) định nghĩa câu từ chối.
- Khi truyền options: đọc `result.response[0]["content"]` và `result.log.activated_rails`.

**Chạy:**
```bash
python -m pytest tests/test_phase_c.py -q
python scripts/run_experiments.py --phase c --live --latency-samples 20
```

**Deliverable:** `artifacts/guard_results.json` chứa **20 attack results, 8 clean results, 4 output results** và **latency raw samples/statistics**.

**Bonus Phase C (+3):** ≥18/20 attacks **và** clean 8/8 allowed.

**Bằng chứng commit:** `feat(phase-c): ...`.

---

## 5. Ma trận phụ thuộc

```
CP0 (A) ──┬──> Phase A (B) ──┐
          ├──> Phase B (C) ──┼──> Task 13 Blueprint (A) ──> TEAM (A)
          └──> Phase C (D) ──┘           │
                                         v
                             check_lab.py ──> push & nộp link (A)
```

| Phụ thuộc | Lý do |
|---|---|
| **CP0 → Phase A/B/C** | Cả 3 phase cần `artifacts/answers_50q.json`. Phase B còn cần nó làm **nguồn A**. |
| **Phase A/B/C → Task 13** | Blueprint viết từ bằng chứng của cả 3 phase. |
| **Task 13 + TEAM → check_lab → nộp** | Checker validate schema/counts/sources trước khi nộp. |

✅ **B, C, D làm hoàn toàn song song** sau khi CP0 xong — không chặn nhau (khác file, khác artifact).
🚧 **A là critical path** — nếu CP0 trễ, cả nhóm đứng.

---

## 6. Hằng số & hợp đồng dùng chung

Thống nhất để mỗi người không hardcode một kiểu (nguồn: `config.py`, `src/report_contracts.py`):

| Hằng số | Giá trị |
|---|---|
| `GENERATION_MODEL` | `gpt-4o-mini` |
| `JUDGE_MODEL` | `gpt-4o-mini` |
| Embedding model | `BAAI/bge-m3` |
| Qdrant collection | `lab24_production` |
| Latency budget | **500ms** (mục tiêu, không phải ngưỡng cắt số) |
| `PAIR_QUESTION_IDS` | `(1, 5, 12, 21, 41)` |

**Hợp đồng JSON:**
- Mọi artifact phải có `metadata.format_version = 2` với **4 danh sách model tách theo vai trò**: generation / evaluator / judge / guard.
- Checker cross-check **id, nguồn, trung bình, matrix, κ, pass flags, percentile** — lệch nhỏ cũng bị từ chối.
- Số hàm TODO phải xóa hết: `phase_a` = 4, `phase_b` = 4, `phase_c` = 5 (tổng **13**).

---

## 7. Quy ước làm việc nhóm

| Quy ước | |
|---|---|
| **Sở hữu file** | Mỗi người **chỉ sửa file mình sở hữu**. Sửa file chung (`src/experiment_support.py`, `src/experiment_runners.py`, `scripts/*`) → **báo nhóm trước**. |
| **Commit message** | `<type>(<scope>): <mô tả>` — ví dụ `feat(phase-a): task 1-2 group_by_distribution + run_ragas_50q` |
| **Commit hộ** | ❌ Không. Ai làm người đó commit — đây là bằng chứng chấm điểm cá nhân. |
| **Chạy `--live`** | ❌ Không chạy 2 lần cho cùng batch (tránh trả phí 2 lần). |
| **Integration tests** | Là **lựa chọn thay thế** cho batch B/C — ❌ không chạy cả hai. |
| **Tests & network** | Tests mặc định **chặn network**. Muốn gọi API phải dùng `--run-live` / `--live`. |
| **Báo cáo** | Là bằng chứng thật, không viết chung chung. ❌ Không `{{placeholder}}`, không bảng rỗng. |
| **Secrets** | Commit `artifacts/*.json` **sau khi kiểm secrets**. ❌ Không commit `.env`, API key, virtualenv, cache model. |

---

## 8. Checklist nộp bài

- [ ] 5 module **m1–m5** trong `src/` + `src/phase_*.py` hoàn thiện, **hết `# TODO`** (còn TODO: **trừ 5/module**)
- [ ] `artifacts/answers_50q.json` — 50 id, 20/20/10
- [ ] `artifacts/ragas_50q.json`
- [ ] `artifacts/judge_results.json`
- [ ] `artifacts/guard_results.json`
- [ ] `doc/reports/failure_clusters.md` — điền đầy đủ
- [ ] `doc/reports/bias_report.md` — điền đầy đủ
- [ ] `doc/reports/blueprint.md` — điền đầy đủ, không placeholder
- [ ] `doc/TEAM.md` — bảng thành viên + mục `INDIVIDUAL` cho **từng người** + commit SHA
- [ ] `python -m pytest tests/ -q` — pass (mỗi test fail: **trừ 3**)
- [ ] `python scripts/check_lab.py` — pass
- [ ] Không có API key / `.env` / virtualenv / cache model trong repo
- [ ] Mọi thành viên đều có commit thật
- [ ] Trưởng nhóm gửi **một link** repo qua vlearn trước **23:59**

### Điểm trừ cần tránh

| Lỗi | Hệ quả |
|---|---|
| Còn `# TODO` trong `phase_*.py` | **−5 / module** |
| Student test fail | **−3 / test** |
| Blueprint trống, giữ placeholder hoặc chỉ giữ mẫu | **−10** |
| Thiếu `artifacts/answers_50q.json` | **Phase A = 0 điểm** |
