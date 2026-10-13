# Phân tích lỗi Phase A

Nhóm: K4 — Track 3A (Day 24)

Người phụ trách: Nguyễn Trọng Minh — MSSV 2A202602496

Nguồn: `artifacts/ragas_50q.json`; run timestamp: `2026-10-12T14:44:02.839923+00:00`
(UTC), tức 21:44 ngày 12/10/2026 theo giờ Asia/Ho_Chi_Minh (UTC+07:00).

Generation mode/fallback và điều kiện chạy: cả 50/50 câu đều `generation_mode = llm`
(model `longcat-2.5-preview-free`, model dự phòng `glm-5.3-flash`, không có câu nào rơi
vào extractive fallback). `M5_ENRICHMENT=off` nên pipeline dùng 100 chunk gốc; Qdrant
chạy ở chế độ `:memory:` vì Docker daemon không bật trên máy; hai tài liệu scan ảnh
(`BCTC.pdf`, `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf`) bị bỏ qua vì
không có text layer và lab không yêu cầu OCR.

Models generation/evaluator: `metadata.models.generation = [longcat-2.5-preview-free]`;
`metadata.models.evaluator = [longcat-2.5-preview-free, qwen3.8-max, glm-5.3-flash,
text-embedding-bge-m3]`. Trong lượt chạy này 37/50 câu cho metric hữu hạn ngay từ model
chính; 13 câu còn lại có metric không hữu hạn do evaluator không parse được output, và
được chạy lại bằng `qwen3.8-max` (sửa được 8 câu) rồi `glm-5.3-flash` (sửa nốt 5 câu).
Danh sách evaluator trong metadata ghi đúng các model đã thực sự tạo ra con số, không
giấu phần chạy lại.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.9458 | 0.6808 | 0.9500 |
| answer_relevancy | 0.9048 | 0.7291 | 0.8796 |
| context_precision | 0.9667 | 0.7458 | 0.8667 |
| context_recall | 0.9000 | 0.6158 | 0.5333 |
| avg_score | 0.9293 | 0.6929 | 0.8074 |

## Bottom 10 và nguyên nhân

| Rank | id | Câu hỏi | Distribution | avg_score | worst_metric | diagnosis | suggested_fix |
|---|---|---|---|---|---|---|---|
| 1 | 30 | So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức (id 30) | multi_hop | 0.125 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài, thời hạn đổi và MFA (id 39) | multi_hop | 0.250 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 3 | 37 | Tự ý xóa malware và chia sẻ thông tin sự cố trên Slack nội bộ vi phạm những chính sách nào (id 37) | multi_hop | 0.328 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 40 | Manager thử việc 90 ngày, tháng thứ 3, phát hiện vi phạm bảo mật nên và không nên làm gì (id 40) | multi_hop | 0.374 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 5 | 33 | Manager thâm niên 12 năm: tổng phụ cấp tháng và số ngày phép năm theo v2024 (id 33) | multi_hop | 0.429 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 6 | 42 | Thâm niên bao nhiêu năm thì được cộng thêm ngày phép (id 42) | adversarial | 0.571 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 7 | 22 | Mua laptop 30 triệu cho nhân viên mới: ai phê duyệt và cần gì từ phòng CNTT (id 22) | multi_hop | 0.626 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 34 | Tạm ứng 4 triệu và 7 triệu: quy trình phê duyệt khác nhau thế nào (id 34) | multi_hop | 0.635 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 9 | 35 | Junior P1 lương cơ bản 12 triệu vào thử việc: tháng đầu nhận lương và phụ cấp gì (id 35) | multi_hop | 0.675 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 10 | 20 | Phụ cấp đi lại tối đa mỗi tháng và điều kiện để được hưởng (id 20) | factual | 0.690 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |

Đối chiếu answer/contexts/reference của các câu đại diện cho thấy ba nguyên nhân khác
nhau, không phải một:

**Nhóm generation từ chối trả lời dù retrieval đã lấy đúng chunk (id 30, id 39).**
Với id 30, `contexts[0]` chứa nguyên câu "Nhân viên thử việc được tham gia bảo hiểm xã
hội bắt buộc nhưng chưa được hưởng gói bảo hiểm sức khỏe PVI" — tức bằng chứng nằm ngay
trong ngữ cảnh — nhưng `answer` lại là "Không tìm thấy thông tin.". Vì câu trả lời không
có phát biểu nào để đối chiếu, faithfulness và answer_relevancy đều bằng 0, còn
context_recall vẫn 0.50 nên đây là lỗi ở bước sinh, không phải lỗi tìm kiếm. Đây là
trường hợp mô hình generation quá thận trọng với câu hỏi dạng so sánh hai đối tượng.

**Nhóm retrieval lấy sai chunk (id 37, id 34).** id 37 hỏi về vi phạm chính sách bảo mật,
`contexts[0]` lại là "Chính sách phân loại dữ liệu" — sai tài liệu hoàn toàn — nên câu
trả lời tuy dài và có vẻ liên quan (answer_relevancy 0.73) nhưng faithfulness bằng 0 và
context_recall bằng 0: câu trả lời trích dẫn một điều khoản không nằm trong ngữ cảnh
đúng. id 34 là mặt trái: context_precision thấp vì ngữ cảnh chứa nhiều chunk không liên
quan (hai mức tạm ứng 4 triệu và 7 triệu nằm ở hai tài liệu khác nhau).

**Nhóm trả lời thiếu do không tổng hợp hết ngữ cảnh (id 33, id 35).** id 33 có
context_precision bằng 1.00 (chunk lấy về đúng chủ đề) nhưng câu trả lời chỉ nêu 15 ngày
phép cơ bản và tự nói "trong context không cung cấp" phần phụ cấp, thiếu phần cộng ngày
theo thâm niên mà reference yêu cầu (15 + 4 = 19 ngày). Lỗi ở bước tổng hợp nhiều chunk
của câu hỏi multi-hop, không phải ở khâu lấy chunk.

## Matrix và nhóm yếu nhất

Mỗi câu được đếm đúng một lần theo `worst_metric` của nó (không coi cả 50 câu là lỗi):

| worst_metric | factual | multi_hop | adversarial |
|---|---|---|---|
| faithfulness | 2 | 7 | 1 |
| answer_relevancy | 14 | 6 | 0 |
| context_precision | 1 | 2 | 1 |
| context_recall | 3 | 5 | 8 |

Nhóm yếu theo mean thấp nhất: multi_hop; mean: 0.6929.
Worst metric xuất hiện nhiều nhất: answer_relevancy; số câu: 20.

Nhóm multi_hop yếu không phải vì số câu nhiều (20/20/10) mà vì cả bốn metric đều thấp
hơn factual: faithfulness 0.6808 so với 0.9458, context_recall 0.6158 so với 0.9000.
Nguyên nhân chính là câu hỏi multi-hop cần ghép bằng chứng từ nhiều tài liệu (ví dụ id 34
cần cả chính sách tạm ứng lẫn quy trình phê duyệt, id 33 cần cả bảng phụ cấp lẫn quy tắc
thâm niên), trong khi `top_k` chỉ trả về 3 chunk cho mỗi truy vấn và chunk được tạo bằng
m1 mà không có M5 enrichment.

Đề xuất sửa cụ thể, kèm cách chạy lại để biết sửa có hiệu quả:

1. Sinh câu trả lời: sửa `GENERATION_SYSTEM_PROMPT` để buộc mô hình nêu rõ "không đủ
   thông tin" chỉ khi thật sự không có bằng chứng, và phải liệt kê đủ mọi phần mà câu hỏi
   yêu cầu (id 30, id 33, id 39). Chạy lại `scripts/setup_answers.py --live`, rồi
   `scripts/run_experiments.py --phase a --live`; so sánh mean của multi_hop trước và sau
   và kiểm tra lại `bottom_10`.
2. Retrieval: tăng `top_k` cho câu multi_hop và giữ reranker `BAAI/bge-reranker-v2-m3`
   đang bật, thêm lọc theo metadata tài liệu để hai tài liệu khác nhau của cùng câu hỏi
   đều vào ngữ cảnh (id 34, id 37). Chạy lại Phase A trên 20 câu multi_hop; kỳ vọng
   context_recall của nhóm tăng, còn faithfulness không giảm.
3. Phân loại trước khi trả lời: với câu hỏi dạng so sánh/hai mốc, thêm bước tách thành
   hai truy vấn con rồi hợp nhất ngữ cảnh.

## Bẫy adversarial và giới hạn

Adversarial có mean thấp hơn factual (0.8074 so với 0.9293) nên thỏa điều kiện bonus
Phase A. Nhưng đọc theo từng metric thì chênh lệch đó **không** đến từ faithfulness:
adversarial faithfulness 0.9500 còn cao hơn factual 0.9458; phần yếu thật nằm ở
context_recall (0.5333 so với 0.9000) và context_precision (0.8667 so với 0.9667). Nói
cách khác, hệ thống trả lời trung thành với ngữ cảnh nó lấy được, nhưng ngữ cảnh đó
thường không chứa phiên bản còn hiệu lực.

Bằng chứng cụ thể cho điều này là id 42 ("Thâm niên bao nhiêu năm thì được cộng thêm
ngày phép") trong bottom 10: reference yêu cầu chính sách v2024 (từ 3 năm, mỗi 3 năm
cộng 1 ngày), trong khi `contexts[0]` là bản cũ ("từ 5 năm trở lên") và câu trả lời lặp
lại đúng nội dung bản cũ đó — faithfulness 1.00 nhưng context_recall 0.00. Vậy điểm thấp
của nhóm adversarial phản ánh retrieval chọn nhầm phiên bản đã hết hiệu lực, **không**
chứng minh được pipeline "nhận ra" bẫy. Trong bottom 10 chỉ có một câu adversarial (id 42)
và không có câu nào thuộc nhóm phủ định (id 47, 48, 50 đều nằm ngoài bottom 10), nên chưa
đủ cơ sở để nói hệ thống chống được bẫy phủ định.

Giới hạn cần ghi rõ: nhóm adversarial chỉ có 10 câu; evaluator là model preview miễn phí
`longcat-2.5-preview-free` chứ không phải gpt-4o-mini như cấu hình gốc của lab;
`answer_relevancy` chạy ở mức nghiêm ngặt giảm (n=1) vì provider trả lỗi "n: 3 is not
less or equal to 1", nên điểm relevancy có thể cao hơn thực tế; 13/50 câu phải nhờ
`qwen3.8-max` và `glm-5.3-flash` tạo metric; `M5_ENRICHMENT=off`; và hai tài liệu scan
ảnh bị bỏ khỏi corpus — trong đó có Nghị định 13/2023 về bảo vệ dữ liệu cá nhân, nên mọi
câu hỏi cần tài liệu đó không thể được trả lời đúng bởi bất kỳ model nào.
