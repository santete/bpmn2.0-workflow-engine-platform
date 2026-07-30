---
description: Phân loại project và recommend Pattern A/B/C — chạy lần đầu HOẶC khi project grow đáng kể
---

Bạn đang chạy classifier cho project hiện tại. Output theo format ở cuối file.
KHÔNG đoán — phải dùng tool để đo thật.

## Bước 0 — Detect deployment context (BẮT BUỘC, chạy TRƯỚC)

User có thể đang setup framework theo 1 trong 3 case → next steps khác nhau hoàn toàn. Phải auto-detect, KHÔNG hỏi user thay vì dùng signal.

Dùng Glob/Read để check 4 signal:

| Signal | Cách check | Ý nghĩa |
|---|---|---|
| `framework_only` | Chỉ có `.claude/`, `docs/`, `CLAUDE.md` ở root, KHÔNG có `package.json`/`pom.xml`/`*.csproj`/`go.mod`/`pyproject.toml`/`Cargo.toml`/`src/` | Greenfield post-copy (project mới, chưa có source) |
| `has_real_source` | Có `src/` HOẶC manifest file (`package.json`, `pom.xml`, `*.csproj`, `go.mod`, etc.) HOẶC LOC > 500 | Brownfield (đã có source code thật) |
| `claude_old_present` | File `CLAUDE_OLD.md` exists ở root | Brownfield, project cũ đã có CLAUDE.md → user đã rename để tránh collision |
| `claude_md_foreign` | `CLAUDE.md` exists nhưng KHÔNG chứa string `"AI Agent Operating Pipeline (Merged)"` (signature framework) | Brownfield, project cũ có CLAUDE.md riêng → CHƯA layer framework, có thể conflict |

**Phân loại deployment context:**

| Case | Điều kiện | Flow |
|---|---|---|
| **Greenfield post-copy** | `framework_only=true` AND `has_real_source=false` | Fast-path: skip Bước 1+2, chỉ hỏi Q2 |
| **Brownfield (clean)** | `has_real_source=true` AND `claude_old_present=false` AND `claude_md_foreign=false` | Full-path: chạy hết Bước 1→5 + auto-scaffold |
| **Brownfield (with collision)** | `has_real_source=true` AND (`claude_old_present=true` OR `claude_md_foreign=true`) | Full-path + merge step trước auto-scaffold |

Ghi nhận `deployment_context` (1 trong 3) → dùng để branch flow ngay dưới đây.

---

## Bước 0.5 — Branch flow theo deployment_context (BẮT BUỘC)

**Đây là gate quan trọng nhất** — chọn sai flow sẽ waste token (greenfield đọc framework files vô ích) hoặc miss data (brownfield không scan codebase).

```
IF deployment_context == "Greenfield post-copy":
    → Skip Bước 1 + Bước 2 (KHÔNG đọc codebase, KHÔNG đo LOC, KHÔNG glob indicators)
    → Set: total_loc=0, file_count=0, indicators=N/A
    → Skip Q1 ở Bước 3 (đã biết là greenfield)
    → Hỏi DUY NHẤT Q2 (team_size)
    → Bước 4: default Pattern A; team ≥ 5 → override B
    → Bước 5: output với Greenfield Next Steps (Case A)

ELSE (Brownfield clean / with collision):
    → Run Bước 1 → 5 đầy đủ
    → Bước 5: auto-scaffold PROJECT_MAP + schema_snapshot + project_state (Case B/C)
```

> 💡 **Why**: framework files (`.claude/`, `docs/`) ~5–10k tokens nếu đọc hết. Greenfield không có source thật → đọc cái đó để "đo LOC" là waste. Brownfield đọc codebase đáng giá vì quyết định pattern + auto-fill được 3 file core.

---

## Bước 0.7 — Load existing memory  *(BROWNFIELD ONLY — context preservation)*

**Mục tiêu**: Nếu repo đã có memory file từ session/dev trước → load làm **baseline**, KHÔNG regenerate từ đầu. Đảm bảo *consistency* khi dev khác clone về (bảo tồn decisions, gotchas, schema notes đã ghi nhận).

**IF deployment_context != Greenfield post-copy**:

Check tồn tại + non-empty 3 file:

| File | Check | Nếu có |
|---|---|---|
| `.claude/memory/project_state.yaml` | exists + size > 100 bytes | Read full → set `existing_state=true`, lưu: `pattern`, `team_size`, `loc_at_classification`, `decisions[]`, `known_gotchas[]` |
| `docs/ai/PROJECT_MAP.md` | exists + size > 200 bytes | Read full → set `existing_map=true` |
| `.claude/memory/schema_snapshot.yaml` | exists + size > 100 bytes | Read full → set `existing_schema=true` |

**Set scoping flags cho các bước sau:**
- `existing_state=true` → Bước 4 ưu tiên `pattern` cũ (chỉ override nếu LOC vượt threshold rõ rệt).
- `existing_map=true` → Bước 5 Case B: **KHÔNG** regenerate `PROJECT_MAP.md` từ đầu, chỉ append/update section còn thiếu.
- `existing_schema=true` → Bước 5 Case B: **KHÔNG** rewrite `schema_snapshot.yaml`, chỉ merge thêm endpoints/tables phát hiện mới.

> 💡 **Why**: dev A đã chạy /classify, ghi `decisions: ["chọn Postgres thay Redis vì..."]`. Dev B clone về chạy /classify lại → nếu regenerate thì *mất* decision đó → context drift giữa team. Phải load + preserve.

**Anti-pattern**: regenerate memory file dù đã tồn tại + non-empty (mất context cũ).

---

## Bước 1 — Đo codebase size  *(BROWNFIELD ONLY — skip nếu Greenfield post-copy)*

Chạy command đếm LOC (chọn 1, ưu tiên git nếu có):

  # Nếu là git repo:
  git ls-files | grep -E '\.(py|js|ts|jsx|tsx|java|go|rb|php|cs|cpp|c|h|swift|kt|rs|scala|vue|svelte)$' \
    | xargs wc -l 2>/dev/null | tail -1

  # Nếu KHÔNG phải git repo:
  find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \
    -o -name "*.tsx" -o -name "*.go" -o -name "*.java" \) \
    -not -path "*/node_modules/*" -not -path "*/.git/*" \
    -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/vendor/*" \
    -not -path "*/.venv/*" -not -path "*/.claude/*" -not -path "*/docs/ai/*" \
    | xargs wc -l 2>/dev/null | tail -1

> ⚠️ Loại trừ `.claude/` và `docs/ai/` — đó là framework files, không tính vào project LOC.

Ghi nhận: total_loc, file_count, primary_language(s).

## Bước 2 — Detect indicators  *(BROWNFIELD ONLY — skip nếu Greenfield post-copy)*

Dùng Glob/Read để check (KHÔNG đoán):

| Indicator | Check |
|---|---|
| `has_git` | `.git/` exists |
| `has_tests` | glob `**/test*` hoặc `**/spec*` hoặc `**/__tests__/**` |
| `has_docker` | `Dockerfile` hoặc `docker-compose.yml` |
| `has_ci` | `.github/workflows/` hoặc `.gitlab-ci.yml` |
| `has_api` | glob `**/api/**` hoặc `**/routes/**` hoặc `**/controllers/**` |
| `has_db` | glob `**/migrations/**` hoặc `**/models/**` hoặc `schema.sql` |
| `has_frontend` | có `.jsx/.tsx/.vue/.svelte` không trong vendor/node_modules |
| `manifest_files` | List manifest tìm thấy: `package.json`, `pom.xml`, `*.csproj`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `Gemfile` |

**Phân biệt thật vs placeholder**: nếu thư mục `tests/` chỉ có 1 file rỗng → coi như không có test.

## Bước 3 — Hỏi user

**Greenfield post-copy** — chỉ hỏi Q2:

  Q2: "Bao nhiêu developer sẽ dùng Claude trên project này?
       1. 1–2 người    →  Pattern A
       2. 3–5 người    →  Pattern A
       3. 6–10 người   →  Pattern B (team ≥ 5 cần shared state)
       4. > 10 người   →  Pattern B"

**Brownfield (clean / with collision)** — hỏi đủ Q1 + Q2:

  Q1: "Project này thuộc loại nào?
       1. Brownfield — làm tiếp codebase hiện tại
       2. Feature add (thêm tính năng cụ thể)
       3. Bug fix / refactor"
       (greenfield đã loại ở Bước 0)

  Q2: "Bao nhiêu developer sẽ dùng Claude trên project này?
       1. 1–2 người
       2. 3–5 người
       3. 6–10 người
       4. > 10 người"

## Bước 4 — Classify

**Greenfield post-copy:**
- Default Pattern A (project chưa có code → bắt đầu solo).
- Override: team ≥ 5 (Q2 = 3 hoặc 4) → Pattern B.

**Brownfield** — áp dụng matrix theo LOC:

| Size | Range | Pattern |
|---|---|---|
| small | ≤ 10k LOC | A — Solo Agent |
| medium | 10k – 100k LOC | B — Scoped Multi-Agent |
| large | > 100k LOC | C — Council of 6 |

**Override rules:**
- `small + team ≥ 5` → upgrade lên Pattern B (cần shared state cho team lớn)
- `bug fix only + scope hẹp` → có thể downgrade 1 bậc

**Token budget tương ứng:**
- Pattern A: working zone ≤ 100k, total ≤ 120k
- Pattern B: working zone ≤ 120k, total ≤ 140k (per agent)
- Pattern C: working zone ≤ 120k, total ≤ 190k (per agent)

## Bước 5 — Output report (format BẮT BUỘC)

```
## Codebase Analysis
- Total LOC:   <số> lines across <số> files     ← "N/A (greenfield)" nếu skip Bước 1
- Languages:   <list>                            ← "N/A (greenfield)" nếu skip
- Indicators:  Git ✓ | Tests ✓ | ...             ← "N/A (greenfield)" nếu skip Bước 2
- Manifests:   <list>                            ← chỉ brownfield

## Classification
- Size:        <small/medium/large> hoặc "n/a (greenfield)"
- Type:        <greenfield/brownfield/feature/bugfix>
- Team:        <số> developers
- Deployment:  <Greenfield post-copy | Brownfield clean | Brownfield with collision>

## Recommended Pattern: <A/B/C> — <name>
Why: <1-2 dòng giải thích, dựa vào size + team + deployment>

## Token Budget
- Working zone:  ≤ <100k|120k|120k> tokens (rotate ở đây)
- Total max:    ≤ <120k|140k|190k> tokens
```

### Bước 5.5 — Log metrics event (BẮT BUỘC, fail-open)

Sau khi output report, log classify event vào events.jsonl:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.claude/hooks/python')))
from metrics_writer import write_event
write_event('classify', {
    'pattern_recommended': '<A|B|C>',
    'loc': <total_loc>,
    'team_size': <team_size>,
    'deployment_context': '<greenfield_post_copy|brownfield_clean|brownfield_collision>',
    'existing_state': <true|false>,
})
```

Event log cho phép `/metrics` track classify frequency + deployment context distribution.

### Bước 5.7 — Auto-setup task tracker + Beads CLI (BẮT BUỘC cho MỌI pattern)

Sau khi output report, chạy auto-setup script:

```bash
python .claude/hooks/python/post-classify-setup.py <pattern> <team_size>
```

- `<pattern>`: A, B, hoặc C (kết quả Bước 4)
- `<team_size>`: số developer (kết quả Q2)

Script tự động (cho MỌI pattern A/B/C):
1. Tạo `.claude/memory/task_tracker.yaml` nếu chưa có
2. Tạo `.claude/memory/agent_mail.yaml` nếu multi-dev hoặc Pattern C
3. Detect Beads CLI → init nếu có, recommend nếu team >= 3
4. Verify hooks trong `settings.json` (task-summary, mail-summary, session-end)
5. Chạy health check `/beads-doctor`

Hiển thị output cho user. Script fail-open (không block classify flow).

### Next Steps — BRANCH theo deployment context

#### Case A — Greenfield post-copy (project mới, chưa có source)

User sẽ tự fill 2 file core khi bắt đầu code thật. Claude KHÔNG auto-fill (chưa có data nguồn để đọc).

1. Append overlay vào CLAUDE.md:
   type ..\config-harness-for-claude-code\patterns\pattern-<a|b|c>-*\CLAUDE.md.overlay >> CLAUDE.md
2. **User tự fill** `docs\ai\PROJECT_MAP.md` với tech stack DỰ KIẾN (sẽ update khi code thật xuất hiện).
3. **User tự fill** `.claude\memory\schema_snapshot.yaml` với external API/DB sẽ dùng (Stripe, Postgres, etc.).
4. Bắt đầu code → Phase 0 sẽ tự enforce pipeline.

#### Case B — Brownfield clean (source có sẵn, không collision CLAUDE.md)

**Auto-scaffold** — Claude THỰC HIỆN, không chỉ hướng dẫn:

1. Append overlay vào CLAUDE.md (1 lệnh):
   type ..\config-harness-for-claude-code\patterns\pattern-<a|b|c>-*\CLAUDE.md.overlay >> CLAUDE.md

2. **AUTO-FILL/UPDATE `docs\ai\PROJECT_MAP.md`** — phụ thuộc `existing_map` (set ở Bước 0.7):
   - `existing_map=false` (file chưa có) → tạo mới từ manifest đã detect ở Bước 2.
   - `existing_map=true` (đã có) → **KHÔNG** rewrite. Chỉ append section thiếu (mới detect được manifest/framework chưa có trong file cũ). Show diff cụ thể.
   
   Khi tạo mới, Claude tự đọc manifest đã detect ở Bước 2 (`manifest_files`) và viết file:
   - Node: parse `package.json` → `scripts.build/test/lint`, `dependencies` (top-level), `devDependencies`
   - .NET: parse `*.csproj` → `<TargetFramework>`, `<PackageReference>` chính
   - Java: parse `pom.xml` → `<dependencies>` chính, `mvn` build cmd; `build.gradle` → tasks
   - Go: parse `go.mod` → module path + Go version + main deps
   - Python: parse `pyproject.toml`/`requirements.txt` → deps + entry point
   → Output đầy đủ section: tech stack, build/test/lint cmd, framework, deploy target.

3. **AUTO-FILL/MERGE `.claude\memory\schema_snapshot.yaml`** — phụ thuộc `existing_schema`:
   - `existing_schema=false` → tạo mới.
   - `existing_schema=true` → **KHÔNG** rewrite. Merge: append entry mới detect, KHÔNG xóa entry cũ (kể cả khi không tìm thấy lại — có thể là code đã refactor mà schema_snapshot ghi nhận thông tin nguồn ngoài).
   
   Khi tạo mới, Claude scan + extract:
   - Glob `migrations/**/*.sql`, `db/**/*.sql`, `schema.rb`, `**/*.migration.ts` → extract `CREATE TABLE` + columns
   - Glob `openapi.yaml`, `swagger.json`, `**/api-spec.*` → extract endpoint + schema
   - Grep external client code (`src/clients/`, `services/external/`) → tìm `fetch(...)`, `axios.*(...)`, `httpx.*(...)` để liệt kê external API đang gọi
   → Output structure: `external_apis:`, `db_tables:`, mỗi entry có `fields`, `nullability`, `notes`.

4. **AUTO-SEED/UPDATE `.claude\memory\project_state.yaml`** — phụ thuộc `existing_state`:
   - `existing_state=false` → seed mới từ scratch.
   - `existing_state=true` → **PRESERVE** `decisions[]`, `known_gotchas[]` cũ (KHÔNG xóa). Chỉ update: `last_classified_at`, `loc_at_classification`, `next_review_threshold`. `pattern` chỉ override nếu LOC vượt rõ threshold cũ + user xác nhận.
   
   Khi seed mới, Claude scan:
   - Grep `TODO|FIXME|HACK|XXX` trong source → `pending_tasks`
   - Read `README.md`, `CHANGELOG.md`, `docs/ONBOARDING.md` (nếu tồn tại) → extract `known_gotchas`
   - Read `docs/adr/*.md`, `docs/decisions/*.md` (nếu tồn tại) → `decisions`
   - Set: `pattern`, `classified_at`, `loc_at_classification`, `next_review_threshold`, `team_size`

5. Sau auto-fill → **show diff cho user verify**, KHÔNG silent commit. User có thể edit thêm trước khi start coding.

6. **Stamp drift baseline** — sau khi user verify diff (step 5) thành công:

   ```
   python .claude/hooks/python/drift_check.py --baseline --source classify
   ```

   Stamp HEAD hiện tại vào `.claude/memory/_sync_state.yaml` làm sync point. Đây là baseline mà `drift_check.py` so sánh ở SessionStart/Stop sau này — nếu watched_paths thay đổi sau commit này, dev session sau sẽ thấy drift warning.

   - Lệnh fail-open: nếu repo chưa init git, output `not a git repo or HEAD missing` — bỏ qua, không block.
   - Nếu `_sync_state.yaml` chưa tồn tại (project pre-M6): copy template từ `core/.claude/memory/_sync_state.yaml` của framework trước.

   > 💡 **Why bước này tách khỏi step 4?**: project_state.yaml ghi *what* (pattern, decisions). _sync_state.yaml ghi *when relative to code* (commit pointer). Hai concern khác nhau, hai file khác nhau, nhưng cả hai đều stamp ở /classify để dev B clone về đúng 1 sync point.

#### Case C — Brownfield with collision (CLAUDE_OLD.md hoặc CLAUDE.md foreign)

**Merge step TRƯỚC, sau đó auto-scaffold như Case B:**

1. **Merge rule cũ:**
   - Nếu `CLAUDE_OLD.md` exists: đọc → rule project-specific cũ → thêm vào "Reference Map" của CLAUDE.md framework HOẶC tạo `docs\ai\CODING_RULES.md` để hold convention riêng.
   - Nếu `CLAUDE.md` foreign (chưa rename): backup `ren CLAUDE.md CLAUDE_OLD.md` → re-copy framework CLAUDE.md → quay lại bước 1.
2. Xóa `CLAUDE_OLD.md` sau khi merge xong (tránh confusion).
3. Tiếp tục như Case B từ bước 1 (overlay → auto-fill PROJECT_MAP → schema_snapshot → project_state).

## Threshold gợi ý cho `next_review_threshold`

- Pattern A (≤10k):   threshold = 12000   (re-classify khi gần 10k để chuẩn bị B)
- Pattern B (≤100k):  threshold = 120000
- Pattern C (>100k):  threshold = không cần (đã top tier)

## Anti-pattern khi chạy /classify

- ❌ Đoán LOC mà không chạy command thật
- ❌ Skip Bước 0 (deployment context) — Next Steps sẽ sai → user bối rối "phải làm gì tiếp"
- ❌ Skip Bước 0.5 (branch flow) — đọc codebase trên greenfield = waste 5–10k token vô ích
- ❌ Chạy Bước 1+2 trên Greenfield post-copy — measure framework files thay vì project code
- ❌ Skip Bước 3 (hỏi user) — team_size + project_type ảnh hưởng pattern
- ❌ Brownfield mà không auto-scaffold 3 file core — user phải tự fill thủ công, dễ thiếu sót
- ❌ Auto-fill xong silent commit — phải show diff cho user verify trước
- ❌ Pattern A cho team ≥ 5 dev (thiếu shared state)
- ❌ Đề xuất `git clone source` SAU khi đã layer framework — overwrite hoặc destination conflict (xem QUICK_START Path 2 cho thứ tự đúng)
- ❌ **Regenerate memory file dù đã tồn tại + non-empty** — mất `decisions[]`, `known_gotchas[]` cũ → context drift giữa team. Phải skip Bước 0.7 → load preserve.
