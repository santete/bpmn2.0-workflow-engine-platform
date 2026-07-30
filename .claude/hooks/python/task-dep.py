#!/usr/bin/env python3
"""CLI: /task-dep — Declare dependency (A blocks B) with circular check."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task,
                             check_circular_deps, now_iso, emit_event)

    if len(sys.argv) < 4 or sys.argv[2].lower() != 'blocks':
        print("Usage: task-dep.py <id-A> blocks <id-B>", file=sys.stderr)
        sys.exit(1)

    id_a = sys.argv[1]
    id_b = sys.argv[3]

    if id_a == id_b:
        print(f"Task cannot block itself: {id_a}", file=sys.stderr)
        sys.exit(1)

    data = load_tracker()
    tasks = data['tasks']
    task_a = find_task(tasks, id_a)
    task_b = find_task(tasks, id_b)

    if not task_a:
        print(f"Task {id_a} not found", file=sys.stderr)
        sys.exit(1)
    if not task_b:
        print(f"Task {id_b} not found", file=sys.stderr)
        sys.exit(1)

    # Check duplicate dependency
    blocks_a = task_a.get('blocks', [])
    if id_b in blocks_a:
        print(f"Dependency already exists: {id_a} blocks {id_b}", file=sys.stderr)
        sys.exit(1)

    # Check circular dependency
    cycle = check_circular_deps(tasks, id_a, id_b)
    if cycle:
        path_str = ' -> '.join(cycle)
        print(f"Circular dependency detected: {path_str}", file=sys.stderr)
        sys.exit(1)

    # Set dependency: A.blocks += B, B.blocked_by += A
    if 'blocks' not in task_a or not isinstance(task_a['blocks'], list):
        task_a['blocks'] = []
    task_a['blocks'].append(id_b)
    task_a['updated_at'] = now_iso()

    if 'blocked_by' not in task_b or not isinstance(task_b['blocked_by'], list):
        task_b['blocked_by'] = []
    task_b['blocked_by'].append(id_a)
    task_b['updated_at'] = now_iso()

    # If task B is open, change to blocked
    if task_b.get('status') == 'open':
        task_b['status'] = 'blocked'

    if save_tracker(data):
        title_a = task_a.get('title', '?')
        title_b = task_b.get('title', '?')
        print(f"Dependency set: {id_a} ({title_a}) blocks {id_b} ({title_b})")
        print(f"   {id_b} sẽ ready sau khi {id_a} closed.")
        emit_event('task_dep', {'from': id_a, 'to': id_b})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
