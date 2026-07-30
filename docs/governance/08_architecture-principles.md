# 08 — Architecture Principles (Ratified)

> 7 nguyên tắc nền từ Reference Architecture §2 được **nâng thành nguyên tắc quản trị chính thức**: mỗi
> nguyên tắc có lý do, hàm ý thiết kế, và **cơ chế thực thi** (ADR/Fitness) để không chỉ là khẩu hiệu.
> Mọi ADR & quyết định thiết kế phải nhất quán với các nguyên tắc này. Trạng thái: `DRAFT` chờ ARB ratify (G0-9).

**Trạng thái mỗi nguyên tắc:** `Ratified` sau khi ARB duyệt tại G0.

---

## P1 — Phân tầng + Hướng sự kiện
- **Tuyên bố:** Giao tiếp giữa các phân hệ ưu tiên bất đồng bộ qua event bus thay vì gọi trực tiếp.
- **Lý do:** Tách rời (decoupling) để chịu tải, chống lỗi dây chuyền.
- **Hàm ý:** Message broker là "bể giảm chấn"; call đồng bộ chỉ cho query độ trễ thấp.
- **Thực thi:** ADR-003 · `FIT-007` (coupling) · phục vụ G3,G4,G6.
- **Đánh đổi đã chấp nhận:** eventual consistency (giải tại P-liên-quan X2/ADR-004).

## P2 — Domain-Driven Design
- **Tuyên bố:** Mỗi nghiệp vụ là một bounded context độc lập; khởi đầu modular monolith, tách microservice theo điểm nghẽn.
- **Lý do:** Capability & Scalability có kỷ luật; tránh over-engineering sớm.
- **Hàm ý:** Ranh giới context vẽ từ đầu; DB-per-service; tách theo bằng chứng.
- **Thực thi:** ADR-002, ADR-010 · `FIT-007` · Event Storming M1.

## P3 — Dữ liệu phân tán, không kho chung
- **Tuyên bố:** Dữ liệu do đơn vị chủ quản nắm giữ; trao đổi qua tầng interoperability chuẩn hóa.
- **Lý do:** Tránh SPOF tầng dữ liệu; giữ chủ quyền đơn vị.
- **Hàm ý:** Mô hình X-Road; tổng hợp toàn cục qua event → read model (không kho trung tâm).
- **Thực thi:** ADR-009, ADR-004 (giải X3) · phục vụ G5,G4.

## P4 — Tháo lắp được (Pluggable)
- **Tuyên bố:** Thành phần chiến lược (đặc biệt workflow engine) nằm sau tầng trừu tượng + adapter, chuẩn mở.
- **Lý do:** Tránh khóa cứng nhà cung cấp; khả chuyển.
- **Hàm ý:** Ports & adapters + ACL; 3 điều kiện C1/C2/C3 (`04_ph5`).
- **Thực thi:** ADR-001, ADR-011 · `FIT-007`, `FIT-010` (engine-swap) · phục vụ G1,G6.
- **Ghi chú:** đây là **nguyên tắc gắn với rủi ro cốt lõi R-01** — vi phạm = Hard Stop kiến trúc.

## P5 — Security-by-design / Zero Trust
- **Tuyên bố:** Không tin tưởng mặc định bất kỳ request nào; xác thực & phân quyền lại ở mọi tầng; nhiều lớp phòng thủ.
- **Lý do:** Hệ thống an ninh quốc gia — security là yêu cầu hàng đầu.
- **Hàm ý:** Verify token 1 lần tại gateway + authZ theo ngữ cảnh (giải X1); defense-in-depth 6 lớp.
- **Thực thi:** ADR-007, ADR-008 · threat model TM-001…012 · phục vụ G2.
- **Quyền:** Security Architect có veto (ARB Charter §3).

## P6 — Chủ quyền số (Digital Sovereignty)
- **Tuyên bố:** Ưu tiên chuẩn mở & OSS kiểm soát được; tránh khóa cứng; dữ liệu không ra khỏi biên giới.
- **Lý do:** Tự chủ công nghệ/dữ liệu/hạ tầng cho hệ mật.
- **Hàm ý:** Air-gap registry; đánh giá lock-in định kỳ; engine-swap drill làm bằng chứng.
- **Thực thi:** ADR-011 · REQ-O-006, REQ-S-011 · phục vụ G2,G5,G6.

## P7 — Hiện đại hóa tăng dần
- **Tuyên bố:** Không "đập đi xây lại"; xây từng phần, rút kinh nghiệm, mở rộng; không gián đoạn dịch vụ.
- **Lý do:** Giảm rủi ro vận hành & chính trị của big-bang.
- **Hàm ý:** Walking skeleton trước; giao hàng gia tăng theo domain; blue-green/canary.
- **Thực thi:** ADR-002 · REQ-O-005 · RAID R-05 · phục vụ G4,G6.

---

## Bảng thực thi tổng hợp (principle → cơ chế)

| Nguyên tắc | ADR chính | Fitness bảo vệ | Rủi ro RAID liên quan |
|-----------|-----------|----------------|-----------------------|
| P1 | ADR-003 | FIT-007 | R-11 |
| P2 | ADR-002, 010 | FIT-007 | R-02 |
| P3 | ADR-009, 004 | — | R-10 |
| **P4** | **ADR-001, 011** | **FIT-007, 010** | **R-01** |
| P5 | ADR-007, 008 | — (pentest M6) | R-08 |
| P6 | ADR-011 | FIT-010 | R-01 |
| P7 | ADR-002 | — | R-05 |

---

## Quy tắc áp dụng
- Xung đột giữa 2 nguyên tắc → đưa ARB; ghi cách hóa giải vào ADR (như 9 xung đột X1–X9 đã làm).
- Nguyên tắc **không phải luật cứng tuyệt đối** nhưng lệch phải có ADR biện minh + ARB duyệt.
- Rà soát nguyên tắc mỗi lần re-classification hoặc khi bối cảnh pháp lý/công nghệ đổi.
