#!/usr/bin/env python3
"""CLI: /task-claim — Claim task for work (open → in_progress)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task,
                             now_iso, emit_event)

    if len(sys.argv) < 2:
        print("Usage: task-claim.py <task-id>", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]

    data = load_tracker()
    task = find_task(data['tasks'], task_id)

    if not task:
        print(f"Task {task_id} not found", file=sys.stderr)
        sys.exit(1)

    status = task.get('status', '')

    if status == 'in_progress':
        assignee = task.get('assignee', '?')
        print(f"Task {task_id} already claimed by {assignee}", file=sys.stderr)
        sys.exit(1)

    if status == 'blocked':
        blocked_by = ', '.join(task.get('blocked_by', []))
        print(f"Task {task_id} is blocked by: {blocked_by}", file=sys.stderr)
        sys.exit(1)

    if status == 'closed':
        print(f"Task {task_id} is already closed", file=sys.stderr)
        sys.exit(1)

    if status != 'open':
        print(f"Task {task_id} has unexpected status '{status}'", file=sys.stderr)
        sys.exit(1)

    # Check if blocked_by has unresolved deps
    blocked_by = task.get('blocked_by', [])
    if blocked_by:
        closed_ids = {t['id'] for t in data['tasks']
                      if isinstance(t, dict) and t.get('status') == 'closed'}
        unresolved = [b for b in blocked_by if b not in closed_ids]
        if unresolved:
            print(f"Task {task_id} is blocked by unresolved: {', '.join(unresolved)}", file=sys.stderr)
            sys.exit(1)

    task['status'] = 'in_progress'
    task['assignee'] = 'current-session'
    task['updated_at'] = now_iso()

    if save_tracker(data):
        title = task.get('title', '')
        print(f"Claimed task {task_id}")
        print(f"   Title: {title}")
        print(f"   Status: open -> in_progress")
        print()
        print(f"-> Khi xong: `/task-note {task_id} <note>` rồi `/task-close {task_id}`")
        emit_event('task_claim', {'task_id': task_id})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
