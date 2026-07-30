---
description: Đóng session hiện tại — write memory + viết session snapshot + chuẩn bị mở session mới
---

Khi nào dùng:
- Session > 120k tokens (Loop Logic mandatory)
- Hoàn thành task lớn, muốn natural checkpoint
- Chuyển sang module/feature khác
- Claude bắt đầu repeat / contradict output trước
- Output chất lượng giảm rõ rệt

## Bước 1 — Write session snapshot

Tạo file `.claude/memory/session_<YYYYMMDD>.md` (hoặc append nếu đã có hôm nay):

```markdown
# Session <YYYY-MM-DD>

## Completed
- [x] <task 1 đã xong>
- [x] <task 2 đã xong>

## Decisions made
- <decision 1>: <reason>
- <decision 2>: <reason>

## Gotchas discovered
- <gotcha 1>: <workaround>

## Pending / Next session
- [ ] <task chưa xong / cần làm tiếp>

## Files modified
<list>

## Tokens used
~<số ước lượng>k tokens
```

## Bước 2 — Update project_state.yaml

Append vào các section tương ứng:
- `completed_tasks`: thêm task mới
- `decisions`: thêm decision không hiển nhiên
- `known_gotchas`: thêm gotcha phát hiện được
- `pending_tasks`: cập nhật (xóa cái đã xong, thêm cái mới)
- `last_successful_task`: update
- `session_count`: +1

## Bước 3 — Update schema_snapshot.yaml (nếu có)

Nếu trong session phát hiện:
- External API field mới
- Gotcha về schema (nullable, behavior khác doc)
- DB column/table mới
→ Update `schema_snapshot.yaml` ngay.

## Bước 3.5 — Log metrics event (fail-open)

```python
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path('.claude/hooks/python')))
from metrics_writer import write_event

# Read current tokens from statusline cache
tokens_at_rotate = 0
try:
    cache = json.loads(Path('.claude/cache/last_tokens.json').read_text(encoding='utf-8'))
    tokens_at_rotate = int(cache.get('tokens', 0))
except Exception:
    pass

write_event('rotate', {
    'tokens_at_rotate': tokens_at_rotate,
    'session_summary_path': '.claude/memory/session_<YYYYMMDD>.md',
})
```

## Bước 4 — Báo user

Output cho user theo format:

```
🔄 SESSION ROTATED

📝 Snapshot saved: .claude/memory/session_<YYYYMMDD>.md
🧠 State updated:  .claude/memory/project_state.yaml
📊 Schema updated: <yes/no>

Để tiếp tục, mở session mới với prompt:
  "Đọc .claude/memory/project_state.yaml và session_<YYYYMMDD>.md,
   sau đó tiếp tục từ pending tasks."
```

## KHÔNG làm khi rotate

- ❌ Copy-paste conversation history vào session mới (dùng snapshot thay thế)
- ❌ Paste toàn bộ code đã viết vào session mới (đọc từ actual files)
- ❌ Mô tả lại từng bước đã làm (summary 10-20 dòng là đủ)
- ❌ Bỏ qua step 2 (update project_state) — sẽ mất context cross-session
