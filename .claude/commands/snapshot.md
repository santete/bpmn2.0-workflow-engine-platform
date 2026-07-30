---
description: Viết session snapshot thủ công (giữa session, không đóng session)
---

Khác `/rotate`: snapshot KHÔNG đóng session, chỉ ghi lại progress hiện tại để
phòng case crash hoặc muốn share với teammate.

## Quy trình

1. Tạo / append `.claude/memory/session_<YYYYMMDD>.md`:

```markdown
# Session <YYYY-MM-DD> — Snapshot @ <HH:MM>

## In progress
- <đang làm gì>

## Completed so far
- [x] <task xong>

## Decisions
- <decision>: <reason>

## Gotchas
- <gotcha>: <workaround>

## Files modified so far
<list>
```

2. KHÔNG update `project_state.yaml` (chỉ rotate mới update)

3. Báo user:
```
📸 Snapshot saved: .claude/memory/session_<YYYYMMDD>.md
   (session vẫn đang chạy — dùng /rotate để đóng session)
```

## Khi nào dùng `/snapshot` thay vì `/rotate`

| Trường hợp | Dùng |
|---|---|
| Session chưa dài, muốn save progress | `/snapshot` |
| Session > 120k tokens | `/rotate` (mandatory) |
| Hoàn thành task lớn | `/rotate` |
| Đi nghỉ trưa, sợ Claude crash | `/snapshot` |
| Muốn handoff cho teammate | `/snapshot` |
