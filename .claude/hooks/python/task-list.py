#!/usr/bin/env python3
"""CLI: /task-list — Show all tasks grouped by status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, remaining_summary, status_icon,
                             compute_ready)

    data = load_tracker()
    tasks = data.get('tasks', [])

    if not tasks:
        print("Task tracker rỗng. Dùng `/task-add <title>` để tạo task.")
        sys.exit(0)

    # Group by status
    groups = {'in_progress': [], 'open': [], 'blocked': [], 'closed': []}
    for t in tasks:
        s = t.get('status', 'open')
        if s in groups:
            groups[s].append(t)
        else:
            groups.setdefault('other', []).append(t)

    # Compute ready set for open tasks
    ready_ids = {t['id'] for t in compute_ready(tasks)}

    total = len(tasks)
    print(f"## Task Tracker — {total} tasks\n")

    # In Progress
    ip = groups['in_progress']
    if ip:
        print(f"### {status_icon('in_progress')} In Progress ({len(ip)})")
        print("| ID | Title | Assignee | Notes |")
        print("|----|-------|----------|-------|")
        for t in ip:
            notes_count = len(t.get('notes', []))
            assignee = t.get('assignee') or '-'
            print(f"| {t['id']} | {t['title']} | {assignee} | {notes_count} notes |")
        print()

    # Open
    op = groups['open']
    if op:
        print(f"### {status_icon('open')} Open ({len(op)})")
        print("| ID | Title | Blocked by | Ready? |")
        print("|----|-------|-----------|--------|")
        for t in op:
            blocked_by = ', '.join(t.get('blocked_by', [])) or '-'
            ready = 'yes' if t['id'] in ready_ids else 'no (waiting)'
            print(f"| {t['id']} | {t['title']} | {blocked_by} | {ready} |")
        print()

    # Blocked
    bl = groups['blocked']
    if bl:
        print(f"### {status_icon('blocked')} Blocked ({len(bl)})")
        print("| ID | Title | Blocked by | Last note |")
        print("|----|-------|-----------|-----------|")
        for t in bl:
            blocked_by = ', '.join(t.get('blocked_by', [])) or '-'
            notes = t.get('notes', [])
            last_note = notes[-1].get('text', '')[:50] if notes else '-'
            print(f"| {t['id']} | {t['title']} | {blocked_by} | {last_note} |")
        print()

    # Closed
    cl = groups['closed']
    if cl:
        print(f"### {status_icon('closed')} Closed ({len(cl)})")
        print("| ID | Title | Closed at |")
        print("|----|-------|----------|")
        for t in cl:
            closed_at = t.get('updated_at', '-')[:10]
            print(f"| {t['id']} | {t['title']} | {closed_at} |")
        print()

    print(f"---\nSummary: {remaining_summary(tasks)}")
    print("→ Next ready: `/task-ready` | Add: `/task-add <title>` | Graph: `/task-graph`")

except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)

sys.exit(0)
