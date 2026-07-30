#!/usr/bin/env python3
"""
Statusline — Merged Template framework (v3 — clean context display)
Hiển thị: [Pattern] ▓▓▓░░ base+work/threshold (remain) | ctx% | model | schema | HRS | duration | cwd

Color logic (theo framework rule "≥120k working = ROTATE NGAY"):
  🟢 < 50% threshold      Safe
  🟡 50-75%                Watch
  🟠 75-100%               Approaching rotate
  🔴 ≥ 100% (≥120k abs)   ROTATE mandatory

Token total persisted to .claude/cache/last_tokens.json (tokens, baseline, working).
Fast path: <50ms typical (no jsonl parsing — Claude Code passes context_window directly).
"""
import sys
import io
import json
import os
import re
import time
from pathlib import Path

# Windows fix: force utf-8 stdout (default cp1252 can't render emoji/box chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ANSI color codes
def c(s, code): return f"\033[{code}m{s}\033[0m"
RED, ORANGE, YELLOW, GREEN, GRAY, BOLD = "31", "38;5;208", "33", "32", "90", "1"
CYAN, DIM = "36", "2"

# Runtime thresholds (override via .claude/config/thresholds.json)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
    from thresholds import load as _load_thresholds
    _cfg = _load_thresholds()
except Exception:
    _cfg = {
        "rotate_threshold": 120_000,
        "recent_drop_reset": 10_000,
        "pattern_budgets": {
            "A": {"total": 120_000}, "B": {"total": 140_000}, "C": {"total": 190_000},
        },
    }
ROTATE_THRESHOLD = int(_cfg.get("rotate_threshold", 120_000))
RECENT_DROP_RESET = int(_cfg.get("recent_drop_reset", 10_000))
PATTERN_BUDGET = {
    k: int((v or {}).get("total", ROTATE_THRESHOLD))
    for k, v in (_cfg.get("pattern_budgets") or {}).items()
}
try:
    _raw = sys.stdin.read() or "{}"
    inp = json.loads(_raw)
except Exception:
    _raw = "{}"
    inp = {}

cwd = inp.get("cwd") or inp.get("workspace", {}).get("current_dir", "")
model_id = inp.get("model", {}).get("display_name") or inp.get("model", {}).get("id", "?")
ctx = inp.get("context_window", {}) or {}
usage = ctx.get("current_usage", {}) or {}
ctx_pct_native = ctx.get("used_percentage")

# Total token estimation from used_percentage (reliable — always provided by Claude Code).
# Note: Claude Code does NOT provide per-type breakdown (input/cache_read/cache_create/output)
# in statusline stdin — only used_percentage is available.
if ctx_pct_native is not None:
    max_ctx = ctx.get("max_tokens") or ctx.get("context_limit") or 200_000
    tokens = int(float(ctx_pct_native) / 100 * max_ctx)
else:
    tokens = 0

# Baseline / working split: baseline = floor (sys prompt + eager loads + post-compact
# summary); working = accumulated this session. /compact and /clear drop tokens
# sharply → re-capture baseline. RECENT_DROP_RESET avoids re-baselining on normal noise.
cache_dir = Path(".claude/cache")
cache_file = cache_dir / "last_tokens.json"
prev_baseline = 0
prev_tokens = 0
if cache_file.exists():
    try:
        prev = json.loads(cache_file.read_text(encoding="utf-8"))
        prev_baseline = int(prev.get("baseline", 0))
        prev_tokens = int(prev.get("tokens", 0))
    except Exception:
        pass

prev_session_start = 0
if cache_file.exists():
    try:
        prev_session_start = int(prev.get("session_start", 0))
    except Exception:
        pass

if tokens <= 0:
    baseline = prev_baseline
elif prev_baseline == 0:
    baseline = tokens
elif tokens < prev_tokens - RECENT_DROP_RESET:
    baseline = tokens
else:
    baseline = prev_baseline
working = max(0, tokens - baseline)

# Session start: capture first render timestamp, persist across renders.
# Reset when baseline resets (new session after /compact or /clear).
now_ts = int(time.time())
if prev_session_start > 0 and baseline == prev_baseline:
    session_start = prev_session_start
else:
    session_start = now_ts
session_duration_s = max(0, now_ts - session_start)

# Pattern from project_state.yaml (don't crash if missing)
pattern = "?"
state_path = Path(".claude/memory/project_state.yaml")
if state_path.exists():
    try:
        text = state_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^pattern:\s*([ABC])\b", text, re.MULTILINE)
        if m:
            pattern = m.group(1)
    except Exception:
        pass

threshold = PATTERN_BUDGET.get(pattern, ROTATE_THRESHOLD)

# Schema staleness (days since last mtime)
schema_age_d = -1
schema_path = Path(".claude/memory/schema_snapshot.yaml")
if schema_path.exists():
    try:
        schema_age_d = int((time.time() - schema_path.stat().st_mtime) / 86400)
    except Exception:
        pass


# --- Helper: format token count with smart precision ---
def fmt_k(n):
    """Format token count: <1k → '0.5k', 1-999k → '42k', ≥1M → '1.2M'."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.0f}k"
    if n > 0:
        return f"{n/1000:.1f}k"
    return "0"


# --- Helper: build visual progress bar ---
def progress_bar(pct, width=10):
    """Render a bar like ▓▓▓▓░░░░░░ with color based on fill level."""
    filled = min(width, int(pct * width))
    empty = width - filled
    bar = "▓" * filled + "░" * empty
    if pct >= 1.0:
        return c(bar, RED)
    if pct >= 0.75:
        return c(bar, ORANGE)
    if pct >= 0.5:
        return c(bar, YELLOW)
    return c(bar, GREEN)


parts = []

# 1) Pattern badge
parts.append(c(f"[{pattern}]", BOLD))

# 2) Progress bar + token count with remaining
pct = (tokens / ROTATE_THRESHOLD) if ROTATE_THRESHOLD else 0
remaining = max(0, ROTATE_THRESHOLD - tokens)

bar = progress_bar(pct)

if baseline > 0:
    tok_disp = f"{fmt_k(baseline)}+{fmt_k(working)}/{fmt_k(ROTATE_THRESHOLD)}"
else:
    tok_disp = f"{fmt_k(tokens)}/{fmt_k(ROTATE_THRESHOLD)}"

if tokens >= ROTATE_THRESHOLD:
    parts.append(f"{bar} {c(tok_disp, RED)} {c('ROTATE', f'{RED};{BOLD}')}")
elif pct >= 0.75:
    parts.append(f"{bar} {c(tok_disp, ORANGE)} {c(f'-{fmt_k(remaining)}', DIM)}")
elif pct >= 0.5:
    parts.append(f"{bar} {c(tok_disp, YELLOW)} {c(f'-{fmt_k(remaining)}', DIM)}")
else:
    parts.append(f"{bar} {c(tok_disp, GREEN)} {c(f'-{fmt_k(remaining)}', DIM)}")

# 3) Native context % (informational, gray)
if ctx_pct_native is not None:
    parts.append(c(f"ctx {ctx_pct_native}%", GRAY))

# 4) Model (short)
model_short = re.sub(r"^claude-", "", str(model_id)).replace("-20251001", "")
parts.append(c(model_short, GRAY))

# 5) Schema age
if schema_age_d >= 0:
    if schema_age_d > 30:
        parts.append(c(f"schema {schema_age_d}d", RED))
    elif schema_age_d > 7:
        parts.append(c(f"schema {schema_age_d}d", YELLOW))
    else:
        parts.append(c(f"schema {schema_age_d}d", GRAY))

# 6) HRS-7d badge (from pre-computed cache, written by /halluc-score)
hrs_cache = cache_dir / "hrs_7d.json"
if hrs_cache.exists():
    try:
        hrs_data = json.loads(hrs_cache.read_text(encoding="utf-8"))
        hrs_val = float(hrs_data.get("avg_hrs", -1))
        hrs_color = hrs_data.get("dominant_color", "")
        if hrs_val >= 0:
            hrs_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}.get(hrs_color, "")
            _hc = RED if hrs_color == "RED" else (ORANGE if hrs_color == "ORANGE" else
                  (YELLOW if hrs_color == "YELLOW" else GREEN))
            parts.append(c(f"HRS {hrs_val:.2f} {hrs_emoji}", _hc))
    except Exception:
        pass

# 7) Session duration
if session_duration_s >= 60:
    mins = session_duration_s // 60
    if mins >= 60:
        parts.append(c(f"{mins // 60}h{mins % 60:02d}m", GRAY))
    else:
        parts.append(c(f"{mins}m", GRAY))

# 8) Cwd basename
if cwd:
    parts.append(c(os.path.basename(cwd.rstrip("/\\")) or cwd, GRAY))

print(" · ".join(parts))

# Persist session tokens so /halluc-score can read same value (single source of truth).
# Wrap in try — never fail statusline due to cache I/O.
try:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps({
            "tokens": tokens,
            "baseline": baseline,
            "working": working,
            "session_start": session_start,
            "ts": now_ts,
        }),
        encoding="utf-8",
    )
except Exception:
    pass
