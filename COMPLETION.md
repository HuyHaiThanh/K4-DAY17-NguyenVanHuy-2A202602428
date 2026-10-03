# Đối chiếu hoàn thành Guide.md

| Bước | Triển khai và bằng chứng |
|---|---|
| 1 | Môi trường, cấu trúc và requirements.txt; toàn bộ test chạy được |
| 2 | LabConfig, paths, compact settings, sáu provider và judge config; test factory/config |
| 3 | Token estimator, User.md CRUD, extraction, summary/compact; test persistence và repeated compaction |
| 4 | Baseline nhớ trong thread, quên thread mới; offline + LangGraph live checkpoint |
| 5 | Advanced có cả ba lớp memory; live tools/dynamic prompt/LLM summarization, profile sau restart |
| 6 | Hai benchmark, đủ sáu cột; CLI offline/live/judge, chi phí phụ trợ tách riêng |
| 7 | 60 test pass, gồm contract scaffold và integration graph/tools/middleware |
| 8 | STEP8.md phân tích kết quả cuối, REPORT.md ghi phương pháp/giới hạn |
| 9 | Confidence threshold, memory decay, entity fields, correction/conflict và question/noise filtering đều có mã và test |

Bản triển khai hoàn thành toàn bộ chín bước cùng phần live được mô tả trong scaffold. Kiểm chứng remote service cần credentials/server thực; hiện không có credentials remote trong cấu hình, nên phạm vi kiểm chứng live là graph thật với fake model. Không cam kết điểm hoặc test ẩn.

Lệnh kiểm tra: python -m pytest src -v; python src/benchmark.py; python src/benchmark_decay.py. Hướng dẫn live và cấu hình: REPORT.md và .env.example.
