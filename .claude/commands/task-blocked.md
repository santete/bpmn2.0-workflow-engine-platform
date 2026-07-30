---
description: Đánh dấu task bị blocked (status → blocked, ghi lý do)
---

Đánh dấu task bị blocked. Argument format: `<task-id> <reason>`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-blocked.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Parse argument: phần đầu tiên = task ID, phần còn lại = reason
2. Đọc `.claude/memory/task_tracker.yaml`
3. Tìm task có `id` = parsed ID
4. Validate: task phải tồn tại, status nên là `open` hoặc `in_progress`
5. Update task:
   ```yaml
   status: blocked
   updated_at: "<ISO 8601 now>"
   ```
6. Append note giải thích block reason:
   ```yaml
   notes:
     - date: "<ISO 8601 now>"
       author: "current-session"
       text: "BLOCKED: <reason>"
   ```
7. Ghi lại file
8. Output:
```
🚫 Blocked task <id>: <title>
   Reason: <reason>

→ Để unblock: resolve blocker rồi `/task-claim <id>` (sẽ chuyển về in_progress)
→ Hoặc: set dependency `/task-dep <blocker-id> blocks <id>`
```

## Lưu ý
- Task blocked sẽ KHÔNG xuất hiện trong `/task-ready`
- Khi blocker resolved: manually set status về `open` hoặc dùng `/task-claim` để claim lại
- Nếu block do dependency → dùng `/task-dep` thay vì `/task-blocked`
