#!/usr/bin/env python3
"""CLI: /task-close — Close task + auto-unblock dependents."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task,
                             auto_unblock, remaining_summary, now_iso,
                             emit_event)

    if len(sys.argv) < 2:
        print("Usage: task-close.py <task-id>", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]

    data = load_tracker()
    tasks = data['tasks']
    task = find_task(tasks, task_id)

    if not task:
        print(f"Task {task_id} not found", file=sys.stderr)
        sys.exit(1)

    status = task.get('status', '')
    title = task.get('title', '')

    # Warning if closing from open (may have forgotten to claim)
    if status == 'open':
        print(f"Warning: closing task {task_id} from 'open' (was not claimed)", file=sys.stderr)
    elif status == 'closed':
        print(f"Task {task_id} is already closed", file=sys.stderr)
        sys.exit(1)

    task['status'] = 'closed'
    task['updated_at'] = now_iso()

    # Auto-unblock dependents
    unblocked = auto_unblock(tasks, task_id)

    if save_tracker(data):
        print(f"Closed task {task_id}: {title}")

        if unblocked:
            print()
            print("Auto-unblocked:")
            for uid in unblocked:
                ut = find_task(tasks, uid)
                ut_title = ut.get('title', '?') if ut else '?'
                print(f"- {uid}: \"{ut_title}\" (was blocked by {task_id})")

        print()
        print(f"Remaining: {remaining_summary(tasks)}")
        print(f"-> Next: `/task-ready`")
        emit_event('task_close', {'task_id': task_id, 'unblocked': unblocked})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
