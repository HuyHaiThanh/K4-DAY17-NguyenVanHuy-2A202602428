# Câu trả lời cho bước 8 trong phần GUIDE.md

## 1. Vì sao Advanced có recall tốt hơn Baseline?

Standard Benchmark cho recall Baseline 3,6% và Advanced 100%; stress lần lượt 0% và 100%. Baseline có memory growth 0 byte, Advanced lần lượt 957 và 647 byte.

Advanced trích facts, qua confidence gate rồi lưu theo field vào User.md; _offline_response() đọc các facts còn active từ file ở thread mới. Baseline chỉ có lịch sử theo thread_id nên không nhớ phiên trước. Bộ đếm metadata phục vụ decay cũng được tính vào memory growth.

Giới hạn: Baseline 3,6% đến từ dữ kiện có sẵn trong một recall input, không chứng minh nhớ dài hạn; 100% là recall substring trên dataset này, không chứng minh hiểu mọi câu tiếng Việt.

## 2. Vì sao Advanced có thể tốn hơn ở hội thoại ngắn?

Ở Standard, Agent tokens only là 1.521 của Baseline và 1.664 của Advanced; Prompt tokens processed là 14.865 và 21.732, Advanced tăng khoảng 46,2%. Compactions của cả hai bằng 0 ở ngưỡng mặc định 1.000.

Advanced đưa active profile vào prompt mỗi lượt, còn lịch sử chưa đủ dài để compact bù lại chi phí bổ sung. Output tăng do Advanced trả lời được thêm facts đã nhớ; thao tác ghi file không trực tiếp sinh token LLM trong offline.

Giới hạn: hai agent có cùng output token cũng không chứng minh persistent write bị bỏ qua. Agent tokens only đo output; việc profile được đưa vào context cần kiểm tra bằng prompt load và test persistence/recall.

## 3. Vì sao compact giúp Advanced có lợi thế ở hội thoại dài?

Ở stress, Baseline xử lý 22.423 prompt tokens, Advanced 11.937 (giảm khoảng 46,8%) và compact 4 lần. Output tokens là 281 và 312: lợi ích chủ yếu nằm ở Prompt tokens processed. Trace từng lượt cho thấy prompt của Baseline tăng từ 187 ở lượt đầu lên 2.537 ở lượt 16.

Compact hợp nhất summary cũ với facts/correction và giữ recent messages thay vì kéo toàn bộ lịch sử mỗi lượt. Phép thử riêng trên cùng dữ liệu, cùng recall protocol và state sạch cho kết quả:

| Stress ablation | Prompt tokens processed | Agent tokens only | Recall | Memory growth bytes | Compactions |
|---|---:|---:|---:|---:|---:|
| Baseline | 22.423 | 281 | 0% | 0 | 0 |
| Advanced compact ON | 11.937 | 312 | 100% | 647 | 4 |
| Advanced compact OFF | 23.337 | 312 | 100% | 647 | 0 |

Tắt compact bằng config copy có ngưỡng 10^12 làm prompt cost Advanced tăng gần về mức Baseline, còn cao hơn vì profile overhead. Bật compact giảm khoảng 48,8% so với chính Advanced không compact, trong khi output/recall/growth không đổi. Config mặc định không bị sửa.

Giới hạn: summary có giới hạn vẫn có thể mất facts/excerpts ít ưu tiên; recall dataset chủ yếu đo profile. Kết quả và trace nằm trong [ablation_results.txt](ablation_results.txt), chạy lại bằng python src/benchmark_ablation.py.

## 4. File memory tăng trưởng ra sao và rủi ro gì?

Standard tăng 957 byte (287 User.md + 670 metadata); stress tăng 647 byte (207 User.md + 440 metadata) và compact 4 lần. Baseline không ghi profile, growth bằng 0. Hai suite độc lập nên không cộng growth thành kích thước của một hồ sơ.

Upsert theo field tránh phình file chỉ vì lặp lại cùng fact; correction thay giá trị cũ. Compact giảm lịch sử trong prompt, không xóa dữ liệu trên đĩa. Decay giảm ưu tiên truy xuất và cũng không tự thu nhỏ User.md; sidecar còn tăng chi phí lưu trữ.

Rủi ro đã kiểm chứng bằng case nhiễu: câu hỏi, câu đùa hoặc “có lẽ mình ở Hà Nội” có thể làm sai location nếu ghi quá dễ dãi. Confidence gate 0.8 ngăn case uncertain overwrite; gate 0.4 trong test ablation chấp nhận nó. Decay có thể bỏ khỏi prompt fact vẫn đúng, còn regex có thể lọc nhầm câu hợp lệ. STEP9.md mô tả bonus, cơ chế, bằng chứng và rủi ro.

## Phương pháp và output

Một thread recall mới cho mỗi conversation, dùng chung cho các câu hỏi recall của conversation đó và cùng ID protocol ở cả hai agent. Main benchmark tạo state tạm sạch riêng mỗi suite và cố định clock offline, nên không cần xóa state cá nhân; hai lần chạy cho cùng output.

Tokens offline là ceil(len(text.strip())/4); cả training và recall đều tính. Quality là proxy recall/concision dùng cùng công thức cho hai agent. Memory growth gồm profile và metadata; không phải tốc độ byte/giây. Dữ liệu data/ giữ nguyên nội dung so với scaffold gốc. Kết quả đầy đủ: [benchmark_results.txt](benchmark_results.txt).
