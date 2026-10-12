### VuDuyDiep-2A202602703

- Phần được giao và phần thực tế đã làm: Member C — Phase B, Tasks 5–8. Hoàn thiện pairwise_judge, swap_and_average, cohen_kappa và bias_report trong src/phase_b_judge.py; kiểm tra JSON, đảo winner/scores về candidate gốc; tích hợp client provider cho pairwise và binary. Viết doc/reports/bias_report.md từ kết quả thật.
- Bằng chứng: src/phase_b_judge.py, tests/test_phase_b.py, artifacts/judge_results.json, doc/reports/bias_report.md. Chưa commit; học viên tự commit phần mình và bổ sung SHA khi bàn giao.
- Cách kiểm tra: 88 tests offline pass (Phase B, support, report contracts, llm_client). Chạy một batch --phase b --live bằng deepseek-flash: đủ 5 cặp × 2 lượt và 10 binary judgments, κ=1.0, position inconsistency=0/5, longer-answer win rate=4/5. Runner validate schema và nguồn trước khi lưu.
- Điều đã học: Pairwise A/B/tie khác calibration 0/1. Swap cần đảo cả scores lẫn winner; κ điều chỉnh đồng thuận ngẫu nhiên. Tỷ lệ câu dài thắng không tự chứng minh bias vì chất lượng và độ dài có thể cùng thay đổi.
- Giới hạn/cách xử lý: Chỉ 5 cặp và 10 nhãn; không suy rộng κ=1.0 sang production. Case 21 cho thấy answer ngắn nhưng đầy đủ thắng answer dài thiếu lương. Cần mở rộng tập nhãn và thiết kế candidates cùng nội dung khác độ dài; giữ human review cho quyết định quan trọng.
- Nguồn/AI hỗ trợ nếu có: Codex hỗ trợ implement, tích hợp provider, viết tests, chạy API được cho phép và soạn báo cáo từ artifact thật. Không đưa human_label/human_note vào prompt; không sửa dữ liệu hoặc chạy lại để tăng điểm. Học viên cần tự đọc và kiểm chứng trước khi nộp.
