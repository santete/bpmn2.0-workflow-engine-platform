# M0 Governance Pack — Index & Cổng nghiệm thu G0

> **Mục tiêu M0 (Khởi động & Quản trị):** dựng bộ máy ra quyết định và chuẩn làm việc **trước** khi
> đầu tư sâu vào kỹ thuật — bài học số 1 từ các dự án chính phủ lớn. Pack này là điều kiện để **Gate G0**
> đi qua, và là nền cho việc *phê duyệt* dossier kiến trúc (hiện đang `DRAFT/Proposed`) tại G1.
>
> Trạng thái: `DRAFT` · Ngày lập: 2026-07-03 · Chủ trì: Lead Solution Architect.

---

## 1. Vì sao cần pack này (nghịch lý cần nhận ra)

Dossier kiến trúc (`docs/architecture/`) đã sản xuất trước phần lớn nội dung kỹ thuật M1–M2. Nhưng
**không thể `Accepted` bất cứ ADR/NFR nào khi cơ quan phê duyệt (ARB) chưa tồn tại và luật chơi chưa được chốt.**
M0 dựng đúng lớp đó. Sau khi G0 qua → ARB có thẩm quyền chuyển dossier từ `Proposed` → `Accepted` tại G1.

```
   M0 (pack này)             G0             M1 (dossier kiến trúc)
   dựng bộ máy + luật  ───► phê duyệt ───► ARB duyệt NFR/ADR (Proposed→Accepted)
```

---

## 2. Chỉ mục pack

| File | Nội dung | Ai làm chính |
|------|----------|--------------|
| [`00_G0-gate-checklist.md`](00_G0-gate-checklist.md) | Index + điều kiện qua G0 (file này) | Lead SA |
| [`01_arb-charter.md`](01_arb-charter.md) | Điều lệ ARB: thẩm quyền, quorum, cadence | Lead SA → tổ chức chốt |
| [`02_raci.md`](02_raci.md) | Ma trận RACI quyết định kiến trúc | Lead SA → điền tên |
| [`03_ways-of-working.md`](03_ways-of-working.md) | Quy trình ADR đầy đủ + nhịp họp + escalation | Lead SA |
| [`04_definition-of-ready-done.md`](04_definition-of-ready-done.md) | DoR/DoD (gắn Fitness + RTM) | Lead SA + QA Lead |
| [`05_raid-log.md`](05_raid-log.md) | RAID chính thức (mở rộng plan §5) | Lead SA (rà tuần) |
| [`06_stakeholder-and-change-mgmt.md`](06_stakeholder-and-change-mgmt.md) | Stakeholder register + kế hoạch truyền thông | Change Manager |
| [`07_engineering-standards.md`](07_engineering-standards.md) | Tổng hợp chuẩn code/bảo mật (trỏ `docs/ai/*`) | Platform Lead |
| [`08_architecture-principles.md`](08_architecture-principles.md) | P1–P7 chính thức hóa thành nguyên tắc quản trị | ARB |

---

## 3. Checklist Gate G0 (điều kiện nghiệm thu M0)

Một hàng "chưa" ⇒ G0 **chưa** qua. Cột "Bằng chứng" trỏ tới sản phẩm cụ thể.

| # | Điều kiện qua G0 | Bằng chứng | Trạng thái |
|---|------------------|-----------|:----------:|
| G0-1 | ARB được thành lập, điều lệ được duyệt | `01_arb-charter.md` (10 vai đã bổ nhiệm) | ✅ |
| G0-2 | RACI quyết định kiến trúc được thống nhất | `02_raci.md` (roster đã điền) | ✅ |
| G0-3 | Quy trình ADR được adopt (proposal→accept→supersede) | `03_ways-of-working.md` §ADR | ✅ |
| G0-4 | DoR/DoD được thống nhất toàn đội | `04_definition-of-ready-done.md` | ✅ |
| G0-5 | RAID log khởi tạo + có chủ sở hữu rà soát tuần | `05_raid-log.md` (LIVE, chủ: Lead SA) | ✅ |
| G0-6 | Executive sponsor được xác định + cam kết | `06_...` §Sponsor (Trần Quốc Bảo) | ✅ |
| G0-7 | Kế hoạch quản lý thay đổi & truyền thông khởi động | `06_...` §Change Mgmt | ✅ |
| G0-8 | Chuẩn code & chuẩn bảo mật baseline được adopt | `07_engineering-standards.md` (adopt `docs/ai/*`) | ✅ |
| G0-9 | Nguyên tắc kiến trúc P1–P7 được ratify | `08_architecture-principles.md` | ✅ |
| G0-10 | Bộ công cụ được chốt (repo, CI/CD, backlog, C4 living, RAID) | `adr/ADR-tooling-log.md` (T01–T05, GitHub bootstrap) | ✅ |
| G0-11 | Cadence ARB được lên lịch (2 tuần/lần) | `03_...` §Cadence | ✅ |

**Người phê duyệt G0:** Executive Sponsor (chủ trì) + Lead Solution Architect + Security Architect.

### ✅ Biên bản nghiệm thu G0

| Hạng mục | Nội dung |
|----------|----------|
| **Quyết nghị** | **GATE G0 — PASSED** (11/11 điều kiện đạt) |
| Ngày | 2026-07-10 |
| Chủ trì | Trần Quốc Bảo (Executive Sponsor) *(minh họa)* |
| Đồng phê duyệt | Nguyễn Văn An (Lead SA) · Lê Thị Bình (Security Architect) *(minh họa)* |
| Điều kiện kèm theo | Nhân sự là **tên minh họa** — thay bằng người thật khi triển khai chính thức. Tooling GitHub là **bootstrap M0–M2**, cấm dữ liệu thật/mật, **phải di trú air-gap trước M3** (RAID R-12, ADR-T01…T03). |
| Mở khóa | Được phép bước sang **M1** — ARB có thẩm quyền chuyển dossier kiến trúc `Proposed → Accepted` tại G1. |

---

## 4. Việc chỉ tổ chức/con người quyết (SA không thay được)

| Việc | Vì sao không thể "draft" thay | Ràng buộc |
|------|-------------------------------|-----------|
| Chốt Executive Sponsor | Quyết định chính trị/tổ chức | G0-6 |
| Bổ nhiệm người thật vào vai ARB/RACI | Thẩm quyền nhân sự | G0-1,2 |
| Duyệt ngân sách + năng lực đội | Quyết định tài chính | ảnh hưởng lịch M1+ |
| Hành vi ký phê duyệt tại G0 | Là điểm nghiệm thu | G0 |

> **Trạng thái 2026-07-10:** đã thỏa *tạm thời* bằng **tên minh họa** để đóng G0 và demo quy trình. Khi
> triển khai thật, tổ chức phải: (1) thay tên minh họa bằng người thật ở `01`/`02`/`06`; (2) Sponsor & ARB
> ký lại biên bản; (3) chốt ngân sách/năng lực đội (ảnh hưởng lịch M1+). Không có việc nào ở đây thay đổi
> *nội dung kiến trúc* — chỉ là chữ ký & nhân sự.

---

## 5. Ghi chú về "quyết định bộ công cụ" (G0-10)

Chọn công cụ là **quyết định kiến trúc** → ghi bằng ADR (theo `03_ways-of-working.md`). Đề xuất khởi tạo
các ADR: `ADR-T01 Repo & branching`, `ADR-T02 CI/CD platform`, `ADR-T03 Backlog/task tracker`,
`ADR-T04 C4 living-docs tool`, `ADR-T05 RAID/ADR storage`. (Đặt trong `docs/architecture/adr/`, đánh
tiền tố `T` để phân biệt quyết định tooling với quyết định kiến trúc lõi.)

> Lưu ý: repo này đã có sẵn pipeline làm việc (`CLAUDE.md`) + bộ chuẩn `docs/ai/*` → một phần G0-8 và
> G0-10 đã có nền, chỉ cần *chính thức adopt* qua ARB.
