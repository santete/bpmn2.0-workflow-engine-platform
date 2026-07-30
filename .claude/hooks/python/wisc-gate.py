#!/usr/bin/env python3
"""
Hook: PreToolUse — Edit|Write|MultiEdit
WISC Governance Gate (Tier 2) — chặn code change khi WISC gates chưa satisfied.

Logic đơn giản:
  1. Đọc wisc_gates từ project_state.yaml
  2. Nếu gate nào có status == 'required' → BLOCK
  3. COMPRESS: luôn check token count bất kể status (real-time gate)

State calculation đã được wisc-state.py xử lý sau /classify-task.
Hook này chỉ đọc, KHÔNG derive logic từ D5/D6.

Backward compatible: nếu wisc_gates trống nhưng có classification với D5/D6,
fallback về Tier 1 logic (derive từ D5/D6 + check artifact).

Exit 0 = cho phép
Exit 2 = block (hiển thị lý do, Claude phải fix trước khi tiếp)

Fail-open: parse error / missing yaml / missing PyYAML → exit 0.
"""
import sys
import json
import io
from pathlib import Path

# Windows fix: force utf-8 stderr
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Fail-open wrapper ────────────────────────────────────────────────────────
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


def _emit_audit(gate: str, action: str, detail: str, root: Path):
    """Emit wisc_audit event (fail-open). Unified audit trail for Tier 3."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event
        write_event('wisc_audit', {
            'action': action,
            'gate': gate,
            'detail': detail[:200],
        }, root=root)
    except Exception:
        pass


def block(gate: str, reason: str, fix_hint: str, root: Path):
    """Block the tool call with clear guidance."""
    _emit_audit(gate, 'gate_blocked', reason, root)
    D = "\u2500" * 58
    print(f"\n{D}", file=sys.stderr)
    print(f"\U0001f6e1\ufe0f  WISC GATE BLOCKED \u2014 {gate}", file=sys.stderr)
    print(D, file=sys.stderr)
    print(f"\n  L\u00fd do : {reason}", file=sys.stderr)
    print(f"  Fix   : {fix_hint}", file=sys.stderr)
    print(f"\n  Bypass: /wisc-bypass {gate} --reason \"<l\u00fd do>\" (ho\u1eb7c: python .claude/hooks/python/wisc-bypass.py {gate} --reason \"...\")", file=sys.stderr)
    print(f"          (c\u1ea7n user approve)", file=sys.stderr)
    print(f"\n{D}\n", file=sys.stderr)
    sys.exit(2)


# ── Tier 1 fallback ─────────────────────────────────────────────────────────
def _tier1_fallback(state: dict, root: Path, compress_threshold: int):
    """Backward-compatible: derive gates from D5/D6 if wisc_gates not populated."""
    classification = state.get('last_task_classification') or {}
    if not classification:
        return  # No classification → no enforcement

    d5 = str(classification.get('D5', '')).lower()
    d6 = str(classification.get('D6', '')).lower()

    # WRITE gate
    if d5 == 'vague':
        candidates = [root / 'spec.md', root / 'docs' / 'spec.md',
                      root / '.claude' / 'memory' / 'spec.md']
        if not any(p.exists() for p in candidates):
            block('WRITE',
                  f'D5={d5} \u2014 spec ch\u01b0a r\u00f5, nh\u01b0ng ch\u01b0a c\u00f3 spec.md',
                  'Vi\u1ebft spec.md tr\u01b0\u1edbc khi code, ho\u1eb7c ch\u1ea1y /classify-task \u0111\u1ec3 set wisc_gates',
                  root)

    # ISOLATE gate
    if d6 in ('unknown', 'legacy-undocumented', 'cross-module'):
        memory_dir = root / '.claude' / 'memory'
        scouts = list(memory_dir.glob('scout_report*')) if memory_dir.exists() else []
        if not scouts:
            block('ISOLATE',
                  f'D6={d6} \u2014 codebase ch\u01b0a quen, nh\u01b0ng ch\u01b0a c\u00f3 scout report',
                  'Ch\u1ea1y sub-agent scout tr\u01b0\u1edbc khi code, ho\u1eb7c ch\u1ea1y /classify-task \u0111\u1ec3 set wisc_gates',
                  root)

    # COMPRESS gate
    _check_compress(root, compress_threshold)


def _check_compress(root: Path, threshold: int):
    """Real-time token check — applies regardless of Tier."""
    token_cache = root / '.claude' / 'cache' / 'last_tokens.json'
    if not token_cache.exists():
        return
    try:
        cached = json.loads(token_cache.read_text(encoding='utf-8'))
        current_tokens = int(cached.get('tokens', 0))
        if current_tokens > threshold:
            block('COMPRESS',
                  f'Token count ({current_tokens:,}) v\u01b0\u1ee3t threshold ({threshold:,})',
                  'Ch\u1ea1y /rotate \u0111\u1ec3 \u0111\u00f3ng session hi\u1ec7n t\u1ea1i v\u00e0 m\u1edf session m\u1edbi. '
                  'Ho\u1eb7c: /compact c\u00f3 focus \u0111\u1ec3 gi\u1ea3m context.',
                  root)
    except (json.JSONDecodeError, ValueError, KeyError):
        pass


try:
    # ── Parse stdin ──────────────────────────────────────────────────────────
    data = json.loads(sys.stdin.read() or "{}")
    tool_input = data.get("tool_input", {})

    target_file = (tool_input.get("file_path") or
                   tool_input.get("path") or "")

    if not target_file:
        sys.exit(0)  # No target file — nothing to gate

    # Skip non-source files
    SKIP_PATTERNS = [
        '.claude/', '.claude\\',
        'docs/ai/', 'docs\\ai\\',
        'node_modules/', '__pycache__/',
        '.yaml', '.yml', '.md', '.json', '.toml',
        '.gitignore', '.env',
    ]
    if target_file:
        target_lower = target_file.lower().replace('\\', '/')
        if any(skip in target_lower for skip in SKIP_PATTERNS):
            sys.exit(0)

    # ── Load project state ───────────────────────────────────────────────────
    root = find_project_root()
    state_path = root / '.claude' / 'memory' / 'project_state.yaml'
    if not state_path.exists():
        sys.exit(0)

    state = yaml.safe_load(state_path.read_text(encoding='utf-8')) or {}

    # ── Load thresholds ──────────────────────────────────────────────────────
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'config'))
        from thresholds import load as _load_thresholds
        cfg = _load_thresholds()
        compress_threshold = int(cfg.get('rotate_threshold', 120_000))
    except Exception:
        compress_threshold = 120_000

    # ── Read wisc_gates ──────────────────────────────────────────────────────
    wisc_gates = state.get('wisc_gates') or {}

    # If wisc_gates has no structured status fields → Tier 1 fallback
    has_tier2_gates = any(
        isinstance(g, dict) and 'status' in g
        for g in wisc_gates.values()
    )

    if not has_tier2_gates:
        _tier1_fallback(state, root, compress_threshold)
        sys.exit(0)

    # ═══════════════════════════════════════════════════════════════════════════
    # Tier 2: Read status field directly
    # ═══════════════════════════════════════════════════════════════════════════

    GATE_FIX_HINTS = {
        'WRITE': 'Viết spec.md (hoặc hỏi user clarify) trước khi code. '
                 'wisc-satisfy.py sẽ auto-flip khi spec.md được tạo.',
        'ISOLATE': 'Chạy sub-agent scout → .claude/memory/scout_report_<task>.md '
                   'trước khi code. wisc-satisfy.py sẽ auto-flip khi report được tạo.',
    }

    for gate_name in ('WRITE', 'ISOLATE'):
        gate = wisc_gates.get(gate_name)
        if not isinstance(gate, dict):
            continue
        if gate.get('status') == 'required':
            artifact = gate.get('artifact', '')
            # Double-check: maybe artifact was created but wisc-satisfy hasn't run yet
            if artifact and (root / artifact).exists():
                continue  # Artifact exists — don't block (satisfy will catch up)
            block(
                gate=gate_name,
                reason=f'{gate_name} gate is REQUIRED but not yet satisfied'
                       + (f' (artifact: {artifact})' if artifact else ''),
                fix_hint=GATE_FIX_HINTS.get(gate_name, f'Satisfy {gate_name} gate first'),
                root=root,
            )

    # COMPRESS: always real-time check regardless of status
    compress_gate = wisc_gates.get('COMPRESS') or {}
    if isinstance(compress_gate, dict) and compress_gate.get('status') not in ('satisfied', 'bypassed'):
        _check_compress(root, compress_threshold)

    sys.exit(0)

except SystemExit:
    raise
except Exception:
    sys.exit(0)
