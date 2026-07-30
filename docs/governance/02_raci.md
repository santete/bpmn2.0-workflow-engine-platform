# 02 — RACI cho Quyết định Kiến trúc

> **RACI:** R=Responsible (làm) · A=Accountable (chịu trách nhiệm cuối, **duy nhất 1 người/hàng**) ·
> C=Consulted (hỏi ý kiến trước) · I=Informed (thông báo sau). Bảng này gỡ mơ hồ "ai quyết cái gì".
> Trạng thái: `DRAFT` — điền tên người tại G0.

**Vai (viết tắt cột):** SA=Lead Solution Architect · SEC=Security Architect · DA=Data Architect ·
PLT=Platform/DevSecOps Lead · DOM=Domain Architect · PO=Product/Business Owner · QA=QA/Test Lead ·
OPS=SRE/Ops · CM=Change Manager · ES=Executive Sponsor.

### Roster (chốt tại G0 · 2026-07-10 · *tên minh họa — thay khi triển khai thật*)

| Mã | Vai trò | Người | Mã | Vai trò | Người |
|----|---------|-------|----|---------|-------|
| SA | Lead Solution Architect | Nguyễn Văn An | PO | Product/Business Owner | Đỗ Văn Em |
| SEC | Security Architect | Lê Thị Bình | QA | QA/Test Lead | Bùi Thị Giang |
| DA | Data Architect | Phạm Minh Cường | OPS | SRE/Ops | Đặng Văn Hải |
| PLT | Platform/DevSecOps Lead | Hoàng Đức Dũng | CM | Change Manager | Ngô Thị Lan |
| DOM | Domain Architect | Vũ Thị Hà | ES | Executive Sponsor | Trần Quốc Bảo |

---

## 1. Quyết định kiến trúc & công nghệ

| Quyết định | SA | SEC | DA | PLT | DOM | PO | QA | OPS | CM | ES |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Nguyên tắc kiến trúc (P1–P7) | A | C | C | C | C | I | I | I | I | I |
| Ranh giới bounded context | A | I | C | I | R | C | I | I | I | I |
| Chọn/đổi workflow engine (ADR-011) | A | C | C | C | C | C | I | I | I | I |
| Chọn event backbone / datastore | A | C | R | C | C | I | I | C | I | I |
| Hợp đồng API / schema (breaking) | A | C | R | C | R | C | C | I | I | I |
| Chọn công cụ (repo/CI/CD/backlog) | C | C | I | A | I | I | I | C | I | I |
| Tách microservice khỏi monolith | A | I | C | C | R | I | I | C | I | I |

## 2. An ninh, tuân thủ & dữ liệu

| Quyết định | SA | SEC | DA | PLT | DOM | PO | QA | OPS | CM | ES |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Mô hình Zero Trust / IAM | C | A | C | R | I | I | I | C | I | I |
| Phân loại độ mật dữ liệu | C | C | A | I | C | C | I | I | I | I |
| Cấp độ NĐ 85/2016 (4/5) | C | A | C | I | I | C | I | I | I | R |
| Threat model & xử lý rủi ro Cao | C | A | C | C | C | I | C | C | I | I |
| Chính sách retention / audit | C | C | A | I | C | C | I | I | I | I |
| Break-glass / bốn mắt / SoD | C | A | I | C | C | C | I | C | I | I |

## 3. NFR, chất lượng & vận hành

| Quyết định | SA | SEC | DA | PLT | DOM | PO | QA | OPS | CM | ES |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Chốt NFR định lượng (ký tại G1) | A | C | C | C | C | C | C | C | I | R |
| Định nghĩa Fitness Functions | C | C | C | A | I | I | R | C | I | I |
| DoR / DoD | C | I | I | C | C | C | A | I | I | I |
| Chiến lược HA/DR (RPO/RTO) | C | C | C | R | I | I | I | A | I | I |
| Kế hoạch chaos / DR drill | C | I | I | R | I | I | C | A | I | I |

## 4. Quản trị, gate & con người

| Quyết định | SA | SEC | DA | PLT | DOM | PO | QA | OPS | CM | ES |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Phê duyệt Gate G0 | R | C | I | I | I | I | I | I | C | A |
| Phê duyệt Gate G1 (kiến trúc+NFR) | R | C | C | C | C | C | C | I | I | A |
| Phê duyệt Gate G2 (tech qua PoC) | A | C | C | C | C | C | C | C | I | C |
| Phê duyệt Gate G6 (an ninh) | C | A | I | C | I | I | C | C | I | R |
| Kế hoạch change mgmt & truyền thông | I | I | I | I | I | C | I | I | A | R |
| Bổ nhiệm thành viên ARB | C | I | I | I | I | I | I | I | I | A |

---

## 5. Quy tắc dùng RACI

- Mỗi hàng **đúng 1 chữ A** (không được 0 hoặc >1) — nếu vi phạm là dấu hiệu quyền quyết mơ hồ.
- **A ký, R làm, C hỏi trước, I báo sau.** C ≠ quyền phủ quyết (trừ veto của SEC/DA ghi ở ARB Charter §3).
- Quyết định chạm ngưỡng ARB (Charter §4) → A vẫn là người trong bảng, nhưng **phải qua phiên ARB**.
- RACI rà soát lại mỗi lần re-classification hoặc khi cơ cấu đội đổi.
