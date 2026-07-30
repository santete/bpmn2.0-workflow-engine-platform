---
description: Đọc messages chưa đọc trong Agent Mail
---

Hiển thị unread messages cho session hiện tại.

## Execution

Chạy script:
```bash
python .claude/hooks/python/mail-read.py
```

Hiển thị stdout output cho user.

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/agent_mail.yaml`
2. Filter messages chưa đọc:
   - `to: "all"` VÀ "current-session" không trong `read_by`
   - HOẶC `to: "current-session"` (hoặc tên agent hiện tại) VÀ chưa trong `read_by`
3. Hiển thị:

```
## 📬 Unread Messages (<N>)

### msg-x1y2 — from: worker-A (2026-06-11 14:00)
**Subject:** Schema change: users table
**Body:** Added column phone_verified (boolean, default false). Update all queries.
**Task ref:** tsk-a1b2

---

### msg-y3z4 — from: orchestrator (2026-06-11 15:00)
**Subject:** Priority change
**Body:** Task tsk-c3d4 moved to high priority. Claim next.

---

→ Reply: `/mail-send <to> <subject> | <body>`
```

4. Mark messages as read: append "current-session" vào `read_by` cho mỗi message hiển thị
5. Ghi lại file
6. Nếu không có unread: `📬 No unread messages.`

## Lưu ý
- Đọc = mark as read (không cần confirm riêng)
- Messages cũ vẫn xem được qua `/mail-list`
