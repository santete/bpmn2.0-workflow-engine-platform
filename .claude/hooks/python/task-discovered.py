#!/usr/bin/env python3
"""CLI: /task-discovered — Create discovered task (bug found during work)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task, generate_id,
                             get_existing_ids, append_note, now_iso, emit_event)

    if len(sys.argv) < 3:
        print("Usage: task-discovered.py <parent-task-id> \"Title\" [priority]", file=sys.stderr)
        sys.exit(1)

    parent_id = sys.argv[1]
    title = sys.argv[2]
    priority = sys.argv[3] if len(sys.argv) > 3 else 'medium'

    if priority not in ('low', 'medium', 'high', 'critical'):
        priority = 'medium'

    data = load_tracker()
    tasks = data['tasks']
    parent = find_task(tasks, parent_id)

    if not parent:
        print(f"Parent task {parent_id} not found", file=sys.stderr)
        sys.exit(1)

    existing_ids = get_existing_ids(tasks)
    new_id = generate_id(existing_ids)
    ts = now_iso()
    parent_title = parent.get('title', '?')

    new_task = {
        'id': new_id,
        'title': title,
        'status': 'open',
        'assignee': None,
        'type': 'discovered-from',
        'parent_task': parent_id,
        'priority': priority,
        'blocks': [],
        'blocked_by': [],
        'notes': [{
            'date': ts,
            'author': 'current-session',
            'text': f"Discovered during work on {parent_id}: {parent_title}",
        }],
        'created_at': ts,
        'updated_at': ts,
    }
    tasks.append(new_task)

    # Append note to parent
    append_note(parent, f"Discovered issue: {title} -> created {new_id} (priority: {priority})")

    if save_tracker(data):
        print(f"Discovered task {new_id}: {title}")
        print(f"   Parent: {parent_id} ({parent_title})")
        print(f"   Priority: {priority}")
        print(f"   Type: discovered-from")
        print()
        print(f"-> Note added to parent task")
        print(f"-> To assign: `/task-claim {new_id}`")
        print(f"-> To block parent on this: `/task-dep {new_id} blocks {parent_id}`")
        emit_event('task_discovered', {'task_id': new_id, 'parent': parent_id, 'priority': priority})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
