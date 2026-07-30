#!/usr/bin/env python3
"""
Hook: PostToolUse — Write|Edit|MultiEdit
WISC Auto-Satisfy — detect when WISC gate artifacts are created/modified
and auto-flip gate status from 'required' → 'satisfied'.

Detects:
  - spec.md → satisfies WRITE gate
  - scout_report*.md → satisfies ISOLATE gate

Exit 0 always (informational hook, never blocks).
Fail-open: any error → exit 0.
"""
import sys
import json
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
    sys.exit(0)


def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def _emit_audit(gate: str, artifact: str, task: str, root: Path):
    """Emit wisc_audit gate_satisfied event (fail-open)."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event
        write_event('wisc_audit', {
            'action': 'gate_satisfied',
            'gate': gate,
            'task': task,
            'from_status': 'required',
            'to_status': 'satisfied',
            'artifact': artifact,
            'satisfied_by': 'auto',
        }, root=root)
    except Exception:
        pass


try:
    data = json.loads(sys.stdin.read() or "{}")
    tool_input = data.get("tool_input", {})

    # Get target file from tool_input
    target = (tool_input.get("file_path") or
              tool_input.get("path") or "")
    if not target:
        sys.exit(0)

    target_lower = target.lower().replace('\\', '/')
    target_name = Path(target).name.lower()

    # ── Detect which gate artifact this might be ─────────────────────────
    gate_to_satisfy = None

    # WRITE gate: spec.md anywhere
    if target_name == 'spec.md':
        gate_to_satisfy = 'WRITE'

    # ISOLATE gate: scout_report*.md in .claude/memory/
    if (target_name.startswith('scout_report') and target_name.endswith('.md')
            and '.claude/memory' in target_lower):
        gate_to_satisfy = 'ISOLATE'

    if not gate_to_satisfy:
        sys.exit(0)

    # ── Load project state and update gate ───────────────────────────────
    root = find_project_root()
    state_path = root / '.claude' / 'memory' / 'project_state.yaml'
    if not state_path.exists():
        sys.exit(0)

    state = yaml.safe_load(state_path.read_text(encoding='utf-8')) or {}
    gates = state.get('wisc_gates') or {}

    gate = gates.get(gate_to_satisfy)
    if not gate or not isinstance(gate, dict):
        sys.exit(0)

    # Only auto-satisfy if currently 'required'
    if gate.get('status') != 'required':
        sys.exit(0)

    # Flip to satisfied
    gate['status'] = 'satisfied'
    gate['satisfied_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    gate['satisfied_by'] = 'auto'

    gates[gate_to_satisfy] = gate
    state['wisc_gates'] = gates

    state_path.write_text(
        yaml.dump(state, allow_unicode=True, default_flow_style=False,
                  sort_keys=False),
        encoding='utf-8')

    # Inform user
    remaining = [n for n, g in gates.items()
                 if isinstance(g, dict) and g.get('status') == 'required']
    print(f"WISC: {gate_to_satisfy} gate satisfied (artifact: {target_name})")
    if remaining:
        print(f"  Remaining required gates: {', '.join(remaining)}")
    else:
        print(f"  All WISC gates satisfied — code changes unblocked")

    # Audit trail
    cls = state.get('last_task_classification') or {}
    _emit_audit(gate_to_satisfy, target_name, cls.get('task', 'unknown'), root)

except SystemExit:
    raise
except Exception:
    pass

sys.exit(0)
