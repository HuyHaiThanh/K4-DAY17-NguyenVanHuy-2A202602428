# Câu trả lời cho bước 9 trong phần Guide.md

## Phạm vi bonus đã chọn

Guide.md đưa ra các hướng bonus; Rubric.md yêu cầu ít nhất một mở rộng hữu ích, không yêu cầu triển khai mọi hướng. Bản này chọn tổ chức entity thành field, xử lý correction/conflict và lọc câu hỏi/nhiễu bằng quy tắc. Chưa triển khai confidence threshold hoặc memory decay.

| Hướng | Trạng thái | Bằng chứng |
|---|---|---|
| Entity extraction có cấu trúc | Có ở mức regex heuristic | extract_profile_updates() trả dict; facts()/upsert_fact() lưu theo field trong User.md |
| Conflict handling | Có cho các field hiện tại và các correction được kiểm thử | Nơi ở/nghề mới thay field cũ; test_noise_and_corrections và test_user_markdown_read_write_edit |
| Tránh lưu câu hỏi/nhiễu | Có bộ lọc quy tắc cho các tình huống đã kiểm thử | Test câu hỏi không trích tên, recall không đổi profile, bỏ qua nơi họp/câu đùa |
| Confidence threshold | Chưa có | Không có score hoặc ngưỡng định lượng trước khi ghi |
| Memory decay | Chưa có | Không có timestamp hoặc trọng số giảm theo thời gian |

## Vấn đề được giải quyết

Ghi nối toàn bộ lời người dùng có thể giữ đồng thời nơi ở/nghề cũ và mới, khiến agent trả lời mâu thuẫn. Lưu theo field giúp cập nhật fact hiện tại. Bộ lọc câu hỏi, phủ định và câu đùa giảm nguy cơ ghi một nội dung chỉ được nhắc tới thành hồ sơ thật.

Ví dụ đã kiểm thử: Đà Nẵng chuyển thành Huế; backend engineer chuyển thành MLOps engineer; Hà Nội chỉ là nơi họp và product manager chỉ là câu đùa, nên không ghi đè nơi ở/nghề hiện tại.

## Tác động đến recall và token

Hai dataset hiện có đạt 100% recall với Advanced. Correction đúng giúp tránh trả nghề/nơi ở cũ. Upsert theo field tránh tăng profile chỉ vì lặp lại cùng facts, từ đó hạn chế context bổ sung khi đọc User.md.

Tuy nhiên, chưa có ablation so sánh phiên bản có/không có bonus, nên không quy toàn bộ 100% recall hoặc mức giảm 50,6% prompt tokens cho bonus. Mức giảm prompt ở stress chủ yếu do compact memory, còn recall qua phiên chủ yếu do persistent profile.

## Rủi ro và giới hạn

Regex chưa tổng quát cho mọi cách diễn đạt. Bộ lọc có thể bỏ sót fact hợp lệ hoặc ghi nhầm một câu hỏi chưa được nhận diện. Fact mới được ưu tiên chưa có confidence xác thực; interests được hợp nhất nhưng chưa hỗ trợ xóa sở thích cũ. Việc lưu theo field cũng mất lịch sử thay đổi. Test correction/nhiễu chứng minh các case cụ thể, không chứng minh hiểu ngôn ngữ hoàn chỉnh.

Các hướng tiếp theo là confidence threshold có hiệu chuẩn và memory decay có timestamp; hai hướng này chưa nằm trong bản nộp hiện tại.

## Đối chiếu toàn bộ Guide

| Bước | Trạng thái | Kết quả |
|---|---|---|
| 1. Môi trường và cấu trúc | Hoàn thành | Python/pytest chạy được, vai trò các module được mô tả |
| 2. Cấu hình | Hoàn thành | LabConfig, paths, compact settings, model/judge config và factory sáu provider |
| 3. Memory | Hoàn thành offline | Estimator, read/write/edit profile, extraction, compact và bộ đếm |
| 4. Baseline | Hoàn thành offline | Nhớ trong thread, quên qua thread; không có persistent profile |
| 5. Advanced | Hoàn thành offline | Short-term, User.md, compact; recall sau restart |
| 6. Benchmark | Hoàn thành offline | Standard và Stress, đủ sáu chỉ số |
| 7. Test | Hoàn thành | 11 test pass, gồm kiểm tra khai báo scaffold gốc |
| 8. Phân tích | Hoàn thành | STEP8.md và REPORT.md |
| 9. Bonus | Có các hướng đã chọn | Entity fields, conflict/correction và lọc câu hỏi/nhiễu; không có threshold/decay |

Live mode chỉ có direct chat model invocation; chưa có LangGraph tool/middleware và chưa kiểm chứng API thật. README xác định live là phần mở rộng. Vì vậy không gọi bản này là hoàn thành mọi mở rộng hoặc bảo đảm điểm 90–100; điểm và test ẩn thuộc người chấm.

Kiểm chứng ngày 03/10/2026: python -m pytest src -v cho 11 passed; python src/benchmark.py khớp benchmark_results.txt.
