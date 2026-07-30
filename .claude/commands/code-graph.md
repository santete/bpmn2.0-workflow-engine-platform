---
description: Query code knowledge graph — tìm relationships giữa functions/classes không cần đọc file
---

Query code knowledge graph để hiểu codebase mà không đốt token đọc file.

## Bước 1 — Kiểm tra graph tồn tại

Kiểm tra `.claude/memory/code_graph.json` có tồn tại và không quá cũ:
- Nếu chưa có → hỏi user: "Code graph chưa được build. Chạy build? (`python .claude/scripts/build-graph.py`)"
- Nếu có → đọc `meta.built_at`, nếu > 7 ngày → suggest rebuild

## Bước 2 — Query

Chạy query via script:
```bash
python .claude/scripts/build-graph.py --query "$ARGUMENTS"
```

Hoặc đọc `.claude/memory/code_graph.json` trực tiếp và filter:
- Tìm symbols matching query name
- Tìm edges (calls, imports, extends) from/to query name

## Bước 3 — Output format

```
## 🔍 Code Graph: <query>

### Symbols found
| Name | Type | File | Line |
|------|------|------|------|
| processPayment | function | src/payment/stripe.py | 42 |

### Calls (outgoing)
- processPayment → stripe.PaymentIntent.create
- processPayment → db.save_transaction
- processPayment → logger.info

### Called by (incoming)
- api.routes.checkout → processPayment
- tests.test_payment.test_success → processPayment

### Imports
- payment.stripe → stripe (external)
- payment.stripe → db.models.Transaction

### Extends
(none)

---
Graph: <N> symbols, <M> edges (built <date>)
→ Rebuild: `python .claude/scripts/build-graph.py`
```

## Bước 4 — Sử dụng kết quả

Output graph query thay vì đọc 15 file → tiết kiệm ~15K tokens.
Agent dùng kết quả để:
- Hiểu call chain trước khi modify function
- Tìm impact scope khi refactor
- Phát hiện cross-module dependencies

## Build commands

```bash
# Build cho tất cả languages
python .claude/scripts/build-graph.py

# Build chỉ Python
python .claude/scripts/build-graph.py --lang py

# Build từ thư mục cụ thể
python .claude/scripts/build-graph.py --root src/

# Query trực tiếp
python .claude/scripts/build-graph.py --query "processPayment"
```

## Lưu ý
- `code_graph.json` nên gitignore (rebuild on demand, không commit)
- Rebuild khi code thay đổi đáng kể hoặc trước investigate task
- POC: Python dùng AST (chính xác), JS/TS dùng regex (approximate)
