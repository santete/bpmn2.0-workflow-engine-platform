#!/usr/bin/env python3
"""
WISC Bypass Protocol — controlled gate bypass with validation + audit trail.

Usage:
  python .claude/hooks/python/wisc-bypass.py <GATE> --reason "<lý do>"
  python .claude/hooks/python/wisc-bypass.py ISOLATE --reason "User confirmed codebase familiar"

Validates:
  - Gate exists in wisc_gates
  - Gate status is 'required' (can't bypass inactive/satisfied)
  - Reason is non-empty

Actions:
  - Flips gate status: required → bypassed
  - Sets bypass_reason, satisfied_at, satisfied_by=bypass
  - Emits wisc_audit event with full trail

Exit 0 = success
Exit 1 = invalid args / validation failure
"""
import argparse
import io
import sys
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
    print("wisc-bypass: PyYAML not installed", file=sys.stderr)
    sys.exit(1)

VALID_GATES = ('WRITE', 'ISOLATE', 'SELECT', 'COMPRESS')


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def emit_audit(gate: str, task: str, reason: str, root: Path):
    """Emit wisc_audit gate_bypassed event."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event
        write_event('wisc_audit', {
            'action': 'gate_bypassed',
            'gate': gate,
            'task': task,
            'from_status': 'required',
            'to_status': 'bypassed',
            'reason': reason[:500],
            'approved_by': 'user',
        }, root=root)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(
        description='WISC Bypass Protocol — bypass a required gate with audit trail')
    ap.add_argument('gate', type=str, help='Gate to bypass (WRITE, ISOLATE, COMPRESS)')
    ap.add_argument('--reason', '-r', type=str, required=True,
                    help='Reason for bypass (required, will be audited)')
    args = ap.parse_args()

    gate_name = args.gate.upper()
    reason = args.reason.strip()

    # ── Validate gate name ───────────────────────────────────────────────
    if gate_name not in VALID_GATES:
        print(f"Error: '{gate_name}' is not a valid gate. Valid: {', '.join(VALID_GATES)}",
              file=sys.stderr)
        sys.exit(1)

    if gate_name == 'SELECT':
        print("Error: SELECT gate is structural (always satisfied) — cannot bypass",
              file=sys.stderr)
        sys.exit(1)

    # ── Validate reason ──────────────────────────────────────────────────
    if not reason or len(reason) < 5:
        print("Error: --reason must be at least 5 characters (audit requirement)",
              file=sys.stderr)
        sys.exit(1)

    # ── Load state ───────────────────────────────────────────────────────
    root = find_project_root()
    state_path = root / '.claude' / 'memory' / 'project_state.yaml'
    if not state_path.exists():
        print("Error: project_state.yaml not found", file=sys.stderr)
        sys.exit(1)

    state = yaml.safe_load(state_path.read_text(encoding='utf-8')) or {}
    gates = state.get('wisc_gates') or {}

    # ── Validate gate exists and is required ─────────────────────────────
    gate = gates.get(gate_name)
    if not gate or not isinstance(gate, dict):
        print(f"Error: {gate_name} gate not found in wisc_gates. "
              f"Run /classify-task first to compute gates.", file=sys.stderr)
        sys.exit(1)

    current_status = gate.get('status', 'inactive')
    if current_status == 'bypassed':
        print(f"Warning: {gate_name} already bypassed (reason: {gate.get('bypass_reason', '?')})")
        sys.exit(0)

    if current_status != 'required':
        print(f"Error: {gate_name} status is '{current_status}' — can only bypass 'required' gates",
              file=sys.stderr)
        sys.exit(1)

    # ── Apply bypass ─────────────────────────────────────────────────────
    gate['status'] = 'bypassed'
    gate['bypass_reason'] = reason
    gate['satisfied_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    gate['satisfied_by'] = 'bypass'

    gates[gate_name] = gate
    state['wisc_gates'] = gates

    state_path.write_text(
        yaml.dump(state, allow_unicode=True, default_flow_style=False,
                  sort_keys=False),
        encoding='utf-8')

    # ── Audit ────────────────────────────────────────────────────────────
    cls = state.get('last_task_classification') or {}
    task_name = cls.get('task', 'unknown')
    emit_audit(gate_name, task_name, reason, root)

    # ── Report ───────────────────────────────────────────────────────────
    remaining = [n for n, g in gates.items()
                 if isinstance(g, dict) and g.get('status') == 'required']

    print(f"\u26a0\ufe0f  {gate_name} gate BYPASSED")
    print(f"   Reason: {reason}")
    print(f"   Task: {task_name}")
    if remaining:
        print(f"   Remaining required: {', '.join(remaining)}")
    else:
        print(f"   All gates satisfied/bypassed \u2014 code changes unblocked")


if __name__ == '__main__':
    main()
