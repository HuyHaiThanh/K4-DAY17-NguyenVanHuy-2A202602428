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

Chạy: python -m pytest src -v. Hiện 65 test pass, gồm cả contract scaffold và test benchmark đầy đủ.

## Tác động và phản biện

Gate giảm nguy cơ profile bị nhiễm fact không chắc chắn, giúp giữ recall đúng khi có input gây nhiễu. Các dataset gốc vẫn đạt 100% recall Advanced; stress prompt tokens là 11.937 so với 22.423 Baseline, giảm khoảng 46,8%, compact 4 lần. Gate chạy bằng quy tắc local, không gọi LLM bổ sung. Không quy mức tiết kiệm prompt này cho gate: lợi ích đó chủ yếu từ compact.

Score là trọng số heuristic, không phải xác suất được hiệu chuẩn. Gate có thể từ chối fact đúng nhưng diễn đạt dè dặt, hoặc chấp nhận fact sai được khẳng định rõ ràng. Câu chứa lẫn evidence mâu thuẫn được xử lý thận trọng ở phạm vi câu. Chưa có xác minh ngoài ngôn ngữ hoặc confidence học từ dữ liệu.

## Các bonus khác

Đã có entity fields và conflict handling bằng cập nhật field, cùng bộ lọc câu hỏi/nhiễu. Memory decay đã được triển khai trong src/memory_decay.py và tích hợp vào AdvancedAgent. Guide/Rubric cho phép chọn ít nhất một mở rộng; bản này triển khai thêm confidence gate thực tế, không tuyên bố làm mọi hướng bonus hay bảo đảm điểm số.

## Đối chiếu Guide

Bước 1–7: môi trường, cấu hình, memory, hai agent, hai benchmark và test đã hoàn thành offline. Bước 8: STEP8.md phân tích số liệu. Bước 9: confidence gate đã tích hợp và có test ablation/correction/restart và memory decay với thời gian giả lập. Live LangGraph middleware/tools/checkpoints và CLI judge đã triển khai, kiểm thử bằng fake models trên graph thật. API remote chưa được gọi vì chưa có credentials.

## Memory decay đã triển khai

Metadata mỗi field gồm value, updated_at và confirmations, lưu trong memory_metadata.json bên cạnh User.md. Chỉ fact đã vượt confidence gate mới cập nhật metadata; câu hỏi recall hoặc fact bị từ chối không tự làm mới tuổi memory.

Priority = min(1, reinforcement × 2^(-age_days / half_life_days)), với reinforcement = min(2, 1 + log2(confirmations)/4). MEMORY_HALF_LIFE_DAYS mặc định 30; MEMORY_MIN_PRIORITY mặc định 0.25. Fact dưới ngưỡng không vào persistent context hoặc câu trả lời offline. Name luôn được giữ; legacy/manual facts thiếu metadata có tuổi chưa biết được giữ, không gán ngày hết hạn tùy tiện.

Xác nhận lại cập nhật thời điểm và tăng confirmations. Correction đổi giá trị reset confirmations về 1. Dữ liệu raw không bị xóa, giúp khôi phục bằng xác nhận lại. Metadata vẫn đọc được sau restart. Decay không xóa recent messages/summary của thread đang diễn ra; nó kiểm soát phần hồ sơ bền vững được truy xuất.

Demo chạy python src/benchmark_decay.py: ngày 0 có name/location/profession; ngày 90 chưa xác nhận chỉ name còn active; nhắc lại location thì field này được kích hoạt. Kết quả ghi trong decay_results.txt. Test agent chứng minh prompt token giảm sau decay và không trả nơi ở hết ưu tiên từ profile.

Trade-off: giảm persistent context nhưng có thể bỏ khỏi prompt một fact vẫn đúng và tăng chi phí lưu metadata. Profile và sidecar được replace riêng, chưa có transaction chung hoặc lock đa tiến trình. Không tuyên bố decay giảm dung lượng trên đĩa. Benchmark Memory growth hiện tính cả User.md và sidecar (957/647 byte); memory_file_size() vẫn trả riêng User.md để giữ nghĩa API cũ.
