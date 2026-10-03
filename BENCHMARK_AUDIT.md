# Đối chiếu hướng dẫn benchmark bổ sung

| Yêu cầu | Kiểm chứng |
|---|---|
| Một lệnh, hai bảng, hai agent và sáu metric | python src/benchmark.py; test schema và output main |
| Sáu hàm và tên field scaffold | Giữ chữ ký/tên field; contract snapshot và schema test pass |
| Cùng input/order/questions | Test trace hash từng input và cùng thread IDs giữa hai agent |
| Một recall thread mới mỗi conversation | recall:<id>, khác conversation:<id>, chung cho mọi question của conversation |
| Recall 0/0.5/1, cùng quality formula | recall_points và heuristic_quality chung; judge chỉ dùng khi bật explicit flag |
| State sạch và chạy lặp giống nhau | Temp state từng suite, clock offline cố định; test hai lần và giữ nguyên profile cá nhân |
| Không sửa data | Hash nội dung khớp commit gốc dc0e2da, có test; CRLF checkout được chuẩn hóa |
| Tắt compact để xác định tác động | benchmark_ablation.py; 11937 ON vs 23337 OFF, compactions 4 vs 0 |
| Trả ngưỡng mặc định sau thử | Chỉ dùng dataclasses.replace; config gốc vẫn 1000 |
| Phân tích bằng số và có giới hạn | STEP8.md, REPORT.md, benchmark_results.txt và ablation_results.txt |
| Bonus có vấn đề/cải thiện/rủi ro | STEP9.md cùng test confidence ablation, decay clock, entity/correction/noise |

65 test pass. Phạm vi lab được đáp ứng; không gọi là hoàn hảo hay bảo đảm điểm số/test ẩn. API remote chưa có credentials, live graph được test bằng fake models.

Một nhận định trong hướng dẫn cần điều chỉnh: output token bằng nhau không đủ kết luận profile write bị bỏ qua. Profile read làm tăng prompt tokens; file write local không sinh token LLM. Test persistence và cross-session recall mới xác định được việc ghi memory.
