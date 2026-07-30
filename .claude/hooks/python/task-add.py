#!/usr/bin/env python3
"""CLI: /task-add — Create new task in task tracker."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, generate_id,
                             get_existing_ids, now_iso, emit_event)

    # Parse args
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: task-add.py \"Task title\"", file=sys.stderr)
        sys.exit(1)

    title = ' '.join(sys.argv[1:]).strip()

    data = load_tracker()
    tasks = data['tasks']

    # Check duplicate title
    for t in tasks:
        if isinstance(t, dict) and t.get('title', '').lower() == title.lower():
            print(f"Task with title '{title}' already exists: {t.get('id')}", file=sys.stderr)
            sys.exit(1)

    existing_ids = get_existing_ids(tasks)
    task_id = generate_id(existing_ids)
    ts = now_iso()

    new_task = {
        'id': task_id,
        'title': title,
        'status': 'open',
        'assignee': None,
        'blocks': [],
        'blocked_by': [],
        'notes': [],
        'created_at': ts,
        'updated_at': ts,
    }
    tasks.append(new_task)

    if save_tracker(data):
        print(f"Created task {task_id}: {title}")
        emit_event('task_add', {'task_id': task_id, 'title': title})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)  # fail-open
