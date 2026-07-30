#!/usr/bin/env python3
"""
WISC Audit Trail Query — search and display wisc_audit events.

Usage:
  python .claude/hooks/python/wisc-audit.py [--days 7] [--gate WRITE] [--action bypassed] [--json]

Filters:
  --days N       Show events from last N days (default: 7)
  --gate NAME    Filter by gate (WRITE, ISOLATE, SELECT, COMPRESS)
  --action NAME  Filter by action (gate_computed, gate_satisfied, gate_blocked, gate_bypassed, gates_reset)
  --json         Output as JSON array
"""
import argparse
import io
import json
import sys
import time
from pathlib import Path

# Windows fix
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def load_audit_events(log_path: Path, since_ts: int):
    if not log_path.exists():
        return []
    events = []
    with log_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if ev.get('event') != 'wisc_audit':
                    continue
                if ev.get('ts', 0) < since_ts:
                    continue
                events.append(ev)
            except (json.JSONDecodeError, ValueError):
                continue
    return events


def format_ts(ts):
    try:
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))
    except Exception:
        return str(ts)


ACTION_ICONS = {
    'gate_computed': '\u2699\ufe0f ',
    'gate_satisfied': '\u2705',
    'gate_blocked': '\u274c',
    'gate_bypassed': '\u26a0\ufe0f ',
    'gates_reset': '\U0001f504',
    'session_summary': '\U0001f4cb',
}


def main():
    ap = argparse.ArgumentParser(description='WISC Audit Trail Query')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--gate', type=str, default=None,
                    help='Filter by gate (WRITE, ISOLATE, SELECT, COMPRESS)')
    ap.add_argument('--action', type=str, default=None,
                    help='Filter by action (gate_computed, gate_satisfied, gate_blocked, gate_bypassed)')
    ap.add_argument('--json', action='store_true', help='Output as JSON')
    args = ap.parse_args()

    root = find_project_root()
    log_path = root / '.claude' / 'metrics' / 'events.jsonl'
    since_ts = int(time.time()) - args.days * 86400

    events = load_audit_events(log_path, since_ts)

    # Apply filters
    if args.gate:
        gate_filter = args.gate.upper()
        events = [e for e in events if e.get('data', {}).get('gate', '').upper() == gate_filter]
    if args.action:
        events = [e for e in events if e.get('data', {}).get('action', '') == args.action]

    if args.json:
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return

    D = '\u2500' * 58

    if not events:
        print(f"\n{D}")
        print(f"  WISC Audit Trail \u2014 last {args.days} days")
        print(D)
        filters = []
        if args.gate:
            filters.append(f"gate={args.gate}")
        if args.action:
            filters.append(f"action={args.action}")
        filter_str = f" (filters: {', '.join(filters)})" if filters else ""
        print(f"\n  No wisc_audit events found{filter_str}.")
        print(f"  Source: {log_path}\n")
        return

    print(f"\n{D}")
    print(f"  WISC Audit Trail \u2014 last {args.days} days ({len(events)} events)")
    print(D)

    for ev in events:
        ts = format_ts(ev.get('ts', 0))
        data = ev.get('data', {})
        action = data.get('action', '?')
        gate = data.get('gate', '?')
        icon = ACTION_ICONS.get(action, ' ')

        # Build detail string based on action type
        detail_parts = []
        if action == 'gate_computed':
            to_st = data.get('to_status', '?')
            detail_parts.append(to_st)
            artifact = data.get('artifact', '')
            if artifact:
                detail_parts.append(f"artifact={artifact}")
        elif action == 'gate_satisfied':
            by = data.get('satisfied_by', 'auto')
            artifact = data.get('artifact', '')
            detail_parts.append(f"by={by}")
            if artifact:
                detail_parts.append(f"artifact={artifact}")
        elif action == 'gate_blocked':
            detail = data.get('detail', '')
            if detail:
                detail_parts.append(detail[:60])
        elif action == 'gate_bypassed':
            reason = data.get('reason', '')
            approved = data.get('approved_by', '')
            if approved:
                detail_parts.append(f"by={approved}")
            if reason:
                detail_parts.append(f'"{reason[:50]}"')
        elif action == 'gates_reset':
            detail_parts.append('all gates cleared')

        task = data.get('task', '')
        if task and task != 'unknown':
            detail_parts.append(f"task={task}")

        detail_str = '  '.join(detail_parts)
        # Pad columns for alignment
        print(f"  {ts}  {icon} {gate:<10} {action:<18} {detail_str}")

    # Summary
    from collections import Counter
    actions = Counter(e.get('data', {}).get('action') for e in events)
    gates_seen = Counter(e.get('data', {}).get('gate') for e in events)

    print(f"\n  Summary:")
    action_parts = [f"{n} {a}" for a, n in actions.most_common()]
    print(f"    Actions: {', '.join(action_parts)}")
    gate_parts = [f"{n} {g}" for g, n in gates_seen.most_common() if g != '*']
    if gate_parts:
        print(f"    Gates:   {', '.join(gate_parts)}")

    # Highlight bypasses
    bypasses = [e for e in events if e.get('data', {}).get('action') == 'gate_bypassed']
    if bypasses:
        print(f"\n  \u26a0\ufe0f  Bypasses ({len(bypasses)}):")
        for bp in bypasses:
            d = bp.get('data', {})
            print(f"    {format_ts(bp.get('ts', 0))}  {d.get('gate', '?')}  "
                  f'"{d.get("reason", "?")[:60]}"  (approved: {d.get("approved_by", "?")})')

    print(f"\n  Source: {log_path}")
    print(f"{D}\n")


if __name__ == '__main__':
    main()
