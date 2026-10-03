# Day 17 — Memory Systems for AI Agent

**Học viên:** Nguyễn Văn Huy — **MSSV:** 2A202602428 — **Cohort:** K4

**Repo nộp:** [K4-DAY17-NguyenVanHuy-2A202602428](https://github.com/HuyHaiThanh/K4-DAY17-NguyenVanHuy-2A202602428).

Người chấm đọc file này để chạy bài, sau đó đọc [STEP8.md](STEP8.md) để xem phân tích số liệu và bonus.

## Cài đặt và hai lệnh kiểm bài

Python >= 3.11; Python 3.11/3.12 phù hợp để tránh warning dependency đang thấy ở Python 3.14.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/benchmark.py
pytest src/test_agents.py -v
```

Hai lệnh cuối chạy offline, không cần .env/API key hay state có sẵn. Benchmark tạo state tạm sạch riêng cho mỗi suite và cố định clock offline; kết quả hai lần chạy giống nhau. File state/ được sinh khi dùng config/agent và được Git bỏ qua.

Benchmark in Standard Benchmark và Long-Context Stress Benchmark, mỗi bảng có Baseline/Advanced và sáu metric. Test_agents có đủ bốn test yêu cầu cùng ba test bổ sung; lệnh chấm hiện cho **7 passed**. Bộ test mở rộng: `python -m pytest src -v` (65 passed ở bản đã kiểm chứng).

## Cấu trúc và phần triển khai

```text
K4-DAY17-NguyenVanHuy-2A202602428/
├── src/                 # agent, memory, benchmark và tests
├── data/                # hai input gốc, không chỉnh sửa
├── STEP8.md             # phân tích bốn câu hỏi + bonus
├── README.md            # hướng dẫn chạy và nộp
├── requirements.txt     # phiên bản trực tiếp đã kiểm thử
├── .env.example         # mẫu cấu hình live, không có credentials
├── results/             # output benchmark/ablation/decay và kiểm tra sạch
└── docs/reference/      # Guide/Rubric gốc, chỉ để tham khảo
```

Baseline chỉ nhớ trong thread. Advanced có User.md bền vững, short-term và compact summary; cập nhật facts theo field để xử lý correction. Confidence gate chặn facts không chắc chắn/câu hỏi trước khi ghi; memory decay giảm ưu tiên truy xuất facts cũ. Chữ ký hàm và dataclass fields của scaffold gốc được giữ và có test contract.

Recall dùng một thread mới cho mỗi conversation, khác training thread và cùng protocol ở cả hai agent. Input/thứ tự/câu hỏi không lọc hoặc sửa. Memory growth tính cả User.md và sidecar decay. Tokens offline là ước lượng, quality offline là proxy recall/concision; giới hạn và bằng chứng nằm trong STEP8.md.

## Kiểm chứng bổ sung và live

```powershell
python src/benchmark_ablation.py
python src/benchmark_decay.py
python src/benchmark.py --live
python src/benchmark.py --live --judge
```

Hai lệnh đầu offline. Live cần cấu hình provider/model/credentials qua .env, tham khảo .env.example; không commit .env. --live gọi LangGraph với InMemorySaver, dynamic profile prompt, tools read/write/edit có gate và middleware LLM summarization. --judge chấm ngữ nghĩa bằng judge model; summary/judge overhead được in riêng. Hỗ trợ OpenAI, custom-compatible, Gemini, Anthropic, Ollama và OpenRouter.

Live đã được kiểm thử bằng graph thật với fake models; chưa gọi API remote vì chưa có credentials. Offline summary/regex và confidence weights là heuristic; decay có thể loại khỏi prompt fact vẫn đúng. Chưa hỗ trợ lock/transaction đa tiến trình; InMemorySaver giữ checkpoints trong RAM.

## Nộp VLearn

Link repo ở đầu README đã được nộp trên VLearn theo xác nhận của học viên ngày 03/10/2026.

Checklist 6/6: hai bảng benchmark; mỗi bảng hai agent và sáu metric; đủ bốn test cốt lõi (7 test trong lệnh chấm đều pass); repo đúng mẫu tên và không track .env/state; có STEP8.md; link VLearn đã nộp.
