---
description: Liệt kê tất cả messages trong Agent Mail
---

Hiển thị toàn bộ mailbox.

## Execution

Chạy script:
```bash
python .claude/hooks/python/mail-list.py
```

Hiển thị stdout output cho user.

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/agent_mail.yaml`
2. Output tất cả messages, mới nhất trước:

```
## 📬 Agent Mail — <total> messages (<N> unread)

| # | ID | From | To | Subject | Date | Read? |
|---|----|------|----|---------|------|-------|
| 1 | msg-x1y2 | worker-A | all | Schema change: users | 2026-06-11 14:00 | ❌ |
| 2 | msg-y3z4 | orchestrator | all | Priority change | 2026-06-11 15:00 | ✅ |
| 3 | msg-a1b2 | worker-B | worker-A | Need clarification | 2026-06-11 16:00 | ❌ |

→ Read unread: `/mail-read` | Send: `/mail-send <to> <subject> | <body>`
```

3. Nếu mailbox rỗng: `📬 Mailbox rỗng. Dùng /mail-send để gửi message.`

## Lưu ý
- Command này KHÔNG mark messages as read (chỉ `/mail-read` mới mark)
- Hiển thị "Read?" dựa trên "current-session" có trong `read_by` không
