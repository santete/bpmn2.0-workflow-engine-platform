# Task Routing Matrix — 6D Classification → Methodology Profile

> Lazy-load rule file. Load khi bắt đầu task mới (Phase 1 step 1).
> Tham chiếu: Product Spec Module 1 — Input Classifier.

---

## 6 chiều phân loại đầu vào

Mỗi task/ticket/CR được phân loại 6 chiều TRƯỚC khi plan:

| # | Chiều | Giá trị | Tín hiệu nhận biết |
|---|-------|---------|---------------------|
| D1 | **Bản chất task** | `new-develop` · `bug-fix` · `investigate` · `refactor` · `documentation` · `translation` | Từ khóa ticket, loại Jira issue, user mô tả |
| D2 | **Quy mô** | `S` (<5 subtask, vài giờ) · `M` (5–7 subtask) · `L` (8+ subtask, nhiều ngày) | Ước lượng số subtask sau khi break |
| D3 | **Tính liên tục** | `single-session` · `multi-session` | Estimate > 1 ngày làm việc? |
| D4 | **Cộng tác** | `solo` (1 dev+AI) · `multi-dev` (nhiều dev/agent song song) | Cần phối hợp ai-đợi-ai? |
| D5 | **Độ rõ spec** | `clear` · `vague` · `legacy-undocumented` | Khách hiểu rõ nhu cầu? Có tài liệu? |
| D6 | **Độ quen codebase** | `known-subsystem` · `unknown` · `cross-module` | Dev đã hiểu luồng xử lý liên quan chưa? |

---

## Quyết định 2a / 2b — rẽ nhánh chính

Đây là rẽ nhánh quan trọng nhất, quyết định execution mode cho toàn bộ task:

```
NẾU (D2 = L) HOẶC (D3 = multi-session) HOẶC (D4 = multi-dev)
    → 2b: EPIC MODE
      - Cần persist state xuyên session (task tracker + dependency DAG)
      - Dùng /task-add, /task-ready, /task-claim, /task-close loop
      - HANDOFF.md bắt buộc cuối mỗi session
      - Agent Mail nếu multi-dev

NGƯỢC LẠI (S–M, single-session, solo)
    → 2a: SUB-AGENT MODE
      - Xong → commit → đóng, không cần track dài
      - Dùng pipeline 6-phase chuẩn (CLAUDE.md)
      - Không cần task tracker
```

---

## Routing Matrix — từ 6D → Methodology Profile

| Tín hiệu đầu vào | Execution Mode | WISC nhấn mạnh | Planning | Pre-action |
|-------------------|----------------|-----------------|----------|------------|
| D5 = `vague` | **(chưa code)** | WRITE (viết spec.md) | AI đặt câu hỏi ngược (QA-back) tới user | STOP — làm rõ spec trước, output: `spec.md` hoặc list câu hỏi |
| D6 = `unknown` hoặc `legacy-undocumented` | **(chưa code)** | ISOLATE (scout sub-agent) | Investigate trước | Scout đọc code → output: impact analysis + solution report |
| D2=S, D3=single, D4=solo | **2a Sub-agent** | SELECT + COMPRESS | Bite-size TDD (Phase 1 chuẩn) | — |
| D2=L hoặc D3=multi hoặc D4=multi | **2b Epic** | WRITE + SELECT (persist) | Epic plan → task breakdown + dependency graph | Tạo tasks via /task-add, set dependencies via /task-dep |
| D1 = `bug-fix` | 2a hoặc 2b (tùy D2) | WRITE (ghi notes) | Source diff + similar/impact detection | Đọc error log/stack trace trước khi plan |
| D1 = `investigate` | 2a (thường) | ISOLATE (scout) | Output là report, KHÔNG phải code | Khai báo scope rõ (Hallucination Rule 5) |
| D1 = `refactor` | 2a hoặc 2b (tùy D2) | SELECT (viewpoint) | File Map đặc biệt quan trọng (nhiều file thay đổi) | Verify test coverage trước khi refactor |
| D1 = `documentation` | atomic (2a nhẹ) | — | Giữ format gốc | — |
| D1 = `translation` | atomic (2a nhẹ) | — | Giữ format + improve nội dung | — |

### WISC Enforcement Level (Tier 3 Governance)

5 hooks phối hợp: `wisc-state.py` (compute) → `wisc-gate.py` (enforce) → `wisc-satisfy.py` (auto-flip) → `wisc-bypass.py` (controlled bypass) → `wisc-audit.py` (query trail).

| WISC Strategy | Mức enforcement | Cơ chế | Trigger |
|---------------|-----------------|--------|---------|
| **WRITE** | 🔴 **Hook block** | `wisc-gate.py` chặn Edit/Write khi `status: required` | D5 = `vague` |
| **ISOLATE** | 🔴 **Hook block** | `wisc-gate.py` chặn Edit/Write khi `status: required` | D6 = `unknown` / `legacy-undocumented` / `cross-module` |
| **SELECT** | 🟢 **Structural** | Eager/lazy architecture (`@` vs backtick) — `status: satisfied` by design | Mọi session |
| **COMPRESS** | 🔴 **Real-time** | `wisc-gate.py` check token count bất kể status | Token > 120K (configurable) |

**State lifecycle**: `inactive` → `required` → `satisfied` | `bypassed`

**Auto-satisfy**: `wisc-satisfy.py` (PostToolUse) detect khi `spec.md` hoặc `scout_report_*.md` được tạo → auto-flip `status: satisfied`.

**Bypass protocol**: Dùng `/wisc-bypass <GATE> --reason "<lý do>"` — validation + audit trail. KHÔNG edit YAML trực tiếp.

**Audit trail**: Mọi gate transition (compute/satisfy/block/bypass) ghi `wisc_audit` event vào `events.jsonl`. Query bằng `/wisc-audit`.

**Feedback loop**: `metrics-summary.py` [9] phân tích `wisc_audit` data → đề xuất tuning (bypass rate cao, block-to-satisfy nhanh, etc.).

---

## Output format — Methodology Profile

Sau khi classify 6D, output profile này ở đầu Phase 1:

```yaml
task_classification_6d:
  D1_nature: <new-develop|bug-fix|investigate|refactor|documentation|translation>
  D2_scale: <S|M|L>
  D3_continuity: <single-session|multi-session>
  D4_collaboration: <solo|multi-dev>
  D5_spec_clarity: <clear|vague|legacy-undocumented>
  D6_codebase: <known-subsystem|unknown|cross-module>

methodology_profile:
  execution_mode: <2a-subagent|2b-epic>
  wisc_emphasis: [<WRITE|ISOLATE|SELECT|COMPRESS>]
  planning: <bite-size-tdd|epic-plan|investigate-first|clarify-spec-first>
  pre_action: <none|clarify-spec|scout-investigate|create-task-graph>

# WISC gates — computed by wisc-state.py, enforced by wisc-gate.py, auto-flipped by wisc-satisfy.py
wisc_gates:
  WRITE:
    status: required                  # inactive | required | satisfied | bypassed
    artifact: "spec.md"
    satisfied_at: ""
    satisfied_by: ""                  # auto | manual | bypass | structural
    bypass_reason: ""
  ISOLATE:
    status: required
    artifact: ".claude/memory/scout_report_<task>.md"
    satisfied_at: ""
    satisfied_by: ""
    bypass_reason: ""
  SELECT:
    status: satisfied
    artifact: ""
    satisfied_at: "<timestamp>"
    satisfied_by: structural
    bypass_reason: ""
  COMPRESS:
    status: inactive                  # real-time token check by wisc-gate.py
    artifact: ""
    satisfied_at: ""
    satisfied_by: ""
    bypass_reason: ""
```

---

## Pre-action gates — hành động BẮT BUỘC trước khi plan

| Pre-action | Điều kiện trigger | Hành động | Output trước khi code |
|------------|------------------|-----------|----------------------|
| `clarify-spec` | D5 = vague | AI đặt 3–5 câu hỏi cụ thể cho user. KHÔNG plan khi chưa có answer | List câu hỏi hoặc `spec.md` draft |
| `scout-investigate` | D6 = unknown/legacy | Sub-agent scout đọc code liên quan (max 15 file), output summary | Impact analysis ≤500 tokens |
| `create-task-graph` | execution_mode = 2b | `/task-add` cho mỗi subtask + `/task-dep` cho dependencies + `/task-graph` visualize | Task list + dependency graph |
| `none` | Mọi TH còn lại | Vào plan trực tiếp | — |

---

## Ví dụ phân loại nhanh

**Ví dụ 1:** *"Sửa bug Login validate sai message"*
→ D1=bug-fix, D2=S, D3=single, D4=solo, D5=clear, D6=known → **2a**, planning=bite-size-tdd

**Ví dụ 2:** *"Epic SP395: thêm search theo mã SP, 8 task, 3 ngày, 3 developer"*
→ D1=new-develop, D2=L, D3=multi, D4=multi → **2b bắt buộc**, pre_action=create-task-graph

**Ví dụ 3:** *"Khách nói muốn thêm chức năng gì đó, chưa rõ"*
→ D5=vague → **STOP, clarify-spec trước**, chưa chọn 2a/2b

**Ví dụ 4:** *"Investigate tại sao API chậm ở module X"*
→ D1=investigate, D6=unknown → **2a**, pre_action=scout-investigate, output=report

---

## Anti-patterns

- ❌ Skip classify, nhảy thẳng vào code → chọn sai methodology, waste effort
- ❌ Classify xong nhưng không follow pre-action gate → vague spec vẫn code, unknown codebase vẫn đoán
- ❌ Dùng 2a cho task L/multi-session → mất state khi compact/rotate
- ❌ Dùng 2b cho bug-fix nhỏ → overhead không cần thiết
- ❌ Classify mà không ghi profile vào output → session sau không biết methodology đã chọn
