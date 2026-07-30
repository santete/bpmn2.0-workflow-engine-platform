---
description: Đóng task (status → closed, auto-unblock dependents)
---

Đóng task đã hoàn thành. Argument: `<task-id>`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-close.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/task_tracker.yaml`
2. Tìm task có `id` = argument
3. Validate:
   - Task phải tồn tại
   - Task nên ở `status: in_progress` (warning nếu close từ `open` — có thể quên claim)
4. Update task:
   ```yaml
   status: closed
   updated_at: "<ISO 8601 now>"
   ```
5. **Auto-unblock dependents**: scan tất cả tasks khác, nếu task nào có `blocked_by` chứa ID vừa close:
   - Kiểm tra: tất cả items trong `blocked_by` của task đó đều đã `closed`?
   - Nếu đúng VÀ task đang `blocked` → chuyển `status: open` (auto-unblock)
   - Output danh sách tasks vừa unblock
6. Ghi lại file
7. Output:
```
✅ Closed task $ARGUMENTS: <title>

🔓 Auto-unblocked:
- tsk-c3d4: "Write search tests" (was blocked by $ARGUMENTS)

📋 Remaining: <N> open, <M> in_progress, <K> blocked
→ Next: `/task-ready`
```

## Lưu ý
- Close TRƯỚC khi ghi note cuối → note nằm trong task đã closed, vẫn đọc được
- Hoặc ghi note TRƯỚC rồi close — cả 2 đều OK
- Task closed không thể reopen trực tiếp — tạo task mới nếu cần revisit
