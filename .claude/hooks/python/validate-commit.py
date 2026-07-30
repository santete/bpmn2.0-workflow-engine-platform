#!/usr/bin/env python3
"""
Hook: PreToolCall — Bash
Chặn git commit với message sai format.
Generic version — hoạt động với mọi project dùng Conventional Commits.
Customize COMMIT_TYPES và MAX_SUBJECT_LEN cho project của bạn.

Exit 0 = cho phép Claude tiếp tục
Exit 1 = block Claude, hiển thị error
"""
import sys, json, re, io

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Config — sửa theo project ─────────────────────────────────────────────────
COMMIT_TYPES    = "feat|fix|hotfix|refactor|test|docs|ci|chore|perf|security"
MAX_SUBJECT_LEN = 72
MAX_TOTAL_LEN   = 500
BAD_MESSAGES    = [
    r"^fix\s+bug", r"^fixed$", r"^update\s+code", r"^update$",
    r"^wip", r"^temp", r"^test\s+commit", r"^minor$",
    r"^changes$", r"^\.\.*$", r"^sửa", r"^fix\.$",
]

try:
    data    = json.loads(sys.stdin.read() or "{}")
    command = data.get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

if "git commit" not in command:
    sys.exit(0)

msg = ""
for pat in [r'-m\s+"((?:[^"\\]|\\.)+)"', r"-m\s+'((?:[^'\\]|\\.)+)'"]:
    m = re.search(pat, command)
    if m:
        msg = m.group(1).replace('\\"', '"').replace("\\'", "'")
        break

if not msg:
    sys.exit(0)

subject = msg.split("\n")[0].strip()
errors, warnings = [], []

CC = re.compile(rf"^(\[AI\] )?({COMMIT_TYPES})(\([^)]+\))?!?: .+")
if not CC.match(subject):
    errors.append(
        f"❌  Commit message không đúng Conventional Commits format\n"
        f"    Got    : '{subject}'\n"
        f"    Expect : feat(scope): description  |  Types: {COMMIT_TYPES}"
    )

if len(subject) > MAX_SUBJECT_LEN:
    errors.append(f"❌  Subject dài quá ({len(subject)}/{MAX_SUBJECT_LEN} chars)")

if len(msg) > MAX_TOTAL_LEN:
    errors.append(f"❌  Message vượt {MAX_TOTAL_LEN} chars ({len(msg)} chars)")

for bad in BAD_MESSAGES:
    if re.match(bad, subject, re.IGNORECASE):
        errors.append(f"❌  Message quá chung chung: '{subject}'")
        break

has_bang   = bool(re.match(rf"^(\[AI\] )?({COMMIT_TYPES})(\([^)]+\))?!:", subject))
has_footer = "BREAKING CHANGE:" in msg
if has_bang and not has_footer:
    warnings.append(
        "⚠️   Breaking change (!) phát hiện — nên thêm:\n"
        "    BREAKING CHANGE: <mô tả thay đổi + migration plan>"
    )

D = "─" * 58
if errors:
    print(f"\n{D}\n🚫  COMMIT BLOCKED — Conventional Commits violation\n{D}")
    for e in errors:
        print(f"\n{e}")
    for w in warnings:
        print(f"\n{w}")
    print(f"\n{D}\n")
    sys.exit(1)

if warnings:
    print(f"\n{D}\n⚠️   COMMIT WARNING\n{D}")
    for w in warnings:
        print(f"\n{w}")
    print(f"\n{D}\n")

print(f"✅  Commit OK: '{subject}'")
sys.exit(0)
