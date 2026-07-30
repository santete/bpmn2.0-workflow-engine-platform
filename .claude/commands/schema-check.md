---
description: Verify code reference khớp với schema_snapshot.yaml — anti-hallucination
---

Chạy schema-check khi:
- Nghi ngờ Claude vừa hallucinate API field
- Phase 3 — sub-step (nếu task touch external API/DB)
- Trước khi commit code có touch external integration

## Bước 1 — Load schema

Đọc `.claude/memory/schema_snapshot.yaml`. Nếu file rỗng / chưa có entries → STOP và báo user:
```
⚠️  schema_snapshot.yaml chưa có entries.
    Cần điền schema trước khi schema-check work được.
    Xem template tại core/.claude/memory/schema_snapshot.yaml
```

## Bước 2 — Quét code đã thay đổi

Lấy file đã thay đổi:
```
git diff --name-only HEAD
# hoặc files vừa write trong session này
```

## Bước 3 — Match references

Với MỖI file:
1. Tìm mọi reference đến external API (vd: `stripe_client.payment_intents.create(...)`,
   `gitlab.projects.get(...)`)
2. Tìm mọi field access trên response (vd: `response.additions`, `data["customer_id"]`)
3. Kiểm tra:
   - Endpoint có trong `external_apis.<key>.endpoint` không?
   - Field có trong `external_apis.<key>.returns` HOẶC `optional` không?
   - Field có trong `external_apis.<key>.NOT_available`? → 🚨 Type 1 hallucination
   - Field nullable không có null-check → ⚠️ warning

## Bước 4 — Match DB fields

Với mọi query/ORM access:
1. Table có trong `database.<table>` không?
2. Column có trong `database.<table>.columns` không?
3. Column nullable không có handling? → ⚠️ warning

## Bước 5 — Output report

```
🔍 SCHEMA-CHECK REPORT

Files scanned: <số>
External API refs:  <số>
DB refs:            <số>

🚨 BLOCKERS (hallucination detected):
  - <file>:<line>  — Field `<x>` không có trong schema cho `<api>`
    → có thể là Type 1 invented API
    → ACTION: re-check actual API hoặc update schema_snapshot

⚠️  WARNINGS:
  - <file>:<line>  — Field `<y>` nullable nhưng không có null-check

✅ <số> refs verified OK
```

## Action khi có BLOCKER

Áp dụng Recovery Protocol từ `docs/ai/HALLUCINATION_RULES.md`:
1. STOP — không build thêm code trên hallucination
2. Classify (Type 1 / 3?)
3. Cung cấp ground truth: load actual API doc, paste cho Claude
4. Update `schema_snapshot.yaml` với info đúng
5. Regenerate code (KHÔNG patch)

## KHÔNG làm

- ❌ Skip schema-check vì "tao chắc chắn API có field này"
- ❌ Add field vào schema chỉ vì code đang dùng (verify với actual API trước)
- ❌ Patch hallucinated code — phải regenerate sau khi có ground truth
