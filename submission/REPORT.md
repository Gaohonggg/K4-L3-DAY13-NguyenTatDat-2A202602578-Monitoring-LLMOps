# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Tất Đạt
- **MSSV:** 2A202602578
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/Gaohonggg/K4-L3-DAY13-NguyenTatDat-2A202602578-Monitoring-LLMOps
- **Commit SHA cuối:** Chưa chốt; điền SHA của commit chứa báo cáo và đủ 14 ảnh trước khi nộp trên LMS/Codelabs.
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602578`

## 2. Evidence index

Bộ evidence của bài nộp này gồm ba output text và 14 ảnh đã chụp. Ảnh terminal là bản chụp của các kết quả text; các ảnh còn lại thể hiện log, PII, Langfuse, dashboard và incident. Mọi đường dẫn dưới đây tính từ `submission/REPORT.md`.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [pytest.txt](evidence/pytest.txt) |
| Log validator | [log-validator.txt](evidence/log-validator.txt) |
| Dashboard validator | [dashboard-validator.txt](evidence/dashboard-validator.txt) |
| 01 — Pytest | [01-pytest.png](evidence/01-pytest.png) |
| 02 — Log validator | [02-log-validator.png](evidence/02-log-validator.png) |
| 03 — Dashboard validator | [03-dashboard-validator.png](evidence/03-dashboard-validator.png) |
| 04 — Structured log | [04-structured-log.png](evidence/04-structured-log.png) |
| 05 — PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) |
| 06 — Langfuse trace list | [06-trace-list.png](evidence/06-trace-list.png) |
| 07 — Trace tree và generation | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| 08 — Trace metadata và redaction | [08-trace-metadata.png](evidence/08-trace-metadata.png) |
| 09 — Prompt v1/v2 và labels | [09-prompt-versions.png](evidence/09-prompt-versions.png) |
| 10 — Prompt sau rollback | [10-prompt-rollback.png](evidence/10-prompt-rollback.png) |
| 11 — Dashboard tổng quan | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) |
| 12 — Dashboard cửa sổ incident | [12-incident-metric.png](evidence/12-incident-metric.png) |
| 13 — Incident log | [13-incident-log.png](evidence/13-incident-log.png) |
| 14 — Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả/evidence | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 22 log records, 20 thiếu required/context, 0 correlation ID hợp lệ | **100/100**; 140 records, 65 correlation IDs, 0 PII hit tại thời điểm chạy validator | [Kết quả validator](evidence/log-validator.txt), [ảnh](evidence/02-log-validator.png); log còn được ghi tiếp khi chụp incident lúc 14:42. |
| `validate_dashboard.py` | Hợp lệ 6/6 panel theo contract | **6/6 panel** và `/dashboard/data` có dữ liệu runtime | [Kết quả validator](evidence/dashboard-validator.txt), [ảnh](evidence/03-dashboard-validator.png); validator chỉ kiểm tra contract. |
| `pytest` | 22 passed (3.22s) | **29 passed**; file text ghi 1.31s, ảnh terminal ghi 1.32s ở lần chạy khác | Chạy bằng `.venv/bin/python -m pytest -q`; [output](evidence/pytest.txt), [ảnh](evidence/01-pytest.png). |
| Số traces hợp lệ | 10 trace IDs riêng biệt, mỗi trace có một observation `lab-agent-run` | 43 trace IDs phân biệt tại lần truy vấn API trước khi chụp; ảnh 06 có nhiều hơn 10 dòng observation; ảnh 14 có đủ root, retrieval, generation | Số 43 là snapshot API, không phải bộ đếm đọc từ ảnh 06. |
| Số PII leak | 0 theo `validate_logs.py` trên workload mẫu | **0** trong 140 records tại thời điểm chạy validator; incident trace được chọn không có PII thô | Ảnh 05 còn hiển thị input kiểm thử nguyên văn ở terminal, tách biệt với nội dung log đã scrub. |
| Latency P95 / TTFT P95 | 1018 ms / 55 ms | Dashboard ảnh 12 lúc 14:44 ICT: **7654 ms / 55 ms** trên cửa sổ 60 phút | Trong log, năm request incident phút 14:42 có P95 **2666 ms**; năm request sau khi tắt incident phút 14:44 có P95 **175 ms**. P95 toàn cửa sổ bị chi phối bởi request thử PII lúc 14:08 với latency 7654 ms. |
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
- **Cách kiểm chứng kết quả:** [Ảnh structured log](evidence/04-structured-log.png) cho thấy `request_received` và `response_sent` chia sẻ `req-888a1fc6`, có model/env/feature, latency, token và cost. [Ảnh PII](evidence/05-pii-redaction.png) cho thấy input kiểm thử ở terminal và `message_preview` trong log được thay bằng các marker `REDACTED_*`; ảnh này vẫn chứa dữ liệu mẫu nguyên văn ở terminal. Validator đã đạt 100/100 trên **140 records tại thời điểm chụp ảnh 02**, 65 correlation ID hợp lệ, 0 thiếu field/context và 0 PII hit. Log tiếp tục phát sinh sau thời điểm đó, nên kết quả 140 records không đại diện cho toàn bộ file log hiện tại. Pytest đạt 29 passed.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces trong project cá nhân:** [Ảnh trace list](evidence/06-trace-list.png) hiển thị project `day13-k4-l3b-2A202602578`, khoảng thời gian một ngày và nhiều hơn 10 dòng observation. Truy vấn observations API v2 trước khi chụp ảnh trả 107 observations trên 43 trace IDs phân biệt; 32 generation observations có prompt version v1 hoặc v2. Đây là số liệu ở thời điểm truy vấn, không phải bộ đếm đọc trực tiếp từ ảnh 06.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` (agent) chứa `retrieval` (retriever) và `generation` (generation). [Ảnh 07](evidence/07-trace-waterfall.png) cho thấy cây observation, prompt `day13-chat` v1, token và cost của request thử PII; [ảnh 08](evidence/08-trace-metadata.png) cho thấy metadata `correlation_id=req-a1b2c3d4` và query preview đã scrub. Đây là request thử PII lúc 14:08, **khác** request incident ở ảnh 13–14. Incident trace cũng có đủ ba observation và được phân tích riêng ở mục 7.
- **Cách nối trace với log:** Middleware tạo hoặc xác thực `correlation_id` dạng `req-<8-hex>`; cùng ID xuất hiện trong structured log và trace metadata. Ảnh 05 và 08 cùng dùng `req-a1b2c3d4`; ảnh 13 và 14 cùng dùng `req-d90cb39c`. Một request khác sau khi promote v2 có `correlation_id=req-cf8f7014` và trace ID `fc7656929cb7338f2ebe5da628f6564d`, được đối chiếu qua API nhưng không xuất hiện trong bộ ảnh.
- **Prompt name:** `day13-chat`, lấy từ Langfuse qua `LANGFUSE_PROMPT_NAME` và label được cấu hình trong môi trường chạy; fallback local chỉ dùng khi fetch thất bại.
- **Version/label baseline:** v1 có `baseline` và `production` sau rollback; nội dung chứa đủ ba biến `feature`, `docs`, `message`. [Ảnh 10](evidence/10-prompt-rollback.png) cho thấy trạng thái này.
- **Version/label candidate:** v2 có `candidate` và `latest`; thêm chỉ dẫn trả lời tối đa ba bullet, giữ nguyên ba biến. [Ảnh 09](evidence/09-prompt-versions.png) cho thấy v1 và v2 trên cùng trang versions.
- **Trace ID của mỗi version:** baseline v1 `e86240454301f581c4c04dce3951cdf1`; candidate v2 `6fdb80b482f0b47fca1edd91240c1842`.
- **Cách promote và rollback `production`:** Chuyển label `production` từ v1 sang v2, chạy request mới và xác nhận trace `fc7656929cb7338f2ebe5da628f6564d` có `prompt_label=production`, `prompt_version=2`, `prompt_source=langfuse` qua API. Sau đó chuyển `production` về v1; ảnh 09–10 ghi nhận trạng thái sau rollback: `production` và `baseline` ở v1, `candidate` ở v2. Bộ ảnh không chụp trace `production` v2 tại thời điểm promote.
- **Prompt của incident:** [Ảnh 14](evidence/14-incident-trace.png) hiển thị generation metadata `prompt_name=day13-chat`, `prompt_label=production`, `prompt_version=1`; lần chậm này không gắn với promote v2.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** API phục vụ `/dashboard` và `/dashboard/data`, đọc trực tiếp `data/logs.jsonl` trong cửa sổ 60 phút và làm mới 30 giây. [Ảnh 11](evidence/11-dashboard-overview.png) và [ảnh 12](evidence/12-incident-metric.png) hiển thị đủ sáu panel: latency P50/P95/P99 cùng TTFT P95, traffic, errors cùng retrieval success, cost, input/output tokens và quality proxy. Đơn vị, time range và threshold hiển thị theo [dashboard.yaml](../config/dashboard.yaml); validator đạt 6/6 panel. Ảnh 11 lúc 14:37 chỉ có một request thử PII trong cửa sổ; ảnh 12 lúc 14:44 có 11 request gồm request đó, năm request incident và năm request phục hồi.
- **SLO và lý do chọn:** [slo.yaml](../config/slo.yaml) định nghĩa `fast_successful_requests`, mục tiêu 99.5% request trả thành công trong tối đa 3000 ms trên cửa sổ 28 ngày. Baseline CP0 có P95 1018 ms trên 10 request, chưa đủ mẫu cho tail latency dài hạn; ngưỡng 3000 ms cho khoảng dự phòng nhưng vẫn nhận diện chậm nghiêm trọng.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; với 10,000 request trong cửa sổ, tối đa 50 request được phép lỗi hoặc vượt 3000 ms.
- **Ba alert và runbook tương ứng:** [alert_rules.yaml](../config/alert_rules.yaml) định nghĩa `HighLatencyP95` (warning, P95 > 3000 ms), `HighErrorRate` (critical, > 2%), `LowRetrievalSuccess` (warning, < 90%). Mỗi rule có duration 5 phút, owner, kênh Slack `#k4-l3b-alerts` và mục riêng trong [runbook](../docs/alerts.md); các bước đi từ dashboard sang log/correlation ID rồi trace và mitigation.

Incident có ngưỡng riêng 2000 ms trong `config/challenge.json`, thấp hơn ngưỡng SLO 3000 ms. P95 **riêng phút 14:42** vượt ngưỡng challenge nhưng chưa vượt SLO. P95 **toàn cửa sổ 60 phút** trong ảnh 12 là 7654 ms vì bao gồm request thử PII lúc 14:08; con số này không được quy toàn bộ cho challenge. Ảnh chụp một thời điểm cũng chưa chứng minh alert `HighLatencyP95` duy trì vượt ngưỡng đủ 5 phút. Dashboard đo thời gian xử lý agent từ `response_sent.latency_ms`; thời gian chờ phía client khi các request bị xếp hàng phải được xem riêng.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`, incident `rag_slow`, seed 1312, feature `monitoring`; file challenge chính thức giữ nguyên.
- **Khoảng thời gian điều tra:** 2026-09-30 **14:42:08–14:42:21 ICT** (07:42:08–07:42:21 UTC), khi năm query trong challenge được chạy với concurrency 5. Lượt phục hồi sau khi tắt `rag_slow` diễn ra lúc **14:44:10–14:44:11 ICT**.
- **Triệu chứng từ metrics:** [Ảnh dashboard 12](evidence/12-incident-metric.png) lúc 14:44:48 hiển thị 11 request trong cửa sổ 60 phút, P95 toàn cửa sổ **7654 ms**, error 0% và retrieval success 100%. Giá trị 7654 ms đến từ request thử PII lúc 14:08 trong [ảnh 05](evidence/05-pii-redaction.png), nên không đại diện cho riêng challenge. Từ năm dòng `response_sent` của phút 14:42, các latency là **2666, 2663, 2661, 2664, 2662 ms**; theo cách tính nearest-rank của dashboard, P95 phút incident là **2666 ms**, vượt ngưỡng challenge 2000 ms. Sau khi tắt incident, năm request cùng workload ở phút 14:44 có latency **155, 175, 160, 160, 160 ms**, P95 **175 ms**. Hai lượt đều không ghi lỗi; đây là phép so sánh theo log, còn ảnh 12 là snapshot tổng hợp cả cửa sổ.
- **Log line và correlation ID liên quan:** [Ảnh 13](evidence/13-incident-log.png) cho thấy request `k4-l3b-challenge-s05` với `correlation_id=req-d90cb39c`; `request_received` lúc `2026-09-30T07:42:19.143191Z` và `response_sent` lúc `07:42:21.807090Z`. Dòng response ghi `feature=monitoring`, `model=claude-sonnet-4-5`, `env=dev`, `latency_ms=2662`, `ttft_ms=55`, `tool_name=retrieval`, `tool_success=true`, `tokens_in=35`, `tokens_out=167`, `cost_usd=0.00261`.
- **Trace ID và span gây ảnh hưởng:** [Ảnh 14](evidence/14-incident-trace.png) hiển thị trace `9f9941257bae08da3419361ea54d78b4` với metadata `correlation_id=req-d90cb39c`, trùng ảnh 13. Root `lab-agent-run` dài khoảng **2,66 giây**; child `retrieval` khoảng **2,50 giây**, child `generation` **157 ms**. Generation ghi 202 tokens, estimated cost **0.00261 USD**, prompt `day13-chat` `production` v1.
- **Root cause:** Challenge bật `rag_slow`; [mock_rag.py](../app/mock_rag.py) thêm `time.sleep(2.5)` vào `retrieve()`. Trong ảnh 14, retrieval chiếm gần toàn bộ thời gian trace, còn generation chỉ 157 ms. Năm `request_received` của phút 14:42 được ghi nối tiếp cách nhau khoảng 2,67 giây; kết hợp với việc endpoint async gọi retrieval đồng bộ, điều này phù hợp với hiện tượng các request phải chờ nhau trên event loop. `response_sent.latency_ms` chỉ đo thời gian xử lý bên trong mỗi request, không bao gồm toàn bộ thời gian chờ phía client.
- **Fix action:** Log ghi `incident_disabled` lúc `07:44:10.448026Z`; chạy lại đúng năm query, P95 theo log giảm từ **2666 xuống 175 ms**. Với dịch vụ thực, cần chuyển retrieval chặn sang async I/O hoặc thread pool, áp timeout cho vector store và đo lại dưới tải đồng thời.
- **Preventive measure:** Theo dõi thêm latency end-to-end từ middleware/client để phát hiện thời gian xếp hàng, vì `response_sent.latency_ms` hiện chỉ đo agent. Kiểm thử đồng thời với cùng workload, cảnh báo khi P95 vượt ngưỡng phù hợp và dùng runbook `docs/alerts.md` để nối metric → log → trace.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng `data/logs.jsonl` làm nguồn cho dashboard runtime và đưa cùng `correlation_id` vào log lẫn Langfuse trace. Nhờ vậy năm request chậm ở phút 14:42 dẫn được tới request `req-d90cb39c` và child span retrieval trong ảnh 13–14.
- **Một lỗi/blocker đã gặp:** SDK từng báo `Failed to export spans batch` do timeout tới Langfuse Cloud trong một lượt challenge trước đó; việc đối chiếu trace bằng API bị gián đoạn.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra output server, truy vấn observations API v2 để biết trace nào đã xuất thành công, rồi dùng lượt chạy 14:42 có trace `9f9941257bae08da3419361ea54d78b4` và log `req-d90cb39c` để chụp ảnh 13–14. Export timeout vẫn là hạn chế cần giám sát.
- **Cách hiểu luồng Metrics → Logs → Traces:** Ảnh dashboard 12 cho thấy latency bất thường trong cửa sổ; log riêng phút 14:42 cho P95 2666 ms. Ảnh log 13 xác định request `req-d90cb39c` mất 2662 ms; ảnh trace 14 với cùng ID cho thấy retrieval 2500 ms còn generation 157 ms. Kết hợp với `rag_slow`, nguyên nhân chậm nằm ở retrieval. P95 tổng cửa sổ 7654 ms còn chịu ảnh hưởng của request thử PII, nên không được dùng như số đo riêng của challenge.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Trace incident dùng `production` v1; v2 đã rollback nên không quy lỗi cho prompt mới. Token/cost và TTFT giúp loại trừ giả thuyết generation tăng tải. SLO 99.5%/3000 ms có error budget 0.5%; ngưỡng incident 2000 ms cho phép phát hiện sớm hơn ngưỡng SLO.
- **Điều quan trọng nhất đã học:** Một P95 tăng chỉ là triệu chứng. Cần cùng time range, `correlation_id` và span duration để xác định nguyên nhân; cũng phải biết metric đang đo thời gian xử lý hay thời gian người dùng chờ.
- **Hạn chế hoặc phần chưa hoàn thành:** Bộ 14 ảnh đã chụp nhưng chưa được đưa vào commit nộp và chưa có SHA cuối. Ảnh 05 hiển thị dữ liệu mẫu nguyên văn ở terminal; ảnh 08 và 14 hiển thị Langfuse `public_key` trong metadata. Ảnh 09–10 chỉ ghi nhận trạng thái labels sau rollback, không hiển thị trace `production` v2 ở thời điểm promote. Export Langfuse từng timeout ở lượt trước.

## 9. Checklist trước khi nộp

- [ ] Commit báo cáo và 14 ảnh, rồi điền SHA cuối của commit đó.
- [x] Có 3 file text và 14 ảnh, mỗi file được dẫn bằng đường dẫn tương đối trong evidence index.
- [x] Incident đã đối chiếu metric → log → trace bằng `req-d90cb39c` trong ảnh 12–14 và log runtime.
- [ ] Xác nhận yêu cầu bảo mật của đề mới đối với input mẫu trong ảnh 05 và `public_key` hiển thị ở ảnh 08/14.
- [ ] Repository chạy lại được theo README.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
