---
description: Tạo discovered task (bug/issue phát sinh trong khi làm task khác)
---

Tạo task phát sinh khi đang làm task khác. Argument format: `<parent-task-id> <title> [priority]`.

Ví dụ: `/task-discovered tsk-a1b2 SQL injection in user search high`

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-discovered.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Parse argument: parent-task-id, title, priority (default: medium)
2. Đọc `.claude/memory/task_tracker.yaml`
3. Validate: parent task phải tồn tại
4. Sinh ID mới: `tsk-` + 4 ký tự hex ngẫu nhiên
5. Tạo task entry:
   ```yaml
   - id: "<generated>"
     title: "$title"
     status: open
     assignee: null
     type: discovered-from        # KHÁC với task thường (không có type field)
     parent_task: "<parent-task-id>"
     priority: "<low|medium|high|critical>"
     blocks: []
     blocked_by: []
     notes:
       - date: "<ISO 8601 now>"
         author: "current-session"
         text: "Discovered during work on <parent-task-id>: <parent title>"
     created_at: "<ISO 8601 now>"
     updated_at: "<ISO 8601 now>"
   ```
6. Append note vào parent task:
   ```yaml
   notes:
     - date: "<ISO 8601 now>"
       author: "current-session"
       text: "⚠️ Discovered issue: <title> → created <new-task-id> (priority: <priority>)"
   ```
7. Ghi lại file
8. Nếu priority = `critical` hoặc `high` → tự động `/mail-send orchestrator Discovered: <title> | <details>`
9. Output:
```
🔍 Discovered task <new-id>: <title>
   Parent: <parent-id> (<parent title>)
   Priority: <priority>
   Type: discovered-from

→ Note added to parent task
→ To assign: `/task-claim <new-id>`
→ To block parent on this: `/task-dep <new-id> blocks <parent-id>`
```

## Khi nào dùng
- Phát hiện bug trong code liên quan khi đang fix bug khác
- Phát hiện security issue khi đang review
- Phát hiện missing test coverage khi đang implement
- Phát hiện technical debt cần address

## Lưu ý
- Discovered task KHÔNG tự động block parent — developer quyết định
- Priority `critical` → tự động gửi mail cho orchestrator
- Audit trail: luôn có link ngược về parent task qua `parent_task` field + note
