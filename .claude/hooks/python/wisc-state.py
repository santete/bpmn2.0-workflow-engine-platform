#!/usr/bin/env python3
"""
WISC State Calculator — compute wisc_gates from 6D classification.

Called AFTER /classify-task writes last_task_classification to project_state.yaml.
This script reads the classification, computes which WISC gates are required,
and writes the wisc_gates section back to project_state.yaml.

Usage:
  python .claude/hooks/python/wisc-state.py [--reset]

  --reset: Clear wisc_gates (for new task start)

NOT a hook (no stdin). Called explicitly by /classify-task command.
Fail-open: any error → exit 0 with warning on stderr.
"""
import sys
import io
import re
import time
from pathlib import Path

# Windows fix
for stream_name in ('stdout', 'stderr'):
    stream = getattr(sys, stream_name)
    if stream.encoding and stream.encoding.lower() != 'utf-8':
        try:
            setattr(sys, stream_name, io.TextIOWrapper(
                stream.buffer, encoding='utf-8', errors='replace'))
        except Exception:
            pass

try:
    import yaml
except ImportError:
    print("wisc-state: PyYAML not installed, skipping", file=sys.stderr)
    sys.exit(0)


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def _emit_audit(action: str, gate: str, data: dict, root: Path):
    """Emit wisc_audit event (fail-open). Unified audit trail for Tier 3."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event
        payload = {'action': action, 'gate': gate}
        payload.update(data)
        write_event('wisc_audit', payload, root=root)
    except Exception:
        pass


def make_gate(status: str, artifact: str = '', reason: str = '') -> dict:
    """Create a gate entry with standard fields."""
    gate = {
        'status': status,          # inactive | required | satisfied | bypassed
        'artifact': artifact,
        'satisfied_at': '',
        'satisfied_by': '',        # auto | manual | bypass
        'bypass_reason': '',
    }
    return gate


def compute_gates(classification: dict, root: Path) -> dict:
    """Derive wisc_gates from 6D classification."""
    d5 = str(classification.get('D5', '')).lower()
    d6 = str(classification.get('D6', '')).lower()
    task_name = classification.get('task', 'unknown')

    # Sanitize task name for file path
    safe_task = re.sub(r'[^a-zA-Z0-9_-]', '_', task_name)[:30]

    gates = {}

    # ── WRITE gate ───────────────────────────────────────────────────────
    if d5 == 'vague':
        gates['WRITE'] = make_gate(
            status='required',
            artifact='spec.md',
        )
    else:
        gates['WRITE'] = make_gate(status='inactive')

    # ── ISOLATE gate ─────────────────────────────────────────────────────
    if d6 in ('unknown', 'legacy-undocumented', 'cross-module'):
        gates['ISOLATE'] = make_gate(
            status='required',
            artifact=f'.claude/memory/scout_report_{safe_task}.md',
        )
    else:
        gates['ISOLATE'] = make_gate(status='inactive')

    # ── SELECT gate — always satisfied (structural enforcement) ──────────
    gates['SELECT'] = make_gate(status='satisfied')
    gates['SELECT']['satisfied_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    gates['SELECT']['satisfied_by'] = 'structural'

    # ── COMPRESS gate — inactive by default, wisc-gate.py checks token ───
    gates['COMPRESS'] = make_gate(status='inactive')

    # ── Auto-satisfy: check if artifacts already exist ───────────────────
    if gates['WRITE']['status'] == 'required':
        artifact = gates['WRITE']['artifact']
        candidates = [root / artifact, root / 'spec.md',
                      root / 'docs' / 'spec.md',
                      root / '.claude' / 'memory' / 'spec.md']
        if any(p.exists() for p in candidates):
            gates['WRITE']['status'] = 'satisfied'
            gates['WRITE']['satisfied_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            gates['WRITE']['satisfied_by'] = 'auto'

    if gates['ISOLATE']['status'] == 'required':
        memory_dir = root / '.claude' / 'memory'
        scout_files = list(memory_dir.glob('scout_report*')) if memory_dir.exists() else []
        artifact = gates['ISOLATE']['artifact']
        if scout_files or (artifact and (root / artifact).exists()):
            gates['ISOLATE']['status'] = 'satisfied'
            gates['ISOLATE']['satisfied_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            gates['ISOLATE']['satisfied_by'] = 'auto'

    return gates


def main():
    try:
        reset_mode = '--reset' in sys.argv

        root = find_project_root()
        state_path = root / '.claude' / 'memory' / 'project_state.yaml'
        if not state_path.exists():
            print("wisc-state: project_state.yaml not found, skipping", file=sys.stderr)
            sys.exit(0)

        state = yaml.safe_load(state_path.read_text(encoding='utf-8')) or {}

        if reset_mode:
            state['wisc_gates'] = {}
            state_path.write_text(
                yaml.dump(state, allow_unicode=True, default_flow_style=False,
                          sort_keys=False),
                encoding='utf-8')
            print("wisc-state: gates reset")
            _emit_audit('gates_reset', '*', {'task': 'reset'}, root)
            sys.exit(0)

        classification = state.get('last_task_classification') or {}
        if not classification:
            print("wisc-state: no classification found, skipping", file=sys.stderr)
            sys.exit(0)

        # Preserve existing bypass_reason if user already set one
        old_gates = state.get('wisc_gates') or {}

        gates = compute_gates(classification, root)

        # Merge: keep bypass info from old gates if gate was bypassed
        for name in ('WRITE', 'ISOLATE', 'COMPRESS'):
            old = old_gates.get(name) or {}
            if old.get('status') == 'bypassed' or old.get('bypass_reason'):
                gates[name]['status'] = 'bypassed'
                gates[name]['bypass_reason'] = old.get('bypass_reason', '')
                gates[name]['satisfied_at'] = old.get('satisfied_at', '')
                gates[name]['satisfied_by'] = 'bypass'

        state['wisc_gates'] = gates

        # Write back — preserve comments by using yaml.dump
        state_path.write_text(
            yaml.dump(state, allow_unicode=True, default_flow_style=False,
                      sort_keys=False),
            encoding='utf-8')

        # Summary output
        summary_parts = []
        for name in ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS'):
            g = gates[name]
            icon = {'inactive': '⬜', 'required': '🔴', 'satisfied': '✅',
                    'bypassed': '⚠️'}.get(g['status'], '?')
            summary_parts.append(f"{name[0]}{icon}")

        required = [n for n, g in gates.items() if g['status'] == 'required']
        print(f"WISC gates: {' '.join(summary_parts)}")
        if required:
            print(f"  Required gates: {', '.join(required)} — satisfy before coding")
            for name in required:
                g = gates[name]
                print(f"    {name}: artifact={g['artifact']}")

        task_name = classification.get('task', 'unknown')
        for name in ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS'):
            g = gates[name]
            old = old_gates.get(name) or {}
            _emit_audit('gate_computed', name, {
                'task': task_name,
                'from_status': old.get('status', 'none'),
                'to_status': g['status'],
                'artifact': g.get('artifact', ''),
            }, root)

    except SystemExit:
        raise
    except Exception as e:
        print(f"wisc-state: error ({e}), skipping", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
