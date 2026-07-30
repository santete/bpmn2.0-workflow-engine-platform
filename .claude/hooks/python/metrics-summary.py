#!/usr/bin/env python3
"""
Summarize .claude/metrics/events.jsonl → 7 framework metrics + auto-tuning.

Usage:
  python .claude/hooks/python/metrics-summary.py [--days 7] [--json] [--export csv|md]

Metrics:
  1. Sessions + token efficiency (avg final, % rotate)
  2. HRS distribution (% GREEN/YELLOW/ORANGE/RED)
  3. Hook block rate (BLOCKER/session)
  4. Phase 3 loop count
  5. Classify frequency
  6. Schema staleness
  7. Auto-tuning recommendations
  8. WISC compliance — gate pass/bypass/fail rates per session
"""
import argparse
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# Runtime thresholds (override via .claude/config/thresholds.json)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'config'))
    from thresholds import load as _load_thresholds
    _cfg = _load_thresholds()
    ROTATE_THRESHOLD = int(_cfg.get('rotate_threshold', 120_000))
    METRICS_TOK_WARN = int(_cfg.get('metrics_tok_warn', 90_000))
except Exception:
    ROTATE_THRESHOLD, METRICS_TOK_WARN = 120_000, 90_000


def find_project_root() -> Path:
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def load_events(path: Path, since_ts: int):
    if not path.exists():
        return []
    out = []
    try:
        with path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get('ts', 0) >= since_ts:
                        out.append(ev)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def schema_age_days(root: Path) -> int:
    try:
        p = root / '.claude' / 'memory' / 'schema_snapshot.yaml'
        if not p.exists():
            return -1
        return int((time.time() - p.stat().st_mtime) / 86400)
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--export', choices=['csv', 'md'], help='Export format: csv or md')
    args = ap.parse_args()

    root = find_project_root()
    log_path = root / '.claude' / 'metrics' / 'events.jsonl'
    since_ts = int(time.time()) - args.days * 86400
    events = load_events(log_path, since_ts)

    sessions = [e for e in events if e.get('event') == 'session_end']
    halluc_runs = [e for e in events if e.get('event') == 'halluc_score']
    blocks = [e for e in events if e.get('event') == 'hook_block']
    classify_runs = [e for e in events if e.get('event') == 'classify']
    verify_runs = [e for e in events if e.get('event') == 'verify_done']
    loop_retries = [e for e in events if e.get('event') == 'loop_retry']
    wisc_events = [e for e in events if e.get('event') == 'wisc_compliance']
    wisc_audit = [e for e in events if e.get('event') == 'wisc_audit']

    by_type = Counter(e.get('event') for e in events)
    hrs_colors = Counter(e.get('data', {}).get('color') for e in halluc_runs if e.get('data', {}).get('color'))
    blocks_by_hook = Counter(e.get('data', {}).get('hook') for e in blocks if e.get('data', {}).get('hook'))
    blocks_by_rule = Counter(e.get('data', {}).get('rule') for e in blocks if e.get('data', {}).get('rule'))

    tokens = [int(e.get('data', {}).get('final_tokens', 0)) for e in sessions]
    rotated_count = sum(1 for e in sessions if e.get('data', {}).get('rotated'))
    avg_tokens = (sum(tokens) / len(tokens)) if tokens else 0
    rotate_rate = (rotated_count / len(sessions) * 100) if sessions else 0
    block_per_session = (len(blocks) / len(sessions)) if sessions else 0

    # Phase 3 loop count (from verify_done + loop_retry events)
    verify_retries = [int(e.get('data', {}).get('total_retries', 0)) for e in verify_runs]
    avg_retries = (sum(verify_retries) / len(verify_retries)) if verify_retries else 0.0
    total_loop_retries = len(loop_retries)
    retries_by_gate = Counter(e.get('data', {}).get('gate') for e in loop_retries
                              if e.get('data', {}).get('gate'))
    escalated_count = sum(1 for e in verify_runs if e.get('data', {}).get('escalated'))

    schema_age = schema_age_days(root)
    pattern = '?'
    if events:
        pattern = events[-1].get('pattern', '?')

    if args.json:
        print(json.dumps({
            'window_days': args.days,
            'total_events': len(events),
            'pattern': pattern,
            'by_type': dict(by_type),
            'hrs_distribution': dict(hrs_colors),
            'sessions_count': len(sessions),
            'avg_final_tokens': round(avg_tokens),
            'rotate_rate_pct': round(rotate_rate, 1),
            'loop_count': {
                'verify_runs': len(verify_runs),
                'avg_retries_per_verify': round(avg_retries, 2),
                'total_loop_retries': total_loop_retries,
                'retries_by_gate': dict(retries_by_gate),
                'escalated_count': escalated_count,
            },
            'blocks_per_session': round(block_per_session, 2),
            'blocks_by_hook': dict(blocks_by_hook),
            'blocks_by_rule': dict(blocks_by_rule),
            'classify_runs': len(classify_runs),
            'schema_age_days': schema_age,
            'wisc_compliance': _wisc_summary(wisc_events),
            'log_path': str(log_path),
        }, ensure_ascii=False, indent=2))
        return

    D = '═' * 62

    if not events:
        print(f"\n{D}")
        print(f"  FRAMEWORK METRICS — last {args.days} days")
        print(D)
        print(f"\n  Empty event log. (path: {log_path})")
        print(f"  Hooks chưa fire trong window này. Cần:")
        print(f"    - Edit/Write file → post-write-check log block (nếu có violation)")
        print(f"    - End session → Stop hook log session_end")
        print(f"    - Run /halluc-score → log halluc_score event\n")
        return

    print(f"\n{D}")
    print(f"  FRAMEWORK METRICS — last {args.days} days  [{len(events)} events, pattern {pattern}]")
    print(D)

    # 1. Sessions + token efficiency
    rot_emoji = '🟢' if rotate_rate < 20 else ('🟡' if rotate_rate < 40 else '🔴')
    tok_emoji = '🟢' if avg_tokens < METRICS_TOK_WARN else ('🟡' if avg_tokens < ROTATE_THRESHOLD else '🔴')
    print(f"\n  [1] Sessions:           {len(sessions)}")
    print(f"      Avg final tokens:   {avg_tokens:>7,.0f}  {tok_emoji}  (target < {METRICS_TOK_WARN//1000}k)")
    print(f"      Rotate rate (≥{ROTATE_THRESHOLD//1000}k): {rotate_rate:>5.1f}%  {rot_emoji}  (target < 20%)")

    # 2. HRS distribution
    total_hrs = sum(hrs_colors.values())
    print(f"\n  [2] HRS distribution ({total_hrs} runs):")
    if total_hrs == 0:
        print(f"      (no /halluc-score runs in window)")
    else:
        for color in ('GREEN', 'YELLOW', 'ORANGE', 'RED'):
            n = hrs_colors.get(color, 0)
            pct = n / total_hrs * 100
            emoji = {'GREEN': '🟢', 'YELLOW': '🟡', 'ORANGE': '🟠', 'RED': '🔴'}[color]
            bar = '█' * int(pct / 5) if pct > 0 else ''
            print(f"      {emoji} {color:<7} {n:>3} ({pct:>5.1f}%) {bar}")
        red_pct = hrs_colors.get('RED', 0) / total_hrs * 100
        green_pct = hrs_colors.get('GREEN', 0) / total_hrs * 100
        if red_pct > 10:
            print(f"      🔴 RED rate {red_pct:.1f}% > 10% — hallucination chưa control")
        elif green_pct < 50:
            print(f"      🟡 GREEN rate {green_pct:.1f}% < 50% — verify thêm")

    # 3. Hook blocks
    blk_emoji = '🟢' if 0.5 <= block_per_session <= 2 else '🟡'
    print(f"\n  [3] Hook blocks:")
    print(f"      Per session:       {block_per_session:>6.2f}   {blk_emoji}  (target 0.5–2)")
    if block_per_session == 0:
        print(f"      ⚠️  Zero blocks — rules có thể vô dụng hoặc dev không touch hook category")
    elif block_per_session > 5:
        print(f"      🔴 > 5/session — false positive friction, review rule precision")
    if blocks_by_hook:
        for hook, n in blocks_by_hook.most_common():
            print(f"      {hook:<22} {n}")
    if blocks_by_rule:
        print(f"      Top rules:")
        for rule, n in blocks_by_rule.most_common(5):
            print(f"        {rule:<28} {n}")

    # 4. Phase 3 loop count
    print(f"\n  [4] Phase 3 loops:")
    if verify_runs:
        loop_emoji = '🟢' if avg_retries < 1.5 else ('🟡' if avg_retries < 2.5 else '🔴')
        print(f"      Verify runs:       {len(verify_runs):>6}")
        print(f"      Avg retries/verify:{avg_retries:>6.1f}   {loop_emoji}  (target < 1.5)")
        print(f"      Total loop retries:{total_loop_retries:>6}")
        if retries_by_gate:
            print(f"      By gate:")
            for gate, n in retries_by_gate.most_common():
                print(f"        {gate:<20} {n}")
        if escalated_count:
            print(f"      Escalated to user: {escalated_count}")
    else:
        print(f"      (no /verify runs in window — loop count tracked when /verify is used)")

    # 5. Classify frequency
    print(f"\n  [5] Classify runs:      {len(classify_runs)}")

    # 6. Schema staleness (live, not from events)
    if schema_age >= 0:
        sch_emoji = '🟢' if schema_age < 14 else ('🟡' if schema_age < 30 else '🔴')
        print(f"\n  [6] Schema staleness:   {schema_age}d  {sch_emoji}  (target < 14d)")

    # 7. Auto-tuning recommendations (data-driven, need ≥5 sessions)
    tuning = _auto_tuning(sessions, tokens, rotate_rate,
                          hrs_colors, avg_retries, verify_runs, schema_age,
                          wisc_audit)
    if tuning:
        print(f"\n  [7] Auto-tuning recommendations:")
        for t in tuning:
            print(f"      💡 {t}")
    elif len(sessions) >= 5:
        print(f"\n  [7] Auto-tuning: all metrics within targets 🟢")
    else:
        print(f"\n  [7] Auto-tuning: need ≥5 sessions for recommendations ({len(sessions)} so far)")

    # 8. WISC compliance
    ws = _wisc_summary(wisc_events)
    print(f"\n  [8] WISC compliance ({ws['total']} sessions tracked):")
    if ws['total'] == 0:
        print(f"       (no wisc_compliance events — run /classify-task + wisc-state.py to enable)")
    else:
        pass_pct = ws['all_passed'] / ws['total'] * 100
        wisc_emoji = '\U0001f7e2' if pass_pct >= 80 else ('\U0001f7e1' if pass_pct >= 50 else '\U0001f534')
        print(f"       All gates passed:  {ws['all_passed']:>4} / {ws['total']}  ({pass_pct:>5.1f}%)  {wisc_emoji}")
        if ws['bypass_sessions'] > 0:
            print(f"       Sessions w/bypass: {ws['bypass_sessions']:>4} / {ws['total']}  ({ws['bypass_sessions']/ws['total']*100:>5.1f}%)")
        if ws['fail_sessions'] > 0:
            print(f"       Sessions w/fail:   {ws['fail_sessions']:>4} / {ws['total']}  ({ws['fail_sessions']/ws['total']*100:>5.1f}%)  \U0001f534")
        if ws['gate_stats']:
            print(f"       Per gate:")
            for gate, stats in ws['gate_stats'].items():
                counts = ', '.join(f"{st}={n}" for st, n in sorted(stats.items()) if n > 0)
                print(f"         {gate:<10} {counts}")

    print(f"\n  Source: {log_path.relative_to(root) if log_path.is_relative_to(root) else log_path}")
    print(f"{D}\n")

    # Export if requested
    if args.export:
        _export(args.export, root, args.days, sessions, tokens, rotate_rate,
                avg_tokens, hrs_colors, schema_age, block_per_session, tuning)


def _wisc_summary(wisc_events):
    """Aggregate wisc_compliance events into summary stats."""
    total = len(wisc_events)
    if total == 0:
        return {'total': 0, 'all_passed': 0, 'bypass_sessions': 0,
                'fail_sessions': 0, 'gate_stats': {}}

    all_passed = sum(1 for e in wisc_events if e.get('data', {}).get('all_passed'))
    bypass_sessions = sum(1 for e in wisc_events if e.get('data', {}).get('bypass_count', 0) > 0)
    fail_sessions = sum(1 for e in wisc_events if e.get('data', {}).get('fail_count', 0) > 0)

    gate_stats = {}
    for gate in ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS'):
        stats = Counter()
        for e in wisc_events:
            st = e.get('data', {}).get(gate, 'inactive')
            stats[st] += 1
        gate_stats[gate] = dict(stats)

    return {
        'total': total,
        'all_passed': all_passed,
        'bypass_sessions': bypass_sessions,
        'fail_sessions': fail_sessions,
        'gate_stats': gate_stats,
    }


def _auto_tuning(sessions, tokens, rotate_rate,
                 hrs_colors, avg_retries, verify_runs, schema_age,
                 wisc_audit=None):
    """Generate data-driven config suggestions based on collected metrics."""
    tips = []
    n = len(sessions)
    if n < 5:
        return tips

    # Rotate threshold tuning
    if tokens:
        p90_tok = sorted(tokens)[int(n * 0.9)] if n >= 10 else max(tokens)
        p50_tok = sorted(tokens)[n // 2]
        if rotate_rate < 5 and p90_tok < 90_000:
            tips.append(f"Rotate rate {rotate_rate:.0f}% very low, P90={p90_tok//1000}k — "
                        f"consider lowering rotate_threshold to {max(80_000, p90_tok + 10_000)//1000}k "
                        f"for earlier quality cutoff")
        elif rotate_rate > 60:
            tips.append(f"Rotate rate {rotate_rate:.0f}% very high — sessions hit ceiling too often. "
                        f"Break tasks into smaller units or increase rotate_threshold if quality is acceptable")

    # HRS rebalancing
    total_hrs = sum(hrs_colors.values())
    if total_hrs >= 5:
        red_pct = hrs_colors.get('RED', 0) / total_hrs * 100
        green_pct = hrs_colors.get('GREEN', 0) / total_hrs * 100
        if red_pct > 20:
            tips.append(f"HRS RED rate {red_pct:.0f}% — review hallucination patterns. "
                        f"Consider increasing schema_match weight in hrs_weights")
        elif green_pct > 90:
            tips.append(f"HRS GREEN rate {green_pct:.0f}% — scoring may be too lenient. "
                        f"Consider raising threshold or tightening weights")

    # Schema staleness
    if schema_age > 30:
        tips.append(f"Schema {schema_age}d old — run /schema-check to refresh ground truth")
    elif schema_age > 14:
        tips.append(f"Schema {schema_age}d — approaching staleness, schedule refresh")

    # Loop efficiency
    if verify_runs and avg_retries > 2.5:
        tips.append(f"Avg retries {avg_retries:.1f} > 2.5 — review typecheck/lint config, "
                    f"may need stricter Phase 2 checks before verify")

    # WISC governance feedback (from wisc_audit events)
    if wisc_audit and len(wisc_audit) >= 5:
        wa = wisc_audit
        bypasses = [e for e in wa if e.get('data', {}).get('action') == 'gate_bypassed']
        blocks_w = [e for e in wa if e.get('data', {}).get('action') == 'gate_blocked']
        satisfies = [e for e in wa if e.get('data', {}).get('action') == 'gate_satisfied']

        for gate in ('WRITE', 'ISOLATE', 'COMPRESS'):
            gate_bypasses = [e for e in bypasses if e.get('data', {}).get('gate') == gate]
            gate_computes = [e for e in wa
                             if e.get('data', {}).get('action') == 'gate_computed'
                             and e.get('data', {}).get('gate') == gate
                             and e.get('data', {}).get('to_status') == 'required']
            if gate_computes and len(gate_bypasses) > 0:
                bypass_rate = len(gate_bypasses) / len(gate_computes) * 100
                if bypass_rate > 60:
                    tips.append(
                        f"WISC {gate} bypass rate {bypass_rate:.0f}% — "
                        f"review D{'5' if gate == 'WRITE' else '6'} classification accuracy")

        if blocks_w and n > 0:
            block_rate = len(blocks_w) / n * 100
            if block_rate > 40:
                gate_blk = Counter(e.get('data', {}).get('gate') for e in blocks_w)
                top = gate_blk.most_common(1)[0] if gate_blk else ('?', 0)
                tips.append(
                    f"WISC block rate {block_rate:.0f}% — top: {top[0]} ({top[1]}x)")

    return tips


def _export(fmt, root, days, sessions, tokens, rotate_rate, avg_tokens,
            hrs_colors, schema_age, block_per_session, tuning):
    """Export metrics as CSV or Markdown report."""
    export_dir = root / '.claude' / 'metrics'
    export_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    date_str = datetime.now().strftime('%Y-%m-%d')

    if fmt == 'csv':
        csv_path = export_dir / f'metrics_{date_str}.csv'
        lines = [
            'metric,value,target,status',
            f'sessions,{len(sessions)},,',
            f'avg_final_tokens,{avg_tokens:.0f},<90000,{"OK" if avg_tokens < 90000 else "WARN"}',
            f'rotate_rate_pct,{rotate_rate:.1f},<20,{"OK" if rotate_rate < 20 else "WARN"}',
            f'schema_age_days,{schema_age},<14,{"OK" if schema_age < 14 else "WARN"}',
            f'blocks_per_session,{block_per_session:.2f},0.5-2,{"OK" if 0.5 <= block_per_session <= 2 else "WARN"}',
        ]
        total_hrs = sum(hrs_colors.values())
        for color in ('GREEN', 'YELLOW', 'ORANGE', 'RED'):
            n = hrs_colors.get(color, 0)
            pct = n / total_hrs * 100 if total_hrs > 0 else 0
            lines.append(f'hrs_{color.lower()}_pct,{pct:.1f},,')
        csv_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f"\n  📊 Exported CSV: {csv_path.relative_to(root)}")

    elif fmt == 'md':
        md_path = export_dir / f'report_{date_str}.md'
        total_hrs = sum(hrs_colors.values())
        lines = [
            f'# Framework Metrics Report — {date_str}',
            f'',
            f'**Window:** {days} days | **Sessions:** {len(sessions)}',
            f'',
            f'## Summary',
            f'',
            f'| Metric | Value | Target | Status |',
            f'|--------|-------|--------|--------|',
            f'| Avg final tokens | {avg_tokens:,.0f} | < 90k | {"✅" if avg_tokens < 90000 else "⚠️"} |',
            f'| Rotate rate | {rotate_rate:.1f}% | < 20% | {"✅" if rotate_rate < 20 else "⚠️"} |',
            f'| Schema age | {schema_age}d | < 14d | {"✅" if schema_age < 14 else "⚠️"} |',
            f'| Blocks/session | {block_per_session:.2f} | 0.5–2 | {"✅" if 0.5 <= block_per_session <= 2 else "⚠️"} |',
        ]
        if total_hrs > 0:
            lines += [
                f'',
                f'## HRS Distribution',
                f'',
                f'| Color | Count | % |',
                f'|-------|-------|---|',
            ]
            for color in ('GREEN', 'YELLOW', 'ORANGE', 'RED'):
                n = hrs_colors.get(color, 0)
                pct = n / total_hrs * 100
                lines.append(f'| {color} | {n} | {pct:.1f}% |')
        if tuning:
            lines += [f'', f'## Auto-tuning Recommendations', f'']
            for t in tuning:
                lines.append(f'- {t}')
        lines.append(f'\n---\n*Generated by framework metrics-summary*\n')
        md_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\n  📄 Exported Markdown: {md_path.relative_to(root)}")


if __name__ == '__main__':
    main()
