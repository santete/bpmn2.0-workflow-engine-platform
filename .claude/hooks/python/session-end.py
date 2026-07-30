#!/usr/bin/env python3
"""
Hook: Stop — Claude Code session ends.
Write `session_end` event với final tokens + rotated flag, sau đó nudge
drift_check để emit `drift_nudge` event nếu memory đã lệch baseline.
Fail-open: bất kỳ exception nào → exit 0 (không block shutdown).
"""
import io
import json
import subprocess
import sys
from pathlib import Path

# Windows fix: force utf-8 stdout for Unicode icons
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from metrics_writer import find_project_root, write_event

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'config'))
        from thresholds import load as _load_thresholds
        _cfg = _load_thresholds()
        _rotate_threshold = int(_cfg.get('rotate_threshold', 120_000))
    except Exception:
        _rotate_threshold = 120_000

    stdin_data = {}
    try:
        stdin_data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        pass

    root = find_project_root()

    final_tokens = 0
    try:
        cache = root / '.claude' / 'cache' / 'last_tokens.json'
        if cache.exists():
            cached = json.loads(cache.read_text(encoding='utf-8'))
            final_tokens = int(cached.get('tokens', 0))
    except Exception:
        pass

    rotated = bool(stdin_data.get('rotated')) or final_tokens >= _rotate_threshold

    write_event('session_end', {
        'final_tokens': final_tokens,
        'rotated': rotated,
        'session_id': stdin_data.get('session_id', ''),
    }, root=root)

    # Task tracker check — warn if tasks left in_progress without notes
    try:
        import yaml
        tracker_path = root / '.claude' / 'memory' / 'task_tracker.yaml'
        if tracker_path.exists():
            tracker = yaml.safe_load(tracker_path.read_text(encoding='utf-8')) or {}
            tasks = tracker.get('tasks', [])
            in_progress = [t for t in tasks if t.get('status') == 'in_progress']
            if in_progress:
                labels = ', '.join(f"{t['id']}({t.get('title','')})" for t in in_progress[:3])
                print(f"\n⚠️  Task(s) still in_progress: {labels}")
                print("   Consider: /task-note <id> <context> + /task-close <id>")
                print("   Or: /task-blocked <id> <reason>\n")
                write_event('task_in_progress_at_end', {
                    'count': len(in_progress),
                    'task_ids': [t['id'] for t in in_progress],
                }, root=root)
    except ImportError:
        pass  # yaml not available — skip silently
    except Exception:
        pass

    # WISC compliance summary — emit event + print status line
    try:
        import yaml as _yaml_wisc
        state_path = root / '.claude' / 'memory' / 'project_state.yaml'
        if state_path.exists():
            _wisc_state = _yaml_wisc.safe_load(state_path.read_text(encoding='utf-8')) or {}
            _wisc_gates = _wisc_state.get('wisc_gates') or {}
            if _wisc_gates and any(isinstance(g, dict) and 'status' in g for g in _wisc_gates.values()):
                gate_statuses = {}
                icons = {'inactive': '\u2b1c', 'required': '\u274c',
                         'satisfied': '\u2705', 'bypassed': '\u26a0\ufe0f'}
                bypass_count = 0
                fail_count = 0
                for name in ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS'):
                    g = _wisc_gates.get(name)
                    if isinstance(g, dict) and 'status' in g:
                        st = g['status']
                        gate_statuses[name] = st
                        if st == 'bypassed':
                            bypass_count += 1
                        elif st == 'required':
                            fail_count += 1
                    else:
                        gate_statuses[name] = 'inactive'

                all_passed = fail_count == 0
                summary_parts = []
                for name in ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS'):
                    st = gate_statuses[name]
                    icon = icons.get(st, '?')
                    summary_parts.append(f"{name[0]}{icon}")

                wisc_line = "\n\U0001f6e1\ufe0f  WISC: " + ' '.join(summary_parts)
                if all_passed and bypass_count == 0:
                    wisc_line += "  \u2014 all passed"
                if bypass_count:
                    wisc_line += f"  \u2014 {bypass_count} bypassed"
                if fail_count:
                    wisc_line += f"  \u2014 {fail_count} UNSATISFIED"
                print(wisc_line)

                write_event('wisc_compliance', {
                    'WRITE': gate_statuses.get('WRITE', 'inactive'),
                    'ISOLATE': gate_statuses.get('ISOLATE', 'inactive'),
                    'SELECT': gate_statuses.get('SELECT', 'inactive'),
                    'COMPRESS': gate_statuses.get('COMPRESS', 'inactive'),
                    'all_passed': all_passed,
                    'bypass_count': bypass_count,
                    'fail_count': fail_count,
                }, root=root)
    except ImportError:
        pass
    except Exception:
        pass

    # Drift nudge — fire-and-forget. We don't print at session end (the
    # session is already closing); we just record an event so /metrics can
    # show how often sessions ended with drift outstanding.
    try:
        drift_script = Path(__file__).parent / 'drift_check.py'
        proc = subprocess.run(
            ['python', str(drift_script), '--json'],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            payload = json.loads(proc.stdout.strip())
            if payload.get('status') == 'drift':
                write_event('drift_nudge', {
                    'baseline': payload.get('baseline', '')[:8],
                    'committed': len(payload.get('committed', [])),
                    'uncommitted': len(payload.get('uncommitted', [])),
                }, root=root)
    except Exception:
        pass

except Exception:
    pass

sys.exit(0)
