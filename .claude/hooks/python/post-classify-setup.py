#!/usr/bin/env python3
"""
post-classify-setup — Auto-initialize task tracker, agent mail, Beads CLI,
and verify hooks after /classify.

Chạy cho MỌI pattern (A/B/C):
- Anti-Amnesia (Beads) hữu ích cho mọi pattern — session continuity
- Task tracker cần cho mọi 2b epic task (kể cả Pattern A solo + D3=multi-session)
- Chỉ agent_mail mới giới hạn cho multi-dev/Pattern C

Usage:
  python .claude/hooks/python/post-classify-setup.py <pattern> <team_size>

Arguments:
  pattern:   A, B, or C
  team_size: integer (number of developers)

Actions performed (ALL patterns):
  1. Init .claude/memory/task_tracker.yaml if missing
  2. Init .claude/memory/agent_mail.yaml if missing (multi-dev or Pattern C)
  3. Detect Beads CLI, init if found, recommend if team >= 3
  4. Verify hooks in settings.json
  5. Run beads-doctor health check

Fail-open: unexpected errors → warning, exit 0.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def find_project_root(start=None):
    cwd = start or Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / '.claude').is_dir() or (p / '.git').is_dir():
            return p
    return cwd


def init_yaml_file(path, default_content, label):
    """Create YAML file with default content if missing or empty."""
    if path.exists():
        content = path.read_text(encoding='utf-8').strip()
        # Check if file has actual data (not just comments)
        lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
        if lines:
            print(f"  OK: {label} already exists ({path.name})")
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_content, encoding='utf-8')
    print(f"  CREATED: {label} ({path.name})")
    return True


def detect_beads_cli():
    """Check if Beads CLI is installed. Returns (installed, version)."""
    try:
        result = subprocess.run(['bd', '--version'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False, None


def install_beads_cli():
    """Attempt to install Beads CLI. Returns True if successful."""
    print("\n  Installing Beads CLI...")
    try:
        # Try npm install (most common)
        result = subprocess.run(['npm', 'install', '-g', 'beads-cli'],
                                capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("  OK: Beads CLI installed via npm")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try pip install
    try:
        py = 'python3' if subprocess.run(['python3', '--version'],
                                          capture_output=True).returncode == 0 else 'python'
        result = subprocess.run([py, '-m', 'pip', 'install', 'beads-cli'],
                                capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("  OK: Beads CLI installed via pip")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("  SKIP: Could not auto-install Beads CLI")
    print("        Install manually: npm install -g beads-cli")
    print("        Or: pip install beads-cli")
    return False


def init_beads(root):
    """Initialize Beads in project: bd init + bd setup claude."""
    try:
        # bd init with auto-generated prefix
        prefix = root.name[:3].lower() or 'prj'
        result = subprocess.run(['bd', 'init', '--prefix', prefix],
                                capture_output=True, text=True, timeout=10,
                                cwd=str(root))
        if result.returncode == 0:
            print(f"  OK: Beads initialized (prefix: {prefix})")
        else:
            # May already be initialized
            if 'already' in result.stderr.lower():
                print(f"  OK: Beads already initialized")
            else:
                print(f"  WARNING: bd init: {result.stderr.strip()[:80]}")

        # bd setup claude
        result = subprocess.run(['bd', 'setup', 'claude'],
                                capture_output=True, text=True, timeout=10,
                                cwd=str(root))
        if result.returncode == 0:
            print(f"  OK: Beads Anti-Amnesia hooks configured")
        else:
            print(f"  WARNING: bd setup claude: {result.stderr.strip()[:80]}")

        return True
    except Exception as e:
        print(f"  WARNING: Beads init failed: {e}")
        return False


def verify_hooks(root):
    """Check settings.json has required hooks for Pattern B/C."""
    settings_path = root / '.claude' / 'settings.json'
    if not settings_path.exists():
        print("  WARNING: .claude/settings.json not found")
        return

    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
        hooks = settings.get('hooks', {})

        # Check SessionStart hooks
        session_cmds = []
        for h in hooks.get('SessionStart', []):
            for hook in h.get('hooks', []):
                session_cmds.append(hook.get('command', ''))

        required_session = {
            'task-summary': 'task-summary.py',
            'mail-summary': 'mail-summary.py',
        }
        for label, script in required_session.items():
            if any(script in c for c in session_cmds):
                print(f"  OK: SessionStart hook: {label}")
            else:
                print(f"  MISSING: SessionStart hook: {label}")
                print(f"           Add to settings.json hooks.SessionStart")

        # Check Stop hooks
        stop_cmds = []
        for h in hooks.get('Stop', []):
            for hook in h.get('hooks', []):
                stop_cmds.append(hook.get('command', ''))

        if any('session-end' in c for c in stop_cmds):
            print(f"  OK: Stop hook: session-end")
        else:
            print(f"  MISSING: Stop hook: session-end")

    except Exception as e:
        print(f"  WARNING: Cannot verify hooks: {e}")


def run_beads_doctor(root):
    """Run beads-doctor.py for health check."""
    doctor_script = Path(__file__).resolve().parent / 'beads-doctor.py'
    if not doctor_script.exists():
        print("  SKIP: beads-doctor.py not found")
        return

    try:
        py = sys.executable or 'python'
        result = subprocess.run([py, str(doctor_script)],
                                capture_output=True, text=True, timeout=15,
                                cwd=str(root))
        # Show summary line only
        for line in result.stdout.split('\n'):
            if 'Score:' in line or 'Issues:' in line:
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"  WARNING: beads-doctor failed: {e}")


# ── Main ─────────────────────────────────────────────────────────────

try:
    if len(sys.argv) < 3:
        print("Usage: post-classify-setup.py <pattern> <team_size>", file=sys.stderr)
        sys.exit(1)

    pattern = sys.argv[1].upper()
    try:
        team_size = int(sys.argv[2])
    except ValueError:
        team_size = 1

    root = find_project_root()
    memory_dir = root / '.claude' / 'memory'

    print(f"## Post-Classify Auto-Setup (Pattern {pattern}, team={team_size})\n")

    # ── All patterns get setup ──────────────────────────────────
    multi_dev = team_size >= 3

    # Step 1: Initialize memory files
    print("### Step 1: Initialize Memory Files\n")

    tracker_template = (
        "# Task Tracker — state xuyên session\n"
        "# Auto-created by post-classify-setup.py\n"
        "# Git-committable, chia sẻ giữa sessions và team members\n\n"
        "tasks: []\n"
    )
    init_yaml_file(memory_dir / 'task_tracker.yaml', tracker_template, 'Task Tracker')

    if multi_dev or pattern == 'C':
        mail_template = (
            "# Agent Mail — kênh truyền tin giữa agents/sessions\n"
            "# Auto-created by post-classify-setup.py\n"
            "# Git-committable, chia sẻ giữa sessions và team members\n\n"
            "mailbox: []\n"
        )
        init_yaml_file(memory_dir / 'agent_mail.yaml', mail_template, 'Agent Mail')
    else:
        print(f"  SKIP: Agent Mail (single dev, Pattern {pattern})")

    print()

    # Step 2: Beads CLI detection and setup
    print("### Step 2: Beads CLI\n")

    beads_installed, beads_version = detect_beads_cli()

    if beads_installed:
        print(f"  OK: Beads CLI installed (v{beads_version})")
        init_beads(root)
    elif multi_dev or pattern == 'C':
        print("  INFO: Beads CLI not found")
        print(f"  RECOMMENDED for team of {team_size}: Beads CLI provides")
        print("    - Conflict-free task IDs (no merge conflicts)")
        print("    - Anti-Amnesia hooks (auto session load/save)")
        print()
        print("  To install manually:")
        print("    npm install -g beads-cli  # or: pip install beads-cli")
        print("    bd init --prefix <2-5 chars>")
        print("    bd setup claude")
        print("    bd doctor")
        print()
        print("  YAML fallback active — works without Beads CLI")
    else:
        print("  INFO: Beads CLI not installed — using YAML fallback (OK for solo dev)")

    print()

    # Step 3: Verify hooks
    print("### Step 3: Verify Hooks\n")
    verify_hooks(root)

    print()

    # Step 4: Health check
    print("### Step 4: Health Check\n")
    run_beads_doctor(root)

    print()

    # Summary
    print("### Setup Complete\n")
    print(f"Pattern {pattern} initialized:")
    print(f"  - Task Tracker:  .claude/memory/task_tracker.yaml")
    if multi_dev or pattern == 'C':
        print(f"  - Agent Mail:    .claude/memory/agent_mail.yaml")
    print(f"  - Beads CLI:     {'installed' if beads_installed else 'YAML fallback'}")
    print()
    print("Next steps:")
    print("  1. Start a task: describe your task to begin Phase 1")
    print("  2. /classify-task will auto-classify and scaffold DAG if needed")
    print("  3. Use /task-add, /task-dep, /task-graph for epic orchestration")

    # Emit metrics
    try:
        from task_engine import emit_event
        emit_event('post_classify_setup', {
            'pattern': pattern,
            'team_size': team_size,
            'beads_installed': beads_installed,
            'multi_dev': multi_dev,
        })
    except Exception:
        pass

    sys.exit(0)

except SystemExit:
    raise
except Exception as e:
    print(f"Warning: post-classify-setup error: {e}", file=sys.stderr)
    sys.exit(0)  # fail-open
