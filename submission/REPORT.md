# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Tất Đạt
- **MSSV:** 2A202602578
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/Gaohonggg/K4-L3-DAY13-NguyenTatDat-2A202602578-Monitoring-LLMOps
- **Commit SHA cuối:** Bổ sung khi đã thêm đủ năm ảnh, tạo commit nộp và ghi cùng SHA đó trên LMS/Codelabs.
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602578`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [pytest.txt](evidence/pytest.txt) |
| Log validator | [log-validator.txt](evidence/log-validator.txt) |
| Dashboard validator | [dashboard-validator.txt](evidence/dashboard-validator.txt) |
| Structured log + incident log | [01-incident-log.png](evidence/01-incident-log.png) — cần chụp |
| Trace list | [02-trace-list.png](evidence/02-trace-list.png) — cần chụp |
| Trace waterfall + metadata + incident trace | [03-incident-trace.png](evidence/03-incident-trace.png) — cần chụp |
| Prompt versions + promote/rollback | [04-prompt-versioning.png](evidence/04-prompt-versioning.png) — cần chụp |
| Dashboard + incident metric | [05-dashboard-incident.png](evidence/05-dashboard-incident.png) — cần chụp |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 22 log records, 20 thiếu required/context, 0 correlation ID hợp lệ | **100/100**; 140 records, 65 correlation IDs, 0 PII hit | [Kết quả validator](evidence/log-validator.txt); baseline còn TODO CP1. |
| `validate_dashboard.py` | Hợp lệ 6/6 panel theo contract | **6/6 panel** và `/dashboard/data` có dữ liệu runtime | [Kết quả validator](evidence/dashboard-validator.txt); validator chỉ kiểm tra contract. |
| `pytest` | 22 passed (3.22s) | **29 passed (1.31s)** | Chạy bằng `.venv/bin/python -m pytest -q`; [output](evidence/pytest.txt). |
| Số traces hợp lệ | 10 trace IDs riêng biệt, mỗi trace hiện có một observation `lab-agent-run` | 43 trace IDs phân biệt trong Langfuse; incident trace có đủ root, retrieval, generation | Truy vấn observations API v2 của project cá nhân; một số batch export của lần challenge bị timeout. |
| Số PII leak | 0 theo `validate_logs.py` trên workload mẫu | **0** theo validator; incident trace được chọn không có PII thô | Validator đọc toàn bộ log hiện có. |
| Latency P95 / TTFT P95 | 1018 ms / 55 ms | **2667 ms / 55 ms** trong cửa sổ dashboard lúc 12:31 ICT | Riêng phút incident 12:27, P95 là 2666 ms; sau tắt incident, phút 12:31 là 161 ms. |
| Retrieval success rate | 10/10 request có `tool_success=true` (100%) | **100%** trong cửa sổ dashboard | Sự cố làm chậm retrieval, không làm request lỗi. |

### Baseline CP0 — 2026-09-30, khoảng 11:24 ICT

- Dùng môi trường `.venv` hiện có (Python 3.12.13), không tạo môi trường mới.
- `/health` trả `ok=true`, `tracing_enabled=true`; cả ba practice incident đều tắt.
- `python scripts/load_test.py` gửi 10 request mẫu, cả 10 trả HTTP 200. Response hiện trả `correlation_id=MISSING`.
- Langfuse nhận 10 observation `lab-agent-run` thuộc 10 trace ID riêng; prompt `day13-chat` với label `production` chưa tồn tại nên app dùng local fallback.
- `/metrics` sau workload: traffic 10, latency P50/P95/P99 = 415/1018/1018 ms, TTFT P95 = 55 ms, tổng cost 0.0207 USD, quality trung bình 0.88.
- `data/logs.jsonl` là file runtime được `.gitignore` bỏ qua; baseline validator đọc 22 records vì có hai lần khởi động API. Không dùng file này làm evidence cuối sau khi CP1 hoàn thiện.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context cũ ở đầu request, chấp nhận `x-request-id` đúng dạng `req-<8-hex>` hoặc sinh ID mới, rồi bind vào structlog, `request.state`, response body và hai header `x-request-id`/`x-response-time-ms`. Context được xóa khi request kết thúc.
- **Các metadata được ghi vào structured log:** Trước `request_received`, API bind `user_id_hash` (SHA-256 rút gọn), `session_id`, `feature`, `model`, `env`; các event tiếp theo giữ cùng `correlation_id`. Trace dùng cùng ID trong metadata và scrub các dimension do người dùng nhập.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor đệ quy che email, số điện thoại Việt Nam, CCCD và thẻ trong mọi giá trị chuỗi của event, bao gồm context, payload lồng nhau và exception đã format. Processor chạy trước cả file JSONL writer và terminal renderer.
- **Cách kiểm chứng kết quả:** Workload 10 request với concurrency 5 đều trả HTTP 200; lần kiểm tra cuối `validate_logs.py` đạt 100/100 trên 140 records, 65 correlation ID hợp lệ, 0 thiếu field/context và 0 PII hit. Langfuse observations API v2 cho phép đối chiếu `correlation_id` trong log và trace. Pytest đạt 29 passed, gồm kiểm tra request đồng thời, error path, response header và PII trong log/trace dimensions.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces trong project cá nhân:** Dùng Langfuse Python SDK với key project trong `.env` để truy vấn Projects và observations API v2 sau khi chạy workload trên API local. Hai lượt 10 request cho baseline và candidate trước đó có trace ID riêng với root/retrieval/generation. Ở lần kiểm tra cuối, API trả 107 observations trên 43 trace IDs phân biệt; 32 generation observations có prompt version v1 hoặc v2. Các trace ID bên dưới đã được tra lại trực tiếp.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` (agent) chứa `retrieval` (retriever) và `generation` (generation). Retrieval ghi số tài liệu, trạng thái và query preview đã scrub. Generation ghi model, managed prompt, prompt/answer preview đã scrub, input/output/total tokens, estimated cost và TTFT; raw prompt/output không được capture tự động.
- **Cách nối trace với log:** Middleware tạo hoặc xác thực `correlation_id` dạng `req-<8-hex>`; cùng ID xuất hiện trong structured log và trace metadata. Ví dụ request chạy với label `production` sau promote có `correlation_id=req-cf8f7014` và trace ID `fc7656929cb7338f2ebe5da628f6564d`.
- **Prompt name:** `day13-chat`, lấy từ Langfuse qua `LANGFUSE_PROMPT_NAME` và label được cấu hình trong môi trường chạy; fallback local chỉ dùng khi fetch thất bại.
- **Version/label baseline:** v1 có `baseline`; nội dung chứa đủ ba biến `feature`, `docs`, `message`.
- **Version/label candidate:** v2 có `candidate`; thêm chỉ dẫn trả lời tối đa ba bullet, giữ nguyên ba biến.
- **Trace ID của mỗi version:** baseline v1 `e86240454301f581c4c04dce3951cdf1`; candidate v2 `6fdb80b482f0b47fca1edd91240c1842`.
- **Cách promote và rollback `production`:** Chuyển label `production` từ v1 sang v2, chạy request mới và xác nhận trace `fc7656929cb7338f2ebe5da628f6564d` có `prompt_label=production`, `prompt_version=2`, `prompt_source=langfuse`. Sau đó chuyển `production` về v1; đọc lại trực tiếp từ Langfuse xác nhận `production=1`, `baseline=1`, `candidate=2`.
- **Prompt của incident:** Trace `e4caa452ff97c42cd5a1b1f1c5c5ccac` dùng `production` v1, nên lần chậm này không phải do promote v2.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** API phục vụ `/dashboard` và `/dashboard/data`, đọc trực tiếp `data/logs.jsonl` trong cửa sổ 60 phút và làm mới 30 giây. Sáu panel là latency P50/P95/P99 cùng TTFT P95, traffic, errors cùng retrieval success, cost, input/output tokens và quality proxy. Trang hiển thị đơn vị, time range và threshold theo [dashboard.yaml](../config/dashboard.yaml); runtime đã được mở và kiểm tra bằng dữ liệu workload thực. `validate_dashboard.py` đạt 6/6 panel.
- **SLO và lý do chọn:** [slo.yaml](../config/slo.yaml) định nghĩa `fast_successful_requests`, mục tiêu 99.5% request trả thành công trong tối đa 3000 ms trên cửa sổ 28 ngày. Baseline CP0 có P95 1018 ms trên 10 request, chưa đủ mẫu cho tail latency dài hạn; ngưỡng 3000 ms cho khoảng dự phòng nhưng vẫn nhận diện chậm nghiêm trọng.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; với 10,000 request trong cửa sổ, tối đa 50 request được phép lỗi hoặc vượt 3000 ms.
- **Ba alert và runbook tương ứng:** [alert_rules.yaml](../config/alert_rules.yaml) định nghĩa `HighLatencyP95` (warning, P95 > 3000 ms), `HighErrorRate` (critical, > 2%), `LowRetrievalSuccess` (warning, < 90%). Mỗi rule có duration 5 phút, owner, kênh Slack `#k4-l3b-alerts` và mục riêng trong [runbook](../docs/alerts.md); các bước đi từ dashboard sang log/correlation ID rồi trace và mitigation.

Incident có ngưỡng riêng 2000 ms trong `config/challenge.json`, thấp hơn ngưỡng SLO 3000 ms. P95 của riêng phút incident vượt ngưỡng challenge nhưng chưa vượt SLO; không coi đó là bằng chứng alert `HighLatencyP95` đã kích hoạt. Dashboard đang đo thời gian xử lý agent từ `response_sent.latency_ms`, còn thời gian chờ phía client khi nhiều request bị xếp hàng phải được xem riêng.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`, incident `rag_slow`, seed 1312, feature `monitoring`; file challenge chính thức giữ nguyên.
- **Khoảng thời gian điều tra:** 2026-09-30 12:27:16–12:27:29 ICT (05:27:16–05:27:29 UTC), khi 5 query challenge chạy với concurrency 5. Lượt sau tắt incident diễn ra khoảng 12:31:34 ICT.
- **Triệu chứng từ metrics:** Dashboard dùng log thật cho thấy phút 12:27 có 5 request, latency P95 **2666 ms**, cao hơn ngưỡng challenge **2000 ms**; phút 12:31 sau khi tắt incident, cùng 5 query có P95 **161 ms**. Cả hai lượt đều không có lỗi; retrieval success 100%, TTFT khoảng 52–55 ms. Ở phía client, lượt incident mất 10,68–13,35 giây/request do các request chờ nhau, còn lượt phục hồi khoảng 0,82 giây/request. Phải phân biệt số đo client với `latency_ms` trong log, vốn chỉ tính từ khi agent bắt đầu xử lý.
- **Log line và correlation ID liên quan:** `response_sent` lúc `2026-09-30T05:27:19.267671Z`, `correlation_id=req-ed5d4851`, `feature=monitoring`, `model=claude-sonnet-4-5`, `env=dev`, `latency_ms=2664`, `ttft_ms=53`, `tool_name=retrieval`, `tool_success=true`, `tokens_in=34`, `tokens_out=161`, `cost_usd=0.002517`. Dòng `request_received` cùng ID ở `05:27:16.601806Z`.
- **Trace ID và span gây ảnh hưởng:** Langfuse trace `e4caa452ff97c42cd5a1b1f1c5c5ccac` có metadata `correlation_id=req-ed5d4851`; root `lab-agent-run` dài **2,665 giây**, child `retrieval` **2,506 giây**, child `generation` **0,158 giây** với 34 input tokens, 161 output tokens và estimated cost 0.002517 USD. Child observations gắn đúng root; prompt là `day13-chat` `production` v1.
- **Root cause:** Challenge bật `rag_slow`; `app/mock_rag.py` đưa `time.sleep(2.5)` vào `retrieve()`. Trace xác định retrieval chiếm gần như toàn bộ thời gian xử lý, còn generation và token/cost không tăng tương ứng. Năm `request_received` được ghi nối tiếp cách nhau khoảng 2,67 giây; kết hợp với việc endpoint `async def chat` gọi agent/retrieval đồng bộ, đây là bằng chứng các request chờ nhau trên event loop, làm tail latency phía client cao hơn số đo trong từng log.
- **Fix action:** Đã tắt incident bằng `scripts/inject_incident.py --disable` và chạy lại cùng 5 query; P95 trong log giảm về 161 ms. Với dịch vụ thực, chuyển retrieval chặn sang async I/O hoặc thread pool, áp timeout cho vector store và kiểm tra lại latency dưới tải đồng thời.
- **Preventive measure:** Theo dõi thêm latency end-to-end từ middleware/client để phát hiện thời gian xếp hàng, vì `response_sent.latency_ms` hiện chỉ đo agent. Kiểm thử đồng thời với cùng workload, cảnh báo khi P95 vượt ngưỡng phù hợp và dùng runbook `docs/alerts.md` để nối metric → log → trace.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng `data/logs.jsonl` làm nguồn duy nhất cho dashboard runtime, và đưa cùng `correlation_id` vào log lẫn Langfuse trace. Nhờ vậy metric phút 12:27 dẫn được tới một request cụ thể và child span chậm mà không dựa vào suy đoán từ aggregate.
- **Một lỗi/blocker đã gặp:** SDK báo `Failed to export spans batch` do timeout tới Langfuse Cloud trong lượt challenge; chỉ một trong năm request incident được xác nhận có đủ ba observations trên Cloud tại lúc kiểm tra.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra output server, sau đó truy vấn observations API v2 và chọn trace `e4caa452ff97c42cd5a1b1f1c5c5ccac` đã xuất thành công, đối chiếu `req-ed5d4851` với log. Không dùng trace chưa xuất hoặc bịa ID làm evidence. Export timeout còn là giới hạn cần theo dõi nếu triển khai lâu dài.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metric phút 12:27 cho biết P95 2666 ms; log `req-ed5d4851` chứng minh request `monitoring` mất 2664 ms và retrieval vẫn thành công; trace cùng ID cho thấy retrieval 2506 ms còn generation 158 ms. Kết hợp với challenge `rag_slow`, kết luận chậm nằm ở retrieval.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Trace incident dùng `production` v1; v2 đã rollback nên không quy lỗi cho prompt mới. Token/cost và TTFT giúp loại trừ giả thuyết generation tăng tải. SLO 99.5%/3000 ms có error budget 0.5%; ngưỡng incident 2000 ms cho phép phát hiện sớm hơn ngưỡng SLO.
- **Điều quan trọng nhất đã học:** Một P95 tăng chỉ là triệu chứng. Cần cùng time range, `correlation_id` và span duration để xác định nguyên nhân; cũng phải biết metric đang đo thời gian xử lý hay thời gian người dùng chờ.
- **Hạn chế hoặc phần chưa hoàn thành:** Năm ảnh runtime chưa được chụp. Export Langfuse có timeout với một số trace của lượt challenge. Sau khi thêm ảnh, cần đối chiếu chúng với các ID trong báo cáo, chốt commit và nộp SHA cuối.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối sau khi thêm ảnh.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối sau khi thêm ảnh.
- [ ] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident đã đối chiếu metric → log → trace bằng `req-ed5d4851`; cần chụp màn hình tương ứng.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
