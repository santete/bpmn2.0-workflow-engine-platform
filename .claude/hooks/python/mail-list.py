#!/usr/bin/env python3
"""CLI: /mail-list — Show all agent messages."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from mail_engine import load_mailbox, get_unread

    data = load_mailbox()
    mailbox = data.get('mailbox', [])

    if not mailbox:
        print("Mailbox rỗng. Dùng `/mail-send <to> <subject> | <body>` để gửi message.")
        sys.exit(0)

    unread = get_unread(mailbox)
    unread_ids = {m.get('id') for m in unread}
    total = len(mailbox)
    unread_count = len(unread)

    print(f"## Agent Mail — {total} messages ({unread_count} unread)\n")
    print("| # | ID | From | To | Subject | Date | Read? |")
    print("|---|----|------|----|---------|------|-------|")

    # Sort newest first
    sorted_mail = sorted(mailbox, key=lambda m: m.get('created_at', ''), reverse=True)
    for i, msg in enumerate(sorted_mail, 1):
        msg_id = msg.get('id', '?')
        frm = msg.get('from', '?')
        to = msg.get('to', '?')
        subject = msg.get('subject', '?')[:40]
        date = msg.get('created_at', '?')[:16]
        read_status = 'no' if msg_id in unread_ids else 'yes'
        print(f"| {i} | {msg_id} | {frm} | {to} | {subject} | {date} | {read_status} |")

    print(f"\n→ Read unread: `/mail-read` | Send: `/mail-send <to> <subject> | <body>`")

except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)

sys.exit(0)
