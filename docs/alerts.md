# Alert và runbook

Ba rule trong [`config/alert_rules.yaml`](../config/alert_rules.yaml) theo dõi triệu chứng từ structured log. Người trực là `student-2A202602578`; kênh thông báo được cấu hình là Slack `#k4-l3b-alerts`. Mỗi rule phải duy trì vượt ngưỡng 5 phút. Tại tải thấp, rule error và retrieval chỉ đánh giá khi có tối thiểu 10 request/attempt trong cửa sổ để tránh nhiễu từ một mẫu đơn lẻ.

## Alert 1

**HighLatencyP95 · warning · P95 > 3000 ms trong 5 phút.** Người dùng phải chờ lâu hơn để nhận câu trả lời. Rule liên quan trực tiếp đến ngưỡng latency của SLO `fast_successful_requests`.

1. Mở dashboard latency với cùng cửa sổ thời gian; xác nhận P95, P99, TTFT và thời điểm bắt đầu tăng.
2. Lọc `data/logs.jsonl` theo `response_sent.latency_ms > 3000`, lấy `correlation_id` của request chậm.
3. Mở trace cùng `correlation_id` trên Langfuse; so sánh retrieval, khoảng giữa retrieval và generation (bao gồm prompt fetch), rồi generation để xác định bước chiếm thời gian.

Mitigation: giảm tải hoặc khôi phục dependency chậm; rollback prompt chỉ khi trace cho thấy regression gắn với version mới. Theo dõi P95 trở lại dưới ngưỡng trước khi đóng alert.

## Alert 2

**HighErrorRate · critical · error rate > 2% trong 5 phút**, với ít nhất 10 request. Người dùng nhận lỗi thay vì câu trả lời; rule liên quan đến success SLI của SLO.

1. Mở panel Errors; xác nhận tổng request, error rate và breakdown theo `error_type`.
2. Lọc `request_failed` trong khoảng sự cố, chọn một `correlation_id` và kiểm tra `error_type`/`tool_name`.
3. Mở trace cùng ID để tìm span lỗi và phân biệt lỗi retrieval, generation hay dependency ngoài.

Mitigation: khôi phục dependency bị lỗi hoặc quay về cấu hình/prompt ổn định nếu có bằng chứng regression. Kiểm tra error rate và SLO burn sau khi phục hồi.

## Alert 3

**LowRetrievalSuccess · warning · retrieval success < 90% trong 5 phút**, với ít nhất 10 attempt. Người dùng có nguy cơ nhận lỗi hoặc câu trả lời thiếu context; rule bảo vệ chất lượng RAG.

1. Mở panel Errors, xác nhận retrieval success giảm và đối chiếu error rate/quality.
2. Lọc các log `tool_name=retrieval` và `tool_success=false`, chọn `correlation_id` đại diện.
3. Mở trace cùng ID, kiểm tra retriever span, thời gian, trạng thái và số tài liệu trả về.

Mitigation: kiểm tra kết nối vector store và cấu hình truy xuất; chuyển sang fallback an toàn nếu dependency chưa phục hồi. Chỉ đóng alert khi success rate trên 90% với đủ số mẫu.
