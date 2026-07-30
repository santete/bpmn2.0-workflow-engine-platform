---
description: Kết thúc task — auto-writeback memory + re-baseline drift + log metrics
---

Khi user gõ `/done`, thực hiện 6 bước sau. KHÔNG skip bước nào.

## Bước 1 — Gather changes

Chạy lệnh để biết đã sửa gì trong session:

```bash
git diff --name-only HEAD 2>/dev/null || echo "(not a git repo)"
```

Liệt kê files modified. Nếu không có thay đổi nào → vẫn tiếp tục (có thể chỉ cần ghi decision/gotcha).

## Bước 2 — Append completed task

Hỏi user 1 câu DUY NHẤT:

> "Tóm tắt task vừa hoàn thành (1 dòng):"

Sau đó gọi `memory_writer.append_change()`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.claude/hooks/python')))
from memory_writer import append_change
append_change(task="<user summary>", files_modified=[<list from step 1>])
```

## Bước 3 — Append decisions (nếu có)

Tự review: trong session này có decision nào **không hiển nhiên từ code** không?

Ví dụ:
- Chọn Postgres thay vì Redis vì X
- Dùng polling thay vì WebSocket vì Y
- Skip validation ở endpoint Z vì đã validate upstream

Nếu CÓ → gọi `memory_writer.append_decision(decision, reason, impact)` cho mỗi cái.

Nếu KHÔNG → skip, in `📝 No non-obvious decisions to record`.

## Bước 4 — Append gotchas (nếu có)

Tự review: phát hiện hành vi bất ngờ nào không?

Ví dụ:
- API trả `null` thay vì `[]` khi empty
- Column `amount` tính theo cents không phải dollars
- Rate limit 100 req/min thay vì 1000 như doc nói

Nếu CÓ → gọi `memory_writer.append_gotcha(discovery, workaround, files_affected)`.

Nếu KHÔNG → skip, in `📝 No gotchas discovered`.

## Bước 5 — Re-baseline drift

Stamp HEAD hiện tại vào `_sync_state.yaml` để sessions sau không thấy stale drift warning:

```bash
python .claude/hooks/python/drift_check.py --baseline --source done
```

Nếu `_sync_state.yaml` không tồn tại → skip, in `⚠️ _sync_state.yaml not found — run /classify to initialize`.

## Bước 6 — Log metrics + Report

Log event (fail-open):

```python
from metrics_writer import write_event
write_event('task_done', {
    'task': '<summary>',
    'files_count': <len(files)>,
    'decisions_added': <count>,
    'gotchas_added': <count>,
    'drift_rebaselined': True/False,
})
```

Output cho user (format BẮT BUỘC):

```
✅ TASK DONE

📝 Task:       <summary>
📁 Files:      <list hoặc count>
🧠 Decisions:  <N> recorded
⚠️  Gotchas:    <N> recorded
🔄 Drift:      re-baselined at <commit[:8]>
📊 State:      .claude/memory/project_state.yaml updated

💡 Next: start new task, or /rotate if session > 120k tokens.
```

## KHÔNG làm khi /done

- ❌ Skip Bước 5 (drift re-baseline) — sessions sau sẽ thấy false drift
- ❌ Ghi decision hiển nhiên (e.g., "dùng TypeScript") — chỉ ghi cái KHÔNG đoán được từ code
- ❌ Đổi `pattern` trong project_state — chỉ `/classify` mới đổi
- ❌ Update `schema_snapshot.yaml` — dùng Phase 5 hoặc `/rotate` cho việc đó
- ❌ Tự đoán summary — PHẢI hỏi user (Bước 2)

## Khi nào dùng /done vs /rotate vs /snapshot

| Trường hợp | Dùng |
|---|---|
| Hoàn thành 1 task, session vẫn còn context | `/done` |
| Session > 120k tokens, cần đóng | `/rotate` (mandatory) |
| Muốn save progress giữa chừng, chưa xong task | `/snapshot` |
| Hoàn thành task + session cũng cần đóng | `/done` rồi `/rotate` |
