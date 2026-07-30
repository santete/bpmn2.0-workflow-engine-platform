---
description: Bypass a required WISC gate with audit trail. Usage: /wisc-bypass <GATE> --reason "<lý do>"
---

Chạy WISC bypass protocol:

```bash
python .claude/hooks/python/wisc-bypass.py $ARGUMENTS
```

Nếu không có arguments, hỏi user:
1. Gate nào cần bypass? (WRITE / ISOLATE / COMPRESS)
2. Lý do bypass? (tối thiểu 5 ký tự, sẽ được ghi vào audit trail)

**Lưu ý**: Bypass được ghi vào audit trail (`wisc_audit` event trong `events.jsonl`). Không tự bypass mà không có user approval — đây là Hard Stop trong CLAUDE.md.
