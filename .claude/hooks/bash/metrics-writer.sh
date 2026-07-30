#!/usr/bin/env bash
# metrics_writer — append-only event log cho framework telemetry.
# Bash parity with Python metrics_writer.py.
#
# Fail-open invariant: KHÔNG bao giờ exit non-zero.
#
# Usage (source this file, then call):
#   source "$(dirname "$0")/metrics-writer.sh"
#   write_event "hook_block" '{"hook":"block-dangerous","rule":"rm -rf","severity":"BLOCKER"}'

_find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        [ -d "$dir/.claude" ] || [ -d "$dir/.git" ] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

_read_pattern() {
    local root="$1"
    local state="$root/.claude/memory/project_state.yaml"
    [ -f "$state" ] || { echo "?"; return; }
    local pat
    pat=$(grep -m1 '^pattern:' "$state" 2>/dev/null | sed 's/pattern:\s*//;s/\s.*//')
    echo "${pat:-?}"
}

write_event() {
    local event_type="$1"
    local data_json="${2:-{}}"
    local root
    root="$(_find_project_root)"
    local metrics_dir="$root/.claude/metrics"
    local log_path="$metrics_dir/events.jsonl"

    mkdir -p "$metrics_dir" 2>/dev/null || true

    local ts pattern
    ts=$(date +%s 2>/dev/null || echo 0)
    pattern="$(_read_pattern "$root")"

    # Build JSON manually (no jq dependency for basic writes)
    printf '{"ts":%s,"event":"%s","pattern":"%s","data":%s}\n' \
        "$ts" "$event_type" "$pattern" "$data_json" >> "$log_path" 2>/dev/null || true
}
