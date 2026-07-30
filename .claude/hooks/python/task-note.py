#!/usr/bin/env python3
"""CLI: /task-note — Append note to a task."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, save_tracker, find_task,
                             append_note, emit_event)

    if len(sys.argv) < 3:
        print("Usage: task-note.py <task-id> \"Note content\"", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]
    note_text = ' '.join(sys.argv[2:]).strip()

    if not note_text:
        print("Note content cannot be empty", file=sys.stderr)
        sys.exit(1)

    data = load_tracker()
    task = find_task(data['tasks'], task_id)

    if not task:
        print(f"Task {task_id} not found", file=sys.stderr)
        sys.exit(1)

    append_note(task, note_text)

    if save_tracker(data):
        display = note_text[:80] + ('...' if len(note_text) > 80 else '')
        print(f"Note added to {task_id}: \"{display}\"")
        emit_event('task_note', {'task_id': task_id})
        sys.exit(0)
    else:
        print("Failed to save task tracker", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
