# Đánh giá LLM Judge Phase B

Người phụ trách: **Vũ Duy Điệp — 2A202602703 (Member C)**.
Repo nhóm: `K4-Track-3A-Day24-LeManhCuong-2A202602604-Eval-Guard`.
Nguồn: `artifacts/judge_results.json`; thời điểm lưu: **2026-10-12T17:39:14.655252+07:00** (UTC+07:00).
Generation model: `longcat-2.5-preview-free`; judge model: `deepseek-flash`.

## Thiết kế và nguồn dữ liệu

A lấy nguyên trạng từ `artifacts/answers_50q.json:answer`; B từ `fixtures/human_labels_10q.json:model_answer`; question/reference từ `fixtures/test_set_50q.json`. Bộ answers đã validate đủ 50 câu; pairwise dùng các ID 1, 5, 12, 21, 41. Mỗi cặp chấm hai lượt A/B rồi B/A với cùng question/reference. Winner và scores lượt hai được quy về A/B gốc; nếu hai lượt không đồng thuận thì final=tie. Reasoning lượt hai giữ nguyên chữ A/B theo vị trí đã đảo, cần đọc cùng candidate swap để tránh nhầm.

## Năm cặp A/B và hai lượt

| ID | Winner lượt 1 | Winner lượt 2 (quy về gốc) | Final | Nhất quán | Scores lượt 1 A/B | Scores lượt 2 A/B |
|---|---|---|---|---|---|---|
| 1 | A | A | A | True | 1.0/0.7 | 1.0/0.8 |
| 5 | A | A | A | True | 0.8/0.0 | 0.8/0.0 |
| 12 | A | A | A | True | 1.0/0.4 | 1.0/0.6 |
| 21 | B | B | B | True | 0.55/0.9 | 0.5/0.95 |
| 41 | A | A | A | True | 0.9/0.1 | 0.9/0.1 |

### Cặp 1

Câu hỏi: Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?

Candidate A: Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, và số ngày này không bị trừ vào phép năm.

Candidate B: Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn.

Reasoning lượt 1: Câu trả lời A khớp đầy đủ với reference: nghỉ 3 ngày làm việc có lương khi kết hôn và không trừ vào phép năm. Câu trả lời B chỉ nêu đúng phần 3 ngày làm việc có lương nhưng thiếu chi tiết quan trọng là không trừ vào phép năm, nên kém đầy đủ hơn.

Reasoning lượt 2 (nhãn trong văn bản theo vị trí đảo): Câu trả lời B khớp đầy đủ với reference: nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn và số ngày này không trừ vào phép năm. Câu trả lời A nêu đúng số ngày và việc có lương nhưng thiếu điều kiện quan trọng là không trừ vào phép năm, nên kém đầy đủ hơn.

### Cặp 5

Câu hỏi: Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?

Candidate A: Theo quy trình mua sắm, đơn hàng trị giá 55.000.000 VNĐ nằm trong mức **trên 50.000.000 VNĐ**, do đó cần được **Tổng Giám đốc (CEO)** phê duyệt.

Bảng thẩm quyền được quy định tại phiên bản 2.2, có hiệu lực từ ngày 01/04/2024 của phòng Hành chính & Tài chính phân rõ: dưới 5.000.000 VNĐ do Trưởng phòng phê duyệt; từ 5.000.000 đến 50.000.000 VNĐ do Giám đốc phòng ban phê duyệt; trên 50.000.000 VNĐ do Tổng Giám đốc phê duyệt.

Ngoài ra, theo quy trình, mọi chi phí đều cần được **quản lý trực tiếp** phê duyệt trước khi nộp phòng Tài chính, và với giá trị từ 5.000.000 VNĐ trở lên còn cần thêm phê duyệt của **Kế toán trưởng**.

Candidate B: Cần Giám đốc phòng ban phê duyệt.

Reasoning lượt 1: Câu hỏi hỏi về thẩm quyền phê duyệt thiết bị trị giá 55 triệu. Theo reference, đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt. Answer A xác định đúng 55 triệu nằm trên ngưỡng 50 triệu và kết luận cần CEO phê duyệt. Answer B nói cần Giám đốc phòng ban phê duyệt, trái với reference. Answer A có thêm các chi tiết về bảng thẩm quyền, phiên bản và các cấp phê duyệt khác không được reference hỗ trợ, nên không được đánh giá là hoàn hảo, nhưng phần cốt lõi trả lời đúng và đầy đủ theo reference; B sai hoàn toàn.

Reasoning lượt 2 (nhãn trong văn bản theo vị trí đảo): Câu hỏi hỏi về thiết bị 55 triệu, tức trên 50.000.000 VNĐ. Theo reference, mức này cần Tổng Giám đốc (CEO) phê duyệt. Answer A trả lời 'Giám đốc phòng ban' là sai vì áp dụng sai ngưỡng. Answer B xác định đúng cần CEO phê duyệt, nhưng có thêm nhiều chi tiết về phiên bản, ngày hiệu lực và các bước phê duyệt khác không được reference hỗ trợ, nên chưa thật súc tích. Tuy nhiên, xét tính chính xác cốt lõi, B đúng và A sai.

### Cặp 12

Câu hỏi: Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu?

Candidate A: Tất cả nhân viên chính thức có thời gian làm việc từ 6 tháng trở lên được thưởng Tết tối thiểu 1 tháng lương.

Candidate B: Nhân viên được thưởng Tết tối thiểu 1 tháng lương.

Reasoning lượt 1: Answer A khớp chính xác với reference: nhân viên chính thức có thời gian làm việc từ 6 tháng trở lên được thưởng Tết tối thiểu 1 tháng lương. Answer B thiếu điều kiện quan trọng về nhóm nhân viên và mốc 6 tháng, đồng thời không phản ánh quy định pro-rata cho nhân viên dưới 6 tháng, nên kém chính xác và không đầy đủ.

Reasoning lượt 2 (nhãn trong văn bản theo vị trí đảo): Answer B khớp chính xác với reference: nhân viên chính thức có thời gian làm việc từ 6 tháng trở lên được thưởng Tết tối thiểu 1 tháng lương. Answer A chỉ nêu mức thưởng tối thiểu 1 tháng lương nhưng thiếu điều kiện 'chính thức' và 'từ 6 tháng trở lên', nên kém chính xác và có thể gây hiểu nhầm áp dụng cho mọi nhân viên.

### Cặp 21

Câu hỏi: Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?

Candidate A: Theo chính sách nghỉ phép năm phiên bản 2024 (có hiệu lực từ ngày 01/01/2024), một nhân viên chính thức có 9 năm thâm niên được hưởng **18 ngày phép năm có lương**, bao gồm 15 ngày phép cơ bản theo chính sách 2024 cộng thêm 3 ngày cho thâm niên 9 năm.

Candidate B: Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu.

Reasoning lượt 1: Câu hỏi cần cả số ngày phép và khoảng lương. Answer A trả lời đúng và có nêu phiên bản 2024: 18 ngày phép (15 cơ bản + 3 thâm niên), nhưng thiếu hoàn toàn khoảng lương Senior. Answer B trả lời đúng và đầy đủ cả hai ý: 18 ngày phép (15 cơ bản + 3 thâm niên) và lương Senior 20-35 triệu; tuy không nhắc rõ phiên bản 2024 và đơn vị VNĐ/tháng, nhưng các con số phù hợp reference. Do đó B tốt hơn vì đáp ứng đủ trọng tâm câu hỏi.

Reasoning lượt 2 (nhãn trong văn bản theo vị trí đảo): Câu hỏi yêu cầu cả số ngày phép năm và khoảng lương. Reference nêu: 9 năm thâm niên = 15 ngày cơ bản + 3 ngày thâm niên = 18 ngày phép; lương Senior (P3-P4) là 20-35 triệu VNĐ/tháng. Answer A trả lời đúng và đủ cả hai phần: 18 ngày phép và lương 20-35 triệu. Answer B nêu đúng 18 ngày phép và có thêm phiên bản 2024, nhưng thiếu hoàn toàn khoảng lương, đồng thời thêm chi tiết 'có hiệu lực từ ngày 01/01/2024' không được reference hỗ trợ. Do đó A chính xác và đầy đủ hơn.

### Cặp 41

Câu hỏi: Nhân viên được nghỉ bao nhiêu ngày phép năm?

Candidate A: Theo chính sách nghỉ phép năm phiên bản 2024 (có hiệu lực từ 01/01/2024), mỗi nhân viên chính thức được hưởng 15 ngày phép năm có lương, cao hơn mức 12 ngày quy định trong chính sách phiên bản 2023 (có hiệu lực từ 01/01/2023).

Candidate B: Nhân viên được nghỉ 12 ngày phép năm.

Reasoning lượt 1: Reference nêu rõ chính sách hiện hành v2024 là 15 ngày cơ bản, còn v2023 đã bị thay thế chỉ là 12 ngày. Answer A trả lời đúng theo v2024 và phân biệt với v2023; tuy chưa nêu phần cộng thêm +1 ngày/3 năm thâm niên nhưng vẫn đúng trọng tâm. Answer B chỉ nêu 12 ngày, tức dùng chính sách cũ đã bị thay thế, nên sai.

Reasoning lượt 2 (nhãn trong văn bản theo vị trí đảo): Reference xác định chính sách hiện hành là v2024 với 15 ngày cơ bản, kèm +1 ngày/3 năm thâm niên; v2023 đã bị thay thế và chỉ có 12 ngày. Answer A chỉ nêu 12 ngày, tức dùng chính sách cũ và bỏ qua v2024, nên sai. Answer B nêu đúng v2024 là 15 ngày, phân biệt với mức 12 ngày của v2023, phù hợp yêu cầu ưu tiên v2024; tuy nhiên chưa nhắc đến phần cộng thêm 1 ngày/3 năm thâm niên nên chưa đầy đủ tuyệt đối.

## Position và verbosity

Position inconsistency = 0/5 = **0%**. Không quan sát thấy thay đổi winner theo thứ tự trong batch này; scores vẫn thay đổi ở ID 1, 12, 21. Mẫu nhỏ và temperature=0 không chứng minh mọi lần chạy đều ổn định.
Verbosity win rate = (4 A thắng khi A dài hơn + 0 B thắng khi B dài hơn)/5 decisive = **80%**; độ dài đo bằng số ký tự. Không có tie. Đây là dấu hiệu mô tả, không phải bằng chứng nhân quả về bias.
Ở ID 5 và 41, A dài hơn nhưng cũng đúng thẩm quyền/phiên bản, còn B sai. ID 1 và 12, A nêu thêm điều kiện mà pairwise xem là đầy đủ hơn. Đặc biệt ID 21, B ngắn hơn vẫn thắng vì trả lời cả phép năm và khoảng lương, trong khi A thiếu lương. Vì vậy dữ liệu không tách được ảnh hưởng độ dài khỏi chất lượng. Cần thử candidates cùng nội dung nhưng khác độ dài và nhiều câu hơn để đo bias độc lập.

## Calibration trên đúng model_answer

Helper binary nhận đúng question và model_answer của 10 bản ghi được cấp, cùng reference theo ID; không nhận human_label, human_note hoặc phân bố nhãn người. Nhãn human chỉ đối chiếu sau khi chấm xong. Không dùng answer mới của pipeline và không chuyển winner A/B thành nhãn 0/1.

| ID | model_answer gốc | Judge | Human | Đồng thuận | Reasoning judge |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | True | Câu trả lời đúng và đủ ý chính của câu hỏi: nghỉ 3 ngày làm việc có lương khi kết hôn. Việc không nêu chi tiết không trừ vào phép năm không làm sai hoặc thiếu thông tin thiết yếu cho câu hỏi về số ngày nghỉ. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | True | Đơn hàng 55 triệu VNĐ vượt 50 triệu VNĐ nên theo reference phải do Tổng Giám đốc (CEO) phê duyệt, không phải Giám đốc phòng ban. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | True | Câu trả lời nêu đúng mức thưởng Tết tối thiểu là 1 tháng lương cho nhóm nhân viên chính thức từ 6 tháng trở lên theo reference; không mâu thuẫn hay thiếu ý thiết yếu của câu hỏi. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | True | Câu trả lời đúng theo chính sách v2024: 15 ngày cơ bản cộng 3 ngày thâm niên (9÷3=3) thành 18 ngày phép; lương Senior P3-P4 là 20-35 triệu VNĐ/tháng. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | True | Câu trả lời đúng theo reference: nghỉ sau 8 tháng chưa đủ cam kết 1 năm nên phải hoàn trả 100% chi phí, tức 25 triệu VNĐ. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | True | Sai/thiếu: 8 triệu cần cả Trưởng phòng và Kế toán trưởng phê duyệt, không chỉ Trưởng phòng. Phí phạt không chỉ nêu 2%/tháng trên 8 triệu mà reference tính cụ thể 80.000 VNĐ; đồng thời thiếu điều kiện không được tạm ứng mới khi chưa hoàn ứng. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | True | Câu trả lời đúng theo reference: phụ cấp tháng 1.500.000 VNĐ và phép năm 19 ngày cho Manager thâm niên 12 năm. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | True | Câu trả lời dùng chính sách cũ v2023 (12 ngày) trong khi chính sách hiện hành v2024 quy định 15 ngày cơ bản; do đó sai phiên bản và thiếu ý thiết yếu. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | True | Câu trả lời đúng trọng tâm: nhân viên thử việc không được nghỉ phép năm; nếu cần nghỉ thì xin nghỉ không lương. Việc không nhắc chi tiết cần trưởng phòng phê duyệt không làm sai lệch kết luận chính, nên vẫn chấp nhận. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | True | Answer sai với reference: chính sách VPN v1.3 cấm dùng VPN cá nhân như NordVPN, kể cả khi WFH; bắt buộc dùng VPN WireGuard của công ty. |

Observed agreement p_o = 10/10 = **1.0**. Judge và human đều có 6 nhãn 1, 4 nhãn 0 nên chance agreement p_e = (6/10 × 6/10) + (4/10 × 4/10) = **0.52**. Cohen’s κ = (1 − 0.52)/(1 − 0.52) = **1.0**. Không có case lệch human trong batch; kết quả vượt ngưỡng bonus κ > 0.6 của Phase B.
Pairwise và binary không thay thế nhau: ID 1 và 12, B thua pairwise vì thiếu một số chi tiết nhưng vẫn được binary=1 vì đáp ứng trọng tâm câu hỏi. Đây là khác biệt giữa chọn câu tốt hơn và đánh giá một câu đạt yêu cầu. Tuy nhiên pairwise ID 12 còn viện dẫn pro-rata cho nhóm dưới 6 tháng ngoài phạm vi câu hỏi; cần kiểm tra độ nhất quán rubric và tránh thưởng chi tiết không thiết yếu.

## Cấu hình, kiểm chứng và giới hạn

Chạy live một batch bằng `.venv/Scripts/python.exe scripts/run_experiments.py --phase b --live`, gồm 10 lượt pairwise và 10 lượt binary. Runner validate schema, nguồn, counts, κ và bias trước khi lưu artifact. Không chạy lại để cải thiện điểm.
Client đọc key/base URL từ `.env`, dùng DeepSeek endpoint; temperature=0, JSON object và max_tokens=2048. Phase B không tự fallback sang model khác, giúp metadata giữ đúng model cấu hình. Pairwise prompt chấm accuracy, completeness, conciseness theo reference, xem candidates là dữ liệu; binary prompt chấm các ý thiết yếu, phiên bản, phủ định và điều kiện. JSON lỗi, nhãn hoặc scores sai bị từ chối.
Kiểm chứng offline: `.venv/Scripts/python.exe -m pytest tests/test_phase_b.py tests/test_support.py tests/test_report_contracts.py tests/test_llm_client.py -q` → **88 passed**. Network bị chặn trong unit tests. Artifact live là bằng chứng riêng, không suy từ mock tests.
Mẫu chỉ có 5 cặp và 10 nhãn; κ=1 không chứng minh judge đáng tin trên dữ liệu mới. Reference ngắn có thể không chứa toàn bộ chính sách, nên thêm chi tiết chưa được reference hỗ trợ cần kiểm tra tài liệu nguồn. Dùng judge để sàng lọc, giữ human review cho quyết định quan trọng, mở rộng calibration và kiểm tra lại khi đổi model/prompt.
Các câu hỏi/answers/reference được gửi đến API DeepSeek; key chỉ ở `.env` được gitignore. Artifact lưu model, timestamp và SHA256 các file nguồn để đối chiếu. Không công bố key.
Phạm vi AI hỗ trợ: Codex hỗ trợ implement, sửa tích hợp provider, bổ sung tests, chạy batch được cho phép và soạn báo cáo từ JSON thật; người phụ trách cần đọc lại nội dung trước khi nộp.

## Bàn giao tích hợp

File dùng chung sửa cho Phase B: `src/experiment_support.py` (client mặc định binary và token limit), `src/experiment_runners.py` (client binary theo provider); `tests/conftest.py` cung cấp key giả cho mock SDK. Member A cần giữ các thay đổi này khi tích hợp; các phase khác vẫn giữ logic riêng.
