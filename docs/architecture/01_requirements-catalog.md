# 01 — Requirements Catalog (Danh mục yêu cầu đã nguyên tử hóa)

> **Mục đích:** biến các keyword/nhóm mục tiêu ở tầng high-level thành **yêu cầu nguyên tử, có ID, kiểm chứng được**.
> Đây là *backbone truy vết* — mọi ADR, thiết kế, test đều tham chiếu về ID ở đây.
> Nguồn: Reference Architecture §1 (G1–G6), §2 (P1–P7), §4 (PH), §5 (NT), §7 (X).

**Quy ước cột:**
- **Priority (MoSCoW):** M=Must / S=Should / C=Could.
- **Verify:** cách kiểm chứng — Test (T) / Demo (D) / Inspection/Review (I) / Analysis/Fitness-fn (A).
- **Trace:** liên kết ngược về nhóm mục tiêu & phân hệ chịu trách nhiệm.

---

## 1. Yêu cầu chức năng — `REQ-F` (Điều phối, dữ liệu, realtime, tích hợp)

| ID | Yêu cầu | Pri | Phân hệ | Verify | Trace nguồn |
|----|---------|:---:|---------|:------:|-------------|
| **REQ-F-001** | Điều phối quy trình nghiệp vụ theo **BPMN 2.0** chuẩn (định nghĩa quy trình khả chuyển giữa engine). | M | PH-5 | D,I | G1, ADR-011 |
| **REQ-F-002** | Workflow engine **biệt lập & tháo lắp được**: nghiệp vụ chỉ nói chuyện qua Abstraction Layer + Adapter; đổi engine = viết lại adapter, không đụng domain. | M | PH-5 | T,D,A | G1, P4, X8, ADR-001 |
| **REQ-F-003** | **Tách trạng thái tiến trình** (do engine giữ) **khỏi dữ liệu nghiệp vụ** (do domain giữ). | M | PH-5, PH-4 | I,A | G1, X6, ADR-001 |
| **REQ-F-004** | Giao tiếp giữa các phân hệ **ưu tiên bất đồng bộ qua event bus**; không gọi đồng bộ hai chiều giữa domain ↔ workflow. | M | PH-6 | I,A | P1, X6, ADR-003 |
| **REQ-F-005** | Mỗi domain là **bounded context độc lập**, sở hữu dữ liệu riêng (**database-per-service**); khởi đầu modular monolith, tách microservice theo điểm nghẽn. | M | PH-4 | I | G6, P2, X9, ADR-002, ADR-010 |
| **REQ-F-006** | **Đẩy dữ liệu realtime** xuống client qua WebSocket/SSE — **không polling**. | M | PH-1 | T,D | G3, ADR-012 |
| **REQ-F-007** | **CQRS**: read model tối ưu riêng cho dashboard/tra cứu, cập nhật qua sự kiện. | M | PH-7 | T,A | G3, X3, ADR-004 |
| **REQ-F-008** | **Optimistic concurrency**: nhiều user sửa đồng thời, phát hiện xung đột theo phiên bản, không mất dữ liệu, không khóa cứng. | M | PH-7 | T | G3, X7, ADR-006 |
| **REQ-F-009** | **Dữ liệu phân tán, không kho trung tâm** (mô hình X-Road); dữ liệu do đơn vị chủ quản nắm giữ. | M | PH-6, PH-7 | I | G5, P3, ADR-009 |
| **REQ-F-010** | Tầng **interoperability** chuẩn hóa: **once-only principle** + **federation** liên ngành/liên vùng. | S | PH-6 | D,I | G5, ADR-009 |
| **REQ-F-011** | **Giao dịch liên service** không dùng distributed transaction: dùng **Saga** + bù trừ (compensation). | M | PH-4, PH-6 | T | X4, ADR-005 |
| **REQ-F-012** | **Dashboard nghiệp vụ realtime** (hồ sơ tồn đọng ở khâu nào) cho lãnh đạo. | M | PH-8, PH-1 | D | G6, ADR-004 |
| **REQ-F-013** | **Nhất quán mạnh cho đường ghi giao dịch; eventual consistency cho read model.** | M | PH-7 | A | X2, ADR-004 |

---

## 2. Yêu cầu bảo mật — `REQ-S` (An toàn thông tin — Security-first)

| ID | Yêu cầu | Pri | Phân hệ | Verify | Trace nguồn |
|----|---------|:---:|---------|:------:|-------------|
| **REQ-S-001** | **Zero Trust**: mọi request xác thực & phân quyền lại ở mọi tầng, kể cả nội bộ mạng. | M | PH-2, PH-3 | T,I | G2, P5, ADR-007 |
| **REQ-S-002** | **IAM** tập trung **RBAC + ABAC**; phân quyền tới **mức bản ghi & mức trường** (data-/field-level). | M | PH-3 | T | G2, ADR-007 |
| **REQ-S-003** | **MFA bắt buộc** cho mọi truy cập người dùng. | M | PH-3 | T,D | G2 |
| **REQ-S-004** | **Separation of duties** + **nguyên tắc bốn mắt** cho thao tác nhạy cảm. | M | PH-3 | T,I | G2 |
| **REQ-S-005** | **Break-glass access**: cấp quyền khẩn cấp, **luôn để lại dấu vết bất biến**. | M | PH-3, PH-7 | T,I | G2, ADR-008 |
| **REQ-S-006** | **Mã hóa at-rest & in-transit** toàn hệ thống (TLS + mã hóa lưu trữ). | M | NT-1 | I,A | G2 |
| **REQ-S-007** | **Quản lý secret/khóa tập trung**; không nhúng cứng khóa trong mã. | M | NT-1 | I,A | G2 |
| **REQ-S-008** | **Audit log bất biến** ghi mọi thao tác nhạy cảm; **tách khỏi business data**; dùng làm bằng chứng. | M | PH-7 | I,A | G2, X5, ADR-008 |
| **REQ-S-009** | **Phân loại dữ liệu theo độ mật**; kiểm soát truy cập & lưu trữ theo phân loại. | M | PH-7, PH-3 | I | G2 |
| **REQ-S-010** | **Cổng bảo mật biên**: API Gateway + WAF + rate limiting + TLS termination; **điểm chặn bảo mật duy nhất**. | M | PH-2 | T,I | G2, ADR-007 |
| **REQ-S-011** | **Tuân thủ NĐ 85/2016** cấp độ 4/5; dữ liệu **trong biên giới**; hỗ trợ **on-premise/air-gap**. | M | NT-1 | I | G2, P6 |
| **REQ-S-012** | **Insider threat detection**: giám sát hành vi & phát hiện bất thường nội bộ; cảnh báo tự động. | S | PH-8 | D,A | G2 |

---

## 3. Yêu cầu phi chức năng — `REQ-N` (NFR — định lượng ở tài liệu 02)

| ID | Yêu cầu | Pri | Nền tảng | Verify | Trace nguồn |
|----|---------|:---:|----------|:------:|-------------|
| **REQ-N-001** | **Availability** đạt SLA mục tiêu; **no SPOF**. | M | NT-2 | A,T | G4, REQ-N §02 |
| **REQ-N-002** | **Chịu tải cao**: đạt mục tiêu RPS + số user đồng thời; hấp thụ đỉnh tải qua message broker. | M | NT-3, PH-6 | T | G3 |
| **REQ-N-003** | **Độ trễ đẩy realtime** dưới ngưỡng cam kết (p95/p99). | M | NT-3, PH-1 | T | G3 |
| **REQ-N-004** | **DR**: đạt **RPO/RTO** cam kết; backup + diễn tập phục hồi thật. | M | NT-2 | T,D | G4 |
| **REQ-N-005** | **Redundancy / clustering / multi-AZ-DC** (active-active hoặc active-passive). | M | NT-2 | I,T | G4 |
| **REQ-N-006** | **Scalability ngang**: service **stateless** + autoscaling + load balancing. | M | NT-3, PH-4 | A,T | G3, G6 |
| **REQ-N-007** | **Resilience**: circuit breaker + bulkhead + graceful degradation. | M | NT-2 | T | G4 |
| **REQ-N-008** | **Multi-level cache + read replica + sharding** cho tải đọc cao. | S | NT-3, PH-7 | T | G3 |
| **REQ-N-009** | **Observability**: metrics + logs + traces thống nhất; distributed tracing. | M | NT-5 | I,D | G6 |

---

## 4. Yêu cầu vận hành & tổ chức — `REQ-O` (Big System & DevSecOps & con người)

| ID | Yêu cầu | Pri | Nền tảng | Verify | Trace nguồn |
|----|---------|:---:|----------|:------:|-------------|
| **REQ-O-001** | **CI/CD + DevSecOps**: quét bảo mật tự động (SAST/DAST) trong pipeline. | M | NT-4 | I,A | G6 |
| **REQ-O-002** | Triển khai **không gián đoạn**: blue-green / canary + rollback rõ ràng. | M | NT-4 | D | G6 |
| **REQ-O-003** | **Infrastructure as Code**; quản lý cấu hình theo môi trường. | M | NT-4 | I | G6 |
| **REQ-O-004** | **API versioning** tương thích ngược. | M | NT-4 | T | G6 |
| **REQ-O-005** | **Hiện đại hóa tăng dần** — **không rip-and-replace**; giao hàng gia tăng theo domain. | M | P7 | I | G6, X9, ADR-002 |
| **REQ-O-006** | **Chủ quyền số**: ưu tiên chuẩn mở & OSS kiểm soát được; **tránh vendor lock-in**; chứng minh bằng engine-swap drill. | M | P6 | D,A | G6, X8, ADR-011 |
| **REQ-O-007** | **Quản lý thay đổi tổ chức**: executive sponsor, truyền thông sớm, đào tạo người dùng. | M | §8 plan | I | G6 |
| **REQ-O-008** | **Chống nợ kỹ thuật**: kiểm toán kiến trúc định kỳ + ngưỡng nợ trong fitness functions. | S | NT-4 | A | G6 |

---

## 5. Thống kê phủ (coverage self-check)

| Nhóm mục tiêu gốc | REQ phủ | Đủ? |
|---|---|:---:|
| G1 Điều phối quy trình | F-001..004 | ✅ |
| G2 An toàn thông tin | S-001..012 | ✅ |
| G3 Chịu tải & realtime | F-006,007,008 · N-002,003,006,008 | ✅ |
| G4 Sẵn sàng & tin cậy | N-001,004,005,007 | ✅ |
| G5 Dữ liệu & tích hợp | F-009,010,013 | ✅ |
| G6 Big System & vận hành | F-005 · N-009 · O-001..008 | ✅ |
| 9 xung đột X1–X9 | ánh xạ tại RTM §3 | ✅ |

> **Kết luận:** 13+12+9+8 = **42 yêu cầu nguyên tử**, phủ 100% 6 nhóm mục tiêu và 9 xung đột.
> Không có nhóm mục tiêu nào không có REQ; không có REQ nào không có phân hệ chịu trách nhiệm.
