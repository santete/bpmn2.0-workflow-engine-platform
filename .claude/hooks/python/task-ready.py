#!/usr/bin/env python3
"""CLI: /task-ready — List tasks ready to work on."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from task_engine import load_tracker, compute_ready, status_icon

    json_mode = '--json' in sys.argv

    data = load_tracker()
    tasks = data.get('tasks', [])
    ready = compute_ready(tasks)

    if json_mode:
        output = {
            'ready_count': len(ready),
            'tasks': [
                {
                    'id': t['id'],
                    'title': t.get('title', ''),
                    'blocked_by_resolved': t.get('blocked_by', []),
                    'created_at': t.get('created_at', ''),
                }
                for t in ready
            ]
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    if not ready:
        print(f"## Ready Tasks (0 available)\n")
        if not tasks:
            print("Task tracker rỗng. Dùng `/task-add <title>` để tạo task.")
        else:
            closed = sum(1 for t in tasks if t.get('status') == 'closed')
            if closed == len(tasks):
                print("Tất cả tasks đã closed! Done!")
            else:
                print("Không có task nào sẵn sàng. Kiểm tra:")
                print("- Có task bị blocked? → Chạy `/task-list` để xem dependency")
                print("- Có task đang in_progress? → Hoàn thành trước")
        sys.exit(0)

    print(f"## Ready Tasks ({len(ready)} available)\n")
    print("| # | ID | Title | Blocked by (resolved) |")
    print("|---|-----|-------|----------------------|")
    for i, t in enumerate(ready, 1):
        blocked_by = t.get('blocked_by', [])
        resolved = ', '.join(f"{b} {status_icon('closed')}" for b in blocked_by) if blocked_by else '-'
        print(f"| {i} | {t['id']} | {t['title']} | {resolved} |")

    print(f"\n→ Claim: `/task-claim <id>`")

except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)

sys.exit(0)
