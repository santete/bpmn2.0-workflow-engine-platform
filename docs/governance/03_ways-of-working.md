# 03 — Ways of Working (Quy trình ADR · Cadence · Escalation)

> Cách đội vận hành quản trị kiến trúc hàng ngày: vòng đời ADR, nhịp họp, cách escalate xung đột.
> Bổ khuyết phần "quy trình" mà ADR log hiện tại ([`../architecture/adr/ADR-log.md`](../architecture/adr/ADR-log.md))
> chưa mô tả. Trạng thái: `DRAFT` chờ adopt tại G0.

---

## 1. Vòng đời ADR (Architecture Decision Record)

```
  [Proposed] ──ARB review──► [Accepted] ──(quyết định mới thay thế)──► [Superseded by ADR-xxx]
      │                          │
      └──► [Rejected]            └──► [Deprecated] (không còn áp dụng, không có bản thay)
```

| Trạng thái | Ý nghĩa | Ai chuyển |
|-----------|---------|-----------|
| `Proposed` | Đề xuất, chờ duyệt | Tác giả (bất kỳ ai) |
| `Accepted` | Đã duyệt, có hiệu lực | ARB (theo RACI) |
| `Rejected` | Bị từ chối (ghi lý do) | ARB |
| `Superseded by ADR-x` | Bị ADR mới thay | ARB (khi accept ADR mới) |
| `Deprecated` | Hết áp dụng, không thay | ARB |

### 1.1 Quy tắc bất biến
- ADR đã `Accepted` **KHÔNG sửa nội dung** — chỉ tạo ADR mới `Supersedes`. Giữ lịch sử quyết định.
- Mỗi ADR **phải trace về ≥1 REQ** (kiểm tại RTM). ADR không có REQ → Rejected.
- Đánh số tuần tự, không tái sử dụng số. Tooling ADR dùng tiền tố `T` (`ADR-T0x`).
- ADR nhỏ (dưới ngưỡng ARB, Charter §4) → team tự accept, ARB review theo lô mỗi cadence.

### 1.2 Quy trình đề xuất → duyệt
1. Tác giả viết ADR (`Proposed`) theo template trong ADR log, đặt tại `docs/architecture/adr/`.
2. Gắn REQ liên quan + cập nhật RTM (dòng nháp).
3. Đưa vào agenda phiên ARB gần nhất (hoặc ARB khẩn nếu chặn tiến độ).
4. ARB quyết → cập nhật trạng thái + biên bản.
5. `Accepted` → cập nhật RTM chính thức + (nếu cần) fitness function bảo vệ quyết định.

---

## 2. Cadence (nhịp làm việc — khớp ARB Charter §5)

| Nhịp | Tần suất | Đầu ra |
|------|----------|--------|
| ARB định kỳ | 2 tuần | Biên bản + ADR cập nhật + RAID review |
| ARB cổng (Gate) | Theo milestone | Quyết định go/no-go |
| RAID review | Hàng tuần | Cập nhật rủi ro/issue (`05_raid-log.md`) |
| Drift check | Sau mỗi merge lớn / trước gate | Fitness FIT-002/007/009 + so ADR |
| Fitness functions | Mỗi commit (CI) | Xanh/đỏ (gate merge/release) |

---

## 3. Escalation & giải quyết xung đột

Khớp `CLAUDE.md` Hard Stops + ARB Charter. Thang leo:

| Mức | Tình huống | Xử lý tại | Thời hạn |
|-----|-----------|-----------|----------|
| L1 | Bất đồng trong 1 bounded context | Domain Architect | trong ngày |
| L2 | Xung đột liên context / liên quyết định | Lead SA | ≤ 2 ngày |
| L3 | Chạm an ninh/tuân thủ | Security Architect (veto) | ARB gần nhất |
| L4 | Bế tắc quyết định / Hard Stop | ARB (khẩn nếu chặn) | ≤ 1 phiên |
| L5 | Vướng ngân sách/chính trị/tổ chức | Executive Sponsor | theo gate |

**Nguyên tắc:** không "đoán" để đi tiếp khi bế tắc — dừng, escalate đúng mức, ghi quyết định vào ADR/biên bản.

---

## 4. Định nghĩa "quyết định kiến trúc" (khi nào cần ADR)

Cần ADR nếu: chạm ngưỡng ARB (Charter §4) HOẶC quyết định khó đảo ngược HOẶC ảnh hưởng thuộc tính
chất lượng (NFR) HOẶC chọn công nghệ/pattern. Việc thường ngày (đặt tên biến, fix bug) → không cần ADR.

---

## 5. Công cụ & nơi lưu (living docs)

| Hạng mục | Nơi lưu |
|----------|---------|
| ADR | `docs/architecture/adr/` |
| C4 living diagrams | `docs/architecture/03_domain-and-c4-model.md` (Mermaid) |
| RTM | `docs/architecture/rtm/` |
| RAID | `docs/governance/05_raid-log.md` |
| Biên bản ARB | `docs/governance/minutes/` (tạo khi bắt đầu họp) |
| Chuẩn kỹ thuật | `docs/ai/*` (xem `07_engineering-standards.md`) |

> Mọi tài liệu quản trị **nằm trong repo** (docs-as-code) → versioned, review qua MR, không dùng file rời.
