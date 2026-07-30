#!/usr/bin/env python3
"""
Hook: PreToolCall — Bash
Chặn các lệnh nguy hiểm. Hard stops trong CLAUDE.md.

Exit 0 = cho phép Claude tiếp tục
Exit 2 = block Claude, hiển thị error
"""
import sys, json, re, io

if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    data    = json.loads(sys.stdin.read() or "{}")
    command = data.get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

if not command:
    sys.exit(0)


def block(reason: str) -> None:
    # Telemetry: log block event (fail-open)
    try:
        from pathlib import Path as _P
        sys.path.insert(0, str(_P(__file__).parent))
        from metrics_writer import write_event as _write_event
        _write_event('hook_block', {
            'hook': 'block-dangerous',
            'rule': reason,
            'command': command[:200],
            'severity': 'BLOCKER',
        })
    except Exception:
        pass
    print(f"❌ BLOCKED (dangerous command): {reason}", file=sys.stderr)
    print(f"Lệnh: {command}", file=sys.stderr)
    print("Nếu thực sự cần, user phải tự chạy thủ công.", file=sys.stderr)
    sys.exit(2)


# rm -rf nguy hiểm (root, home, /, *)
if re.search(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(/|~|\$HOME|\*)', command):
    block("rm -rf vào path nguy hiểm")

# Force push lên branch chung
if re.search(r'git\s+push.*--force([^-]|$)', command) and \
   re.search(r'(main|master|develop|prod)', command):
    block("git push --force lên branch chung")

# DROP / TRUNCATE qua psql / mysql CLI
if re.search(r'(psql|mysql).*-c.*(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE)', command, re.IGNORECASE):
    block("DROP / TRUNCATE qua DB CLI")

# Disable SSL / cert verify
if re.search(r'(--insecure|--no-check-certificate|GIT_SSL_NO_VERIFY)', command):
    block("Disable SSL verification")

# Curl pipe sh (chạy script không kiểm tra)
if re.search(r'curl[^|]+\|\s*(sh|bash)', command):
    block("curl | sh — không an toàn, phải xem script trước")

# Chmod 777
if re.search(r'chmod\s+(-R\s+)?777', command):
    block("chmod 777 — quá permissive")

# Global install không hỏi
if re.search(r'(npm|pnpm|yarn)\s+(i|install|add)\s+(-g|--global)', command):
    block("Install global package — phải hỏi user")

# Schema migration nguy hiểm
if re.search(r'(DROP\s+TABLE|TRUNCATE\s+TABLE|ALTER\s+TABLE.*DROP)', command, re.IGNORECASE):
    block("Schema migration nguy hiểm — phải hỏi user")

sys.exit(0)
