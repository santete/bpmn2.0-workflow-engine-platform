---
description: Phân loại task 6 chiều → chọn methodology phù hợp (2a sub-agent / 2b epic). Chạy đầu mỗi task mới.
---

Bạn đang chạy 6D Task Classifier. Phân loại task hiện tại để chọn đúng methodology.
KHÔNG đoán — hỏi user nếu thiếu thông tin.

## Bước 1 — Load routing matrix

Đọc `docs/ai/ROUTING_MATRIX.md` để biết 6 chiều + routing rules.

## Bước 2 — Thu thập tín hiệu

Từ task description của user, xác định 6 chiều:

### D1 — Bản chất task
Hỏi nếu không rõ: "Task này thuộc loại nào?"
- `new-develop`: tính năng mới hoàn toàn
- `bug-fix`: sửa bug / lỗi
- `investigate`: tìm hiểu, phân tích, không output code
- `refactor`: cải thiện code hiện có, không thêm tính năng
- `documentation`: viết/cập nhật tài liệu
- `translation`: dịch nội dung

### D2 — Quy mô
Ước lượng nhanh (có thể hỏi user xác nhận):
- `S`: <5 subtask, xong trong vài giờ
- `M`: 5–7 subtask, xong trong 1 ngày
- `L`: 8+ subtask, cần nhiều ngày

### D3 — Tính liên tục
- `single-session`: xong trong 1 session (không cần rotate/handoff)
- `multi-session`: cần nhiều session, phải persist state

### D4 — Cộng tác
- `solo`: 1 developer + AI
- `multi-dev`: nhiều developer/agent song song

### D5 — Độ rõ spec
- `clear`: yêu cầu rõ ràng, có spec/ticket đầy đủ
- `vague`: mơ hồ, cần clarify
- `legacy-undocumented`: hệ thống cũ, không tài liệu

### D6 — Độ quen codebase
- `known-subsystem`: dev đã hiểu module liên quan
- `unknown`: chưa đọc / chưa hiểu code liên quan
- `cross-module`: liên quan nhiều module, phức tạp

## Bước 3 — Apply routing matrix

Theo thứ tự ưu tiên:

1. **Check pre-action gates TRƯỚC** (ưu tiên cao nhất):
   - D5 = `vague` → `clarify-spec-first` (STOP, hỏi user, chưa plan)
   - D6 = `unknown` hoặc `legacy-undocumented` → `investigate-first` (scout trước)

2. **Quyết định 2a / 2b**:
   - NẾU (D2 = L) HOẶC (D3 = multi-session) HOẶC (D4 = multi-dev) → **2b epic**
   - NGƯỢC LẠI → **2a sub-agent**

3. **Xác định WISC emphasis + planning style** theo routing matrix trong `ROUTING_MATRIX.md`.

## Bước 4 — Output Methodology Profile (format BẮT BUỘC)

```
## 🎯 Task Classification (6D)

| Chiều | Giá trị | Tín hiệu |
|-------|---------|-----------|
| D1 Bản chất | <value> | <tín hiệu từ task description> |
| D2 Quy mô | <value> | <ước lượng subtask> |
| D3 Liên tục | <value> | <estimate thời gian> |
| D4 Cộng tác | <value> | <số người tham gia> |
| D5 Spec clarity | <value> | <có spec/ticket không> |
| D6 Codebase | <value> | <dev quen không> |

## Methodology Profile

- **Execution mode**: 2a sub-agent | 2b epic
- **WISC emphasis**: <list>
- **Planning**: <bite-size-tdd | epic-plan | investigate-first | clarify-spec-first>
- **Pre-action**: <none | clarify-spec | scout-investigate | create-task-graph>

## Pre-action (nếu có)
<mô tả hành động cần làm trước khi plan>

## Next Steps
<hướng dẫn cụ thể cho developer>
```

## Bước 5 — Ghi state

Update `.claude/memory/project_state.yaml` field `last_task_classification`:

```yaml
last_task_classification:
  date: "<ISO date>"
  task: "<task summary>"
  D1: "<value>"
  D2: "<value>"
  D3: "<value>"
  D4: "<value>"
  D5: "<value>"
  D6: "<value>"
  execution_mode: "<2a-subagent|2b-epic>"
  pre_action: "<none|clarify-spec|scout-investigate|create-task-graph>"
```

## Bước 6 — Compute WISC gates (BẮT BUỘC)

Sau khi ghi `last_task_classification`, chạy:

```bash
python .claude/hooks/python/wisc-state.py
```

Script này đọc classification vừa ghi → tính `wisc_gates` → ghi lại vào project_state.yaml.
Output sẽ hiển thị gates nào `required` (phải satisfy trước khi code).

**Ví dụ output:**
```
WISC gates: W🔴 I⬜ S✅ C⬜
  Required gates: WRITE — satisfy before coding
    WRITE: artifact=spec.md
```

Nếu có gate `required` → báo user và thực hiện pre-action tương ứng TRƯỚC khi plan.

## Bước 7 — Auto-scaffold DAG (CHỈ khi execution_mode = 2b epic)

Nếu Bước 3 cho kết quả **2b epic**, tự động khởi tạo task tracker + dependency graph:

### 7.1 — Init task tracker (nếu chưa có)

```bash
python .claude/hooks/python/post-classify-setup.py <current_pattern> <team_size>
```

Script sẽ tạo `.claude/memory/task_tracker.yaml` nếu chưa tồn tại.

### 7.2 — Tạo tasks từ subtask breakdown

Dựa vào phân tích task ở Bước 2 (D2 = M hoặc L), break thành subtasks rồi tạo từng task:

```bash
python .claude/hooks/python/task-add.py "Subtask 1: <title>"
python .claude/hooks/python/task-add.py "Subtask 2: <title>"
python .claude/hooks/python/task-add.py "Subtask 3: <title>"
# ... cho mỗi subtask
```

### 7.3 — Set dependencies (DAG)

Phân tích dependency tự nhiên giữa subtasks, rồi khai báo:

```bash
python .claude/hooks/python/task-dep.py tsk-xxxx blocks tsk-yyyy
python .claude/hooks/python/task-dep.py tsk-xxxx blocks tsk-zzzz
# ... cho mỗi dependency
```

**Quy tắc dependency tự nhiên:**
- Setup/infra tasks → block feature tasks
- Schema/migration → block code that uses new tables
- Core logic → block tests that test it
- Feature tasks → block deployment/integration tasks
- KHÔNG over-constrain: chỉ set dependency khi thực sự cần thứ tự

### 7.4 — Hiển thị DAG

Sau khi tạo xong, visualize graph:

```bash
python .claude/hooks/python/task-graph.py
```

Hiển thị output cho user verify dependency structure.

### 7.5 — Output hướng dẫn

```
## DAG Auto-Scaffold Complete

Created <N> tasks with <M> dependencies.

→ View tasks: `/task-list`
→ View graph: `/task-graph` (or `/task-graph --mermaid`)
→ Start work: `/task-ready` then `/task-claim <id>`
→ Edit deps:  `/task-dep <id-A> blocks <id-B>`

Note: DAG là gợi ý ban đầu. Chỉnh sửa dependency nếu cần trước khi bắt đầu implement.
```

## Anti-patterns

- ❌ Đoán D2 (quy mô) mà không break task — phải ước lượng subtask số trước
- ❌ Skip D5 check khi spec mơ hồ — sẽ plan sai, code sai
- ❌ Chọn 2b cho bug-fix S size — overhead không cần thiết
- ❌ Chọn 2a cho task L/multi-session — mất state giữa chừng
- ❌ Không ghi profile vào project_state — session sau không biết methodology
