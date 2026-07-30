#!/usr/bin/env python3
"""
drift_check.py — detect divergence between codebase HEAD and the memory
baseline recorded in `.claude/memory/_sync_state.yaml`.

Three modes:
  drift_check.py             # default: silent if clean, 1-line warn if drift
  drift_check.py --verbose   # grouped report (added/modified/deleted x section)
  drift_check.py --json      # JSON for downstream consumption (hooks, slash)
  drift_check.py --baseline  # stamp current HEAD as the new sync point

Fail-open invariant — every code path catches and exits 0. Drift is
information, not a blocker. A drift_check crash must never freeze a session.

Wired into:
  - SessionStart hook (settings.json) — surfaces drift at session boot
  - Stop hook (session-end.py) — emits drift_nudge metric event at session end
  - /check-drift slash command — explicit invocation
  - /classify Bước 5 step 6 — calls --baseline after auto-scaffold accepted
  - /done step 5 — calls --baseline after successful task with memory writes
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Project root + git helpers
# ─────────────────────────────────────────────────────────────────────

def find_project_root(start: Path = None) -> Path:
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def git(args, cwd: Path) -> str:
    """Run git, return stdout. Empty string on any failure (fail-open)."""
    try:
        out = subprocess.run(
            ['git'] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0:
            return ''
        return out.stdout
    except Exception:
        return ''


def commit_exists(sha: str, cwd: Path) -> bool:
    if not sha:
        return False
    return bool(git(['cat-file', '-e', sha + '^{commit}'], cwd) is not None and
                subprocess.run(['git', 'cat-file', '-e', sha + '^{commit}'],
                               cwd=str(cwd), capture_output=True).returncode == 0)


# ─────────────────────────────────────────────────────────────────────
# Glob → regex (limited dialect, but tested)
# ─────────────────────────────────────────────────────────────────────

def glob_to_regex(pattern: str) -> str:
    """
    Convert a glob to a regex anchored at the start of a path.
    Supported:
      *       → [^/]*       (single segment)
      **      → .*          (any depth)
      ?       → [^/]
      literal . / -          (escaped)
    Limitations: no character classes, no brace expansion. Adequate for
    _sync_state.yaml path patterns.
    """
    out = ['^']
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                out.append('.*')
                i += 2
                # Eat trailing / after ** so "src/**" matches "src/foo"
                if i < len(pattern) and pattern[i] == '/':
                    i += 1
            else:
                out.append('[^/]*')
                i += 1
        elif c == '?':
            out.append('[^/]')
            i += 1
        elif c in '.+(){}|^$\\':
            out.append('\\' + c)
            i += 1
        else:
            out.append(c)
            i += 1
    out.append('$')
    return ''.join(out)


def matches_any(path: str, patterns) -> bool:
    """True if path matches any glob in patterns."""
    for pat in patterns:
        try:
            if re.match(glob_to_regex(pat), path):
                return True
        except Exception:
            continue
    return False


# ─────────────────────────────────────────────────────────────────────
# _sync_state.yaml loader (no PyYAML dep — minimal parser)
# ─────────────────────────────────────────────────────────────────────

def load_sync_state(root: Path) -> dict:
    """
    Minimal YAML reader for _sync_state.yaml. Avoids PyYAML so the harness
    has zero-deps install. Only parses the shape we control.
    """
    path = root / '.claude' / 'memory' / '_sync_state.yaml'
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return {}

    state = {
        'synced_at_commit': '',
        'synced_at_ts': 0,
        'synced_by': '',
        'watched_paths': [],
        'ignored_paths': [],
    }
    def _strip_inline_comment(s: str) -> str:
        # Strip `#...` only if `#` isn't inside quotes. We only support simple
        # values here, so a quoted string never contains `#` in practice — but
        # be conservative: if value starts with " or ', leave it.
        s = s.strip()
        if s.startswith('"') or s.startswith("'"):
            return s
        idx = s.find('#')
        return s[:idx].rstrip() if idx >= 0 else s

    current_list = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        # List item under current_list
        if current_list is not None and line.lstrip().startswith('- '):
            val = _strip_inline_comment(line.lstrip()[2:]).strip().strip('"').strip("'")
            if val:
                state[current_list].append(val)
            continue
        # Top-level key
        if not line.startswith(' ') and ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = _strip_inline_comment(val).strip('"').strip("'")
            if key in ('watched_paths', 'ignored_paths'):
                current_list = key
                continue
            current_list = None
            if key == 'synced_at_ts':
                try:
                    state[key] = int(val) if val else 0
                except Exception:
                    state[key] = 0
            elif key in state:
                state[key] = val
    return state


# ─────────────────────────────────────────────────────────────────────
# Diff + filter
# ─────────────────────────────────────────────────────────────────────

def get_committed_delta(baseline: str, root: Path) -> list:
    """Return list of (status, path) committed since baseline."""
    out = git(['diff', '--name-status', baseline + '..HEAD'], root)
    return _parse_name_status(out)


def get_uncommitted_delta(root: Path) -> list:
    """Return list of (status, path) for staged + unstaged + untracked."""
    delta = []
    # Staged + unstaged tracked files
    out = git(['diff', '--name-status', 'HEAD'], root)
    delta.extend(_parse_name_status(out))
    # Untracked files (status = "?")
    out = git(['ls-files', '--others', '--exclude-standard'], root)
    for line in out.splitlines():
        line = line.strip()
        if line:
            delta.append(('?', line))
    return delta


def _parse_name_status(diff_output: str) -> list:
    items = []
    for line in diff_output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        status = parts[0][:1]  # M / A / D / R (ignore similarity index after R)
        path = parts[-1]       # last column = current path (handles renames)
        items.append((status, path))
    return items


def filter_files(delta: list, watched: list, ignored: list) -> list:
    """Apply ignored (wins) then watched. Return filtered delta."""
    result = []
    for status, path in delta:
        if matches_any(path, ignored):
            continue
        if matches_any(path, watched):
            result.append((status, path))
    return result


def group_by_section(filtered: list) -> dict:
    """Group filtered changes into source/schema/manifest/other buckets."""
    groups = {'source': [], 'schema': [], 'manifest': [], 'other': []}
    for status, path in filtered:
        p = path.lower()
        if (p.startswith(('migrations/', 'db/')) or
                p.endswith(('.sql', '.prisma')) or
                'openapi' in p or 'swagger' in p):
            groups['schema'].append((status, path))
        elif (p in ('package.json', 'pom.xml', 'build.gradle', 'go.mod',
                    'pyproject.toml', 'requirements.txt', 'cargo.toml', 'gemfile')
              or p.endswith(('.csproj', '.fsproj'))
              or p == 'build.gradle.kts'):
            groups['manifest'].append((status, path))
        elif p.startswith(('src/', 'lib/', 'app/', 'internal/', 'pkg/', 'cmd/')):
            groups['source'].append((status, path))
        else:
            groups['other'].append((status, path))
    return groups


# ─────────────────────────────────────────────────────────────────────
# Modes
# ─────────────────────────────────────────────────────────────────────

def run_check(root: Path) -> dict:
    """
    Returns a result dict:
      {
        'status': 'no_sync_state' | 'baseline_missing' | 'clean' | 'drift',
        'baseline': '<sha>',
        'committed': [...],         # filtered (status, path)
        'uncommitted': [...],
        'groups': {...},            # only when status='drift'
        'message': '<short human-readable>',
      }
    """
    state = load_sync_state(root)
    if not state:
        return {'status': 'no_sync_state', 'message': '_sync_state.yaml not found',
                'baseline': '', 'committed': [], 'uncommitted': [], 'groups': {}}

    baseline = state.get('synced_at_commit', '')
    watched = state.get('watched_paths', []) or []
    ignored = state.get('ignored_paths', []) or []

    if not baseline:
        return {'status': 'baseline_missing',
                'message': 'sync_state has no baseline commit (run /classify or /check-drift --baseline)',
                'baseline': '', 'committed': [], 'uncommitted': [], 'groups': {}}

    if subprocess.run(['git', 'cat-file', '-e', baseline + '^{commit}'],
                      cwd=str(root), capture_output=True).returncode != 0:
        return {'status': 'baseline_missing',
                'message': f'baseline commit {baseline[:8]} not in repo (rebased?)',
                'baseline': baseline, 'committed': [], 'uncommitted': [], 'groups': {}}

    committed = filter_files(get_committed_delta(baseline, root), watched, ignored)
    uncommitted = filter_files(get_uncommitted_delta(root), watched, ignored)

    if not committed and not uncommitted:
        return {'status': 'clean', 'message': 'memory in sync with HEAD',
                'baseline': baseline, 'committed': [], 'uncommitted': [], 'groups': {}}

    groups = group_by_section(committed + uncommitted)
    total = len(committed) + len(uncommitted)
    return {
        'status': 'drift',
        'baseline': baseline,
        'committed': committed,
        'uncommitted': uncommitted,
        'groups': groups,
        'message': f'drift: {total} watched file(s) changed since {baseline[:8]}',
    }


def update_baseline(root: Path, source: str = 'manual') -> dict:
    """Stamp current HEAD into _sync_state.yaml. Preserves watched/ignored."""
    head = git(['rev-parse', 'HEAD'], root).strip()
    if not head:
        return {'ok': False, 'reason': 'not a git repo or HEAD missing'}

    path = root / '.claude' / 'memory' / '_sync_state.yaml'
    if not path.exists():
        return {'ok': False, 'reason': '_sync_state.yaml does not exist'}

    try:
        original = path.read_text(encoding='utf-8')
    except Exception as e:
        return {'ok': False, 'reason': f'read failed: {e}'}

    new_lines = []
    seen_keys = set()
    for raw in original.splitlines():
        if raw.startswith('synced_at_commit:'):
            new_lines.append(f'synced_at_commit: "{head}"')
            seen_keys.add('synced_at_commit')
        elif raw.startswith('synced_at_ts:'):
            new_lines.append(f'synced_at_ts: {int(time.time())}')
            seen_keys.add('synced_at_ts')
        elif raw.startswith('synced_by:'):
            new_lines.append(f'synced_by: "{source}"')
            seen_keys.add('synced_by')
        else:
            new_lines.append(raw)

    # Preserve trailing newline shape
    suffix = '\n' if original.endswith('\n') else ''
    try:
        path.write_text('\n'.join(new_lines) + suffix, encoding='utf-8')
    except Exception as e:
        return {'ok': False, 'reason': f'write failed: {e}'}

    return {'ok': True, 'baseline': head, 'source': source}


# ─────────────────────────────────────────────────────────────────────
# Output formatting
# ─────────────────────────────────────────────────────────────────────

def render_short(result: dict) -> str:
    s = result['status']
    if s == 'clean':
        return ''  # silent on clean - don't pollute SessionStart output
    if s == 'no_sync_state':
        return ''  # silent - pre-classify project
    if s == 'baseline_missing':
        return f'[drift_check] {result["message"]}'
    if s == 'drift':
        n = len(result['committed']) + len(result['uncommitted'])
        return f'[drift] {n} watched file(s) changed since baseline {result["baseline"][:8]} - run /check-drift'
    return ''


def render_verbose(result: dict) -> str:
    if result['status'] != 'drift':
        return result['message']
    lines = [f'Drift report - baseline {result["baseline"][:8]}',
             '-' * 56]
    for section in ('source', 'schema', 'manifest', 'other'):
        items = result['groups'].get(section, [])
        if not items:
            continue
        lines.append(f'\n[{section}] ({len(items)} file{"s" if len(items) != 1 else ""})')
        for status, path in items[:20]:  # cap per section
            lines.append(f'  {status}  {path}')
        if len(items) > 20:
            lines.append(f'  ... {len(items) - 20} more')
    lines.append('\nNext: review changes vs memory files. Re-baseline with /done or /check-drift --baseline.')
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Detect memory/codebase drift.')
    parser.add_argument('--verbose', action='store_true', help='full grouped report')
    parser.add_argument('--json', action='store_true', help='emit JSON')
    parser.add_argument('--baseline', action='store_true', help='stamp HEAD as new baseline')
    parser.add_argument('--source', default='manual', help='who is stamping (--baseline only)')
    args = parser.parse_args()

    # Force UTF-8 stdout so non-ASCII output never trips on Windows cp1252
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    try:
        root = find_project_root()

        if args.baseline:
            res = update_baseline(root, source=args.source)
            if args.json:
                print(json.dumps(res))
            else:
                if res.get('ok'):
                    print(f'✓ baseline stamped: {res["baseline"][:8]} (by {res["source"]})')
                else:
                    print(f'✗ baseline stamp failed: {res.get("reason", "unknown")}')
            sys.exit(0)

        result = run_check(root)
        if args.json:
            # Tuples don't serialize cleanly — flatten
            serializable = dict(result)
            for k in ('committed', 'uncommitted'):
                serializable[k] = [{'status': s, 'path': p} for s, p in result.get(k, [])]
            if 'groups' in serializable:
                serializable['groups'] = {
                    sec: [{'status': s, 'path': p} for s, p in items]
                    for sec, items in result['groups'].items()
                }
            print(json.dumps(serializable))
        elif args.verbose:
            out = render_verbose(result)
            if out:
                print(out)
        else:
            out = render_short(result)
            if out:
                print(out)
    except Exception:
        # Fail-open: never block a session
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
