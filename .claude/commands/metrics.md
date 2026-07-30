---
description: Show framework health metrics (last 7d) — 7 metrics including HRS, token efficiency, auto-tuning
---

# /metrics — Framework health summary

Doc `.claude/metrics/events.jsonl` -> in 7 metric core. Local-only, khong gui remote.

## Cach Claude phai execute

Khi user go `/metrics`:

1. Run script:
   - Python: `python .claude/hooks/python/metrics-summary.py --days 7`

2. Show user output truc tiep.

3. Neu output bao "Empty event log" -> giai thich: hook chua fire trong window 7d. User can:
   - Edit/Write file de post-write-check log block (neu vi pham rule)
   - End session de Stop hook log session_end
   - Chay `/halluc-score` de log halluc_score event
   - Chay `/verify` de log loop_retry + verify_done events

4. Neu co signal do -> de xuat action cu the:
   - RED rate > 10% -> review hallucination rules
   - Rotate rate > 40% -> review eager loads, context management
   - Avg retries > 2.5 -> review code quality, typecheck config
   - Schema staleness > 30d -> run /schema-check

## Flags

```
--days N          Window size (default 7)
--json            JSON output cho parser khac
--export csv      Export metrics ra .claude/metrics/metrics_YYYY-MM-DD.csv
--export md       Export metrics ra .claude/metrics/report_YYYY-MM-DD.md
```

## 7 Metrics

| # | Metric | "Tot" | "Can xem lai" |
|---|---|---|---|
| 1 | Sessions + token efficiency | avg < 90k, rotate < 20% | avg > 120k, rotate > 40% |
| 2 | HRS distribution | RED < 5%, GREEN > 70% | RED > 10% |
| 3 | Hook blocks/session | 0.5-2 | 0 or > 5 |
| 4 | Phase 3 loop count | avg retries < 1.5 | > 2.5 |
| 5 | Classify frequency | match LOC growth | spike |
| 6 | Schema staleness | < 14d | > 30d |
| 7 | Auto-tuning | data-driven suggestions | need >=5 sessions |

## Lien quan

- `core/docs/METRICS.md` — design doc + collection mechanism
- `.claude/hooks/python/metrics_writer.py` — append-only writer (fail-open, auto-prune)
- `.claude/hooks/python/session-end.py` — Stop hook
- `.claude/hooks/python/memory_writer.py` — auto-writeback engine
- `.claude/config/thresholds.json` — runtime thresholds
- `.claude/metrics/events.jsonl` — event log (gitignored)
