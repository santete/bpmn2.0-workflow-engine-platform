#!/usr/bin/env python3
"""
Hook: SessionStart — Task tracker summary.
Show in_progress + ready task count at session start.
Fail-open: any error → exit 0 (don't block session).
"""
import io
import sys
from pathlib import Path

# Windows fix: force utf-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import yaml
except ImportError:
    sys.exit(0)  # PyYAML not installed — skip silently

try:
    tracker_path = Path('.claude/memory/task_tracker.yaml')
    if not tracker_path.exists():
        sys.exit(0)

    data = yaml.safe_load(tracker_path.read_text(encoding='utf-8')) or {}
    tasks = data.get('tasks', [])

    # Detect 2b mode with empty tracker → warn
    if not tasks:
        state_path = Path('.claude/memory/project_state.yaml')
        if state_path.exists():
            state = yaml.safe_load(state_path.read_text(encoding='utf-8')) or {}
            cls = state.get('last_task_classification') or {}
            exec_mode = str(cls.get('execution_mode', ''))
            if '2b' in exec_mode:
                print("\u26a0\ufe0f  Task tracker empty but execution_mode=2b-epic!")
                print("   Run /task-add <title> to create subtasks, then /task-dep + /task-graph")
        sys.exit(0)

    in_progress = [t for t in tasks if t.get('status') == 'in_progress']
    blocked = [t for t in tasks if t.get('status') == 'blocked']
    closed = [t for t in tasks if t.get('status') == 'closed']
    open_tasks = [t for t in tasks if t.get('status') == 'open']

    # Ready = open + all blocked_by are closed
    closed_ids = {t['id'] for t in closed}
    ready = [t for t in open_tasks
             if all(b in closed_ids for b in t.get('blocked_by', []))]

    parts = []
    if in_progress:
        labels = ', '.join(f"{t['id']}" for t in in_progress[:3])
        parts.append(f"{len(in_progress)} in_progress ({labels})")
    if ready:
        parts.append(f"{len(ready)} ready")
    if blocked:
        parts.append(f"{len(blocked)} blocked")
    parts.append(f"{len(closed)}/{len(tasks)} closed")

    print(f"Tasks: {' | '.join(parts)}")

except Exception:
    pass  # fail-open

sys.exit(0)
