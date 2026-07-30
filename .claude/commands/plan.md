---
description: Chạy Phase 1 (Plan) cho task mà user vừa mô tả
---

Đây là Phase 1 (Plan) trong pipeline `@CLAUDE.md`. Mục tiêu: đưa ra plan rõ ràng TRƯỚC khi code, để user xác nhận.

## Quy trình

### 1. Hiểu task
- Restate task bằng lời mình để confirm hiểu đúng
- Nếu có gì mơ hồ → HỎI user, KHÔNG đoán

### 2. Context load
- Đã đọc `@docs/ai/PROJECT_MAP.md` chưa? Nếu chưa → đọc
- Đọc `@.claude/memory/project_state.yaml` (last task, decisions, gotchas, pending)
- Task thuộc category nào? Load file rule tương ứng (xem Reference Map trong `@CLAUDE.md`)
- Nếu task đụng external API/DB → BẮT BUỘC load `@.claude/memory/schema_snapshot.yaml`
- Luôn áp dụng `@docs/ai/HALLUCINATION_RULES.md` (cite source mọi reference)

### 3. Investigate
- Đọc file liên quan (KHÔNG đoán nội dung)
- Tìm pattern hiện có trong codebase mà task này nên follow

### 4. Break down
Output TODO list theo format:
```
## Plan

**Goal**: <one-line goal>

**Files dự kiến touch**:
- `path/to/file1` — <vì sao>
- `path/to/file2` — <vì sao>

**Sub-tasks** (atomic, tuần tự):
1. [ ] <task 1>
2. [ ] <task 2>
3. [ ] <task 3>

**Risk / Concern**:
- <điều có thể đi sai>
- <decision cần user input>

**Estimated complexity**: low / medium / high
```

### 5. Wait approval
- Nếu (sub-tasks > 3) HOẶC (files > 5) HOẶC (touch DB / auth / payment / public API)
  HOẶC (cần update `schema_snapshot.yaml`):
  → CHỜ user approve trước khi sang Phase 2
- Nếu task nhỏ (1-2 file, không sensitive):
  → Có thể proceed luôn nhưng vẫn show plan để user thấy

### 6. Cite source
Mọi reference đến code/API/schema hiện có phải có cite:
- "Based on `src/auth/jwt.py:42`"
- "Based on `schema_snapshot.yaml#stripe_payment_intent`"
- Không cite được → state uncertainty, KHÔNG assume (xem HALLUCINATION_RULES.md)

## Anti-patterns
- ❌ Plan chung chung kiểu "implement feature X" → phải break thành step
- ❌ Skip plan cho task lớn vì "thấy dễ"
- ❌ Plan dựa trên giả định mà không đọc code thật
