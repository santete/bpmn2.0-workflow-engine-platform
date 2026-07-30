---
description: Tạo task mới trong task tracker (dùng khi execution_mode = 2b epic)
---

Tạo task mới trong `.claude/memory/task_tracker.yaml`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-add.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/task_tracker.yaml`
2. Sinh ID mới: `tsk-` + 4 ký tự hex ngẫu nhiên (dùng Bash: `python -c "import secrets; print('tsk-' + secrets.token_hex(2))"`)
3. Tạo task entry với argument từ user:
   ```yaml
   - id: "<generated>"
     title: "$ARGUMENTS"
     status: open
     assignee: null
     blocks: []
     blocked_by: []
     notes: []
     created_at: "<ISO 8601 now>"
     updated_at: "<ISO 8601 now>"
   ```
4. Append vào `tasks:` list trong file
5. Output: `✅ Created task <id>: <title>`

## Lưu ý
- Nếu `task_tracker.yaml` chưa có hoặc `tasks: []` → tạo list mới
- KHÔNG tạo duplicate (check title giống nhau)
- Nếu cần tạo nhiều task cùng lúc, user có thể gọi nhiều lần hoặc pass nhiều title cách nhau bằng newline
