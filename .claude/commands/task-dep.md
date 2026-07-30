---
description: Khai báo dependency giữa tasks (A blocks B)
---

Khai báo dependency. Argument format: `<id-A> blocks <id-B>`.
Nghĩa: task A phải xong trước, task B phải đợi A.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-dep.py $ARGUMENTS
```

Hiển thị stdout output cho user. Nếu exit code = 1, hiển thị stderr (lỗi validation).

## Fallback (nếu script không tồn tại)

1. Parse argument: `<id-A> blocks <id-B>`
2. Đọc `.claude/memory/task_tracker.yaml`
3. Validate:
   - Cả 2 task phải tồn tại
   - Không tạo circular dependency (A blocks B blocks A)
   - Không duplicate (dependency chưa tồn tại)
4. Update task A: append `id-B` vào `blocks` list
5. Update task B: append `id-A` vào `blocked_by` list
6. Nếu task B đang `open` và giờ bị blocked → chuyển `status: blocked`
7. Update `updated_at` cho cả 2 task
8. Ghi lại file
9. Output:
```
🔗 Dependency set: <id-A> (<title-A>) blocks <id-B> (<title-B>)
   <id-B> sẽ ready sau khi <id-A> closed.
```

## Circular dependency check

Trước khi set: trace từ B → blocked_by → ... xem có quay lại A không.
Nếu phát hiện cycle → REJECT:
```
❌ Circular dependency detected: <id-A> → <id-B> → ... → <id-A>
   Không thể set dependency này.
```

## Lưu ý
- Dùng `/task-graph` để visualize dependencies sau khi set
- Khi `/task-close <id-A>` → auto-unblock id-B nếu không còn blocker khác
