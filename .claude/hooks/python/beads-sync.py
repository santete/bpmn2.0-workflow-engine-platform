#!/usr/bin/env python3
"""
Hook: Stop / PreCompact — Beads sync (persist state).
If Beads CLI installed: run `bd sync` to persist task state.
If not installed: silently skip (YAML is already git-persisted).
Fail-open: any error → exit 0 (don't block session).
"""
import subprocess
import sys

try:
    # Check if Beads CLI is available
    result = subprocess.run(
        ['bd', '--version'],
        capture_output=True, text=True, timeout=5,
    )
    if result.returncode == 0:
        # Beads CLI available — run sync
        sync = subprocess.run(
            ['bd', 'sync', '--quiet'],
            capture_output=True, text=True, timeout=10,
        )
        if sync.returncode == 0 and sync.stdout.strip():
            print(sync.stdout.strip())
except FileNotFoundError:
    pass  # bd not installed — YAML state is already on disk
except Exception:
    pass  # fail-open

sys.exit(0)
