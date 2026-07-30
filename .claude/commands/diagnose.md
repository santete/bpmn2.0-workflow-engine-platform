---
name: diagnose
description: Debug framework issue — collect state + classify symptom + propose root cause (no auto-patch)
---

# /diagnose — Framework debug helper

Khi dev báo "có vấn đề" với framework (hook không fire / AI không follow rule / HRS sai / pattern misclassify / ...), `/diagnose` gom diagnostic state, classify symptom, và đề xuất root cause + fix.

> **NGUYÊN TẮC**: KHÔNG auto-patch. Output spec để dev review trước khi apply. Lý do: framework state nhạy cảm (memory + settings + hooks), patch nhầm có thể làm worse.

## Cú pháp

```
/diagnose                      # interactive — Claude hỏi symptom
/diagnose "<symptom mô tả>"   # one-shot với context
```

## Cách Claude phải execute

### Bước 1 — Collect state (BẮT BUỘC)

Run diagnostic script từ `core/docs/TROUBLESHOOTING.md` Phần 2:

```bash
{
  echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  bash --version | head -1
  python3 --version 2>/dev/null || python --version 2>/dev/null || echo "python: MISSING"
  python3 -c 'import yaml; print("pyyaml:", yaml.__version__)' 2>/dev/null \
    || python -c 'import yaml; print("pyyaml:", yaml.__version__)' 2>/dev/null \
    || echo "pyyaml: MISSING"
  node --version 2>/dev/null || echo "node: MISSING"
  jq --version 2>/dev/null || echo "jq: MISSING"
  echo "---"
  cat .claude/settings.json 2>/dev/null | head -40
  echo "---"
  grep -E 'pattern|loc_at_classification|consecutive_failures|next_review_threshold' \
    .claude/memory/project_state.yaml 2>/dev/null
  echo "---"
  ls -la .claude/memory/schema_snapshot.yaml 2>/dev/null
  ls .claude/hooks/python/ .claude/hooks/nodejs/ .claude/hooks/bash/ 2>/dev/null
} 2>&1
```

Đọc thêm (nếu liên quan symptom):
- `.claude/memory/project_state.yaml` (full)
- `.claude/memory/schema_snapshot.yaml` (full)
- `CLAUDE.md` Reference Map
- `core/docs/TROUBLESHOOTING.md` Phần 4 (cheatsheet)

### Bước 2 — Classify symptom

Dựa vào symptom hoặc keyword trong arg, route vào 1 trong 3 template:

| Symptom keyword                                      | Template            |
|------------------------------------------------------|---------------------|
| `hook` / `block` / `validate` / `pre-tool` / `post-tool` | **General debug**   |
| `rule` / `không theo` / `drift` / `not following` / `compliance` | **Rule not followed** |
| `halluc` / `hrs` / `red` / `green` / `false positive` / `false negative` | **HRS wrong**       |
| Khác (mơ hồ)                                         | Hỏi clarify trước   |

### Bước 3 — Apply template tương ứng

#### Template A — General debug

1. Diagnostic state đã collect → đối chiếu với "Common issues cheatsheet" (TROUBLESHOOTING.md Phần 4)
2. Identify likely root cause (top 2 candidates, ranked)
3. Output: root cause + file cần xem + fix direction (KHÔNG patch)

#### Template B — Rule not followed

1. Identify rule file dev đề cập (`docs/ai/<RULE>.md` hoặc team-specific)
2. Check 4 điểm:
   - `CLAUDE.md` Reference Map có entry cho rule file không?
   - File rule tồn tại + readable?
   - `project_state.yaml#hallucination_history` có pattern drift?
   - Rule đang ở **SOFT** (markdown) hay **HARD** (hook)?
3. Output:
   - SOFT layer → đề xuất upgrade lên HARD bằng extend `post-write-check.py` (concrete regex pattern)
   - HARD layer miss case → chỉ ra hook nào, regex nào cần tune

#### Template C — HRS sai

1. Run `python .claude/hooks/python/halluc-score.py --files <files> --tokens <n> --json`
   (hoặc bash/node tương ứng theo settings.json)
2. Đọc 7 signal individually → identify dominant
3. Cross-check:
   - Schema staleness: `ls -la .claude/memory/schema_snapshot.yaml` (mtime > 7d?)
   - Cite coverage: count cite-source markers (`file:line`, `schema#key`)
   - Confidence words: count "I think / probably / maybe"
4. Output:
   - False positive → tune threshold hoặc identify signal noise
   - False negative → schema_snapshot thiếu NOT_available entry, hoặc cite coverage trick

### Bước 4 — Output format (BẮT BUỘC)

```
🔍 DIAGNOSE: <one-line restatement of symptom>

📊 STATE
  Pattern: <A/B/C>  |  Stack: <python/node/bash>  |  Tokens: ~<n>k
  consecutive_failures: <n>  |  schema mtime: <Xd ago>
  Hooks present: <list> | Missing dep: <jq/node/...>

🎯 ROOT CAUSE (ranked)
  [1] <most likely cause> — Evidence: <state finding>
  [2] <secondary cause>   — Evidence: <state finding>

🛠 FIX DIRECTION (review trước khi apply)
  - <step 1, file:line nếu có>
  - <step 2>
  - <step 3>

⚠️ DO NOT auto-patch. Tao output spec để mày review.
   Confirm để tao apply fix [1], hoặc paste counter-evidence.
```

## Khi nào KHÔNG dùng /diagnose

- Bug code app (không phải framework state) → debug bình thường
- Câu hỏi general "framework hoạt động sao" → đọc README/QUICK_START
- User đã biết rõ root cause + chỉ cần apply → fix trực tiếp

## Tích hợp với pipeline

- **Loop Logic** — sau retry thứ 2 fail, Claude có thể recommend `/diagnose` thay vì `/halluc-score` nếu nghi framework state vấn đề (không chỉ hallucination)
- **Phase 0** — nếu Phase 0 fail (project_state.yaml corrupt), tự gợi ý `/diagnose`
- **Phase 5** — nếu sau session có `consecutive_failures >= 3`, append note "consider /diagnose next session"

## Liên quan

- `core/docs/TROUBLESHOOTING.md` — full debug guide (info location + cheatsheet + escalation)
- `.claude/memory/project_state.yaml` — framework state
- `.claude/settings.json` — hook stack config
- `/halluc-score` — chỉ HRS scoring (subset của `/diagnose` cho HRS-only case)
