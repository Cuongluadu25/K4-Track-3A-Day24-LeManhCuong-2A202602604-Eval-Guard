# Đánh giá LLM Judge Phase B

Nhóm: {{Tên nhóm}}

Người phụ trách: {{Họ tên và MSSV}}

Nguồn: `artifacts/judge_results.json`; run timestamp: {{created_at}}.
Models generation/judge: {{metadata.models.generation và metadata.models.judge}}.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

{{Điền 5 rows: id, candidate A/B, winner_pass1, winner_pass2 đã quy về A/B gốc,
final_winner, position_consistent, reasoning và scores của hai lượt.}}

Position bias count/rate: {{count và rate}}.
Verbosity win rate: {{giá trị}}; decisive cases: {{số lượng}}.

{{Giải thích các case không nhất quán và các winner dài hơn. Phân biệt dấu hiệu
thống kê với kết luận nguyên nhân bias dựa trên nội dung.}}

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

{{Điền 10 rows theo đúng thứ tự JSON: question_id, model_answer gốc, nhãn judge
0/1, reasoning, human_label và agree. Nhãn human chỉ dùng sau judge để đối chiếu.}}

Cohen’s κ: {{giá trị}}.
Observed/chance agreement và diễn giải: {{phép tính và nhận xét}}.

## Giới hạn và cách dùng judge

{{Nêu model/prompt, số cặp và số nhãn nhỏ; diễn giải nếu κ chưa đạt >0.6.
Nêu case lệch với human, cách kiểm chứng, và việc không xem judge là đáp án tuyệt đối.}}
