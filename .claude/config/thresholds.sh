#!/usr/bin/env bash
# Pure-bash loader for runtime thresholds. Source this script to get:
#   THRESHOLDS_ROTATE        — rotate trigger (default 120000)
#   THRESHOLDS_RECENT_DROP   — re-baseline drop (default 10000)
#   THRESHOLDS_METRICS_WARN  — token warning level (default 90000)
#
# Reads .claude/config/thresholds.json via grep+sed (no jq/python required).
# Falls back to defaults if file missing/unreadable. Only top-level int keys
# are supported here; nested pattern_budgets are not read in bash.

THRESHOLDS_ROTATE=120000
THRESHOLDS_RECENT_DROP=10000
THRESHOLDS_METRICS_WARN=90000

_th_root="$(pwd)"
while [[ "$_th_root" != "/" && "$_th_root" != "" ]]; do
  [[ -d "$_th_root/.claude" || -d "$_th_root/.git" ]] && break
  _th_root="$(dirname "$_th_root")"
done

_th_cfg="$_th_root/.claude/config/thresholds.json"

# $1: key, $2: default — extract `"key": <int>` from JSON via grep
_th_get_int() {
  local key="$1" default="$2" val=""
  if [[ -f "$_th_cfg" ]]; then
    val=$(grep -oE "\"$key\"[[:space:]]*:[[:space:]]*[0-9]+" "$_th_cfg" 2>/dev/null \
          | head -1 | grep -oE '[0-9]+$')
  fi
  [[ -n "$val" ]] && echo "$val" || echo "$default"
}

THRESHOLDS_ROTATE=$(_th_get_int "rotate_threshold" "$THRESHOLDS_ROTATE")
THRESHOLDS_RECENT_DROP=$(_th_get_int "recent_drop_reset" "$THRESHOLDS_RECENT_DROP")
THRESHOLDS_METRICS_WARN=$(_th_get_int "metrics_tok_warn" "$THRESHOLDS_METRICS_WARN")

export THRESHOLDS_ROTATE THRESHOLDS_RECENT_DROP THRESHOLDS_METRICS_WARN
unset _th_root _th_cfg
