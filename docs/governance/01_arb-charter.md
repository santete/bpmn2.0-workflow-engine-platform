# 01 — Điều lệ Architecture Review Board (ARB Charter)

> **Mục đích:** thiết lập cơ quan có thẩm quyền phê duyệt quyết định kiến trúc & cổng milestone, đảm bảo
> nhất quán với 7 nguyên tắc nền ([`08_architecture-principles.md`](08_architecture-principles.md)) và
> khử rủi ro kiến trúc sớm. Trạng thái: `DRAFT` chờ duyệt tại G0.

---

## 1. Sứ mệnh & phạm vi

ARB là cơ quan quản trị kiến trúc **duy nhất** có quyền:
- Duyệt/từ chối **ADR** có tác động kiến trúc (xem ngưỡng §4).
- Phê duyệt **cổng milestone** (G0–G8).
- Chuyển trạng thái tài liệu kiến trúc `Proposed → Accepted / Rejected / Superseded`.
- Giải quyết **conflict** giữa các quyết định/đội (xem escalation `03_ways-of-working.md`).
- Kiểm soát **drift** kiến trúc (thực tế lệch ADR) và nợ kỹ thuật (ngưỡng fitness).

**Ngoài phạm vi ARB:** quyết định nghiệp vụ chi tiết (thuộc Product/Business Owner), quyết định nhân sự,
quyết định ngân sách (thuộc Executive Sponsor).

---

## 2. Thành phần

> ⚠️ **Tên dưới đây là MINH HỌA (placeholder)** — chốt bằng tên minh họa tại G0 ngày 2026-07-10 để hồ sơ
> hoàn chỉnh và demo quy trình. **Thay bằng người thật khi triển khai chính thức** (cập nhật cả `02_raci.md`).

| Vai trò | Bắt buộc? | Trách nhiệm trong ARB | Người *(minh họa)* |
|---------|:---------:|-----------------------|---------------------|
| **Lead Solution Architect** (Chair) | ✅ | Chủ trì, ra quyết định cuối khi bế tắc | Nguyễn Văn An |
| **Security Architect** | ✅ | Veto về an ninh/tuân thủ (quyền phủ quyết security) | Lê Thị Bình |
| **Data Architect** | ✅ | Quyết định dữ liệu/CQRS/phân loại độ mật | Phạm Minh Cường |
| **Platform / DevSecOps Lead** | ✅ | Nền tảng, pipeline, IaC, fitness functions | Hoàng Đức Dũng |
| Domain / Application Architect(s) | ○ | Đại diện bounded context liên quan | Vũ Thị Hà |
| Product / Business Owner | ○ | Ràng buộc nghiệp vụ, ưu tiên | Đỗ Văn Em |
| QA / Test Lead | ○ | DoD, fitness gates, chất lượng | Bùi Thị Giang |
| SRE / Ops | ○ | Vận hành, HA/DR khả thi | Đặng Văn Hải |
| Change Manager | ○ | Tác động tổ chức/con người | Ngô Thị Lan |
| Executive Sponsor | mời khi cần | Phê duyệt gate lớn, gỡ vướng chính trị/ngân sách | Trần Quốc Bảo |

> ✅ = thành viên nòng cốt (tính quorum) · ○ = mời theo chủ đề.

---

## 3. Quorum & cơ chế quyết định

| Hạng mục | Quy tắc |
|----------|---------|
| **Quorum** | ≥ 3/4 thành viên nòng cốt, **bắt buộc có Chair + Security Architect** |
| **Cách quyết** | Đồng thuận (consensus) ưu tiên; không đạt → Chair quyết, ghi lý do vào ADR |
| **Quyền phủ quyết (veto)** | Security Architect có veto về an ninh/tuân thủ; Data Architect có veto về toàn vẹn/độ mật dữ liệu |
| **Bỏ phiếu** | Chỉ khi consensus thất bại: đa số thành viên nòng cốt; hòa → Chair quyết |
| **Xung đột lợi ích** | Thành viên liên quan trực tiếp không bỏ phiếu về hạng mục đó |

---

## 4. Ngưỡng đưa ra ARB (khi nào một quyết định cần ARB duyệt)

Một quyết định **PHẢI** qua ARB nếu chạm ≥1 tiêu chí (khớp Hard Stops trong `CLAUDE.md`):

- Ảnh hưởng ≥2 bounded context hoặc thay đổi ranh giới context.
- Chạm **PH-5** (workflow abstraction) — lõi chiến lược tháo lắp.
- Thay đổi **hợp đồng an ninh/tuân thủ** (Zero Trust, IAM, độ mật, NĐ 85/2016).
- Thay đổi **NFR** đã ký (availability, latency, RPO/RTO).
- Chọn/đổi **công nghệ chiến lược** (engine, event backbone, datastore, IAM, interop).
- Thay đổi **public API contract** (breaking) hoặc schema dữ liệu.
- Vượt **ngưỡng nợ kỹ thuật** trong fitness functions.

Quyết định *dưới ngưỡng* → team tự quyết, ghi ADR nhẹ, ARB review theo lô (batch) mỗi cadence.

---

## 5. Nhịp họp (Cadence)

| Loại phiên | Tần suất | Nội dung |
|-----------|----------|----------|
| **ARB định kỳ** | 2 tuần/lần | Duyệt ADR tồn, review RAID, drift check |
| **ARB cổng (Gate)** | Theo milestone | Nghiệm thu G0…G8 (quyết định go/no-go) |
| **ARB khẩn** | Ad-hoc | Hard Stop / incident kiến trúc / conflict chặn tiến độ |

Đầu ra mỗi phiên: **biên bản (minutes)** + trạng thái ADR cập nhật + RAID cập nhật. Lưu cùng repo.

---

## 6. Trách nhiệm giải trình

- ARB báo cáo lên **Executive Sponsor** theo mỗi gate.
- Mọi quyết định ARB **truy vết được** qua ADR (`docs/architecture/adr/`) + biên bản.
- ARB **không** tự sửa ADR đã `Accepted` — chỉ tạo ADR mới `Supersedes`.

---

## 7. Tiêu chí giải thể / tiến hóa

ARB duy trì suốt vòng đời hệ thống (tới M8 cải tiến liên tục). Khi project phát triển quy mô
(re-classification theo `CLAUDE.md` Pattern A/B/C), thành phần ARB được rà soát lại tại gate tương ứng.
