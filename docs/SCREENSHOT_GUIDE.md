# Hướng dẫn chụp 5 ảnh evidence

Danh sách chính thức nằm trong [SUBMISSION.md](SUBMISSION.md). Bài nộp chỉ có **3 output text và đúng 5 ảnh runtime** tại `submission/evidence/`; không chụp terminal cho pytest hoặc validators. Không chỉnh sửa ảnh làm sai lệch kết quả và không để lộ `.env`, API key, secret hoặc PII thô.

## 1. `01-incident-log.png`

Mở `data/logs.jsonl`, tìm `req-ed5d4851` và bật Word Wrap. Chụp dòng `response_sent` lúc `2026-09-30T05:27:19.267671Z` sao cho đọc được `event`, `correlation_id`, `feature=monitoring`, `model`, `env`, `latency_ms=2664`, `tool_name=retrieval` và `tool_success=true`. Không dùng ảnh trace Langfuse thay cho log.

## 2. `02-trace-list.png`

Mở project Langfuse cá nhân `day13-k4-l3b-2A202602578` → **Traces**. Chọn khoảng thời gian chứa workload ngày 2026-09-30, để tên project và ít nhất 10 trace rows đọc được. Không mở trang API Keys.

## 3. `03-incident-trace.png`

Mở trace `e4caa452ff97c42cd5a1b1f1c5c5ccac` của `req-ed5d4851`. Expand `lab-agent-run`, `retrieval` và `generation`; hiển thị metadata có correlation ID, prompt `day13-chat` production v1, model, usage/cost và duration. Retrieval khoảng 2,506 giây; generation khoảng 0,158 giây. Ảnh này phải nối được trực tiếp với ảnh 01.

## 4. `04-prompt-versioning.png`

Đặt trace `fc7656929cb7338f2ebe5da628f6564d` (đã dùng `production` v2) cạnh trang versions của `day13-chat` sau rollback. Trang versions cần thấy `baseline` và `production` ở v1, `candidate` ở v2. Chụp toàn màn hình đủ đọc ID, name, version và label; không chụp trang chứa key.

## 5. `05-dashboard-incident.png`

Mở `http://127.0.0.1:8000/dashboard` và chụp đủ sáu panel, đơn vị, time range, threshold/SLO line và điểm bất thường. Phút `05:27 UTC` (12:27 ICT) của challenge có 5 request và latency P95 2666 ms; phút phục hồi `05:31 UTC` có P95 161 ms. Dashboard chỉ hiển thị cửa sổ 60 phút, nên hãy chụp khi hai phút này còn trong cửa sổ. Nếu đã hết, chạy lại đúng challenge và cập nhật report cùng ID trước khi chụp; không dùng ảnh rời khỏi dữ liệu được báo cáo.

Lưu đúng năm tên file ở trên, rồi mở lại mọi link trong `submission/REPORT.md` để kiểm tra ảnh đọc được. Với trang dashboard dài, dùng **Capture full size screenshot** của trình duyệt như [SUBMISSION.md](SUBMISSION.md) hướng dẫn.
