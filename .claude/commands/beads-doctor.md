---
description: Validate Beads/task tracker health — schema, dependencies, hooks, consistency
---

Chạy health check cho task tracker + Beads integration.

## Execution

Chạy script:
```bash
python .claude/hooks/python/beads-doctor.py
```

Hiển thị stdout output cho user. Exit code 0 = healthy, 1 = có blockers.

## Fallback (nếu script không tồn tại)

## Bước 1 — Check task tracker schema

Đọc `.claude/memory/task_tracker.yaml`, validate:
- [ ] File tồn tại và parse được (valid YAML)
- [ ] Mỗi task có đủ required fields: `id`, `title`, `status`, `blocks`, `blocked_by`, `notes`, `created_at`, `updated_at`
- [ ] Status chỉ chứa giá trị hợp lệ: `open`, `in_progress`, `blocked`, `closed`
- [ ] Tất cả ID unique (không trùng)

## Bước 2 — Check circular dependencies

Trace dependency graph:
- Build DAG từ `blocks`/`blocked_by`
- Detect cycles: nếu tìm thấy A→B→...→A → report BLOCKER
- Detect orphaned references: task A `blocked_by: [tsk-xxxx]` nhưng tsk-xxxx không tồn tại

## Bước 3 — Check consistency

- [ ] `blocks` và `blocked_by` đối xứng: nếu A.blocks chứa B, thì B.blocked_by phải chứa A
- [ ] Task `blocked` nhưng `blocked_by` rỗng → inconsistent (nên là `open`)
- [ ] Task `open` nhưng có `blocked_by` chưa `closed` → nên là `blocked`
- [ ] Không có task in_progress > 1 cùng lúc (convention warning, không hard block)

## Bước 4 — Check hooks

Đọc `.claude/settings.json`, verify:
- [ ] SessionStart có task-summary hook
- [ ] SessionStart có mail-summary hook
- [ ] Stop có session-end hook

## Bước 5 — Check Beads CLI (optional)

Chạy: `bd --version 2>/dev/null`
- Nếu có → report version + verify `bd doctor` passes
- Nếu không → report "Beads CLI not installed — using YAML fallback (OK for development)"

## Bước 6 — Check agent mail

Đọc `.claude/memory/agent_mail.yaml`, validate:
- [ ] File parse được (valid YAML)
- [ ] Mỗi message có required fields: `id`, `from`, `to`, `subject`, `body`, `created_at`, `read_by`

## Output format

```
## 🩺 Beads Doctor

### Task Tracker
✅ Schema valid (N tasks)
✅ All IDs unique
✅ No circular dependencies
⚠️  1 consistency issue: tsk-a1b2 is "blocked" but blocked_by is empty
✅ Dependency DAG: N tasks, M edges, max depth D

### Hooks
✅ SessionStart: task-summary + mail-summary
✅ Stop: session-end
⚠️  PreCompact: not configured (add bd sync for auto-persist)

### Beads CLI
ℹ️  Not installed — using YAML fallback

### Agent Mail
✅ Schema valid (N messages, M unread)

### Summary
Score: 8/10
Issues: 1 warning, 0 blockers
→ Fix: `/task-blocked tsk-a1b2` → change to open, or add blocked_by
```
