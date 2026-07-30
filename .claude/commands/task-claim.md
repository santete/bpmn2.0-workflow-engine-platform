---
description: Claim task (chuyển status → in_progress, set assignee)
---

Claim task để bắt đầu làm. Argument: `<task-id>`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-claim.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/task_tracker.yaml`
2. Tìm task có `id` = argument
3. Validate:
   - Task phải tồn tại → nếu không: `❌ Task <id> không tìm thấy`
   - Task phải `status: open` → nếu đang `in_progress`: `❌ Task <id> đã được claim bởi <assignee>`
   - Task phải không bị blocked → nếu bị: `❌ Task <id> đang bị blocked bởi: <list>`
4. Update task:
   ```yaml
   status: in_progress
   assignee: "current-session"    # hoặc tên agent/dev nếu biết
   updated_at: "<ISO 8601 now>"
   ```
5. Ghi lại file
6. Output:
```
✅ Claimed task $ARGUMENTS
   Title: <title>
   Status: open → in_progress

→ Khi xong: `/task-note $ARGUMENTS <ghi chú>` rồi `/task-close $ARGUMENTS`
```

## Lưu ý
- Chỉ 1 agent/session claim 1 task tại 1 thời điểm (convention, không hard enforce)
- Nếu cần bỏ claim: đổi status về `open`, xóa assignee
