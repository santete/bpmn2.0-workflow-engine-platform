---
description: Hiển thị tất cả tasks + status + dependencies
---

Hiển thị toàn bộ task tracker.

## Execution

Chạy script:
```bash
python .claude/hooks/python/task-list.py
```

Hiển thị stdout output cho user.

## Fallback (nếu script không tồn tại)

1. Đọc `.claude/memory/task_tracker.yaml`
2. Group tasks theo status
3. Output format:

```
## 📋 Task Tracker — <total> tasks

### 🔴 In Progress (<N>)
| ID | Title | Assignee | Notes |
|----|-------|----------|-------|
| tsk-a1b2 | Add search API | current-session | 2 notes |

### 🟡 Open (<N>)
| ID | Title | Blocked by | Ready? |
|----|-------|-----------|--------|
| tsk-c3d4 | Write search tests | tsk-a1b2 | ❌ (waiting) |
| tsk-e5f6 | Add pagination | — | ✅ |

### 🔵 Blocked (<N>)
| ID | Title | Blocked by | Reason |
|----|-------|-----------|--------|
| tsk-g7h8 | Deploy | tsk-a1b2, tsk-c3d4 | Waiting for search + tests |

### ✅ Closed (<N>)
| ID | Title | Closed at |
|----|-------|----------|
| tsk-i9j0 | Setup project | 2026-06-11 |

---
Summary: <N> open, <M> in_progress, <K> blocked, <L> closed
→ Next ready: `/task-ready` | Add: `/task-add <title>` | Graph: `/task-graph`
```

## Lưu ý
- Command này KHÔNG thay đổi state, chỉ đọc
- Nếu không có tasks: output "Task tracker rỗng. Dùng `/task-add <title>` để tạo task."
