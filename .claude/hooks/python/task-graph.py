#!/usr/bin/env python3
"""CLI: /task-graph — Visualize task dependency DAG."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import load_tracker, status_icon

    mermaid_mode = '--mermaid' in sys.argv

    data = load_tracker()
    tasks = data.get('tasks', [])

    if not tasks:
        print("Task tracker rỗng.")
        sys.exit(0)

    task_map = {t['id']: t for t in tasks if isinstance(t, dict) and t.get('id')}

    # Find tasks with dependencies (roots = tasks that block others)
    has_deps = set()
    for t in tasks:
        for b in t.get('blocks', []):
            has_deps.add(t['id'])
            has_deps.add(b)
        for b in t.get('blocked_by', []):
            has_deps.add(t['id'])
            has_deps.add(b)

    standalone = [t for t in tasks if t['id'] not in has_deps]

    if mermaid_mode:
        # Mermaid diagram
        print("```mermaid")
        print("graph TD")
        for t in tasks:
            tid = t['id']
            label = f"{t.get('title', '?')} {status_icon(t.get('status', ''))}"
            safe_label = label.replace('"', "'")
            print(f'    {tid}["{safe_label}"]')
        for t in tasks:
            for blocked_id in t.get('blocks', []):
                print(f"    {t['id']} --> {blocked_id}")
        print("```")
    else:
        # Text tree
        print("## Task Dependency Graph\n")

        # Build tree from root tasks (those not blocked by anyone)
        roots = [t for t in tasks if not t.get('blocked_by', []) and t.get('blocks', [])]
        printed = set()

        def print_tree(task_id, indent=0):
            if task_id in printed:
                return
            printed.add(task_id)
            t = task_map.get(task_id)
            if not t:
                return
            icon = status_icon(t.get('status', ''))
            ready_tag = ''
            if t.get('status') == 'open' and not t.get('blocked_by', []):
                ready_tag = ' (READY)'
            prefix = '    ' * indent + ('└── blocks → ' if indent > 0 else '')
            print(f"{prefix}{t['id']} [{t.get('title', '?')}] {icon} {t.get('status', '')}{ready_tag}")
            for blocked_id in t.get('blocks', []):
                print_tree(blocked_id, indent + 1)

        for root in roots:
            print_tree(root['id'])

        # Tasks in dependency graph but not roots (may have been missed)
        for tid in has_deps:
            if tid not in printed:
                print_tree(tid)

        # Standalone tasks
        if standalone:
            print()
            for t in standalone:
                icon = status_icon(t.get('status', ''))
                ready_tag = ' (READY, no deps)' if t.get('status') == 'open' else ''
                print(f"{t['id']} [{t.get('title', '?')}] {icon} {t.get('status', '')}{ready_tag}")

        print(f"\nLegend: {status_icon('closed')} closed | {status_icon('open')} open | {status_icon('in_progress')} in_progress | {status_icon('blocked')} blocked")

except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)

sys.exit(0)
