#!/usr/bin/env python3
"""CLI: /beads-doctor — Health check for task tracker, hooks, dependencies, mail."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import (load_tracker, find_task, check_circular_deps,
                             find_project_root)
    from mail_engine import load_mailbox, get_unread

    root = find_project_root()
    score = 10
    warnings = 0
    blockers = 0

    print("## Beads Doctor\n")

    # ── 1. Task Tracker ─────────────────────────────────────────────
    print("### Task Tracker")
    data = load_tracker(root)
    tasks = data.get('tasks', [])

    if not tasks:
        print("  Task tracker rỗng (no tasks)")
        print()
    else:
        # Schema validation
        required_fields = {'id', 'title', 'status'}
        valid_statuses = {'open', 'in_progress', 'blocked', 'closed'}
        schema_ok = True

        for t in tasks:
            if not isinstance(t, dict):
                print(f"  BLOCKER: task entry is not a dict: {t}")
                schema_ok = False
                blockers += 1
                continue
            missing = required_fields - set(t.keys())
            if missing:
                print(f"  BLOCKER: task {t.get('id', '?')} missing fields: {missing}")
                schema_ok = False
                blockers += 1
            if t.get('status') not in valid_statuses:
                print(f"  WARNING: task {t.get('id', '?')} has invalid status: {t.get('status')}")
                warnings += 1
                score -= 1

        if schema_ok:
            print(f"  OK: Schema valid ({len(tasks)} tasks)")

        # Unique IDs
        ids = [t.get('id') for t in tasks if isinstance(t, dict)]
        if len(ids) == len(set(ids)):
            print(f"  OK: All IDs unique")
        else:
            dupes = [i for i in ids if ids.count(i) > 1]
            print(f"  BLOCKER: Duplicate IDs: {set(dupes)}")
            blockers += 1
            score -= 2

        # Circular dependencies
        has_cycle = False
        for t in tasks:
            if not isinstance(t, dict):
                continue
            for blocked_id in t.get('blocks', []):
                cycle = check_circular_deps(tasks, t['id'], blocked_id)
                if cycle:
                    path_str = ' -> '.join(cycle)
                    print(f"  BLOCKER: Circular dependency: {path_str}")
                    has_cycle = True
                    blockers += 1
                    score -= 2
                    break
            if has_cycle:
                break
        if not has_cycle:
            print(f"  OK: No circular dependencies")

        # Consistency: blocks/blocked_by symmetry
        consistency_issues = 0
        task_map = {t['id']: t for t in tasks if isinstance(t, dict) and t.get('id')}
        for t in tasks:
            if not isinstance(t, dict):
                continue
            tid = t.get('id')
            # Check: if A.blocks contains B, then B.blocked_by should contain A
            for b in t.get('blocks', []):
                bt = task_map.get(b)
                if bt and tid not in bt.get('blocked_by', []):
                    print(f"  WARNING: {tid}.blocks has {b} but {b}.blocked_by missing {tid}")
                    consistency_issues += 1
            # Check: if A.blocked_by contains B, then B.blocks should contain A
            for b in t.get('blocked_by', []):
                bt = task_map.get(b)
                if bt and tid not in bt.get('blocks', []):
                    print(f"  WARNING: {b}.blocks missing {tid} but {tid}.blocked_by has {b}")
                    consistency_issues += 1

        if consistency_issues == 0:
            print(f"  OK: blocks/blocked_by symmetry")
        else:
            warnings += consistency_issues
            score -= min(consistency_issues, 2)

        # Status consistency
        status_issues = 0
        closed_ids = {t['id'] for t in tasks if isinstance(t, dict) and t.get('status') == 'closed'}
        for t in tasks:
            if not isinstance(t, dict):
                continue
            status = t.get('status')
            blocked_by = t.get('blocked_by', [])
            # Blocked but no blockers
            if status == 'blocked' and not blocked_by:
                print(f"  WARNING: {t['id']} is 'blocked' but blocked_by is empty")
                status_issues += 1
            # Open but has unresolved blockers
            if status == 'open' and blocked_by:
                unresolved = [b for b in blocked_by if b not in closed_ids]
                if unresolved:
                    print(f"  WARNING: {t['id']} is 'open' but has unresolved blockers: {unresolved}")
                    status_issues += 1

        if status_issues == 0:
            print(f"  OK: Status consistency")
        else:
            warnings += status_issues
            score -= min(status_issues, 2)

        # DAG stats
        edges = sum(len(t.get('blocks', [])) for t in tasks if isinstance(t, dict))
        print(f"  INFO: Dependency DAG: {len(tasks)} tasks, {edges} edges")

    print()

    # ── 2. Hooks ─────────────────────────────────────────────────────
    print("### Hooks")
    settings_path = root / '.claude' / 'settings.json'
    if settings_path.exists():
        import json
        try:
            settings = json.loads(settings_path.read_text(encoding='utf-8'))
            hooks = settings.get('hooks', {})

            # Check SessionStart hooks
            session_hooks = hooks.get('SessionStart', [])
            session_cmds = []
            for h in session_hooks:
                for hook in h.get('hooks', []):
                    session_cmds.append(hook.get('command', ''))

            has_task_summary = any('task-summary' in c for c in session_cmds)
            has_mail_summary = any('mail-summary' in c for c in session_cmds)

            if has_task_summary:
                print(f"  OK: SessionStart: task-summary")
            else:
                print(f"  WARNING: SessionStart: task-summary not configured")
                warnings += 1
                score -= 1

            if has_mail_summary:
                print(f"  OK: SessionStart: mail-summary")
            else:
                print(f"  WARNING: SessionStart: mail-summary not configured")
                warnings += 1
                score -= 1

            # Check Stop hooks
            stop_hooks = hooks.get('Stop', [])
            stop_cmds = []
            for h in stop_hooks:
                for hook in h.get('hooks', []):
                    stop_cmds.append(hook.get('command', ''))

            has_session_end = any('session-end' in c for c in stop_cmds)
            if has_session_end:
                print(f"  OK: Stop: session-end")
            else:
                print(f"  WARNING: Stop: session-end not configured")
                warnings += 1
                score -= 1
        except Exception as e:
            print(f"  WARNING: Cannot parse settings.json: {e}")
            warnings += 1
            score -= 1
    else:
        print(f"  WARNING: settings.json not found")
        warnings += 1
        score -= 1

    print()

    # ── 3. Beads CLI ─────────────────────────────────────────────────
    print("### Beads CLI")
    try:
        result = subprocess.run(['bd', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  OK: Beads CLI installed (v{version})")
            # Run bd doctor if available
            try:
                doc_result = subprocess.run(['bd', 'doctor'], capture_output=True, text=True, timeout=10)
                if doc_result.returncode == 0:
                    print(f"  OK: bd doctor passed")
                else:
                    print(f"  WARNING: bd doctor issues: {doc_result.stderr.strip()[:100]}")
                    warnings += 1
            except Exception:
                pass
        else:
            print(f"  INFO: Beads CLI not functional (exit {result.returncode})")
    except FileNotFoundError:
        print(f"  INFO: Not installed — using YAML fallback")
    except Exception:
        print(f"  INFO: Cannot detect Beads CLI — using YAML fallback")

    print()

    # ── 4. Agent Mail ────────────────────────────────────────────────
    print("### Agent Mail")
    mail_data = load_mailbox(root)
    mailbox = mail_data.get('mailbox', [])

    if not mailbox:
        print(f"  OK: Mailbox empty (no messages)")
    else:
        # Schema validation
        mail_ok = True
        for msg in mailbox:
            if not isinstance(msg, dict):
                print(f"  BLOCKER: message entry is not a dict")
                mail_ok = False
                blockers += 1
                continue
            required = {'id', 'from', 'to', 'subject', 'created_at'}
            missing = required - set(msg.keys())
            if missing:
                print(f"  WARNING: message {msg.get('id', '?')} missing fields: {missing}")
                warnings += 1
                score -= 1
        if mail_ok:
            unread = get_unread(mailbox)
            print(f"  OK: Schema valid ({len(mailbox)} messages, {len(unread)} unread)")

    print()

    # ── Summary ──────────────────────────────────────────────────────
    score = max(0, min(10, score))
    print("### Summary")
    print(f"Score: {score}/10")
    print(f"Issues: {warnings} warning(s), {blockers} blocker(s)")

    if blockers > 0:
        print("-> Fix blockers before continuing")
        sys.exit(1)
    elif warnings > 0:
        print("-> Warnings found but not blocking")

    sys.exit(0)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
    sys.exit(0)
