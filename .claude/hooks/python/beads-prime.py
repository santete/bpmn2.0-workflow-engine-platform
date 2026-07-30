#!/usr/bin/env python3
"""
Hook: SessionStart — Beads prime (load snapshot).
If Beads CLI installed: run `bd prime` to load task snapshot.
If not installed: silently fall back to YAML task tracker.
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
        # Beads CLI available — run prime
        prime = subprocess.run(
            ['bd', 'prime', '--quiet'],
            capture_output=True, text=True, timeout=10,
        )
        if prime.returncode == 0 and prime.stdout.strip():
            print(prime.stdout.strip())
        # If prime fails, fall through silently
except FileNotFoundError:
    pass  # bd not installed — use YAML fallback
except Exception:
    pass  # any other error — fail-open

sys.exit(0)
