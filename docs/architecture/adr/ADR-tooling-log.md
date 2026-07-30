# ADR Tooling Log (T-series) — Quyết định bộ công cụ

> Quyết định về công cụ/nền tảng, tách khỏi ADR kiến trúc lõi bằng tiền tố `T`. Chốt tại **Gate G0** (G0-10).
> Trạng thái template & quy tắc: xem [`ADR-log.md`](ADR-log.md) và [`../../governance/03_ways-of-working.md`](../../governance/03_ways-of-working.md).
> Ngày: 2026-07-10.

> ⚠️ **Bối cảnh chung của T-series:** đây là **quyết định BOOTSTRAP có thời hạn** cho giai đoạn M0–M2
> (thiết kế, PoC, walking skeleton demo trên cloud). **KHÔNG** dùng cho dữ liệu thật/mật. Trước **M3** (khi
> chạm dữ liệu thực) hoặc khi chốt cấp độ NĐ 85/2016 (A-02, D-01), toàn bộ T-series phải được **rà soát &
> có thể Superseded** bằng nền self-managed/air-gap. Rủi ro theo dõi: RAID **R-12**.

---

## ADR-T01 — Repository & branching trên GitHub (cá nhân, bootstrap)
- **Status:** Accepted (BOOTSTRAP, time-boxed M0–M2) · **Trace:** REQ-O-003, G0-10 · RAID R-12
- **Context:** Cần nơi lưu code + docs-as-code ngay để khởi động; chưa có hạ tầng on-prem/air-gap.
- **Decision:** Dùng **GitHub (tài khoản cá nhân)** làm repo cho giai đoạn khởi động. Branching: trunk-based
  + short-lived feature branch + PR review (khớp `docs/ai/GIT_CONVENTION.md`).
- **Consequences:** (+) khởi động tức thì, quen thuộc, docs-as-code. (−) **không tuân thủ** dữ liệu-trong-biên-giới
  → cấm đưa dữ liệu thật/mật; phải di trú trước M3.
- **Alternatives rejected:** GitLab self-managed air-gap — *đúng cho production* nhưng chưa dựng kịp cho khởi động
  → sẽ là ứng viên **superseder** (ADR-T01b) ở M2–M3.

## ADR-T02 — CI/CD bằng GitHub Actions (bootstrap)
- **Status:** Accepted (BOOTSTRAP) · **Trace:** REQ-O-001,002 · G0-10
- **Context:** Cần pipeline chạy fitness functions + quét bảo mật sớm (`09_devsecops`).
- **Decision:** **GitHub Actions** cho CI/CD giai đoạn đầu: build, test, arch-fitness (FIT-007/009), SAST/SCA/secret-scan.
- **Consequences:** (+) tích hợp sẵn với repo, cấu hình nhanh. (−) runner cloud → không air-gap; di trú cùng T01.
- **Alternatives rejected:** Jenkins/GitLab CI self-hosted — hoãn tới khi có hạ tầng on-prem.

## ADR-T03 — Backlog / Task tracking bằng GitHub Issues + Projects (bootstrap)
- **Status:** Accepted (BOOTSTRAP) · **Trace:** REQ-O-005 · G0-10
- **Context:** Cần quản lý epic/task theo domain (M4) + liên kết PR.
- **Decision:** **GitHub Issues + Projects**; tương thích cơ chế task-tracker của `CLAUDE.md` (YAML fallback nếu offline).
- **Consequences:** (+) một chỗ với code & PR. (−) khóa nhẹ vào GitHub; xuất được khi di trú.

## ADR-T04 — C4 living diagrams bằng Mermaid trong repo
- **Status:** Accepted · **Trace:** Master Plan §4 (C4 living docs) · G0-10
- **Context:** Sơ đồ kiến trúc phải "sống" cùng code, versioned, diff được.
- **Decision:** **Mermaid** nhúng trong Markdown (`docs/architecture/03_...`); bản render SVG cho trình bày ARB.
- **Consequences:** (+) không phụ thuộc công cụ ngoài, GitHub render sẵn. (−) sơ đồ phức tạp cần render SVG thủ công.
- **Ghi chú:** quyết định này **không** mang tính bootstrap — giữ nguyên khi di trú (Mermaid độc lập nền tảng).

## ADR-T05 — RAID & ADR lưu docs-as-code trong repo
- **Status:** Accepted · **Trace:** Master Plan §4 · G0-10
- **Context:** Tài liệu quản trị phải versioned, review qua PR, không dùng file rời/wiki ngoài.
- **Decision:** RAID (`governance/05_raid-log.md`), ADR (`architecture/adr/`), biên bản ARB (`governance/minutes/`)
  đều là Markdown trong repo.
- **Consequences:** (+) truy vết + lịch sử qua git. (−) cần kỷ luật cập nhật (gắn vào DoD D5).
- **Ghi chú:** giữ nguyên khi di trú (chỉ đổi nơi host repo, không đổi cấu trúc).

---

### Điều kiện di trú (supersession trigger — bắt buộc)
Trước khi M3 walking skeleton chạm **bất kỳ dữ liệu thật/mật nào**, HOẶC ngay khi chốt cấp độ NĐ 85/2016:
- Tạo **ADR-T01b…T03b** chọn nền self-managed/air-gap (ứng viên: GitLab self-managed) → `Supersedes` T01–T03.
- Cập nhật RAID R-12 → `Closed`. ARB phê duyệt bắt buộc (Hard Stop: thao tác production/dữ liệu mật).
