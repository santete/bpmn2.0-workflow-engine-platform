#!/usr/bin/env python3
"""
Hook: SessionStart — Agent Mail unread summary.
Show unread message count at session start.
Fail-open: any error → exit 0 (don't block session).
"""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit(0)  # PyYAML not installed — skip silently

try:
    mail_path = Path('.claude/memory/agent_mail.yaml')
    if not mail_path.exists():
        sys.exit(0)

    data = yaml.safe_load(mail_path.read_text(encoding='utf-8')) or {}
    messages = data.get('mailbox', [])
    if not messages:
        sys.exit(0)

    # Count unread: messages where "current-session" not in read_by
    # and to is "all" or matches current session
    unread = [m for m in messages
              if 'current-session' not in m.get('read_by', [])]

    if unread:
        subjects = ', '.join(f'"{m.get("subject", "")}"' for m in unread[:3])
        print(f"Mail: {len(unread)} unread — {subjects}")

except Exception:
    pass  # fail-open

sys.exit(0)
