---
description: Chạy đầy đủ Phase 3 (Verify) của pipeline
---

Chạy đầy đủ verification pipeline cho thay đổi hiện tại. Tham khảo `@docs/ai/PROJECT_MAP.md` để lấy command đúng cho project.

## Thứ tự (KHÔNG skip)

1. **Typecheck**
   - Chạy: `<typecheck-cmd>`
   - Fail → đọc lỗi, áp dụng Loop Logic trong `@CLAUDE.md` (max 3 retry)

2. **Lint**
   - Chạy: `<lint-cmd>`
   - Fail auto-fixable → `<lint-fix-cmd>`, rồi re-run
   - Fail thủ công → fix, rồi re-run (max 2 retry)

3. **Test (chỉ liên quan)**
   - Xác định file đã đổi: `git diff --name-only HEAD`
   - Chạy test liên quan tới các file đó
   - Test fail do code mình đổi → fix code (KHÔNG fix test để pass)
   - Test flaky / unrelated → STOP, escalate user

4. **Schema-check** (nếu file đổi touch external API/DB)
   - Chạy `/schema-check` để verify mọi reference khớp `schema_snapshot.yaml`
   - Phát hiện field lạ → Type 1/3 hallucination → STOP, recovery protocol

5. **Hook check** (tự chạy bởi PostToolUse hook)
   - File vừa write phải pass `post-write-check` (debug code, secrets, SQL injection, empty catch)
   - Hook block → fix theo error message

## Log loop metrics (fail-open)

Mỗi lần retry (typecheck fail, lint fail, test fail), log event:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.claude/hooks/python')))
from metrics_writer import write_event
write_event('loop_retry', {
    'gate': 'typecheck|lint|test|schema_check',  # step nào fail
    'attempt': <số lần retry hiện tại>,
    'max_retry': <budget từ Loop Logic>,
    'resolved': True/False,  # retry có fix được không
})
```

Sau khi verify XONG (pass hoặc escalate), log tổng kết:

```python
write_event('verify_done', {
    'total_retries': <tổng số retry qua tất cả gates>,
    'gates_failed': ['typecheck', 'lint'],  # list gates đã fail ít nhất 1 lần
    'escalated': False,  # True nếu phải escalate user
})
```

## Báo cáo
Sau khi chạy xong, báo theo format Phase 5:
```
✅ DONE: Verification passed
🧪 Tests: <X passed / Y failed / Z skipped>
🔁 Loops: <số lần retry>
⚠️  Notes: <gì cần user biết>
```

## Hard rule
KHÔNG được:
- Skip step nào
- Disable test để pass
- Dùng `as any` / `// @ts-ignore` / `# type: ignore` để qua typecheck
- Comment out code lỗi
