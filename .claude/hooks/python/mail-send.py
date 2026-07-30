#!/usr/bin/env python3
"""CLI: /mail-send — Send message to agent(s)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from mail_engine import (load_mailbox, save_mailbox, generate_msg_id,
                             now_iso, emit_event)

    if len(sys.argv) < 3:
        print("Usage: mail-send.py \"to\" \"subject | body\" [--task-ref tsk-xxxx]", file=sys.stderr)
        sys.exit(1)

    to = sys.argv[1]

    # Parse --task-ref if present
    task_ref = None
    args = sys.argv[2:]
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == '--task-ref' and i + 1 < len(args):
            task_ref = args[i + 1]
            i += 2
        else:
            filtered_args.append(args[i])
            i += 1

    content = ' '.join(filtered_args).strip()

    # Split on " | " for subject/body
    if ' | ' in content:
        subject, body = content.split(' | ', 1)
    else:
        subject = content
        body = ''

    if not subject:
        print("Subject cannot be empty", file=sys.stderr)
        sys.exit(1)

    data = load_mailbox()
    mailbox = data['mailbox']
    existing_ids = {m.get('id') for m in mailbox if isinstance(m, dict)}

    msg_id = generate_msg_id(existing_ids)
    ts = now_iso()

    new_msg = {
        'id': msg_id,
        'from': 'current-session',
        'to': to,
        'subject': subject.strip(),
        'body': body.strip(),
        'created_at': ts,
        'read_by': [],
    }
    if task_ref:
        new_msg['task_ref'] = task_ref

    mailbox.append(new_msg)

    if save_mailbox(data):
        print(f"Sent to {to}: \"{subject.strip()}\"")
        emit_event('mail_send', {'msg_id': msg_id, 'to': to, 'subject': subject.strip()})
        sys.exit(0)
    else:
        print("Failed to save mailbox", file=sys.stderr)
        sys.exit(1)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
