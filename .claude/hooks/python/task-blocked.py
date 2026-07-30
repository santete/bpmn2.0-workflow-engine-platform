#!/usr/bin/env python3
"""CLI: /task-blocked — Mark task as blocked with reason."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task,
                             append_note, now_iso, emit_event)

    if len(sys.argv) < 3:
        print("Usage: task-blocked.py <task-id> \"Reason for blocking\"", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]
    reason = ' '.join(sys.argv[2:]).strip()

    if not reason:
        print("Reason cannot be empty", file=sys.stderr)
        sys.exit(1)

    data = load_tracker()
    task = find_task(data['tasks'], task_id)

    if not task:
        print(f"Task {task_id} not found", file=sys.stderr)
        sys.exit(1)

    status = task.get('status', '')
    if status == 'closed':
        print(f"Warning: task {task_id} is closed, cannot block", file=sys.stderr)
        sys.exit(1)

    task['status'] = 'blocked'
    task['updated_at'] = now_iso()
    append_note(task, f"BLOCKED: {reason}")

    if save_tracker(data):
        title = task.get('title', '')
        print(f"Blocked task {task_id}: {title}")
        print(f"   Reason: {reason}")
        print()
        print(f"-> Resolve blocker rồi `/task-claim {task_id}` (chuyển về in_progress)")
        print(f"-> Hoặc: set dependency `/task-dep <blocker-id> blocks {task_id}`")
        emit_event('task_blocked', {'task_id': task_id, 'reason': reason})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
