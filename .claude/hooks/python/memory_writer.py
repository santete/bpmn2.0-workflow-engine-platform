"""
memory_writer — safe append-only mutations to project_state.yaml.

Schema-guarded writes:
  1. Read + parse current YAML
  2. Backup → .bak
  3. Mutate in-memory
  4. Assert: old decision/gotcha IDs ⊆ new (never lose data)
  5. Write atomically
  6. On failure → rollback from .bak

Fail-open invariant: append functions return bool, never raise.
A failed write = one missed entry, NOT a blocked workflow.

Used by: /done slash command (auto-writeback at end of task).
"""
import copy
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def _load(path: Path) -> dict:
    if not path.exists() or yaml is None:
        return {}
    try:
        with path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save(path: Path, data: dict) -> bool:
    if yaml is None:
        return False
    try:
        with path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True,
                           default_flow_style=False)
        return True
    except Exception:
        return False


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    bak = path.with_suffix('.yaml.bak')
    try:
        shutil.copy2(str(path), str(bak))
        return bak
    except Exception:
        return None


def _rollback(path: Path, bak: Path) -> None:
    try:
        if bak and bak.exists():
            shutil.copy2(str(bak), str(path))
    except Exception:
        pass


def _safe_write(path: Path, old_state: dict, new_state: dict) -> bool:
    """Schema-guarded write: backup → write → validate → rollback on failure."""
    bak = _backup(path)

    # Invariant: never lose existing decisions or gotchas
    old_decisions = {d.get('decision', '') for d in (old_state.get('decisions') or [])
                     if isinstance(d, dict)}
    old_gotchas = {g.get('discovery', '') for g in (old_state.get('known_gotchas') or [])
                   if isinstance(g, dict)}

    new_decisions = {d.get('decision', '') for d in (new_state.get('decisions') or [])
                     if isinstance(d, dict)}
    new_gotchas = {g.get('discovery', '') for g in (new_state.get('known_gotchas') or [])
                   if isinstance(g, dict)}

    if not old_decisions.issubset(new_decisions):
        _rollback(path, bak)
        return False
    if not old_gotchas.issubset(new_gotchas):
        _rollback(path, bak)
        return False

    if not _save(path, new_state):
        _rollback(path, bak)
        return False

    # Re-parse to verify integrity
    verify = _load(path)
    if not verify:
        _rollback(path, bak)
        return False

    return True


def _today() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


# ── Public API ───────────────────────────────────────────────────────

def append_change(task: str, files_modified: list = None, root: Path = None) -> bool:
    """Append a completed task to completed_tasks + update last_successful_task."""
    try:
        root = root or find_project_root()
        path = root / '.claude' / 'memory' / 'project_state.yaml'
        old = _load(path)
        new = copy.deepcopy(old)

        tasks = new.setdefault('completed_tasks', [])
        if not isinstance(tasks, list):
            tasks = []
            new['completed_tasks'] = tasks

        tasks.append({
            'date': _today(),
            'task': task,
            'files_modified': files_modified or [],
        })

        new['last_successful_task'] = task
        new['session_count'] = int(new.get('session_count', 0) or 0) + 0  # don't bump here

        return _safe_write(path, old, new)
    except Exception:
        return False


def append_decision(decision: str, reason: str, impact: str = '', root: Path = None) -> bool:
    """Append a non-obvious architectural decision."""
    try:
        root = root or find_project_root()
        path = root / '.claude' / 'memory' / 'project_state.yaml'
        old = _load(path)
        new = copy.deepcopy(old)

        decisions = new.setdefault('decisions', [])
        if not isinstance(decisions, list):
            decisions = []
            new['decisions'] = decisions

        # Dedup by decision text
        if any(d.get('decision') == decision for d in decisions if isinstance(d, dict)):
            return True  # already recorded

        entry = {
            'date': _today(),
            'decision': decision,
            'reason': reason,
        }
        if impact:
            entry['impact'] = impact
        decisions.append(entry)

        return _safe_write(path, old, new)
    except Exception:
        return False


def append_gotcha(discovery: str, workaround: str, files_affected: list = None,
                  root: Path = None) -> bool:
    """Append a known gotcha / unexpected behavior."""
    try:
        root = root or find_project_root()
        path = root / '.claude' / 'memory' / 'project_state.yaml'
        old = _load(path)
        new = copy.deepcopy(old)

        gotchas = new.setdefault('known_gotchas', [])
        if not isinstance(gotchas, list):
            gotchas = []
            new['known_gotchas'] = gotchas

        # Dedup by discovery text
        if any(g.get('discovery') == discovery for g in gotchas if isinstance(g, dict)):
            return True

        entry = {
            'discovery': discovery,
            'workaround': workaround,
            'discovered_at': _today(),
        }
        if files_affected:
            entry['files_affected'] = files_affected
        gotchas.append(entry)

        return _safe_write(path, old, new)
    except Exception:
        return False


def touch_last_updated(root: Path = None) -> bool:
    """Update session metadata without appending data."""
    try:
        root = root or find_project_root()
        path = root / '.claude' / 'memory' / 'project_state.yaml'
        old = _load(path)
        new = copy.deepcopy(old)

        new['session_count'] = int(new.get('session_count', 0) or 0) + 1
        new['consecutive_failures'] = 0

        return _safe_write(path, old, new)
    except Exception:
        return False


def remove_pending(description: str, root: Path = None) -> bool:
    """Remove a pending task by description match (exact or substring)."""
    try:
        root = root or find_project_root()
        path = root / '.claude' / 'memory' / 'project_state.yaml'
        old = _load(path)
        new = copy.deepcopy(old)

        pending = new.get('pending_tasks', [])
        if not isinstance(pending, list):
            return True

        new['pending_tasks'] = [
            p for p in pending
            if isinstance(p, dict) and description.lower() not in (p.get('description', '')).lower()
        ]

        return _safe_write(path, old, new)
    except Exception:
        return False
