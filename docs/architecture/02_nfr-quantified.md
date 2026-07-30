# 02 — NFR Định lượng & Fitness Functions

> **Nguyên tắc M1:** *"Không có số thì không thể nghiệm thu."* Tài liệu này gán **ngưỡng đo được**
> cho mỗi `REQ-N`, kèm **fitness function** (`FIT-###`) — bài test kiến trúc tự động chạy trong CI.
>
> ⚠️ **Trạng thái con số:** tất cả giá trị dưới đây là **`PROPOSED`** — đề xuất của SA làm điểm khởi đầu
> thương lượng. Con số cuối cùng **phải do stakeholder ký** tại **Gate G1** (đầu vào là capacity planning
> thực tế + phân loại cấp độ NĐ 85/2016). SA đề xuất để có mốc, không tự chốt.

---

## 1. Quality Attribute Scenarios (kịch bản thuộc tính chất lượng — chuẩn ISO/IEC 25010)

Mỗi NFR viết dạng kịch bản 6 phần: *Nguồn kích thích → Kích thích → Bối cảnh → Thành phần → Phản hồi → Đo lường*.

| NFR | Kịch bản (Source→Stimulus→Response Measure) |
|-----|---------------------------------------------|
| Availability | *Trong 1 node/1 AZ chết bất ngờ, hệ thống* → tiếp tục phục vụ request → *đo:* uptime tháng ≥ mục tiêu, 0 request lỗi do node chết. |
| Latency (realtime) | *Khi 1 hồ sơ đổi trạng thái, người dùng đang xem dashboard* → thấy cập nhật đẩy xuống → *đo:* p95 ≤ ngưỡng đẩy. |
| Throughput | *Giờ cao điểm, N user đồng thời thao tác* → hệ thống xử lý không suy giảm → *đo:* RPS đạt mục tiêu, p99 API ≤ ngưỡng. |
| Recoverability | *Sau thảm họa mất 1 DC* → khôi phục ở DC dự phòng → *đo:* RTO ≤ X, mất dữ liệu ≤ RPO. |

---

## 2. Bảng NFR định lượng

| REQ | Chỉ số | Mục tiêu (PROPOSED) | Ngưỡng tối thiểu | Phương pháp đo | Fitness fn |
|-----|--------|---------------------|------------------|----------------|:----------:|
| REQ-N-001 | Availability (business hours) | **99.95%** (~22 phút/tháng) | 99.9% | Synthetic probe + uptime monitor | FIT-001 |
| REQ-N-001 | Single Point of Failure | **0** SPOF | 0 | Kiến trúc review + fault injection | FIT-002 |
| REQ-N-002 | Throughput (đường ghi) | **2,000 RPS** sustained | 1,000 RPS | Load test (k6/Gatling) | FIT-003 |
| REQ-N-002 | User đồng thời | **20,000** concurrent | 10,000 | Soak test 2h | FIT-003 |
| REQ-N-003 | Độ trễ đẩy realtime | **p95 ≤ 1s**, p99 ≤ 2.5s | p95 ≤ 2s | End-to-end event→UI probe | FIT-004 |
| REQ-N-003 | Độ trễ API đọc (read model) | **p95 ≤ 200ms**, p99 ≤ 500ms | p95 ≤ 400ms | Load test | FIT-004 |
| REQ-N-003 | Độ trễ API ghi (command) | **p95 ≤ 500ms**, p99 ≤ 1s | p95 ≤ 800ms | Load test | FIT-004 |
| REQ-N-004 | RPO (mất dữ liệu tối đa) | **≤ 1 phút** (domain trọng yếu ≈ 0 nhờ event log) | ≤ 5 phút | DR drill | FIT-005 |
| REQ-N-004 | RTO (thời gian khôi phục) | **≤ 30 phút** | ≤ 1 giờ | DR drill (thật, không giấy) | FIT-005 |
| REQ-N-005 | Multi-AZ | **≥ 2 AZ** active-active (hoặc active-passive nếu air-gap) | 2 AZ | Topology inspection | FIT-002 |
| REQ-N-006 | Autoscale phản ứng | scale-out khi CPU>70% trong **≤ 2 phút** | ≤ 5 phút | Load spike test | FIT-006 |
| REQ-N-006 | Statelessness | **100%** service tầng ứng dụng stateless | 100% | Fitness: quét session in-memory | FIT-007 |
| REQ-N-007 | Circuit breaker | mở mạch khi lỗi > **50%/10s**, half-open sau 30s | — | Chaos test | FIT-008 |
| REQ-N-007 | Graceful degradation | mất tính năng phụ, **giữ tính năng lõi** khi quá tải | — | Chaos test | FIT-008 |
| REQ-N-009 | Trace coverage | **100%** request xuyên biên service có trace-id | ≥ 95% | Fitness: quét header propagation | FIT-009 |

---

## 3. Fitness Functions (test kiến trúc tự động — chạy trong CI mỗi commit hoặc nightly)

> Fitness function = "unit test cho thuộc tính kiến trúc". Đây là thứ biến NFR từ lời hứa thành cổng chặn merge.

| ID | Kiểm tra gì | Loại | Tần suất | Fail → |
|----|-----------|------|----------|--------|
| **FIT-001** | Uptime synthetic probe endpoint core | Runtime probe | Liên tục | Alert SOC |
| **FIT-002** | Không có thành phần nào thiếu redundancy (IaC scan + topology) | Static + fault inject | PR + nightly | Block merge |
| **FIT-003** | Load test đạt RPS/concurrent target trên staging | Perf test | Nightly + pre-release | Block release |
| **FIT-004** | Latency budget p95/p99 cho push/read/write | Perf test | Nightly | Block release |
| **FIT-005** | DR restore đạt RPO/RTO | Game-day (định kỳ) | Hàng quý | Escalate ARB |
| **FIT-006** | Autoscaling phản ứng đúng ngưỡng | Chaos/load | Nightly | Warn |
| **FIT-007** | **Coupling & statelessness**: không service nào giữ state phiên; không domain nào import trực tiếp engine SDK (chỉ qua PH-5 port) | ArchUnit-style static | PR | **Block merge** |
| **FIT-008** | Circuit breaker + bulkhead kích hoạt đúng khi inject lỗi | Chaos test | Nightly | Warn |
| **FIT-009** | Trace propagation 100% qua biên service | Static + runtime | PR + nightly | Block merge |
| **FIT-010** | **Engine-swap fitness**: chạy bộ test contract của Abstraction Layer trên ≥2 adapter → cả hai xanh (bằng chứng tháo lắp được) | Contract test | Pre-release + M8 drill | Block release |

> **FIT-007 & FIT-010 là hai fitness function chiến lược nhất** — chúng cơ học bảo vệ 2 quyết định
> cốt lõi (isolation của workflow engine, statelessness). Vi phạm = chặn merge, không thương lượng.

---

## 4. Ngân sách độ trễ (latency budget) — phân rã p95 đường đọc realtime

Chứng minh mục tiêu p95 ≤ 1s cho push là khả thi (giải quyết xung đột **X1** Zero Trust ⟷ hiệu năng):

```
Sự kiện phát sinh (domain commit)                    ~   50 ms
  → Event bus (publish + route)                       ~   80 ms
  → Projector cập nhật read model                     ~  120 ms
  → Push gateway (WebSocket fan-out)                   ~  100 ms
  → Mạng tới client                                    ~  150 ms
  ─────────────────────────────────────────────────────────────
  Tổng đường nóng                                      ~  500 ms   ◄ p50
  Dự phòng (jitter, GC, retry)                         ~  500 ms
  ─────────────────────────────────────────────────────────────
  Ngân sách p95                                        ~ 1000 ms ✅
```
> **Chốt kiến trúc:** vì token chỉ verify **1 lần tại gateway** (ADR-007) và đọc từ **read model đã tối ưu**
> (ADR-004), Zero Trust **không** nằm trên đường nóng lặp lại → NFR realtime khả thi. Đây là hiện thực của X1.
