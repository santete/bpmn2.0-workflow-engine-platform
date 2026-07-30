#!/usr/bin/env python3
"""CLI: /mail-read — Show unread messages and mark as read."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from mail_engine import (load_mailbox, save_mailbox, get_unread,
                             mark_read, emit_event)

    data = load_mailbox()
    mailbox = data.get('mailbox', [])
    unread = get_unread(mailbox)

    if not unread:
        print("No unread messages.")
        sys.exit(0)

    print(f"## Unread Messages ({len(unread)})\n")

    for msg in unread:
        msg_id = msg.get('id', '?')
        frm = msg.get('from', '?')
        date = msg.get('created_at', '?')[:16]
        subject = msg.get('subject', '?')
        body = msg.get('body', '')
        task_ref = msg.get('task_ref', '')

        print(f"### {msg_id} — from: {frm} ({date})")
        print(f"**Subject:** {subject}")
        if body:
            print(f"**Body:** {body}")
        if task_ref:
            print(f"**Task ref:** {task_ref}")
        print()
        print("---\n")

    # Mark all displayed as read
    mark_read(unread)
    if save_mailbox(data):
        emit_event('mail_read', {'count': len(unread)})

    print(f"→ Reply: `/mail-send <to> <subject> | <body>`")

except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)

sys.exit(0)
