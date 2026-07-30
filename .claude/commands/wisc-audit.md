---
description: Query WISC audit trail — xem lịch sử gate transitions (compute/satisfy/block/bypass). Usage: /wisc-audit [--days 7] [--gate WRITE] [--action bypassed]
---

Chạy WISC audit query:

```bash
python .claude/hooks/python/wisc-audit.py $ARGUMENTS
```

Nếu không có arguments, chạy mặc định `--days 7` (7 ngày gần nhất, tất cả gates + actions).

Ví dụ:
- `/wisc-audit` — tất cả audit events 7 ngày
- `/wisc-audit --gate ISOLATE` — chỉ ISOLATE gate
- `/wisc-audit --action gate_bypassed` — chỉ bypass events
- `/wisc-audit --days 30 --json` — 30 ngày, output JSON
