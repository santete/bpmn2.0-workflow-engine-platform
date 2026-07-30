"""
metrics_writer — append-only event log cho framework telemetry.

Fail-open invariant: KHÔNG bao giờ raise, KHÔNG bao giờ block caller.
Một event ghi sai = mất 1 dòng metric, không ảnh hưởng workflow.

Event schema (1 dòng JSON / event):
  {
    "ts": 1746489600,          # epoch seconds
    "event": "session_end" | "halluc_score" | "hook_block" | "rotate" | "classify" | "task_done" | "loop_retry",
    "pattern": "A" | "B" | "C" | "?",
    "data": { ... }            # event-specific fields
  }

Auto-prune: khi events.jsonl > 100 MB, giữ lại 90 ngày gần nhất.

Path: <project_root>/.claude/metrics/events.jsonl  (gitignored)
"""
import json
import os
import re
import time
from pathlib import Path

# Auto-prune thresholds (configurable via thresholds.json)
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'config'))
    from thresholds import load as _load_thresholds
    _prune_cfg = _load_thresholds()
    _MAX_FILE_SIZE = int(_prune_cfg.get('metrics_max_size_mb', 100)) * 1024 * 1024
    _PRUNE_KEEP_DAYS = int(_prune_cfg.get('metrics_retention_days', 90))
except Exception:
    _MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    _PRUNE_KEEP_DAYS = 90


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def _read_pattern(root: Path) -> str:
    try:
        state_path = root / '.claude' / 'memory' / 'project_state.yaml'
        if not state_path.exists():
            return '?'
        text = state_path.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'^pattern:\s*([ABC])\b', text, re.MULTILINE)
        return m.group(1) if m else '?'
    except Exception:
        return '?'


def _auto_prune(log_path: Path) -> None:
    """Prune events.jsonl when > 100 MB. Keep last 90 days. Fail-open."""
    try:
        if not log_path.exists():
            return
        size = log_path.stat().st_size
        if size <= _MAX_FILE_SIZE:
            return

        cutoff_ts = int(time.time()) - _PRUNE_KEEP_DAYS * 86400
        kept = []
        with log_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get('ts', 0) >= cutoff_ts:
                        kept.append(line)
                except Exception:
                    continue

        # Atomic-ish write: write to .tmp then rename
        tmp = log_path.with_suffix('.jsonl.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            for line in kept:
                f.write(line + '\n')

        # Replace original
        if os.name == 'nt':
            # Windows: can't rename over existing file
            log_path.unlink()
        tmp.rename(log_path)
    except Exception:
        pass


def write_event(event_type: str, data: dict = None, root: Path = None) -> bool:
    """Append 1 event vào .claude/metrics/events.jsonl. Returns False on any error."""
    try:
        if root is None:
            root = find_project_root()
        metrics_dir = root / '.claude' / 'metrics'
        metrics_dir.mkdir(parents=True, exist_ok=True)
        log_path = metrics_dir / 'events.jsonl'

        # Auto-prune before write (fail-open, ~once per 100MB growth)
        _auto_prune(log_path)

        event = {
            'ts': int(time.time()),
            'event': event_type,
            'pattern': _read_pattern(root),
            'data': data or {},
        }
        with log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return True
    except Exception:
        return False
