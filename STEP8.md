# Câu trả lời cho bước 8 trong phần GUIDE.md

## 1. Vì sao Advanced có recall tốt hơn Baseline?

Baseline chỉ giữ lịch sử theo thread_id. Khi câu hỏi recall được hỏi ở thread mới, nó không còn lịch sử các phiên trước. Advanced lưu các facts ổn định vào User.md theo từng người dùng và đưa hồ sơ này vào context, nên vẫn nhớ tên, nơi ở, nghề nghiệp và sở thích qua phiên mới. Cập nhật theo field giúp thay nơi ở/nghề cũ bằng thông tin đính chính, thay vì giữ cả hai như facts hiện tại.

Trong Standard Benchmark, recall của Baseline là 3,6%, Advanced là 100%; trong stress benchmark, lần lượt là 0% và 100%. Điểm 3,6% của Baseline không chứng minh nhớ dài hạn: một câu hỏi chứa sẵn dữ kiện trong input nên phép chấm substring cho điểm một phần.

## 2. Vì sao Advanced có thể tốn hơn ở hội thoại ngắn?

Advanced phải mang thêm User.md vào prompt mỗi lượt. Khi lịch sử còn ngắn, chi phí bổ sung này lớn hơn lợi ích từ nén lịch sử; với ngưỡng mặc định 1.000 token, Standard Benchmark chưa kích hoạt compact.

Prompt tokens processed của Baseline là 14.742, Advanced là 21.582, tăng khoảng 46,4%. Agent tokens only cũng tăng từ 1.521 lên 1.664, vì Advanced trả lời được nhiều thông tin đã nhớ hơn. Vì vậy, recall tốt hơn đi kèm chi phí context lớn hơn trong bộ hội thoại ngắn này.

## 3. Vì sao compact giúp Advanced có lợi thế ở hội thoại dài?

Baseline giữ toàn bộ lịch sử và xử lý lại context tích lũy mỗi lượt. Advanced nén phần lịch sử cũ thành summary có giới hạn, giữ các message gần nhất cùng hồ sơ người dùng. Cách này giảm lượng nội dung phải xử lý lặp lại khi cuộc hội thoại dài.

Trong Long-Context Stress Benchmark, Advanced compact 3 lần. Prompt tokens processed giảm từ 22.300 của Baseline xuống 11.019 của Advanced, tức khoảng 50,6%, trong khi Advanced vẫn đạt 100% recall các facts được kiểm tra. Agent tokens only tăng từ 281 lên 306: lợi ích chính nằm ở prompt load, không phải độ dài câu trả lời.

Kết quả này chưa chứng minh summary giữ được mọi chi tiết cũ: các câu recall của dataset chủ yếu kiểm tra profile. Summary trích đoạn có thể làm mất nội dung tạm thời; đây là đánh đổi giữa chi phí token và độ đầy đủ của ngữ cảnh.

## 4. File memory tăng trưởng ra sao và có rủi ro gì?

Memory growth của Advanced là 287 byte ở Standard Benchmark và 207 byte ở stress benchmark; Baseline là 0 byte vì không có profile bền vững. Hai suite dùng state sạch riêng, nên đây là mức tăng trong từng lần chạy, không phải tổng cộng của cùng một hồ sơ.

User.md lưu theo field và cập nhật fact hiện có, nên việc lặp lại cùng fact không làm file dài thêm như nối toàn bộ hội thoại. Tuy nhiên, tập sở thích hoặc số người dùng tăng vẫn làm tổng memory tăng. Profile dài hơn cũng làm prompt tốn hơn nếu đọc toàn bộ ở mỗi lượt.

Rủi ro khác là lưu nhầm câu hỏi, câu đùa hoặc dữ kiện đã bị phủ định thành fact; giữ thông tin lỗi thời; hoặc làm mất chi tiết khi compact. Bản triển khai có test cho correction và nhiễu trong dữ liệu, nhưng regex extraction chưa tổng quát cho mọi câu tiếng Việt. Hướng cải thiện là confidence threshold, xác nhận khi facts mâu thuẫn, memory decay và chỉ lấy phần profile liên quan đến câu hỏi.

## Giới hạn khi đọc số liệu

Đây là benchmark offline deterministic. Token được ước lượng bằng ceil(len(text.strip()) / 4), không phải token tính phí của provider. Response quality là proxy từ recall và độ ngắn gọn, không phải đánh giá ngữ nghĩa độc lập bằng LLM judge. Kết quả đầy đủ nằm trong [benchmark_results.txt](benchmark_results.txt).
