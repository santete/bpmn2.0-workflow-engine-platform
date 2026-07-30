---
description: Thêm note vào task (thư gửi agent tương lai)
---

Ghi note vào task. Argument format: `<task-id> <note content>`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-note.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Parse argument: phần đầu tiên (trước space) = task ID, phần còn lại = note content
2. Đọc `.claude/memory/task_tracker.yaml`
3. Tìm task có `id` = parsed ID
4. Validate: task phải tồn tại
5. Append note:
   ```yaml
   notes:
     - date: "<ISO 8601 now>"
       author: "current-session"
       text: "<note content>"
   ```
6. Update `updated_at`
7. Ghi lại file
8. Output: `📝 Note added to <id>: "<note content trunc 80 chars>"`

## Khi nào nên ghi note
- Quyết định thiết kế không hiển nhiên (why, không chỉ what)
- Thay đổi schema/API ảnh hưởng task khác
- Gotcha phát hiện khi làm task
- Lý do nếu task bị block
- Handoff context cho session tiếp theo

## Lưu ý
- Notes là append-only, KHÔNG xóa note cũ
- Note ngắn gọn nhưng đủ context (1-3 câu)
- Nếu thay đổi ảnh hưởng task khác → kết hợp `/mail-send` để thông báo
