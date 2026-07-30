---
description: Gửi message cho agent/session khác (inter-agent communication)
---

Gửi message vào Agent Mail. Argument format: `<to> <subject> | <body>`.
- `<to>`: "all", tên agent cụ thể, hoặc "orchestrator"
- `<subject>`: tiêu đề ngắn
- `|` phân cách subject và body
- `<body>`: nội dung chi tiết

Ví dụ: `/mail-send all Schema change: users table | Added column phone_verified (boolean). Update queries.`

## Execution

Chạy script:
```bash
python .claude/hooks/python/mail-send.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Parse argument: to, subject (trước `|`), body (sau `|`)
2. Đọc `.claude/memory/agent_mail.yaml`
3. Sinh ID: `msg-` + 4 ký tự hex ngẫu nhiên
4. Tạo message entry:
   ```yaml
   - id: "<generated>"
     from: "current-session"
     to: "<to>"
     subject: "<subject>"
     body: "<body>"
     task_ref: "<current task id nếu đang claim>"
     created_at: "<ISO 8601 now>"
     read_by: []
   ```
5. Append vào `mailbox:` list
6. Ghi lại file
7. Output: `📨 Sent to <to>: "<subject>"`

## Khi nào nên gửi mail
- Thay đổi schema/API ảnh hưởng agent/session khác
- Phát hiện bug trong module khác
- Hoàn thành task mà agent khác đang đợi
- Cần quyết định từ orchestrator
