# Báo cáo hoàn thành Day 17 — Memory Systems for AI Agent

## Chạy trên Windows

Từ root repo:

```powershell
python -m pip install -r requirements.txt
python -m pytest src -v
python src/benchmark.py
python src/benchmark_decay.py
```

Benchmark mặc định offline, không cần API key. Chế độ live dùng cấu hình .env (mẫu .env.example):

```powershell
python src/benchmark.py --live
python src/benchmark.py --live --judge
```

Live gọi provider được cấu hình; --judge gọi thêm model judge. Nếu thiếu credentials remote, --live báo lỗi thay vì âm thầm chạy offline. Constructor thông thường vẫn fallback offline khi thiếu key; force_offline=True luôn giữ offline. Ollama không cần API key nhưng cần server đang chạy.

## Kiến trúc

Baseline nhớ theo thread, không lưu User.md. Advanced kết hợp lịch sử thread, User.md, compact summary, confidence gate và decay. Contract gồm chữ ký hàm, dataclass fields và AgentContext được đối chiếu tự động với scaffold gốc. Safe user ID dùng profiles/<user>/User.md; ID không an toàn có namespace hash, hỗ trợ đọc hồ sơ hash cũ.

Offline dùng extraction/response deterministic chung cho hai agent. Summary giữ facts có cấu trúc, hợp nhất summary cũ và correction, cùng excerpts giới hạn. Live dùng create_agent của LangChain/LangGraph, InMemorySaver, dynamic profile prompt, tools read/write/edit và SummarizationMiddleware gọi model. User ID được inject từ runtime context, không lấy từ tham số do model tự chọn. Tool chỉ được ghi/correct facts được confidence gate xác nhận trong chính user message hiện tại.

Provider factory hỗ trợ openai/custom/gemini/anthropic/ollama/openrouter; OpenRouter mặc định dùng SDK native, explicit base URL dùng OpenAI-compatible client. Judge có model/key/base URL riêng và mặc định theo provider tương thích.

## Kết quả offline cuối

| Suite | Agent | Output tokens | Prompt tokens | Recall | Growth bytes | Compactions |
|---|---|---:|---:|---:|---:|---:|
| Standard | Baseline | 1521 | 14742 | 3,6% | 0 | 0 |
| Standard | Advanced | 1664 | 21582 | 100% | 957 | 0 |
| Stress | Baseline | 281 | 22300 | 0% | 0 | 0 |
| Stress | Advanced | 312 | 11784 | 100% | 647 | 4 |

Token offline là ceil(len(text.strip())/4). Cả training và recall được tính; recall hỏi ngay sau từng conversation, thread mới riêng mỗi question. Score 0/0,5/1 khi không khớp/khớp một phần/khớp tất cả expected_contains. Quality offline là proxy recall/concision. Growth gồm User.md và sidecar decay: Standard 287 + 670 byte; Stress 207 + 440 byte. Metadata không gửi vào prompt.

Advanced tăng recall qua persistent memory. Standard thêm khoảng 46,4% prompt cost vì mang profile mỗi lượt. Stress compact 4 lần, giảm prompt cost khoảng 47,2%. Summary mới giữ facts tốt hơn nên stress metrics khác bản trích đoạn trước đó. Baseline 3,6% đến từ dữ kiện có sẵn trong một recall input, không chứng minh nhớ dài hạn.

Live accounting lấy usage_metadata khi SDK trả về, fallback estimator khi không có. Main-agent columns gồm các model calls trong agent/tool loop; summary overhead được in riêng bằng ước lượng. Judge score được validate [0,1]; calls và usage được in riêng, không nhập vào main-agent totals.

## Bonus bước 9

Confidence gate trước ghi User.md: ngưỡng 0.8; assertion 0.95, uncertainty 0.4, hypothetical/third-party 0.1, question 0 (luôn từ chối). Đây là policy weights chưa được hiệu chuẩn. Test ablation 0.8 so với 0.4 cho thấy gate ngăn uncertain location ghi đè fact đã xác nhận.

Decay lưu value/updated_at/confirmations ở sidecar. Half-life mặc định 30 ngày, min priority 0.25, reinforcement có giới hạn theo confirmations. Fact cũ bị loại khỏi persistent context, không xóa khỏi profile. Name được bảo vệ; unknown-age legacy/manual facts không bị gán ngày hết hạn giả. Xác nhận lại làm mới tuổi; correction reset count. Test clock giả lập và demo cho thấy profile context 20 xuống 8 token sau 90 ngày, rồi 12 khi xác nhận lại location. Entity fields và correction/noise filtering cũng đã triển khai.

## Kiểm chứng và giới hạn

60 test pass, gồm core memory, confidence, decay, repeated compact, scaffold contract, sáu provider factories, actual graph checkpoints/tools/dynamic prompt/LLM middleware với fake models, SDK usage và live CLI có judge. Hai lần offline benchmark state sạch cho kết quả giống nhau.

Chưa có credentials remote được cấu hình, nên không gọi API trả phí và không tuyên bố có remote-provider smoke test. Fake models chạy graph thật nhưng không chứng minh chất lượng ngữ nghĩa của LLM thực. Python 3.14.7 hiện phát sinh warning Pydantic từ dependency; không có test failure. requirements.txt ghi phiên bản trực tiếp đã kiểm thử, không phải lock toàn bộ dependency bắc cầu.

Regex/heuristic summary có thể bỏ sót hoặc hiểu sai cách diễn đạt mới; summary nhỏ vẫn mất thông tin. Confidence không xác minh sự thật. Decay có thể bỏ fact vẫn đúng và không xóa lịch sử đang diễn ra. User.md/sidecar replace riêng, chưa có transaction chung hoặc lock đa tiến trình. Live InMemorySaver lưu trong RAM, không phải durable checkpoint database. Những cải tiến production này không phải yêu cầu bài lab. Điểm số/test ẩn do người chấm quyết định.
