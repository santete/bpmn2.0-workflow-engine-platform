---
description: Liệt kê tasks sẵn sàng làm (status=open, không bị block)
---

Hiển thị tasks sẵn sàng trong `.claude/memory/task_tracker.yaml`.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-ready.py $ARGUMENTS
```

Nếu cần JSON output cho agent, thêm flag `--json`. Hiển thị stdout output cho user.

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/task_tracker.yaml`
2. Filter tasks thỏa TẤT CẢ điều kiện:
   - `status: open` (chưa ai claim)
   - `blocked_by` rỗng `[]` HOẶC tất cả task trong `blocked_by` đều có `status: closed`
3. Sắp xếp theo thứ tự tạo (`created_at` ascending)
4. Output format:

```
## 📋 Ready Tasks (<N> available)

| # | ID | Title | Blocked by (resolved) |
|---|-----|-------|----------------------|
| 1 | tsk-a1b2 | Add search API | — |
| 2 | tsk-c3d4 | Write search tests | tsk-a1b2 ✅ |

→ Claim: `/task-claim <id>`
```

5. Nếu không có task ready:
```
## 📋 Ready Tasks (0 available)
Không có task nào sẵn sàng. Kiểm tra:
- Tất cả tasks đã closed? → Done! 🎉
- Có task bị blocked? → Chạy `/task-list` để xem dependency
```

## --json flag (cho agent consumption)

Nếu argument chứa `--json`, output structured JSON thay vì table:

```json
{
  "ready_count": 2,
  "tasks": [
    {
      "id": "tsk-a1b2",
      "title": "Add search API",
      "blocked_by_resolved": [],
      "created_at": "2026-06-11T10:00:00Z"
    },
    {
      "id": "tsk-c3d4",
      "title": "Write search tests",
      "blocked_by_resolved": ["tsk-a1b2"],
      "created_at": "2026-06-11T10:05:00Z"
    }
  ]
}
```

Agent dùng JSON output để tự quyết định claim task nào (không cần parse ASCII table).

## Lưu ý
- Command này KHÔNG thay đổi state, chỉ đọc
- Dependency check: task A blocked_by [tsk-x] → check tsk-x.status == closed → nếu closed thì A vẫn ready
