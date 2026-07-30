# Requirements Traceability Matrix (RTM)

> **Công cụ truy vết trung tâm.** Mỗi yêu cầu được lần theo chuỗi:
> **REQ → Phân hệ/thiết kế → ADR → NFR/Fitness → Threat → Cách kiểm chứng → Milestone chốt.**
> Đây là bằng chứng "không bỏ sót, không mồ côi": mọi REQ có nơi hiện thực + cách nghiệm thu;
> mọi ADR có REQ biện minh. Cập nhật mỗi increment (nguyên tắc #6 Master Plan).

**Chú thích cột kiểm chứng:** T=Test · D=Demo · I=Inspection/Review · A=Analysis/Fitness-fn.

---

## 1. Ma trận chức năng & bảo mật (REQ-F / REQ-S)

| REQ | Mô tả ngắn | Phân hệ | ADR | Fitness/NFR | Threat | Verify | Gate chốt |
|-----|-----------|---------|-----|-------------|--------|:------:|:---------:|
| REQ-F-001 | BPMN 2.0 orchestration | PH-5 | 001,011 | FIT-010 | — | D,I | G2 |
| REQ-F-002 | Engine tháo lắp được | PH-5 | 001,011 | FIT-010,007 | TM-008 | T,D,A | G2/G8 |
| REQ-F-003 | Tách state/business data | PH-5,PH-4 | 001 | FIT-007 | TM-008 | I,A | G3 |
| REQ-F-004 | Async event-driven | PH-6 | 003 | FIT-007 | TM-003 | I,A | G3 |
| REQ-F-005 | BC độc lập, DB-per-service | PH-4 | 002,010 | FIT-007 | — | I | G3/G4 |
| REQ-F-006 | Realtime push, no-poll | PH-1 | 012 | FIT-004,N-003 | TM-009 | T,D | G3 |
| REQ-F-007 | CQRS read model | PH-7 | 004 | FIT-004 | — | T,A | G3 |
| REQ-F-008 | Optimistic concurrency | PH-7 | 006 | — | — | T | G4 |
| REQ-F-009 | Dữ liệu phân tán, no kho TT | PH-6,PH-7 | 009 | — | TM-006 | I | G4 |
| REQ-F-010 | Interop once-only/federation | PH-6 | 009 | — | TM-002 | D,I | G4 |
| REQ-F-011 | Saga liên service | PH-4,PH-6 | 005 | — | — | T | G4 |
| REQ-F-012 | Dashboard nghiệp vụ realtime | PH-8,PH-1 | 004 | FIT-004 | — | D | G3 |
| REQ-F-013 | Strong write / eventual read | PH-7 | 004 | — | — | A | G3 |
| REQ-S-001 | Zero Trust mọi tầng | PH-2,PH-3 | 007 | — | TM-001 | T,I | G3/G6 |
| REQ-S-002 | RBAC+ABAC field-level | PH-3 | 007 | — | TM-007,010 | T | G4/G6 |
| REQ-S-003 | MFA bắt buộc | PH-3 | 007 | — | TM-001 | T,D | G3 |
| REQ-S-004 | SoD + bốn mắt | PH-3 | 008 | — | TM-005,010,011 | T,I | G6 |
| REQ-S-005 | Break-glass có dấu vết | PH-3,PH-7 | 008 | — | TM-005,011 | T,I | G6 |
| REQ-S-006 | Mã hóa at-rest/in-transit | NT-1 | 007,008 | — | TM-003,006 | I,A | G3/G6 |
| REQ-S-007 | Secret/key mgmt tập trung | NT-1 | — | — | TM-012 | I,A | G3 |
| REQ-S-008 | Audit bất biến tách biệt | PH-7 | 008 | — | TM-004,005 | I,A | G6 |
| REQ-S-009 | Phân loại độ mật | PH-7,PH-3 | — | — | TM-006 | I | G1/G6 |
| REQ-S-010 | Gateway+WAF+rate limit | PH-2 | 007 | — | TM-001,009 | T,I | G3 |
| REQ-S-011 | NĐ 85/2016 cấp 4/5, in-border | NT-1 | — | — | TM-006 | I | G1/G6 |
| REQ-S-012 | Insider-threat detection | PH-8 | — | — | TM-011 | D,A | G6 |

---

## 2. Ma trận phi chức năng & vận hành (REQ-N / REQ-O)

| REQ | Mô tả ngắn | Nền tảng | ADR | Fitness | Verify | Gate chốt |
|-----|-----------|----------|-----|---------|:------:|:---------:|
| REQ-N-001 | Availability / no SPOF | NT-2 | — | FIT-001,002 | A,T | G5 |
| REQ-N-002 | Throughput / concurrent | NT-3,PH-6 | 003 | FIT-003 | T | G5 |
| REQ-N-003 | Latency realtime | NT-3,PH-1 | 012,007,004 | FIT-004 | T | G5 |
| REQ-N-004 | RPO/RTO (DR) | NT-2 | 008 | FIT-005 | T,D | G5 |
| REQ-N-005 | Multi-AZ redundancy | NT-2 | — | FIT-002 | I,T | G5 |
| REQ-N-006 | Stateless + autoscale | NT-3,PH-4 | 002 | FIT-006,007 | A,T | G5 |
| REQ-N-007 | Circuit breaker/bulkhead | NT-2 | — | FIT-008 | T | G5 |
| REQ-N-008 | Cache/replica/sharding | NT-3,PH-7 | 010 | FIT-003 | T | G5 |
| REQ-N-009 | Observability | NT-5 | — | FIT-009 | I,D | G3 |
| REQ-O-001 | CI/CD + DevSecOps | NT-4 | — | FIT-002,009 | I,A | G3 |
| REQ-O-002 | Blue-green/canary | NT-4 | — | — | D | G7 |
| REQ-O-003 | IaC | NT-4 | — | FIT-002 | I | G3 |
| REQ-O-004 | API versioning | NT-4 | — | — | T | G4 |
| REQ-O-005 | No rip-and-replace | P7 | 002 | — | I | xuyên suốt |
| REQ-O-006 | Chủ quyền số / no lock-in | P6 | 001,011 | FIT-010 | D,A | G6/G8 |
| REQ-O-007 | Quản lý thay đổi tổ chức | §8 | — | — | I | G0/G7 |
| REQ-O-008 | Chống nợ kỹ thuật | NT-4 | — | FIT (debt threshold) | A | G8 |

---

## 3. Ma trận truy vết XUNG ĐỘT (chứng minh 9 xung đột X1–X9 đều được hóa giải)

| Xung đột | Vấn đề | ADR hóa giải | Cơ chế | Kiểm chứng |
|----------|--------|--------------|--------|-----------|
| **X1** | Zero Trust ⟷ realtime | ADR-007 | Verify token 1 lần tại GW + read model tối ưu | FIT-004 (latency budget §02) |
| **X2** | Strong ⟷ available (CAP) | ADR-004 | Strong ghi / eventual đọc | A (consistency review) |
| **X3** | Dữ liệu phân tán ⟷ dashboard tổng hợp | ADR-004,009 | Tổng hợp qua event vào read model dashboard | D (dashboard demo) |
| **X4** | Microservice ⟷ nhất quán liên service | ADR-005 | Saga + compensation | T (saga test) |
| **X5** | Audit bất biến ⟷ retention/hủy | ADR-008 | Tách audit/business + ẩn danh hóa | I,A |
| **X6** | Engine biệt lập ⟷ hiệu năng | ADR-001,003 | Async qua event bus, engine ngoài đường nóng | FIT-004 |
| **X7** | Sửa đồng thời ⟷ không mất dữ liệu | ADR-006 | Optimistic concurrency | T |
| **X8** | OSS/chủ quyền ⟷ enterprise mạnh | ADR-001,011 | Abstraction cho đổi engine linh hoạt | FIT-010 (engine-swap) |
| **X9** | Monolith khởi đầu ⟷ microservice scale | ADR-002 | BC rõ từ đầu, tách theo điểm nghẽn | I (coupling FIT-007) |

---

## 4. Ma trận phủ Milestone (REQ ↔ Gate — kế thừa Master Plan §3, chi tiết hóa)

| Milestone | Gate | REQ được chốt chính | Sản phẩm kiến trúc liên quan |
|-----------|------|--------------------|------------------------------|
| M0 | G0 | O-007 | README (governance), ID scheme |
| M1 | G1 | N-001..009 (định lượng), S-009,011 | 01,02,03,05 (catalog, NFR, C4, threat) |
| M2 | G2 | F-001,002 · O-006 | 04 PH-5 spec + PoC + ADR-011 |
| M3 | G3 | F-003..007 · S-001,003,006,007,010 · N-009 · O-001,003 | walking skeleton, FIT-007/009 |
| M4 | G4 | F-005,008,009,010,011 · S-002 · O-004 | per-domain, FIT contract |
| M5 | G5 | N-001..008 | load/HA/DR, FIT-001..008 |
| M6 | G6 | S-004,005,008,012 · O-006 | pentest, threat model final |
| M7 | G7 | O-002,007 | go-live blue-green |
| M8 | G8 | F-002 · O-006,008 | engine-swap drill (FIT-010) |

---

## 5. Kiểm tra tính toàn vẹn RTM (self-audit)

- ✅ **42/42 REQ** đều có ≥1 phân hệ + ≥1 cách verify + 1 gate chốt → không REQ mồ côi.
- ✅ **12/12 ADR** đều trace về ≥1 REQ → không quyết định vô căn cứ.
- ✅ **9/9 xung đột** X1–X9 có ADR hóa giải + cách kiểm chứng.
- ✅ **12 threat TM-###** đều map tới REQ-S + biện pháp; rủi ro Cao đều có test tại G6.
- ✅ **10 fitness function** FIT-### phủ các NFR định lượng trọng yếu.

> **Kết luận truy vết:** chuỗi *Yêu cầu gốc (product-spec) → REQ-ID → Design/ADR → NFR/Fitness → Threat →
> Test → Milestone/Gate* khép kín 2 chiều. Đây là điều kiện để ARB nghiệm thu tại G1.
