# Framework Metrics — Design

> **TL;DR**: append-only event log tai `.claude/metrics/events.jsonl` (gitignored). Hooks ghi event tu dong (fail-open). `/metrics` slash command in summary 7d/30d. Local-only mac dinh, team aggregate la opt-in.

## Why

Build framework roi ma khong co so lieu thi khong biet:
- Framework co giam hallucination thuc te khong?
- Rule co catch vi pham hay chi tao friction?
- Pipeline co waste context khong?
- Cho nao can cai thien uu tien?

-> Can observability layer **lightweight** (khong gui remote mac dinh, khong anh huong workflow).

## 7 metrics

| # | Metric | Source | "Tot" | "Can xem lai" |
|---|---|---|---|---|
| 1 | Sessions + token efficiency (avg final, % rotate) | `session_end` events | avg < 90k, rotate < 20% | rotate > 40% |
| 2 | HRS distribution (% GREEN/YELLOW/ORANGE/RED 7d) | `halluc_score` events | RED < 5%, GREEN > 70% | RED > 10% |
| 3 | Hook block rate (BLOCKER/session) | `hook_block` events | 0.5-2/session | 0 or > 5 |
| 4 | Phase 3 loop count (avg retries/verify) | `verify_done` + `loop_retry` events | < 1.5 | > 2.5 |
| 5 | Classify frequency (lan/thang) | `classify` events | match LOC growth | spike dot ngot |
| 6 | Schema staleness (days) | live mtime check | < 14d | > 30d |
| 7 | Auto-tuning recommendations | data-driven analysis | all green | actionable tips |

## Event schema

Moi event = 1 dong JSON trong `.claude/metrics/events.jsonl`:

```json
{
  "ts": 1746489600,
  "event": "session_end|halluc_score|hook_block|rotate|classify|task_done|loop_retry|verify_done|drift_nudge",
  "pattern": "A" | "B" | "C" | "?",
  "data": { ... }
}
```

Event-specific `data`:

| Event | data fields |
|---|---|
| `session_end` | `final_tokens`, `rotated`, `session_id` |
| `halluc_score` | `hrs`, `color`, `dominant`, `schema_blocked`, `tokens`, `token_source`, `files_count` |
| `hook_block` | `hook` (post-write-check / block-dangerous), `rule`, `file` hoac `command`, `severity` |
| `classify` | `pattern_recommended`, `loc`, `team_size`, `deployment_context`, `existing_state` |
| `rotate` | `tokens_at_rotate`, `session_summary_path` |
| `task_done` | `task`, `files_count`, `decisions_added`, `gotchas_added`, `drift_rebaselined` |
| `loop_retry` | `gate` (typecheck/lint/test/schema_check), `attempt`, `max_retry`, `resolved` |
| `verify_done` | `total_retries`, `gates_failed`, `escalated` |
| `drift_nudge` | `baseline`, `committed`, `uncommitted` |

## Collection mechanism

| Hook / Command | When | Source | Stack |
|---|---|---|---|
| `Stop` (settings.json) | Cuoi moi session | `session-end.py` | Python |
| `PreToolUse: Bash` | Block dangerous command | `block-dangerous.py/sh/js` | All 3 |
| `PostToolUse: Edit\|Write` | Block code violation | `post-write-check.py/sh/js` | All 3 |
| `/halluc-score` | Every run (manual trigger) | `halluc-score.py` | Python |
| `/classify` | When user runs | Claude calls `metrics_writer.write_event()` | In-prompt |
| `/rotate` | When user rotates | Claude calls `metrics_writer.write_event()` | In-prompt |
| `/done` | Task completion | Claude calls `metrics_writer.write_event()` | In-prompt |
| `/verify` | Phase 3 loop | Claude calls `metrics_writer.write_event()` | In-prompt |

**Fail-open invariant**: `metrics_writer.write_event()` wrap toan bo trong try/except — exception khong bao gio raise. Mot event mat = mat 1 dong metric, KHONG block hook hoac session.

**Auto-prune**: khi `events.jsonl` > 100 MB, `metrics_writer` tu giu lai 90 ngay gan nhat, xoa cu hon. 100 MB ~ ~500k events ~ ~2.7 nam o 50 events/day.

## Surface

### `/metrics` slash command

```bash
python .claude/hooks/python/metrics-summary.py --days 7
```

Output:
```
══════════════════════════════════════════════════════════════
  FRAMEWORK METRICS — last 7 days  [142 events, pattern B]
══════════════════════════════════════════════════════════════

  [1] Sessions:           18
      Avg final tokens:    47,200  🟢  (target < 90k)
      Rotate rate (>=120k):  11.1%  🟢  (target < 20%)

  [2] HRS distribution (12 runs):
      🟢 GREEN     8 ( 66.7%) █████████████
      🟡 YELLOW    3 ( 25.0%) █████
      🟠 ORANGE    1 (  8.3%) █
      🔴 RED       0 (  0.0%)

  [3] Hook blocks:
      Per session:         1.22   🟢  (target 0.5-2)
      post-write-check     18
      block-dangerous       4

  [4] Phase 3 loops:
      Verify runs:            8
      Avg retries/verify:   1.2   🟢  (target < 1.5)
      Total loop retries:    10
      By gate:
        typecheck              5
        lint                   3
        test                   2

  [5] Classify runs:      2

  [6] Schema staleness:   8d  🟢  (target < 14d)

  [7] Auto-tuning: all metrics within targets 🟢
```

### Statusline

Statusline displays (fast path < 50ms):
- Token count: `[A] 48k+24k/120k 🟢`
- Context %: `ctx 42%`
- HRS badge: `HRS 0.28 🟢` (from pre-computed cache `.claude/cache/hrs_7d.json`, written by `/halluc-score`)
- Schema age: `schema 8d`
- Session duration, model name, cwd

### HRS cache

`/halluc-score` writes `.claude/cache/hrs_7d.json` after each run:
```json
{"avg_hrs": 0.28, "dominant_color": "GREEN", "dominant_signal": "cite_coverage", "ts": 1746489600}
```
Statusline reads this file — no events.jsonl parsing needed.

## Token tracking

Statusline reads `context_window.used_percentage` from Claude Code stdin and estimates total tokens as `used_percentage / 100 * max_tokens`. This is the only reliable token data available from Claude Code's statusline API.

**Note**: Claude Code does NOT provide per-type token breakdown (input, cache_read, cache_creation, output) in its statusline stdin. These fields exist in the Anthropic Messages API response but are not forwarded to statusline scripts. Token tracking is limited to total context usage.

### Data flow

```
Claude Code API response (context_window.used_percentage)
    │
    ├─► statusline.py
    │     ├─ Display: [A] 48k+24k/120k 🟢 · ctx 42% · HRS 0.28 🟢
    │     └─ Persist: .claude/cache/last_tokens.json
    │           {tokens, baseline, working, session_start, ts}
    │
    ├─► session-end.py (reads last_tokens.json at session close)
    │     └─ Write event: session_end → events.jsonl
    │           {final_tokens, rotated, session_id}
    │
    ├─► halluc-score.py (reads last_tokens.json on /halluc-score)
    │     ├─ Uses tokens for context_drift signal
    │     └─ Writes .claude/cache/hrs_7d.json for statusline badge
    │
    └─► metrics-summary.py (reads events.jsonl on /metrics)
          └─ Aggregates: avg tokens, rotate rate, auto-tuning
```

## Auto-writeback system (M6-MR3)

### memory_writer.py

Schema-guarded write engine for `project_state.yaml`:

| Function | Purpose |
|---|---|
| `append_change(task, files)` | Add completed task to `completed_tasks[]` |
| `append_decision(decision, reason, impact)` | Add non-obvious decision (dedup by text) |
| `append_gotcha(discovery, workaround, files)` | Add gotcha (dedup by text) |
| `touch_last_updated()` | Bump `session_count` |
| `remove_pending(description)` | Remove completed pending task |

**Safety**: backup `.bak` -> mutate in-memory -> verify `old_ids ⊆ new_ids` -> write -> re-parse -> rollback on failure.

### `/done` slash command

6-step task completion flow:
1. Gather git changes
2. Ask user for 1-line task summary -> `append_change()`
3. Auto-detect decisions -> `append_decision()`
4. Auto-detect gotchas -> `append_gotcha()`
5. Re-baseline drift: `drift_check.py --baseline --source done`
6. Log `task_done` event + report to user

## Privacy + storage

- **Local-only mac dinh**: `events.jsonl` ghi vao `.claude/metrics/`, gitignored.
- **PII risk**: events co `file_path` (post-write-check) va `command` (block-dangerous). Neu sensitive -> user redact truoc khi share.
- **Storage**: ~50 events/day x 200 bytes = 10 KB/day = 3.6 MB/year. Auto-prune khi > 100 MB (giu 90 ngay).

## Team aggregation (opt-in)

Manual workflow neu team muon so sanh:
1. User chay `python .claude/hooks/python/metrics-summary.py --json --days 30 > my-metrics.json`
2. Redact path/command neu can (`jq`)
3. Push len shared dashboard (Grafana, custom internal)

Framework KHONG ship remote telemetry — compliance-safe (PCI/SOC2).

## Roadmap

- **P1 (done)**: events.jsonl + 4 events + `/metrics` summary + Stop hook + Python parity
- **P2 (done)**: instrument `/classify` + `/rotate` events, statusline HRS-7d badge, auto-prune log (100MB -> keep 90d)
- **P3 (done)**: Phase 3 loop count via `loop_retry` + `verify_done` events, metric [4] instrumented
- **P4 (done)**: Bash + Node parity for `metrics_writer` (all 3 stacks log events)
- **M6-MR3 (done)**: Auto-writeback engine (`memory_writer.py`) + `/done` command + `task_done` events
- **P-removed**: Token breakdown (input/cache_read/cache_create/output) and cost estimation — removed because Claude Code statusline API does not provide per-type breakdown data. Only `used_percentage` is available. If Claude Code adds breakdown support in the future, these can be re-enabled.

## Lien quan

- `.claude/hooks/python/metrics_writer.py` — shared writer (Python, with auto-prune)
- `.claude/hooks/bash/metrics-writer.sh` — shared writer (Bash)
- `.claude/hooks/nodejs/metrics-writer.js` — shared writer (Node.js)
- `.claude/hooks/python/metrics-summary.py` — summarizer CLI (7 metrics)
- `.claude/hooks/python/session-end.py` — session close hook
- `.claude/hooks/python/halluc-score.py` — HRS scorer (HRS cache)
- `.claude/hooks/python/memory_writer.py` — schema-guarded write engine for project_state.yaml
- `.claude/statusline/statusline.py` — realtime display (token bar, HRS badge)
- `.claude/cache/last_tokens.json` — single source of truth for current session tokens
- `.claude/cache/hrs_7d.json` — pre-computed HRS for statusline badge
- `.claude/config/thresholds.json` — runtime thresholds config
- `.claude/commands/metrics.md` — /metrics slash command spec
- `.claude/commands/done.md` — /done slash command spec
- `.claude/commands/verify.md` — /verify slash command spec (loop instrumentation)
- `.claude/metrics/events.jsonl` — event log (gitignored)
