# Bước 9 — Bonus đã triển khai

## Confidence threshold trước khi ghi User.md

Mã chạy thật nằm trong src/profile_policy.py và được AdvancedAgent gọi trước upsert_fact(). Không thay chữ ký hàm hoặc field dataclass của scaffold. PROFILE_CONFIDENCE_THRESHOLD mặc định 0.8, có thể cấu hình qua môi trường/.env; giá trị phải hữu hạn trong [0, 1].

| Loại evidence | Score | Hành vi mặc định |
|---|---:|---|
| Câu khẳng định trích được fact | 0.95 | Lưu |
| Có lẽ, hình như, chưa chắc, dự định | 0.4 | Không lưu |
| Giả định, câu đùa, lời người khác | 0.1 | Không lưu |
| Câu hỏi | 0 | Không lưu, kể cả threshold = 0 |

Đánh giá theo từng câu để một câu hỏi sau không loại bỏ câu khẳng định trước. last_profile_decisions giữ kết quả của lượt gần nhất gồm key/value, score, reason và accepted để kiểm tra; không tích lũy lịch sử quyết định vô hạn. Facts bị từ chối cũng không được bộ trả lời offline lấy lại từ recent messages như facts đã xác nhận.

## Vấn đề giải quyết và bằng chứng

Sau “Mình đang ở Huế”, câu “Có lẽ mình đang ở Hà Nội” không ghi đè location. Sau restart, agent vẫn trả lời Huế. Câu “Mình đang ở Hà Nội phải không?” cũng không thay đổi profile. Ngược lại, correction rõ ràng sang Đà Nẵng hoặc MLOps engineer vẫn được lưu.

Test ablation dùng cùng input với ngưỡng 0.8 và 0.4: chính sách 0.8 giữ Huế; chính sách dễ dãi 0.4 ghi Hà Nội từ câu chưa chắc chắn. Đây là bằng chứng gate có tác động đến ghi memory, không chỉ thêm metadata. Test ngưỡng biên và ngưỡng không hợp lệ; test preference “có ví dụ” để không nhầm với câu giả định.

Chạy: python -m pytest src -v. Hiện 26 test pass, gồm cả contract scaffold và test benchmark đầy đủ.

## Tác động và phản biện

Gate giảm nguy cơ profile bị nhiễm fact không chắc chắn, giúp giữ recall đúng khi có input gây nhiễu. Các dataset gốc vẫn đạt 100% recall Advanced; stress prompt tokens là 11.043 so với 22.300 Baseline, giảm khoảng 50.5%, compact 3 lần. Gate chạy bằng quy tắc local, không gọi LLM bổ sung. Không quy mức tiết kiệm prompt này cho gate: lợi ích đó chủ yếu từ compact.

Score là trọng số heuristic, không phải xác suất được hiệu chuẩn. Gate có thể từ chối fact đúng nhưng diễn đạt dè dặt, hoặc chấp nhận fact sai được khẳng định rõ ràng. Câu chứa lẫn evidence mâu thuẫn được xử lý thận trọng ở phạm vi câu. Chưa có xác minh ngoài ngôn ngữ hoặc confidence học từ dữ liệu.

## Các bonus khác

Đã có entity fields và conflict handling bằng cập nhật field, cùng bộ lọc câu hỏi/nhiễu. Chưa triển khai memory decay. Guide/Rubric cho phép chọn ít nhất một mở rộng; bản này triển khai thêm confidence gate thực tế, không tuyên bố làm mọi hướng bonus hay bảo đảm điểm số.

## Đối chiếu Guide

Bước 1–7: môi trường, cấu hình, memory, hai agent, hai benchmark và test đã hoàn thành offline. Bước 8: STEP8.md phân tích số liệu. Bước 9: confidence gate đã tích hợp và có test ablation/correction/restart. Live API và LangGraph middleware vẫn là phần mở rộng chưa kiểm chứng.
