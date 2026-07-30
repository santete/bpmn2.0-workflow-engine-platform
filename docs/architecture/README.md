# Hồ sơ Kiến trúc — Hệ thống Số hóa Toàn trình An ninh Nội địa

> **Architecture Dossier** — bộ hồ sơ kiến trúc thực thi được (executable architecture package).
> Đây là bản *chi tiết hóa* của [Reference Architecture](../../product-spec/Tai-lieu-thiet-ke-kien-truc-An-ninh-noi-dia.md)
> và hiện thực hóa các milestone **M0–M2** của [Master Delivery Plan](../../product-spec/Ke-hoach-tong-the-trien-khai-An-ninh-noi-dia.md).
> Vai trò biên soạn: **Lead Solution Architect**. Trạng thái: `DRAFT v0.1` — chờ ARB duyệt tại Gate G1.

---

## 1. Bộ hồ sơ này thay thế / bổ sung gì

Hai tài liệu product-spec gốc là **reference architecture cấp cao** (high-level, cố ý chưa chốt tech stack).
Bộ hồ sơ này **không thay thế** chúng — nó bổ sung đúng 7 hạng mục mà một SA phải sản xuất để biến
tầm nhìn thành kiến trúc *thi công được và truy vết được*:

| # | Tài liệu | Trả lời câu hỏi | Milestone nguồn | Trạng thái |
|---|----------|-----------------|-----------------|------------|
| 00 | `README.md` (file này) | Đọc thế nào? Quản trị ra sao? | M0 | ✅ |
| 01 | [`01_requirements-catalog.md`](01_requirements-catalog.md) | Mỗi yêu cầu là gì, mã hóa thế nào? | M1 | ✅ |
| 02 | [`02_nfr-quantified.md`](02_nfr-quantified.md) | Ngưỡng *định lượng* để nghiệm thu? | M1 | ✅ (số PROPOSED) |
| 03 | [`03_domain-and-c4-model.md`](03_domain-and-c4-model.md) | Bounded context + sơ đồ C4 L1/L2/L3? | M1 | ✅ |
| 04 | [`04_ph5-workflow-abstraction-layer.md`](04_ph5-workflow-abstraction-layer.md) | **Lõi chiến lược:** interface tháo lắp engine? | M2 | ✅ |
| 05 | [`05_security-and-threat-model.md`](05_security-and-threat-model.md) | Zero Trust + STRIDE threat model? | M1 | ✅ |
| 06 | [`adr/ADR-log.md`](adr/ADR-log.md) | 12 quyết định kiến trúc + lý do? | M1–M2 | ✅ |
| 07 | [`rtm/requirements-traceability-matrix.md`](rtm/requirements-traceability-matrix.md) | Truy vết REQ↔Design↔ADR↔Test? | M1+ | ✅ |

### Đã bổ sung (vòng 2 — hoàn tất bộ M0–M2)
| # | Tài liệu | Trả lời câu hỏi | Milestone nguồn | Trạng thái |
|---|----------|-----------------|-----------------|------------|
| 08 | [`06_data-architecture.md`](06_data-architecture.md) | CQRS/ES, polyglot, phân loại độ mật, retention, sharding? | M1 | ✅ |
| 09 | [`07_availability-scalability-tactics.md`](07_availability-scalability-tactics.md) | HA/DR topology, resilience, autoscale, chaos? | M1 | ✅ |
| 10 | [`08_interoperability-xroad.md`](08_interoperability-xroad.md) | Liên thông kiểu X-Road cho bối cảnh VN (NDXP)? | M1–M2 | ✅ |
| 11 | [`09_devsecops-and-delivery.md`](09_devsecops-and-delivery.md) | CI/CD pipeline, DevSecOps, fitness functions? | M1–M2 | ✅ |

> **Bộ hồ sơ kiến trúc M0–M2 đã ĐẦY ĐỦ** (11 tài liệu). Toàn bộ 5 nền tảng xuyên suốt NT-1..5
> và 8 phân hệ PH-1..8 đều có tài liệu chi tiết hóa + truy vết trong RTM.

### Hạng mục còn lại (tùy chọn, ngoài phạm vi "ra kiến trúc")
- Tách mỗi ADR thành file riêng khi ADR log > 15 mục.
- Trang tổng quan trực quan cho ARB (C4 + RTM + ADR heatmap).

---

## 2. Sơ đồ điều hướng (làm sao ra được kiến trúc)

```
                 product-spec (tầm nhìn, high-level)
                          │
        ┌─────────────────┴──────────────────┐
        ▼                                     ▼
  01 Requirements Catalog   ────────►   02 NFR định lượng
  (REQ-F/S/N/O — atomize)               (số + fitness function)
        │                                     │
        ▼                                     ▼
  03 Domain + C4 model  ──►  04 PH-5 Abstraction  ──►  05 Security + Threat
  (bounded context, container)  (ports/adapters/ACL)     (Zero Trust, STRIDE)
        │                         │                        │
        └────────────┬────────────┴────────────┬───────────┘
                     ▼                          ▼
              06 ADR log (quyết định)    07 RTM (truy vết toàn bộ)
```

**Thứ tự đọc khuyến nghị:** 01 → 02 → 03 → 04 → 05 → ADR → RTM.
Người review nhanh: đọc **RTM trước** để thấy toàn cảnh, rồi drill-down theo REQ-ID.

---

## 3. Hệ thống mã định danh (ID scheme) — nền tảng truy vết

Mọi hạng mục trong bộ hồ sơ dùng ID ổn định; RTM khâu chúng lại với nhau.

| Tiền tố | Loại | Nguồn gốc | Ví dụ |
|---------|------|-----------|-------|
| `REQ-F-###` | Yêu cầu chức năng | G1,G3,G5,G6 + PH-* | `REQ-F-002` engine tháo lắp |
| `REQ-S-###` | Yêu cầu bảo mật | G2 + NT-1 + PH-2/3 | `REQ-S-001` Zero Trust |
| `REQ-N-###` | Yêu cầu phi chức năng (NFR) | G3,G4 + NT-2/3 | `REQ-N-003` độ trễ push |
| `REQ-O-###` | Yêu cầu vận hành/tổ chức | G6 + NT-4 | `REQ-O-005` no rip-and-replace |
| `PH-#` / `NT-#` | Phân hệ / Nền tảng | Reference Architecture §3 | `PH-5` workflow |
| `ADR-###` | Quyết định kiến trúc | Bộ hồ sơ này | `ADR-001` |
| `X#` | Xung đột tính năng đã hóa giải | Reference Architecture §7 | `X6` |
| `FIT-###` | Fitness function (test kiến trúc) | NFR doc | `FIT-003` |
| `TM-###` | Threat (STRIDE) | Threat model | `TM-004` |

> **Nguyên tắc:** không có hạng mục thiết kế nào "mồ côi" — mỗi ADR phải trace về ≥1 REQ;
> mỗi REQ phải xuất hiện trong RTM với ít nhất 1 design element + 1 cách kiểm chứng.

---

## 4. Quản trị hồ sơ (M0 — Documentation Governance)

| Cơ chế | Quy tắc |
|--------|---------|
| **Nguồn chân lý** | Các file `.md` trong `docs/architecture/` là living docs; product-spec là "hiến pháp" bất biến trừ khi ARB sửa. |
| **Thay đổi kiến trúc** | Mọi thay đổi có tác động kiến trúc → 1 ADR mới (không sửa ADR cũ đã `Accepted`, chỉ `Superseded`). |
| **Versioning** | Semantic cho hồ sơ: `v0.x` = draft, `v1.0` = ARB ký tại G1. |
| **Gate** | Hồ sơ này là đầu vào cho **Gate G1** (kiến trúc nền + NFR được ký) và **G2** (tech stack qua PoC). |
| **Vai trò duyệt** | Lead SA (chủ trì) · Security Architect · Data Architect · Platform Lead — theo RACI của M0. |

---

## 5. Ranh giới phạm vi của bộ hồ sơ (rõ ràng để tránh kỳ vọng sai)

**TRONG phạm vi (đã / đang làm):** mô hình miền, C4 L1–L3, đặc tả interface PH-5, NFR định lượng,
threat model, 12 ADR nền tảng, RTM.

**NGOÀI phạm vi (thuộc milestone sau, không thuộc "ra kiến trúc"):** code sản xuất, PoC thực thi (M2),
walking skeleton (M3), IaC thật, pentest (M6). Các con số NFR là **PROPOSED** — chốt bằng chữ ký
stakeholder tại G1 (đây là quy trình đúng, không phải thiếu sót).
