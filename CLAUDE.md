# AI Agent Operating Pipeline (Merged)

> Bạn là AI engineer làm việc trên project này. Mọi task đi qua pipeline 6-phase
> dưới đây. KHÔNG được skip phase. Khi phase fail → áp dụng "Loop Logic".
> Khi đụng "Hard Stops" → DỪNG, hỏi user.
>
> File này là **orchestrator** (HOW). Rule chi tiết nằm ở `docs/ai/*.md`,
> chỉ load khi cần (xem "Reference Map"). Memory state nằm ở
> `.claude/memory/`, được đọc đầu Phase 0 và ghi cuối Phase 5.

---

## Phase 0 — Context Load (luôn chạy đầu tiên)

1. Đọc `@docs/ai/PROJECT_MAP.md` để biết cấu trúc, build/test commands
2. Đọc `@.claude/memory/project_state.yaml` để biết:
   - Pattern đang dùng (A / B / C)
   - Last task, decisions, known_gotchas, pending_tasks
   - `loc_at_classification` và `next_review_threshold`
3. **Auto re-classification check**:
   - Đo LOC hiện tại: `git ls-files | xargs wc -l 2>/dev/null | tail -1`
   - Nếu LOC > `next_review_threshold` → STOP, suggest user chạy `/classify` lại
4. **Internal/compliance rules entry point** (BẮT BUỘC nếu thư mục tồn tại):
   - Nếu tồn tại `@docs/ai/internal_rules/00_INDEX.md` → load **TRƯỚC** mọi rule khác.
   - INDEX có Decision Tree (mục 🎯) — match task vào A/B/C/D/E để biết load file detail nào (01–05).
   - INDEX có BLOCKER table — note tất cả rule ID nằm trong table này, vi phạm = Hard Stop (xem §Hard Stops).
   - INDEX cũng có Workflow tổng (mục 🔄) — verify pipeline 6-phase này có map đúng các bước 1–10 trong workflow của INDEX không.
5. Phân loại task → **TỰ Read** file rule tương ứng (KHÔNG dùng `@` prefix — tránh eager load):
   - Code change       → `docs/ai/CODING_RULES.md` + (nếu có) `docs/ai/internal_rules/06_Coding_Convention.md`
   - Git / commit / MR → `docs/ai/GIT_CONVENTION.md` + (nếu có) `docs/ai/internal_rules/01_MR_Compliance.md`
   - DB / migration    → `docs/ai/DB_RULES.md` + (nếu có) `docs/ai/internal_rules/02_Naming_Microservice.md`
   - API contract      → `docs/ai/API_RULES.md` + `.claude/memory/schema_snapshot.yaml` + (nếu có) `docs/ai/internal_rules/03_API_Naming.md` + `docs/ai/internal_rules/04_API_Response_and_Error.md`
   - I/O / external call / timeout → (nếu có) `docs/ai/internal_rules/05_API_Timeout.md`
   - Service / microservice mới  → (nếu có) `docs/ai/internal_rules/02_Naming_Microservice.md`
   - Security / auth   → `docs/ai/SECURITY_RULES.md`
   - Test              → `docs/ai/TESTING_RULES.md`
   - **Mọi external API/DB ref → BẮT BUỘC** Read `.claude/memory/schema_snapshot.yaml`
6. Áp dụng rule chung: đọc `@docs/ai/HALLUCINATION_RULES.md` (always-load)
7. **Task tracker check** (nếu `execution_mode = 2b` hoặc `.claude/memory/task_tracker.yaml` có tasks):
   - Đọc `.claude/memory/task_tracker.yaml`
   - Hiển thị: tasks in_progress (đang làm dở), tasks ready (sẵn sàng claim)
   - Nếu có task in_progress → resume task đó, không bắt đầu task mới
   - Nếu không có in_progress → chạy `/task-ready` để chọn task tiếp
8. **Agent Mail check** (nếu `.claude/memory/agent_mail.yaml` tồn tại + non-empty):
   - Đọc unread messages → hiển thị cho user
   - Thông tin từ agent khác có thể ảnh hưởng task hiện tại
9. **Skills progressive load** (nếu `.claude/skills/catalog.yaml` tồn tại):
   - Đọc catalog → match task type (từ 6D D1) + current phase → load skill rules tương ứng
   - Skill = condensed rules (~500-800 tokens), thay vì load full rule file (~2-3K tokens)
   - KHÔNG load tất cả skills cùng lúc — chỉ load khi context cần
10. Task không rõ ràng / mơ hồ → STOP. Hỏi user. KHÔNG đoán.

> ⚠️ **Convention `@` vs backtick** (quan trọng — Claude Code eager-loads `@filepath`):
> - `@path` = ALWAYS-load (eager). Chỉ dùng cho 4 file mandatory: `PROJECT_MAP.md`, `project_state.yaml`, `HALLUCINATION_RULES.md`, `internal_rules/00_INDEX.md`.
> - `` `path` `` (backtick, no `@`) = LAZY-load. Claude dùng Read tool khi task match category. Tránh waste 20k+ tokens baseline.

---

## Phase 1 — Plan

1. **6D Task Classification** (BẮT BUỘC trước khi plan):
   - Phân loại task theo 6 chiều: D1 bản chất, D2 quy mô, D3 liên tục, D4 cộng tác, D5 spec clarity, D6 codebase
   - Xem chi tiết: `docs/ai/ROUTING_MATRIX.md` (lazy-load khi bắt đầu task)
   - Output: Methodology Profile (execution_mode, WISC emphasis, planning style, pre-action)
   - **Pre-action gates** (xử lý TRƯỚC khi plan — **ENFORCED by `wisc-gate.py` hook**):
     - D5=vague → STOP, đặt câu hỏi clarify cho user, KHÔNG plan khi chưa rõ
       **→ Hook chặn Edit/Write nếu chưa có `spec.md`**
     - D6=unknown → scout investigate trước (sub-agent đọc code → impact analysis)
       **→ Hook chặn Edit/Write nếu chưa có `.claude/memory/scout_report_*.md`**
   - **WISC gates** (ghi kết quả vào `project_state.yaml` → `wisc_gates` section):
     - Classify xong → set `wisc_gates.WRITE/ISOLATE` tùy D5/D6
     - Gate satisfied khi artifact tồn tại HOẶC `wisc_gates.<GATE>.satisfied: true`
     - Bypass cần user approve + ghi `bypass_reason`
   - **Quyết định 2a/2b**:
     - (D2=L) HOẶC (D3=multi-session) HOẶC (D4=multi-dev) → **2b epic** (persist state, task tracker)
     - Ngược lại → **2a sub-agent** (pipeline chuẩn, xong commit đóng)
   - Có thể chạy `/classify-task` để classify tương tác, hoặc tự classify inline
2. Restate task bằng lời mình để confirm hiểu đúng
3. **File Map** (BẮT BUỘC trước khi chia sub-task):
   - Liệt kê MỌI file sẽ thay đổi / tạo mới — **đọc trước, không đoán cấu trúc**
   - Ghi rõ trách nhiệm từng file. Sub-task chỉ được modify file trong boundary đã định (không vượt)
   - Format: `<file path> — <trách nhiệm> — owned by sub-task #N`
4. Break task thành sub-task atomic (mỗi cái testable độc lập)
5. **TDD-first** (BẮT BUỘC cho mọi sub-task có code change):
   - Mỗi sub-task PHẢI có bước 1: viết test thất bại trước, bước 2: implement minimal để pass
   - Sub-task không có test step → KHÔNG hợp lệ, phải bổ sung
   - Format mỗi sub-task: `a. Write failing test → b. Implement → c. Verify pass → d. Commit`
6. Output dạng TODO list có đánh số rõ ràng
7. **No-Placeholder** (BẮT BUỘC):
   - Plan KHÔNG được chứa: "TBD", "add later", "similar to Task N", "will implement", "TODO:" mà không có code/path/command cụ thể
   - Mỗi step phải có đủ: file path cụ thể, code cụ thể hoặc command cụ thể, expected output
   - Nếu chưa biết chi tiết → DỪNG, research trước (đọc code, hỏi user), KHÔNG để placeholder
8. **Cite source** cho mọi reference đến code/API/schema/rule hiện có:
   - "Based on `src/auth/jwt.py:42`" hoặc "Based on `schema_snapshot.yaml#stripe_payment_intent`"
   - "Per `internal_rules/03_API_Naming.md#R-API-PATH-002`" — cite rule ID khi áp dụng compliance rule
   - Không cite được → state uncertainty, KHÔNG assume
9. **2b epic only** — nếu step 1 cho execution_mode = 2b (**BẮT BUỘC bootstrap**):
   - Check `.claude/memory/task_tracker.yaml` — nếu `tasks: []` → **PHẢI tạo tasks TRƯỚC khi code**
   - Tạo tasks cho mỗi sub-task via `/task-add <title>`
   - Khai báo dependencies via `/task-dep <id-A> blocks <id-B>`
   - Output dependency graph via `/task-graph`
   - Viết HANDOFF.md nếu dự kiến multi-session
   - Optional: nếu Beads CLI available → `bd init` + `bd setup claude` để upgrade engine
10. WAIT user xác nhận plan trước khi sang Phase 2 nếu thuộc 1 trong các TH:
   - sub-task > 3
   - file touch > 5
   - touch DB / auth / payment / public API
   - cần update `schema_snapshot.yaml`

---

## Phase 2 — Implement

Với MỖI sub-task (tuần tự, không song song):
  a. Read các file liên quan (no assumption về nội dung)
  b. **Test-first**: viết test file TRƯỚC, run để confirm FAIL (red)
  c. Apply change — mọi field/method ref phải verify được trong code thật hoặc schema_snapshot
  d. Run test lại — confirm PASS (green). Nếu vẫn fail → fix code, KHÔNG sửa test để pass
  e. Update TODO: `[x] done`
  f. → sub-task tiếp theo

> ⚠️ Nếu sub-task không có test step trong plan → STOP, quay Phase 1 bổ sung.

KHÔNG bao giờ:
- Edit file mà chưa đọc nội dung hiện tại
- Tạo file mới khi có thể extend file cũ
- Copy-paste code mà chưa hiểu nó làm gì
- Reference function/API/field không có cite source rõ ràng

---

## Phase 3 — Verify (deterministic gates)

Chạy theo thứ tự, KHÔNG skip:

1. **Typecheck**: `<project-typecheck-cmd>` (xem PROJECT_MAP.md)
2. **Lint**:      `<project-lint-cmd>`
3. **Test**:      chỉ test liên quan đến file đã đổi
   (full suite chỉ khi user yêu cầu hoặc trước commit chính thức)
4. **Schema-check** (nếu touch external API/DB):
   - Verify mọi field access có trong `schema_snapshot.yaml`
   - Phát hiện field lạ → có thể là Type 1/3 hallucination → STOP, recovery protocol
5. **Hook check**: file vừa write có pass `post-write-check` không
   (debug code, hardcoded secret, SQL injection, empty catch, PAN/CVV logging, **placeholder detection**)
   - **WISC gate** (`wisc-gate.py`): chạy PreToolUse trên mọi Edit/Write — enforce WRITE/ISOLATE/COMPRESS gates.
     Token > `rotate_threshold` → bị chặn cho đến khi `/rotate` hoặc `/compact`.
6. **Compliance check** (nếu `internal_rules/` tồn tại):
   - Đối chiếu với BLOCKER table trong `internal_rules/00_INDEX.md` — vi phạm bất kỳ row nào → STOP, fix.
   - Naming convention (SQL/Mongo/API path/event/branch) — match Cross-cutting #1 trong INDEX.
   - Response wrapper 4 field + error category — match `04_API_Response_and_Error.md` nếu touch controller.
   - Timeout config + retry budget — match `05_API_Timeout.md` nếu touch I/O call.

Phase 3 fail → vào Loop Logic ở dưới.

---

## Phase 4 — Self-Review

Trước khi báo "done", trả lời INTERNAL các câu sau (yes hết mới qua Phase 5):

- [ ] File nào edit nhưng chưa verify?
- [ ] Còn `console.log` / `print` / debug code sót lại?
- [ ] Có hardcode lẽ ra phải là config / env var?
- [ ] Edge case (null, empty, error path, timeout) có cover?
- [ ] Doc / README / comment có cần update không?
- [ ] Có introduce dependency mới? Đã lock version chưa? License OK?
- [ ] Có thay đổi nào breaking không document?
- [ ] **Mọi external API/field ref có cite source được không?**
- [ ] **No-Placeholder**: còn "TBD", "add later", "TODO:" không có ticket ref, "will implement", placeholder nào trong code/plan chưa resolve?
- [ ] **TDD-first**: mọi function/class mới có test tương ứng? Test được viết trước impl? Có sub-task nào skip test step?
- [ ] **File Map**: code thay đổi có nằm trong boundary File Map (Phase 1) không? Có file nào bị modify ngoài phạm vi?
- [ ] **Session token đang ở bao nhiêu? Nếu > 120k → phải rotate ngay sau Phase 5**
- [ ] **Nếu `internal_rules/` tồn tại**: có rule ID nào trong BLOCKER table (`00_INDEX.md` mục "BLOCKER tuyệt đối") đang bị vi phạm không?
- [ ] **MR self-check** (nếu chuẩn bị tạo MR): đã pass 6 item trong `01_MR_Compliance.md / R-MR-CHECKLIST` chưa?

Bất kỳ câu nào "no" → quay Phase 2 fix item đó.

> **Pattern C only**: Phase 4 do `reviewer` agent thực hiện, KHÔNG phải implementer
> tự review. Xem `patterns/pattern-c-council/agents/reviewer.md`.

---

## Phase 5 — Report (format BẮT BUỘC)

```
✅ DONE: <one-line summary>
📁 Files: <list các file đã đổi>
🧪 Tests: <X passed / Y failed / Z skipped>
🔁 Loops: <số lần loop ở Phase 3>
🛡️ WISC: W<icon> I<icon> S<icon> C<icon>   (✅=satisfied ⚠️=bypassed ❌=unsatisfied ⬜=inactive)
⚠️  Notes: <điều user cần biết / TODO còn lại / decision tự đưa ra>
🧠 Memory: <những gì đã update vào project_state.yaml + schema_snapshot.yaml>
```

**Memory write step (mandatory)** — Trước khi kết thúc:
0. **Task tracker update** (nếu đang dùng task tracker — execution_mode 2b):
   - Nếu có task in_progress → BẮT BUỘC `/task-note` ghi context cho session sau
   - Nếu task hoàn thành → `/task-close` (auto-unblock dependents)
   - Nếu task bị stuck → `/task-blocked` với lý do cụ thể
   - **Agent Mail**: nếu thay đổi ảnh hưởng agent/session khác → `/mail-send` thông báo
1. Update `.claude/memory/project_state.yaml` (đã load ở Phase 0):
   - `last_successful_task`, `completed_tasks` (append)
   - `decisions` (nếu có decision không hiển nhiên)
   - `known_gotchas` (nếu phát hiện gotcha)
2. Update `.claude/memory/schema_snapshot.yaml` nếu:
   - Phát hiện external API field mới
   - Phát hiện gotcha về schema (nullable, behavior khác doc)
   - Add DB column/table mới
3. Nếu session > 120k tokens → chạy `/rotate` (viết session snapshot + đóng session)
4. **Nếu chuẩn bị commit + `internal_rules/` tồn tại** — bắt buộc:
   - Conventional Commits format (`R-COMMIT-001` trong `01_MR_Compliance.md`)
   - Tag `[AI]` cuối subject nếu code do AI sinh (`R-COMMIT-002-AI`)
   - Ví dụ: `feat(auth): add login flow [AI]`
5. **Nếu chuẩn bị tạo MR** — bắt buộc 8 section per `R-MR-002` + AI Disclosure mutually exclusive (`R-MR-003-AI-DISCLOSURE`).

---

## Loop Logic (deterministic, có budget)

| Lỗi gặp                          | Action                                  | Max retry |
|----------------------------------|------------------------------------------|-----------|
| Typecheck fail                   | Đọc lỗi → fix → re-run Phase 3          | 3         |
| Lint fail (auto-fixable)         | Run `--fix` → re-run                    | 1         |
| Lint fail (non auto-fixable)     | Fix thủ công → re-run                   | 2         |
| Test fail (do code mình đổi)     | Root cause → fix code → re-run          | 2         |
| Test fail (flaky / unrelated)    | STOP, escalate user — KHÔNG fix test    | —         |
| Schema mismatch (field không có) | STOP → Recovery protocol (HALLUCINATION_RULES.md) | 1 |
| Hallucination detected           | STOP → 5-bước recovery → update schema_snapshot | 1 |
| Self-review fail                 | Quay Phase 2, fix item fail             | 2         |
| Loop retry >= 2                  | Recommend `/halluc-score` để diagnose root cause | —     |
| Context > 120k tokens            | STOP → `/rotate` (mandatory)            | —         |
| Vượt max retry                   | STOP, escalate với context đầy đủ       | —         |

**KHÔNG bao giờ:**
- Disable / skip test để pass
- Dùng `as any`, `// @ts-ignore`, `# type: ignore` để qua typecheck
- Comment out code lỗi để qua lint
- Lặp vô hạn không escalate
- "Đoán" fix mà không hiểu root cause
- Tiếp tục code trên output đã hallucinate (mỗi function build trên hallucination = 3-5x token debug)

---

## Hard Stops — KHÔNG tự quyết, LUÔN hỏi user

**Từ skeleton (operations):**
- Schema migration, `DROP TABLE`, `ALTER` ảnh hưởng prod data
- Rotate / regenerate secret, API key, JWT secret
- `git push --force`, rewrite history, delete branch chung
- Xóa file > 100 dòng, xóa thư mục
- Sửa code trong `docs/ai/IMMUTABLE/` (nếu có)
- Install dependency mới (xác nhận license + size + maintenance)
- Đổi public API contract (breaking change)
- Bypass auth / disable security check / disable rate limit
- Bất kỳ thao tác nào với production env (deploy, env var, DB)

**Bổ sung (memory + hallucination):**
- Schema mismatch giữa code và `schema_snapshot.yaml` không giải thích được
- Hallucination Type 1 detected (invented API/method)
- Cross-domain access trong Pattern B (agent đụng file ngoài scope của mình)
- Implementer self-review trong Pattern C (phải qua reviewer agent)
- Auto re-classify trigger (LOC vượt threshold của pattern hiện tại)

**Bổ sung (WISC governance):**
- `wisc-gate.py` block → KHÔNG tự bypass — phải dùng `/wisc-bypass <GATE> --reason "<lý do>"` (cần user approve)
- Mọi bypass được ghi vào audit trail (`wisc_audit` event) — xem `/wisc-audit`
- KHÔNG edit `project_state.yaml` trực tiếp để set `status: bypassed` — dùng `/wisc-bypass`

**Bổ sung (internal compliance — chỉ apply nếu `docs/ai/internal_rules/` tồn tại):**
- Vi phạm BẤT KỲ rule nào trong `internal_rules/00_INDEX.md` mục **"BLOCKER tuyệt đối"** (single source of truth — table đầy đủ ở INDEX, KHÔNG inline ở đây để tránh drift).
- Conflict resolution không xác định được giữa 2 rule (xem `00_INDEX.md` mục ⚖️) → BLOCK, hỏi user.
- Tạo service mới hoặc đổi engine SQL ↔ Mongo mà không match `R-DECISION` (`02_Naming_Microservice.md`).

---

## Reference Map (lazy load — KHÔNG inline ở đây)

> **`@path` (eager) vs backtick path (lazy)**: chỉ 4 file đầu (mandatory) dùng `@` syntax — Claude Code eager-load ngay session start. Phần còn lại dùng backtick — Claude Read khi task match category. Đảo ngược → bloat baseline ~20k tokens.

| File                                      | Khi nào load                        |
|-------------------------------------------|--------------------------------------|
| `@docs/ai/PROJECT_MAP.md`                 | Mọi session (Phase 0) — **eager**   |
| `@docs/ai/HALLUCINATION_RULES.md`         | Mọi session (Phase 0) — **eager**   |
| `@.claude/memory/project_state.yaml`      | Mọi session (Phase 0 + Phase 5) — **eager** |
| `@docs/ai/internal_rules/00_INDEX.md`     | **BẮT BUỘC** mọi session NẾU thư mục tồn tại — **eager** (entry point, có Decision Tree dispatch + BLOCKER table + Cross-cutting refs) |
| `.claude/memory/schema_snapshot.yaml`     | Khi đụng external API / DB schema — *lazy* |
| `.claude/memory/task_tracker.yaml`        | Khi execution_mode = 2b hoặc file non-empty (Phase 0 step 7) — *lazy* |
| `.claude/memory/agent_mail.yaml`          | Khi multi-dev hoặc file non-empty (Phase 0 step 8) — *lazy* |
| `.claude/memory/code_graph.json`          | Khi investigate hoặc `/code-graph` query — *lazy, gitignored* |
| `.claude/skills/catalog.yaml`             | Phase 0 step 9 — skill progressive disclosure — *lazy* |
| `docs/ai/CODING_RULES.md`                 | Trước khi viết / sửa code — *lazy*  |
| `docs/ai/GIT_CONVENTION.md`               | Trước khi commit / branch / PR — *lazy* |
| `docs/ai/API_RULES.md`                    | Khi đụng REST / GraphQL / RPC — *lazy* |
| `docs/ai/DB_RULES.md`                     | Khi đụng schema / query / migration — *lazy* |
| `docs/ai/SECURITY_RULES.md`               | Khi đụng auth / input / secret — *lazy* |
| `docs/ai/TESTING_RULES.md`                | Khi viết / sửa test — *lazy*        |
| `docs/ai/ROUTING_MATRIX.md`               | Khi bắt đầu task mới (Phase 1 step 1) — *lazy* |
| `docs/ai/internal_rules/06_Coding_Convention.md` | Code change (ưu tiên .NET) — *lazy* |
| `docs/ai/internal_rules/01_MR_Compliance.md` | Branch / commit / MR / self-check (R-BRANCH, R-COMMIT, R-MR, R-CODE) — *lazy* |
| `docs/ai/internal_rules/02_Naming_Microservice.md` | Service / DB / table / column / event naming + R-DECISION — *lazy* |
| `docs/ai/internal_rules/03_API_Naming.md` | REST endpoint, path, HTTP method, query, OpenAPI — *lazy* |
| `docs/ai/internal_rules/04_API_Response_and_Error.md` | Controller return / error handling / error code catalog — *lazy* |
| `docs/ai/internal_rules/05_API_Timeout.md` | Setup HTTP / gRPC / DB / cache client + retry + cancellation — *lazy* |

> **Load order khi `internal_rules/` tồn tại**: `00_INDEX.md` (eager) → match task vào Decision Tree → Claude TỰ Read file detail (lazy). KHÔNG load detail trực tiếp mà bỏ qua INDEX (sẽ miss BLOCKER table + Cross-cutting refs).

---

## Pattern overlay

Project này dùng pattern nào → đọc thêm overlay tương ứng:
- Pattern A (Solo, ≤10k LOC):     `patterns/pattern-a-solo/CLAUDE.md.overlay`
- Pattern B (Scoped, 10–100k LOC): `patterns/pattern-b-scoped/CLAUDE.md.overlay`
- Pattern C (Council, >100k LOC):  `patterns/pattern-c-council/CLAUDE.md.overlay`

Overlay bổ sung rule riêng cho size đó (agent dispatch, role boundary, context budget).

---

## Slash commands (shortcut từng phase)

| Command            | Phase           | Khi nào dùng                                   |
|--------------------|-----------------|------------------------------------------------|
| `/classify`        | Setup / re-eval | Lần đầu setup HOẶC khi project grow đáng kể (project-level Pattern A/B/C) |
| `/classify-task`   | Phase 1         | Phân loại task 6D → chọn methodology 2a/2b (task-level, mỗi task mới) |
| `/plan`            | Phase 1         | Khi bắt đầu task lớn, muốn plan trước          |
| `/verify`          | Phase 3         | Sau khi code xong, muốn chạy đầy đủ check      |
| `/schema-check`    | Phase 3 (sub)   | Chỉ verify schema_snapshot, không chạy test    |
| `/halluc-score`    | Phase 3 / 5     | Tính HRS 7-signal khi nghi hallucinate / loop nhiều / cuối session |
| `/diagnose`        | Any             | Khi framework có vấn đề (hook không fire / rule drift / HRS sai) — gom state + classify + đề xuất root cause, no auto-patch |
| `/check-drift`     | Any             | Sau pull / trước task lớn / khi SessionStart cảnh báo drift — verbose grouped report về watched files đã đổi từ baseline. `--baseline` để re-stamp HEAD sau khi đã reconcile memory. |
| `/commit`          | Git ops         | Khi muốn tạo commit chuẩn convention           |
| `/snapshot`        | Phase 5 (mid)   | Viết session snapshot trước khi rotate         |
| `/rotate`          | Phase 5 (end)   | Đóng session hiện tại, write memory + sang ss mới |
| `/task-add`        | Phase 1 (2b)    | Tạo task mới trong tracker (epic mode)             |
| `/task-ready`      | Phase 0 / any   | List tasks sẵn sàng làm (open + unblocked)         |
| `/task-claim`      | Phase 2 start   | Claim task → in_progress                            |
| `/task-note`       | Phase 5 / any   | Ghi note vào task (thư gửi session sau)             |
| `/task-close`      | Phase 5         | Đóng task, auto-unblock dependents                  |
| `/task-list`       | Any             | Hiển thị tất cả tasks + status                      |
| `/task-blocked`    | Any             | Đánh dấu task bị blocked                            |
| `/task-dep`        | Phase 1 (2b)    | Khai báo dependency (A blocks B)                    |
| `/task-graph`      | Any             | Hiển thị dependency graph                            |
| `/mail-send`       | Any             | Gửi message cho agent/session khác                  |
| `/mail-read`       | Phase 0 / any   | Đọc unread messages                                  |
| `/mail-list`       | Any             | Liệt kê tất cả messages                             |
| `/code-graph`      | Any             | Query code knowledge graph (function/class relationships) |
| `/task-discovered`  | Any (2b)        | Tạo discovered task (bug phát sinh khi đang làm task khác) |
| `/beads-doctor`    | Any             | Health check task tracker + hooks + dependencies           |
| `/benchmark`       | Any             | Do token overhead + metrics analysis + feature ROI         |
| `/wisc-bypass`     | Any             | Bypass WISC gate có audit trail (cần user approve)         |
| `/wisc-audit`      | Any             | Query WISC audit trail (gate transitions, bypasses)        |

---

## Beads Integration (F3.4 Anti-Amnesia)

Framework hỗ trợ 2 engine cho task tracking:
- **YAML engine** (mặc định): `.claude/memory/task_tracker.yaml` — zero dependency, git-native
- **Beads CLI** (production): `bd init && bd setup claude` — conflict-free IDs, JSONL, queryable

Hooks tự detect: nếu Beads CLI installed → dùng `bd prime`/`bd sync`. Nếu không → YAML fallback. Không cần config thêm.

| Hook | Trigger | Beads action | YAML fallback |
|------|---------|-------------|---------------|
| SessionStart | Mỗi session mới | `bd prime` (load snapshot) | task-summary.py (read YAML) |
| Stop | Session kết thúc | `bd sync` (persist state) | session-end.py (warn in_progress) |

Setup Beads (khi cần upgrade):
```bash
curl -fsSL .../install.sh | bash    # cài Beads CLI
bd init --prefix <2-5 char>         # prefix ngắn, tránh ID dài
bd setup claude                     # cài Anti-Amnesia hooks
bd doctor                           # verify
```

---

## Meta

- File này là **pipeline**, không phải nơi chứa rule chi tiết.
- Sửa pipeline → commit message phải bắt đầu bằng `chore(ai-pipeline):`
- Sửa rule chi tiết → sửa file con trong `docs/ai/`, KHÔNG đụng file này.
- Sửa pattern overlay → sửa `patterns/<pattern>/CLAUDE.md.overlay`, không đụng file này.
- Mỗi sự cố AI agent = 1 dòng rule mới (knowledge accumulation theo thời gian).
