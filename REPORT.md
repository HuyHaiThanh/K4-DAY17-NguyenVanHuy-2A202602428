# Báo cáo Day 17 — Memory Systems for AI Agent

## Chạy và kiểm chứng

Từ root: `.\.venv\Scripts\python.exe -m pytest src/test_agents.py -v` và `.\.venv\Scripts\python.exe src/benchmark.py`. Benchmark luôn offline, không cần API key, mỗi suite dùng state tạm sạch. Kết quả đầy đủ: benchmark_results.txt.

## Kiến trúc

Baseline giữ messages theo thread và trích facts từ chính lịch sử đó. Advanced bổ sung User.md theo user, keyed updates thay fact cũ, hợp nhất interests, summary giới hạn và recent messages. Cả hai dùng chung extraction và response để so sánh công bằng. Thread owner check chống trộn user. Profile được ghi UTF-8 bằng file tạm và replace, đường dẫn giữ profiles/<user>/User.md cho ID an toàn; ID không an toàn dùng namespace hash riêng và vẫn đọc được hồ sơ hash của bản trước.

Ngưỡng mặc định 1000 token, giữ 4 messages. Summary giới hạn khoảng 1/3 ngưỡng. Recent messages quá dài vẫn có thể vượt ngưỡng; đây là trigger nén chứ không phải hard context limit.

## Kết quả

| Suite | Agent | Output tokens | Prompt tokens | Recall | Growth bytes | Compactions |
|---|---|---:|---:|---:|---:|---:|
| Standard | Baseline | 1521 | 14742 | 3,6% | 0 | 0 |
| Standard | Advanced | 1664 | 21582 | 100% | 957 | 0 |
| Stress | Baseline | 281 | 22300 | 0% | 0 | 0 |
| Stress | Advanced | 312 | 11043 | 100% | 647 | 3 |

Advanced tăng recall nhờ hồ sơ bền vững. Standard không compact và prompt cost tăng khoảng 46,4% vì mang profile mỗi lượt. Stress compact 3 lần, giảm prompt cost khoảng 50,5%. Output tokens không giảm; lợi ích nằm ở giảm lịch sử xử lý lặp lại. Profile keyed updates hạn chế tăng trưởng do facts lặp.

## Phương pháp

Tokens ước lượng bằng ceil(len(text.strip())/4), không phải usage tính phí. Output chỉ tính assistant response. Prompt tính lịch sử trước sinh câu trả lời, thêm profile và summary với Advanced. Training và recall đều nằm trong tổng. Recall hỏi ngay sau từng conversation, thread mới riêng cho từng question. Score 0/0,5/1 tương ứng không khớp/khớp một phần/khớp tất cả expected_contains, không phân biệt hoa thường. Quality là recall nhân hệ số ngắn gọn, không phải judge độc lập.

## Phản biện và giới hạn

- Baseline có 3,6% vì một recall question chứa tên ngay trong input. Điều đó không chứng minh nhớ dài hạn. Substring scoring có thể thưởng echo, và có thể sai với phủ định. Test memory độc lập kiểm tra baseline quên và Advanced nhớ sau restart.
- 100% trên dataset không chứng minh hiểu mọi câu tiếng Việt hay tuân thủ chính xác style 3 bullet. Offline đo memory plumbing.
- Summary là trích đoạn giới hạn, có thể mất chi tiết tạm thời. Recall dataset chủ yếu kiểm tra profile, không đủ chứng minh nhớ mọi chủ đề news. Tin tức trong input chỉ được xem là dữ liệu test, chưa xác minh sự kiện.
- Regex extraction có test correction và nhiễu nhưng chưa có confidence hiệu chuẩn. Interests hợp nhất chưa hỗ trợ xóa sở thích. Đã thêm confidence gate bằng quy tắc (PROFILE_CONFIDENCE_THRESHOLD=0.8), có test ablation; score chưa được hiệu chuẩn. Đã triển khai memory decay không xóa dữ liệu gốc; còn thiếu transaction chung giữa profile/metadata và đồng bộ nhiều tiến trình.
- Live dùng direct chat invocation với factory sáu provider, bật force_offline=False khi có credentials (Ollama không cần key); thiếu credentials remote thì fallback offline. Chưa triển khai LangGraph tool/middleware hoặc LLM summary. Không gọi API thật và live token vẫn là ước lượng. Model mặc định có thể thay bằng env.
- Env: LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, JUDGE_PROVIDER, JUDGE_MODEL, COMPACT_THRESHOLD_TOKENS, COMPACT_KEEP_MESSAGES, cùng API_KEY/BASE_URL tương ứng provider. Judge config có sẵn nhưng offline không dùng judge.

## Tương thích scaffold

Đã khôi phục AgentContext, force_offline, future annotations, chữ ký hàm, dataclass fields và thứ tự khai báo từ commit đề bài dc0e2da. Test contract dùng snapshot khai báo gốc, không cần Git khi chạy. Không có bộ test ẩn của người chấm nên chỉ cam kết tương thích các khai báo được công bố, không cam kết pass mọi hành vi chưa được mô tả.

## Review cuối

37 test hành vi và contract pass trên Python 3.14.7, gồm profile, compact nhiều lần, same-thread recall, fresh-thread forgetting, restart, user isolation, correction/noise và hai dataset. Hai lần benchmark sạch cho kết quả giống nhau. Không hard-code tên DũngCT trong câu trả lời; test dùng tên Lan. .env, state, .venv và cache được bỏ qua Git.

## Memory decay

DecayingProfile lưu updated_at/confirmations/value ở sidecar, dùng half-life mặc định 30 ngày và ngưỡng priority 0.25. Các field dưới ngưỡng ngừng được đưa vào profile context; name và hồ sơ cũ không rõ tuổi được giữ. Xác nhận lại làm mới tuổi; correction reset reinforcement của giá trị cũ. Confidence gate chạy trước cả ghi fact lẫn cập nhật tuổi. Xem STEP9.md và decay_results.txt cho công thức, demo và trade-off. Memory growth trong bảng tính cả profile và sidecar; metadata không được gửi vào prompt. Benchmark gốc diễn ra nhanh nên chưa có facts hết tuổi; hiệu quả decay được kiểm tra riêng bằng clock giả lập.
