#!/usr/bin/env python3
"""
Hook: PostToolCall — Write|Edit|MultiEdit
Scan code quality violations ngay sau khi Claude viết file.
Generic version — hoạt động với Python, JS, TS, Java, Go, v.v.

Exit 0 = OK hoặc warnings only
Exit 1 = BLOCKER found — yêu cầu dev xem xét
"""
import sys, json, re, io
from pathlib import Path

# Windows fix: force utf-8 stdout (default cp1252 can't render box chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    data      = json.loads(sys.stdin.read() or "{}")
    file_path = data.get("tool_input", {}).get("path", "")
    content   = (data.get("tool_input", {}).get("file_text") or
                 data.get("tool_input", {}).get("new_str") or "")
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

if not content and file_path and Path(file_path).exists():
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        sys.exit(0)

if not content or not file_path:
    sys.exit(0)

SCAN_EXTS  = {".py",".js",".ts",".jsx",".tsx",".java",".go",".rb",".php",".cs"}
SKIP_PATHS = ["test","spec","vendor","node_modules","__pycache__",".venv","dist","build"]

if Path(file_path).suffix.lower() not in SCAN_EXTS:
    sys.exit(0)
if any(s in file_path.lower() for s in SKIP_PATHS):
    sys.exit(0)

lines    = content.splitlines()
blockers = []
warns    = []

def is_comment(line):
    return bool(re.match(r'\s*(#|//|\*|/\*)', line))

# ── BLOCKERS ──────────────────────────────────────────────────────────────────
DEBUG_RE = [
    (r"\bconsole\.(log|debug|warn)\s*\(", "console.log/debug"),
    (r"\bprint\s*\(",                       "print()"),
    (r"\bdebugger\b",                       "debugger"),
    (r"\bpdb\.set_trace\s*\(\)",            "pdb.set_trace()"),
    (r"\bbreakpoint\s*\(\)",                "breakpoint()"),
    (r"\bdd\s*\(",                          "dd()"),
    (r"\bvar_dump\s*\(",                    "var_dump()"),
]
for i, line in enumerate(lines, 1):
    if is_comment(line): continue
    for pat, label in DEBUG_RE:
        if re.search(pat, line):
            blockers.append(f"  L{i:>4}: {label}  →  {line.strip()[:80]}")

SECRET_RE = [
    (r'(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',      "Hardcoded password"),
    (r'(api_key|apikey|api_token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key"),
    (r'(secret|secret_key)\s*=\s*["\'][^"\']{8,}["\']',        "Hardcoded secret"),
    (r'glpat-[A-Za-z0-9_\-]{20,}',                             "GitLab PAT"),
    (r'ghp_[A-Za-z0-9]{36}',                                   "GitHub token"),
    (r'sk-[A-Za-z0-9]{32,}',                                   "OpenAI key"),
    (r'AKIA[0-9A-Z]{16}',                                       "AWS Access Key"),
]
found_secret = False
for i, line in enumerate(lines, 1):
    if found_secret: break
    if any(kw in line for kw in ["os.environ", "os.getenv", "process.env"]): continue
    for pat, label in SECRET_RE:
        if re.search(pat, line, re.IGNORECASE):
            blockers.append(f"  L{i:>4}: 🔴 {label} — verify immediately")
            found_secret = True
            break

SQL_RE = [r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*\{',
          r'".*(?:SELECT|WHERE).*"\s*\+',
          r'`.*(?:SELECT|WHERE).*\$\{']
for i, line in enumerate(lines, 1):
    for pat in SQL_RE:
        if re.search(pat, line, re.IGNORECASE):
            blockers.append(
                f"  L{i:>4}: SQL injection risk  →  {line.strip()[:72]}\n"
                f"        Use parameterized queries / ORM"
            )
            break

PAN_LOG_RE = re.compile(
    r'\b(log|logger|print)\b.*\b(pan|card_number|cvv|cvc|track2)\b',
    re.IGNORECASE)
for i, line in enumerate(lines, 1):
    if is_comment(line): continue
    if PAN_LOG_RE.search(line):
        blockers.append(
            f"  L{i:>4}: 🔴 PAN/CVV logging — PCI DSS violation  →  {line.strip()[:60]}"
        )

# ── PLACEHOLDER BLOCKERS ──────────────────────────────────────────────────────
PLACEHOLDER_RE = [
    (r"\bTBD\b",                                             "TBD placeholder"),
    (r"\bPLACEHOLDER\b",                                    "PLACEHOLDER marker"),
    (r"#\s*placeholder\b",                                   "placeholder comment"),
    (r"//\s*placeholder\b",                                  "placeholder comment"),
    (r"\badd\s+(validation|implementation|logic)\s+later\b", "deferred implementation"),
    (r"\bwill\s+implement\b",                                "deferred implementation"),
    (r"\bsimilar\s+to\s+task\b",                             "vague reference to other task"),
    (r"\bTODO\s*:\s*$",                                      "empty TODO (no description)"),
]
for i, line in enumerate(lines, 1):
    for pat, label in PLACEHOLDER_RE:
        if re.search(pat, line, re.IGNORECASE):
            blockers.append(f"  L{i:>4}: {label}  →  {line.strip()[:80]}")
            break  # one match per line is enough

# ── WARNINGS ─────────────────────────────────────────────────────────────────
TICKET_RE = re.compile(r"(#\d+|[A-Z]{2,}-\d+|TICKET|ISSUE)", re.IGNORECASE)
for i, line in enumerate(lines, 1):
    if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
        if not TICKET_RE.search(line):
            warns.append(f"  L{i:>4}: TODO/FIXME without ticket ref  →  {line.strip()[:60]}")

PII_LOG = re.compile(r"\b(log|logger)\b.*(email|password|token|card|phone|ssn)", re.IGNORECASE)
for i, line in enumerate(lines, 1):
    if PII_LOG.search(line):
        warns.append(f"  L{i:>4}: PII possibly logged  →  {line.strip()[:70]}")

EMPTY_CATCH = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}|except\s*:")
for i, line in enumerate(lines, 1):
    if EMPTY_CATCH.search(line):
        warns.append(f"  L{i:>4}: Empty catch / bare except  →  silent failure risk")

if not blockers and not warns:
    sys.exit(0)

# Telemetry: log block events (fail-open)
if blockers:
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from metrics_writer import write_event as _write_event
        # Extract rule labels from blocker messages (first colon-separated chunk after L<num>:)
        rules = []
        for b in blockers:
            m = re.search(r'L\s*\d+:\s*(?:🔴\s*)?([^→\n]+?)(?:\s*→|\n|$)', b)
            if m:
                rules.append(m.group(1).strip()[:40])
        for rule in rules or ['unknown']:
            _write_event('hook_block', {
                'hook': 'post-write-check',
                'rule': rule,
                'file': file_path,
                'severity': 'BLOCKER',
            })
    except Exception:
        pass

D         = "─" * 58
short     = file_path.replace(str(Path.home()), "~")

print(f"\n{D}")
if blockers:
    print(f"🔴  BLOCKER(s) — {short}")
    print(D)
    print("  Fix before MR submission:\n")
    for b in blockers: print(b)
if warns:
    if blockers: print()
    if not blockers:
        print(f"⚠️   WARNINGS — {short}")
        print(D)
    for w in warns: print(w)
print(f"\n{D}\n")

sys.exit(1 if blockers else 0)
