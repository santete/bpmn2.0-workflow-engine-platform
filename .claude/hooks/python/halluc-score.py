#!/usr/bin/env python3
"""
Hallucination Risk Score (HRS) — composite scoring 7 signals
Trigger-only (KHÔNG chạy tự động trong PreToolUse/PostToolUse)

Usage:
  python3 .claude/hooks/python/halluc-score.py [options]

Options:
  --files <comma-list>     Files để scan (default: git diff vs HEAD)
  --tokens <int>           Session token count hiện tại (default: ước lượng từ chars)
  --save                   Append kết quả vào project_state.yaml hallucination_history
  --json                   Output JSON thay vì text
  --threshold <float>      Custom red threshold (default: 0.7)

Exit code:
  0 = HRS < red threshold
  1 = HRS >= red threshold (caller có thể block flow)
"""
import sys, os, re, json, time, argparse, subprocess, io
from pathlib import Path
from datetime import datetime, timezone

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Runtime thresholds (override via .claude/config/thresholds.json)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "config"))
    from thresholds import load as _load_thresholds
    _cfg = _load_thresholds()
    _ROTATE_THRESHOLD = int(_cfg.get("rotate_threshold", 120_000))
except Exception:
    _cfg = {}
    _ROTATE_THRESHOLD = 120_000

# ── Weights (configurable via thresholds.json → hrs_weights) ─────────────
_DEFAULT_W = {
    'cite_coverage':      0.25,
    'schema_match':       0.25,
    'confidence_density': 0.10,
    'static_errors':      0.20,
    'context_drift':      0.10,
    'failures':           0.05,
    'schema_staleness':   0.05,
}
W = {**_DEFAULT_W, **((_cfg.get("hrs_weights") or {}) if _cfg else {})}

CONFIDENCE_PATTERN = re.compile(
    r'\b(I believe|probably|should work|I think|might be|seems like|'
    r'likely|presumably|maybe|perhaps|in theory|I assume|I guess)\b',
    re.IGNORECASE
)

# ── Helpers ───────────────────────────────────────────────────────────────
def find_project_root() -> Path:
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd

def load_yaml_safe(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def read_cached_tokens(root: Path, max_age_s: int = 300) -> int | None:
    """Read total session token count cached by statusline (.claude/cache/last_tokens.json).
    Returns token count or None if missing/stale/unparseable.
    Cache freshness ensures we don't use a stale count from a previous session.
    """
    cache = root / '.claude' / 'cache' / 'last_tokens.json'
    if not cache.exists():
        return None
    try:
        data = json.loads(cache.read_text(encoding='utf-8'))
        if time.time() - float(data.get('ts', 0)) > max_age_s:
            return None
        toks = int(data.get('tokens', 0))
        return toks if toks > 0 else None
    except Exception:
        return None

def get_modified_files(root: Path) -> list:
    """Lấy files đã modify so với HEAD (or all source files nếu không phải git repo)."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD'],
            cwd=root, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return [str(root / f) for f in result.stdout.strip().split('\n') if f]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fallback: scan recently modified files (last hour)
    files = []
    cutoff = time.time() - 3600
    for ext in ('.py', '.js', '.ts', '.tsx', '.go', '.java'):
        for p in root.rglob(f'*{ext}'):
            if any(skip in str(p) for skip in ('node_modules', '.git', 'dist', 'build', '.venv')):
                continue
            try:
                if p.stat().st_mtime > cutoff:
                    files.append(str(p))
            except OSError:
                pass
    return files[:20]  # cap to 20 files

def read_files_content(files: list) -> str:
    chunks = []
    for f in files:
        try:
            chunks.append(Path(f).read_text(encoding='utf-8', errors='ignore'))
        except (OSError, UnicodeError):
            pass
    return '\n'.join(chunks)

# ── Signal 1: Cite source coverage ────────────────────────────────────────
def signal_cite_coverage(content: str) -> tuple:
    """Returns (score 0-1, total_refs, cited_refs)."""
    # External refs heuristic: method calls + field access
    method_calls = re.findall(r'\b\w+\.(\w+)\s*\(', content)
    field_access = re.findall(r'(?:response|data|result|payload)\s*[\.\[]\s*[\'"]?(\w+)', content)
    refs = set(method_calls + field_access)
    # Filter common Python/JS builtins
    builtins = {'get', 'set', 'append', 'pop', 'keys', 'values', 'items', 'split',
                'join', 'strip', 'replace', 'format', 'len', 'str', 'int', 'list',
                'dict', 'map', 'filter', 'reduce', 'forEach', 'push', 'shift'}
    refs = refs - builtins
    total = len(refs)
    if total == 0:
        return (1.0, 0, 0)
    # Cited: find "Based on `file:line`" or "Based on `schema_snapshot..."
    cited_count = len(re.findall(
        r'Based on\s+`[^`]+:\d+`|Based on\s+`schema_snapshot\.yaml#',
        content
    ))
    score = min(1.0, cited_count / total)
    return (score, total, cited_count)

# ── Signal 2: Schema match rate ───────────────────────────────────────────
def signal_schema_match(content: str, schema: dict) -> tuple:
    """Returns (score 0-1, total_refs, matched_refs, blocked_refs)."""
    if not schema:
        return (1.0, 0, 0, 0)

    known = set()
    not_available = set()

    for cat_name in ('external_apis', 'internal_apis'):
        for api in (schema.get(cat_name) or {}).values():
            if not isinstance(api, dict):
                continue
            ret = api.get('returns')
            if isinstance(ret, dict):
                known.update(ret.keys())
            known.update(api.get('optional') or [])
            known.update(api.get('required') or [])
            not_available.update(api.get('not_in_response') or [])
            not_available.update(api.get('NOT_available') or [])

    for table in (schema.get('database') or {}).values():
        if isinstance(table, dict):
            known.update(table.get('columns') or [])

    for ev in (schema.get('events') or {}).values():
        if isinstance(ev, dict):
            payload = ev.get('payload')
            if isinstance(payload, dict):
                known.update(payload.keys())

    # Extract refs from code
    refs = set()
    refs.update(re.findall(r'(?:response|data|result|row|record|payload)\s*\.\s*(\w+)', content))
    refs.update(re.findall(r'(?:response|data|result|row|record|payload)\s*\[\s*[\'"](\w+)[\'"]', content))
    refs = {r for r in refs if r and not r.startswith('_')}

    if not refs:
        return (1.0, 0, 0, 0)
    if not known:
        return (1.0, 0, 0, 0)  # schema empty — no judgment

    blocked = refs & not_available
    matched = refs & known
    if blocked:
        return (0.0, len(refs), len(matched), len(blocked))
    score = min(1.0, len(matched) / len(refs))
    return (score, len(refs), len(matched), 0)

# ── Signal 3: Confidence language density ─────────────────────────────────
def signal_confidence_density(content: str) -> tuple:
    """Returns (matches per 1k words, total_matches)."""
    matches = len(CONFIDENCE_PATTERN.findall(content))
    words = max(1, len(content.split()))
    density = matches / (words / 1000)
    return (density, matches)

# ── Signal 4: Static assertion failures ───────────────────────────────────
def signal_static_errors(files: list) -> tuple:
    """Returns (error_count, files_checked)."""
    errors = 0
    checked = 0
    for f in files:
        path = Path(f)
        if not path.exists():
            continue
        ext = path.suffix.lower()
        try:
            if ext == '.py':
                result = subprocess.run(
                    [sys.executable, '-c',
                     f'import ast,sys; ast.parse(open(r"{f}").read())'],
                    capture_output=True, timeout=10
                )
                checked += 1
                if result.returncode != 0:
                    errors += 1
                # Try mypy if available
                try:
                    mypy_result = subprocess.run(
                        ['mypy', '--no-error-summary', '--no-color-output', f],
                        capture_output=True, text=True, timeout=15
                    )
                    out = (mypy_result.stdout or '') + (mypy_result.stderr or '')
                    errors += len(re.findall(
                        r'has no attribute|undefined name|cannot find name|Module .* has no attribute',
                        out, re.IGNORECASE
                    ))
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            elif ext in ('.ts', '.tsx'):
                try:
                    tsc_result = subprocess.run(
                        ['npx', '--no-install', 'tsc', '--noEmit', '--allowJs', f],
                        capture_output=True, text=True, timeout=20
                    )
                    out = (tsc_result.stdout or '') + (tsc_result.stderr or '')
                    errors += len(re.findall(
                        r"Property '\w+' does not exist|Cannot find name",
                        out
                    ))
                    checked += 1
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
        except Exception:
            pass
    return (errors, checked)

# ── Signal 5: Context drift factor ────────────────────────────────────────
def signal_context_drift(token_count: int) -> float:
    """Returns drift 0-1 normalized to rotate_threshold from config."""
    return min(1.0, token_count / _ROTATE_THRESHOLD)

# ── Signal 6: Consecutive failures ────────────────────────────────────────
def signal_failures(state: dict) -> int:
    return int(state.get('consecutive_failures', 0) or 0)

# ── Signal 7: Schema staleness ────────────────────────────────────────────
def signal_schema_staleness(schema_path: Path) -> int:
    if not schema_path.exists():
        return 0
    age_days = (time.time() - schema_path.stat().st_mtime) / 86400
    return int(age_days)

# ── Composite ─────────────────────────────────────────────────────────────
def compute_hrs(signals: dict) -> float:
    s = signals
    hrs = (
        W['cite_coverage']      * (1 - s['cite_coverage']) +
        W['schema_match']       * (1 - s['schema_match']) +
        W['confidence_density'] * min(1.0, s['confidence_density'] / 3.0) +
        W['static_errors']      * min(1.0, s['static_errors'] / 3.0) +
        W['context_drift']      * s['context_drift'] +
        W['failures']           * min(1.0, s['failures'] / 4.0) +
        W['schema_staleness']   * min(1.0, s['schema_staleness'] / 30.0)
    )
    return round(hrs, 3)

def color_for(hrs: float, threshold: float) -> str:
    if hrs >= threshold:
        return 'RED'
    elif hrs >= threshold - 0.2:
        return 'ORANGE'
    elif hrs >= threshold - 0.4:
        return 'YELLOW'
    return 'GREEN'

def dominant_signal(signals: dict) -> str:
    contribs = {
        'cite_coverage':      W['cite_coverage']      * (1 - signals['cite_coverage']),
        'schema_match':       W['schema_match']       * (1 - signals['schema_match']),
        'confidence_density': W['confidence_density'] * min(1.0, signals['confidence_density'] / 3.0),
        'static_errors':      W['static_errors']      * min(1.0, signals['static_errors'] / 3.0),
        'context_drift':      W['context_drift']      * signals['context_drift'],
        'failures':           W['failures']           * min(1.0, signals['failures'] / 4.0),
        'schema_staleness':   W['schema_staleness']   * min(1.0, signals['schema_staleness'] / 30.0),
    }
    return max(contribs, key=contribs.get)

# ── Save to history ───────────────────────────────────────────────────────
def append_history(state_path: Path, hrs: float, signals: dict, dominant: str) -> None:
    state = load_yaml_safe(state_path)
    history = state.get('hallucination_history') or []
    history.append({
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'session': int(state.get('session_count', 0) or 0),
        'hrs': hrs,
        'dominant_signal': dominant,
        'signals': {k: round(v, 3) if isinstance(v, float) else v for k, v in signals.items()},
    })
    state['hallucination_history'] = history[-50:]  # keep last 50
    try:
        with state_path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(state, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        print(f"WARN: Cannot save history to {state_path}: {e}", file=sys.stderr)

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Hallucination Risk Score')
    parser.add_argument('--files', help='Comma-separated file list')
    parser.add_argument('--tokens', type=int, help='Session token count')
    parser.add_argument('--save', action='store_true', help='Append to project_state.yaml')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--threshold', type=float, default=0.7, help='Red threshold')
    args = parser.parse_args()

    root = find_project_root()
    schema_path = root / '.claude' / 'memory' / 'schema_snapshot.yaml'
    state_path  = root / '.claude' / 'memory' / 'project_state.yaml'

    schema = load_yaml_safe(schema_path)
    state  = load_yaml_safe(state_path)

    # Determine files
    if args.files:
        files = [f.strip() for f in args.files.split(',') if f.strip()]
    else:
        files = get_modified_files(root)

    content = read_files_content(files) if files else ''

    # Token count: explicit > statusline cache > char/4 estimate
    # Statusline writes .claude/cache/last_tokens.json on each refresh; reading it
    # makes /halluc-score consistent with the badge displayed in the status bar.
    if args.tokens is not None:
        tokens = args.tokens
        token_source = 'arg'
    else:
        cached = read_cached_tokens(root)
        if cached is not None:
            tokens = cached
            token_source = 'statusline-cache'
        else:
            tokens = len(content) // 4 if content else 0
            token_source = 'estimate-chars/4'

    # Compute signals
    cite_score, cite_total, cite_cited = signal_cite_coverage(content)
    schema_score, sch_total, sch_matched, sch_blocked = signal_schema_match(content, schema)
    conf_density, conf_count = signal_confidence_density(content)
    static_errors, static_checked = signal_static_errors(files)
    drift = signal_context_drift(tokens)
    failures = signal_failures(state)
    staleness = signal_schema_staleness(schema_path)

    signals = {
        'cite_coverage':      cite_score,
        'schema_match':       schema_score,
        'confidence_density': conf_density,
        'static_errors':      static_errors,
        'context_drift':      drift,
        'failures':           failures,
        'schema_staleness':   staleness,
    }

    hrs = compute_hrs(signals)
    color = color_for(hrs, args.threshold)
    dom = dominant_signal(signals)

    # Output
    if args.json:
        print(json.dumps({
            'hrs': hrs, 'color': color, 'threshold': args.threshold,
            'dominant_signal': dom, 'signals': signals,
            'details': {
                'cite_total': cite_total, 'cite_cited': cite_cited,
                'schema_total': sch_total, 'schema_matched': sch_matched,
                'schema_blocked': sch_blocked,
                'confidence_count': conf_count,
                'static_files_checked': static_checked,
                'token_count': tokens, 'token_source': token_source,
                'files_count': len(files),
            }
        }, ensure_ascii=False, indent=2))
    else:
        emoji = {'GREEN': '🟢', 'YELLOW': '🟡', 'ORANGE': '🟠', 'RED': '🔴'}[color]
        print(f"\n{'═' * 60}")
        print(f"  HALLUCINATION RISK SCORE")
        print(f"{'═' * 60}")
        print(f"  Overall: {hrs:.2f}  {emoji} {color}")
        print(f"  Threshold: {args.threshold}  |  Dominant: {dom}")
        print(f"  Files scanned: {len(files)}  |  Tokens: {tokens:,} ({token_source})")
        print(f"\n  Signals:")
        print(f"    [1] Cite coverage:     {cite_score*100:>5.0f}%   ({cite_cited}/{cite_total} refs)")
        print(f"    [2] Schema match:      {schema_score*100:>5.0f}%   ({sch_matched}/{sch_total} refs"
              + (f", {sch_blocked} BLOCKED" if sch_blocked else "") + ")")
        print(f"    [3] Confidence dens:   {conf_density:>5.2f}/k ({conf_count} matches)")
        print(f"    [4] Static errors:     {static_errors:>5}    ({static_checked} files checked)")
        print(f"    [5] Context drift:     {drift:>5.2f}     ({tokens:,} tokens / {_ROTATE_THRESHOLD//1000}k)")
        print(f"    [6] Consec failures:   {failures:>5}")
        print(f"    [7] Schema staleness:  {staleness:>5}d   (since last update)")
        print(f"\n  Recommendation:")
        if color == 'RED':
            print(f"    🔴 HALT — run recovery protocol (HALLUCINATION_RULES.md)")
            print(f"    🔴 Fix dominant signal: {dom}")
            if sch_blocked:
                print(f"    🔴 {sch_blocked} ref(s) trong NOT_available — Type 1 hallucination")
        elif color == 'ORANGE':
            print(f"    🟠 Halt Phase 2 — run /schema-check + load actual source")
            print(f"    🟠 Re-verify dominant signal: {dom}")
        elif color == 'YELLOW':
            print(f"    🟡 Warning — Claude tự verify thêm trước khi proceed")
            print(f"    🟡 Watch dominant signal: {dom}")
        else:
            print(f"    🟢 Continue normally")
        print(f"{'═' * 60}\n")

    if args.save:
        append_history(state_path, hrs, signals, dom)
        if not args.json:
            print(f"  📝 Appended to {state_path.relative_to(root)}\n")

    # Telemetry: log every /halluc-score run (fail-open)
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event as _write_event
        _write_event('halluc_score', {
            'hrs': round(hrs, 3),
            'color': color,
            'dominant': dom,
            'schema_blocked': sch_blocked,
            'tokens': tokens,
            'token_source': token_source,
            'files_count': len(files),
        }, root=root)
    except Exception:
        pass

    # Write HRS cache for statusline badge (fail-open)
    try:
        hrs_cache_dir = root / '.claude' / 'cache'
        hrs_cache_dir.mkdir(parents=True, exist_ok=True)
        (hrs_cache_dir / 'hrs_7d.json').write_text(
            json.dumps({
                'avg_hrs': round(hrs, 3),
                'dominant_color': color,
                'dominant_signal': dom,
                'ts': int(time.time()),
            }),
            encoding='utf-8',
        )
    except Exception:
        pass

    sys.exit(1 if hrs >= args.threshold else 0)

if __name__ == '__main__':
    main()
