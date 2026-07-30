"""
mail_engine — shared library for agent mail CLI scripts.

Schema-guarded YAML operations for .claude/memory/agent_mail.yaml.
Follows task_engine.py / memory_writer.py patterns.

Used by: mail-send.py, mail-read.py, mail-list.py, beads-doctor.py
"""
import secrets
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from task_engine import find_project_root, now_iso, emit_event

# Ensure UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


# ── Path helper ──────────────────────────────────────────────────────

def _mailbox_path(root=None):
    root = root or find_project_root()
    return root / '.claude' / 'memory' / 'agent_mail.yaml'


# ── YAML I/O ─────────────────────────────────────────────────────────

def load_mailbox(root=None):
    """Read agent_mail.yaml. Returns {'mailbox': []} on any error."""
    path = _mailbox_path(root)
    if not path.exists() or yaml is None:
        return {'mailbox': []}
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        if 'mailbox' not in data or not isinstance(data['mailbox'], list):
            data['mailbox'] = []
        return data
    except Exception:
        return {'mailbox': []}


def save_mailbox(data, root=None):
    """Atomic write with backup/verify pattern."""
    if yaml is None:
        return False
    path = _mailbox_path(root)
    try:
        # Backup
        bak = None
        if path.exists():
            bak = path.with_suffix('.yaml.bak')
            try:
                shutil.copy2(str(path), str(bak))
            except Exception:
                bak = None

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True,
                           default_flow_style=False)

        # Verify
        with path.open('r', encoding='utf-8') as f:
            verify = yaml.safe_load(f)
        if not verify or not isinstance(verify.get('mailbox'), list):
            if bak and bak.exists():
                shutil.copy2(str(bak), str(path))
            return False

        return True
    except Exception:
        try:
            if bak and bak.exists():
                shutil.copy2(str(bak), str(path))
        except Exception:
            pass
        return False


# ── ID generation ────────────────────────────────────────────────────

def generate_msg_id(existing_ids=None):
    """Generate unique message ID: msg- + 4 hex chars."""
    existing = existing_ids or set()
    for _ in range(10):
        new_id = f'msg-{secrets.token_hex(2)}'
        if new_id not in existing:
            return new_id
    return f'msg-{secrets.token_hex(3)}'


# ── Query helpers ────────────────────────────────────────────────────

def get_unread(mailbox, reader='current-session'):
    """Filter unread messages for the given reader.
    Matches: to='all' or to=reader, AND reader not in read_by."""
    unread = []
    for msg in mailbox:
        if not isinstance(msg, dict):
            continue
        to = msg.get('to', '')
        read_by = msg.get('read_by', [])
        if reader in read_by:
            continue
        if to == 'all' or to == reader:
            unread.append(msg)
    return unread


def mark_read(messages, reader='current-session'):
    """Append reader to read_by of each message (in-place)."""
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if 'read_by' not in msg or not isinstance(msg['read_by'], list):
            msg['read_by'] = []
        if reader not in msg['read_by']:
            msg['read_by'].append(reader)
