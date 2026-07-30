# 05 — RAID Log (Risks · Assumptions · Issues · Dependencies)

> **RAID** là sổ sống theo dõi Rủi ro, Giả định, Vấn đề, Phụ thuộc. Rà soát **hàng tuần** (Ways of Working §2).
> Khởi tạo từ Master Plan §5 (RAID excerpt) + threat model + các điểm mở của dossier.
> Chủ sở hữu log: Lead SA. Trạng thái: `LIVE` từ 2026-07-03.

**Thang mức:** Impact/Prob = Cao(C)/TB/Thấp(T). Status = Open / Mitigating / Closed / Accepted.

---

## 1. RISKS (Rủi ro — điều *có thể* xảy ra)

| ID | Rủi ro | Impact | Prob | Giảm thiểu | Chủ | Xử lý tại | Status |
|----|--------|:------:|:----:|-----------|-----|-----------|:------:|
| R-01 | Khóa cứng vào workflow engine | C | TB | Abstraction Layer + adapter + PoC tháo lắp sớm + FIT-010 | SA | M2, M8 | Mitigating |
| R-02 | Tách microservice quá sớm | TB | TB | Modular monolith, tách theo bằng chứng điểm nghẽn (ADR-002) | SA | M3–M4 | Mitigating |
| R-03 | Realtime không đạt ở tải cao | C | TB | Spike sớm; CQRS+read model+WSS; latency budget; load test | PLT | M2, M5 | Open |
| R-04 | Đánh giá sai cấp độ NĐ 85/2016 | C | TB | Chốt cấp độ ngay M1; hồ sơ tuân thủ sớm | SEC | M1, M6 | Open |
| R-05 | Cám dỗ big-bang (rip-and-replace) | C | TB | Kỷ luật giao hàng gia tăng theo domain (ADR-002, P7) | ES | Xuyên suốt | Mitigating |
| R-06 | Người dùng không chịu dùng hệ thống | C | TB | Change mgmt & truyền thông từ M0; đào tạo M7 | CM | M0, M7 | Open |
| R-07 | Nợ kỹ thuật tích lũy | TB | C | Kiểm toán định kỳ; ngưỡng nợ trong fitness (D6) | PLT | M8 | Mitigating |
| R-08 | Mối đe dọa nội bộ (insider) rò rỉ dữ liệu mật | C | TB | SoD, bốn mắt, break-glass, giám sát hành vi (TM-011) | SEC | M4, M6 | Open |
| R-09 | Eventual consistency gây nhầm lẫn nghiệp vụ | TB | TB | Ranh giới rõ strong/eventual (X2, ADR-004); UX phản ánh trạng thái | DA | M4 | Open |
| R-10 | Interop/X-Road: rò rỉ độ mật khi federation | C | T | Phân loại độ mật lái federation; air-gap cho MẬT (TM-006) | SEC | M6, M8 | Open |
| R-11 | Mất/trùng event (dual-write) | TB | TB | Transactional outbox + idempotency (`06_data` §3.1) | DA | M3–M4 | Mitigating |
| R-12 | **Tooling bootstrap (GitHub cá nhân) không tuân thủ air-gap / dữ liệu-trong-biên-giới** | C | TB | Time-box M0–M2, **cấm dữ liệu thật/mật**; di trú self-managed/air-gap trước M3 (ADR-T01…T03 → superseder). Trace: ADR-T01, A-02, D-01 | PLT | M2–M3 | Mitigating |

---

## 2. ASSUMPTIONS (Giả định — coi là đúng cho tới khi được xác nhận)

| ID | Giả định | Nếu sai thì | Xác nhận tại |
|----|----------|-------------|--------------|
| A-01 | Con số NFR (PROPOSED) sẽ được stakeholder chốt ở khoảng đề xuất | Phải thiết kế lại capacity | G1 |
| A-02 | Cấp độ an toàn là 4 hoặc 5 (hệ mật) | Đổi hạ tầng (air-gap/on-prem) | M1 |
| A-03 | OSS engine (Camunda/Flowable) đáp ứng air-gap | Cân nhắc tự xây (rủi ro schedule) | M2 (PoC) |
| A-04 | Có đội nội bộ đủ năng lực giữ hệ mật | Rủi ro nợ kỹ thuật + phụ thuộc ngoài | M0–M1 |
| A-05 | Dữ liệu phải nằm trong biên giới | Kiến trúc hosting phải điều chỉnh | M1 |
| A-06 | Sprint 2 tuần, đội đa chức năng cỡ trung | Lịch M1+ phải hiệu chỉnh | M0 |

---

## 3. ISSUES (Vấn đề — điều *đang* xảy ra, cần xử lý)

| ID | Vấn đề | Impact | Hành động | Chủ | Status |
|----|--------|:------:|-----------|-----|:------:|
| I-01 | Chưa có Executive Sponsor được xác nhận | C | ĐÃ chốt Sponsor tại G0 (2026-07-10, tên minh họa) | ES | **Closed** |
| I-02 | ARB chưa có người thật (mới có vai) | C | ĐÃ bổ nhiệm ARB/RACI tại G0 (tên minh họa — thay khi triển khai thật) | tổ chức | **Closed** |
| I-03 | Con số NFR chưa ký (đang PROPOSED) | TB | Đưa vào agenda G1 | SA | Open |
| I-04 | Bounded context mới ở mức khởi đầu, chưa Event Storming | TB | Workshop tại M1 | DOM | Open |
| I-05 | Bộ công cụ (repo/CI/CD) chưa chốt chính thức | TB | ĐÃ chốt ADR-T01…T05 (GitHub bootstrap) tại G0 | PLT | **Closed** |

---

## 4. DEPENDENCIES (Phụ thuộc — cần bên ngoài/khác trước khi tiến)

| ID | Phụ thuộc | Cần từ | Chặn việc gì | Status |
|----|-----------|--------|--------------|:------:|
| D-01 | Xác định cấp độ NĐ 85/2016 | Cơ quan quản lý / an ninh | Thiết kế hạ tầng, hosting | Open |
| D-02 | Phê duyệt ngân sách + năng lực đội | Executive Sponsor | Lịch M1+ | Open |
| D-03 | Truy cập môi trường on-prem/air-gap (nếu áp dụng) | Hạ tầng nội bộ | Walking skeleton M3 | Open |
| D-04 | Kết nối trục liên thông (NDXP/LGSP) | Đơn vị quản lý trục quốc gia | Interop federation M4+ | Open |
| D-05 | Bên thứ 3 pentest độc lập | Mua sắm/hợp đồng | Gate G6 | Open |

---

## 5. Quy tắc vận hành RAID

- Mỗi mục có **1 chủ sở hữu** + trạng thái + ngày cập nhật gần nhất.
- Rủi ro Cao (C impact) phải có giảm thiểu *đang chạy* hoặc được `Accepted` tường minh bởi ARB.
- Rà soát hàng tuần; item đóng → chuyển `Closed` (không xóa, giữ lịch sử).
- Rủi ro chạm an ninh → đồng thời phản ánh trong threat model (`docs/architecture/05_...`).
