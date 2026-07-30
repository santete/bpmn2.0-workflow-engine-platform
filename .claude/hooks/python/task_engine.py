"""
task_engine — shared library for task tracker CLI scripts.

Schema-guarded YAML operations for .claude/memory/task_tracker.yaml.
Follows memory_writer.py patterns: backup/write/verify, fail-open, find_project_root.

Used by: task-add.py, task-claim.py, task-close.py, task-dep.py,
         task-graph.py, task-ready.py, task-blocked.py, task-list.py,
         task-discovered.py, task-note.py, beads-doctor.py
"""
import copy
import secrets
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Ensure UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ── Metrics integration (fail-open) ─────────────────────────────────

def emit_event(event_type, data=None):
    """Wrapper around metrics_writer.write_event. Never raises."""
    try:
        from metrics_writer import write_event
        write_event(event_type, data or {})
    except Exception:
        pass


# ── Path helpers ─────────────────────────────────────────────────────

def find_project_root(start=None):
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def _tracker_path(root=None):
    root = root or find_project_root()
    return root / '.claude' / 'memory' / 'task_tracker.yaml'


# ── YAML I/O ─────────────────────────────────────────────────────────

def load_tracker(root=None):
    """Read task_tracker.yaml. Returns {'tasks': []} on any error."""
    path = _tracker_path(root)
    if not path.exists() or yaml is None:
        return {'tasks': []}
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        if 'tasks' not in data or not isinstance(data['tasks'], list):
            data['tasks'] = []
        return data
    except Exception:
        return {'tasks': []}


def save_tracker(data, root=None):
    """Atomic write: backup → write → verify → rollback on failure.
    Invariant: never lose existing task IDs."""
    if yaml is None:
        return False
    path = _tracker_path(root)
    try:
        # Read old state for invariant check
        old_data = load_tracker(root)
        old_ids = {t.get('id') for t in old_data.get('tasks', []) if isinstance(t, dict)}
        new_ids = {t.get('id') for t in data.get('tasks', []) if isinstance(t, dict)}
        if not old_ids.issubset(new_ids):
            return False  # would lose tasks

        # Backup
        bak = None
        if path.exists():
            bak = path.with_suffix('.yaml.bak')
            try:
                shutil.copy2(str(path), str(bak))
            except Exception:
                bak = None

        # Ensure parent dir
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write
        with path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True,
                           default_flow_style=False)

        # Verify re-parse
        with path.open('r', encoding='utf-8') as f:
            verify = yaml.safe_load(f)
        if not verify or not isinstance(verify.get('tasks'), list):
            # Rollback
            if bak and bak.exists():
                shutil.copy2(str(bak), str(path))
            return False

        return True
    except Exception:
        # Rollback on any error
        try:
            if bak and bak.exists():
                shutil.copy2(str(bak), str(path))
        except Exception:
            pass
        return False


# ── ID generation ────────────────────────────────────────────────────

def generate_id(existing_ids=None, prefix='tsk'):
    """Generate unique ID: prefix + '-' + 4 hex chars."""
    existing = existing_ids or set()
    for _ in range(10):
        new_id = f'{prefix}-{secrets.token_hex(2)}'
        if new_id not in existing:
            return new_id
    # Fallback: 6 hex chars
    return f'{prefix}-{secrets.token_hex(3)}'


# ── Task lookup ──────────────────────────────────────────────────────

def find_task(tasks, task_id):
    """Find task by ID. Returns dict reference or None."""
    for t in tasks:
        if isinstance(t, dict) and t.get('id') == task_id:
            return t
    return None


def get_existing_ids(tasks):
    """Get set of all task IDs."""
    return {t.get('id') for t in tasks if isinstance(t, dict) and t.get('id')}


# ── Validation ───────────────────────────────────────────────────────

def validate_status(task, expected):
    """Check task status. expected can be str or list of str.
    Returns error message or None if OK."""
    status = task.get('status', '')
    if isinstance(expected, str):
        expected = [expected]
    if status not in expected:
        return f"Task {task.get('id')} has status '{status}', expected {expected}"
    return None


# ── DAG operations ───────────────────────────────────────────────────

def check_circular_deps(tasks, from_id, to_id):
    """Check if adding dependency 'from_id blocks to_id' creates a cycle.
    Uses iterative DFS from from_id following blocked_by chains.
    Returns cycle path [id1, id2, ..., id1] if found, None if clean."""
    # If from_id blocks to_id, then to_id.blocked_by += from_id
    # Cycle exists if from_id is reachable from to_id via blocked_by chains
    # i.e., to_id already (transitively) blocks from_id
    task_map = {t['id']: t for t in tasks if isinstance(t, dict) and t.get('id')}

    # DFS: start from from_id, follow 'blocked_by' links, see if we reach to_id
    visited = set()
    stack = [(from_id, [from_id])]
    while stack:
        current, path = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        task = task_map.get(current)
        if not task:
            continue
        for blocked_by_id in task.get('blocked_by', []):
            new_path = path + [blocked_by_id]
            if blocked_by_id == to_id:
                return new_path  # Cycle found
            if blocked_by_id not in visited:
                stack.append((blocked_by_id, new_path))
    return None


def compute_ready(tasks):
    """Return list of tasks that are ready to work on.
    Ready = status 'open' AND (blocked_by empty OR all blocked_by are closed).
    Sorted by created_at ascending."""
    closed_ids = {t['id'] for t in tasks
                  if isinstance(t, dict) and t.get('status') == 'closed'}
    ready = []
    for t in tasks:
        if not isinstance(t, dict) or t.get('status') != 'open':
            continue
        blocked_by = t.get('blocked_by', [])
        if all(b in closed_ids for b in blocked_by):
            ready.append(t)
    ready.sort(key=lambda t: t.get('created_at', ''))
    return ready


def auto_unblock(tasks, closed_id):
    """After closing a task, scan and unblock dependents.
    Returns list of unblocked task IDs."""
    closed_ids = {t['id'] for t in tasks
                  if isinstance(t, dict) and t.get('status') == 'closed'}
    unblocked = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if t.get('status') != 'blocked':
            continue
        blocked_by = t.get('blocked_by', [])
        if closed_id not in blocked_by:
            continue
        # Check if ALL blockers are now closed
        if all(b in closed_ids for b in blocked_by):
            t['status'] = 'open'
            t['updated_at'] = now_iso()
            unblocked.append(t['id'])
    return unblocked


# ── Note operations ──────────────────────────────────────────────────

def append_note(task, text, author='current-session'):
    """Append a note to task's notes list."""
    if 'notes' not in task or not isinstance(task['notes'], list):
        task['notes'] = []
    task['notes'].append({
        'date': now_iso(),
        'author': author,
        'text': text,
    })
    task['updated_at'] = now_iso()


# ── Formatting helpers ───────────────────────────────────────────────

def now_iso():
    """UTC ISO 8601 timestamp."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def remaining_summary(tasks):
    """Return summary string: 'N open, M in_progress, K blocked, L closed'."""
    counts = {}
    for t in tasks:
        if isinstance(t, dict):
            s = t.get('status', 'unknown')
            counts[s] = counts.get(s, 0) + 1
    parts = []
    for status in ['open', 'in_progress', 'blocked', 'closed']:
        if counts.get(status, 0) > 0:
            parts.append(f"{counts[status]} {status}")
    return ', '.join(parts) if parts else '0 tasks'


def format_task_short(task):
    """One-liner: 'tsk-xxxx: Title [status]'."""
    return f"{task.get('id', '?')}: {task.get('title', '?')} [{task.get('status', '?')}]"


def status_icon(status):
    """Emoji icon for task status."""
    icons = {
        'in_progress': '\U0001f534',  # red circle
        'open': '\U0001f7e1',         # yellow circle
        'blocked': '\U0001f535',      # blue circle
        'closed': '\u2705',           # green check
    }
    return icons.get(status, '\u2753')
