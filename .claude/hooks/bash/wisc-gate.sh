#!/usr/bin/env bash
# Hook: PreToolUse — Edit|Write|MultiEdit
# WISC Governance Gate — chặn code change khi chưa satisfy WRITE/ISOLATE/COMPRESS.
# Requires: bash >= 4, jq >= 1.6, yq >= 4 (or python3 -c yaml fallback)
# Exit 0 = allow, Exit 2 = block. Fail-open on any error.
set -euo pipefail

D="────────────────────────────────────────────────────────────"
INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/metrics-writer.sh" 2>/dev/null || true

# ── Parse target file ────────────────────────────────────────────────────────
TARGET=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || echo "")
[ -z "$TARGET" ] && exit 0

# Skip non-source files
TARGET_LOWER=$(echo "$TARGET" | tr '[:upper:]' '[:lower:]' | tr '\\' '/')
case "$TARGET_LOWER" in
  *.yaml|*.yml|*.md|*.json|*.toml|*.gitignore|*.env) exit 0 ;;
esac
case "$TARGET_LOWER" in
  *.claude/*|*docs/ai/*|*node_modules/*|*__pycache__/*) exit 0 ;;
esac

# ── Find project root ───────────────────────────────────────────────────────
ROOT="$(pwd)"
p="$ROOT"
while [ "$p" != "/" ]; do
  [ -d "$p/.claude" ] || [ -d "$p/.git" ] && { ROOT="$p"; break; }
  p="$(dirname "$p")"
done

STATE="$ROOT/.claude/memory/project_state.yaml"
[ -f "$STATE" ] || exit 0

# ── YAML reader (yq preferred, python fallback) ─────────────────────────────
yaml_get() {
  local file="$1" key="$2"
  if command -v yq &>/dev/null; then
    yq -r ".$key // \"\"" "$file" 2>/dev/null || echo ""
  elif command -v python3 &>/dev/null; then
    python3 -c "
import yaml, sys
d = yaml.safe_load(open('$file')) or {}
keys = '$key'.split('.')
v = d
for k in keys:
    if isinstance(v, dict): v = v.get(k, '')
    else: v = ''
print(v if v else '')
" 2>/dev/null || echo ""
  elif command -v python &>/dev/null; then
    python -c "
import yaml, sys
d = yaml.safe_load(open('$file')) or {}
keys = '$key'.split('.')
v = d
for k in keys:
    if isinstance(v, dict): v = v.get(k, '')
    else: v = ''
print(v if v else '')
" 2>/dev/null || echo ""
  else
    echo ""  # No yaml parser — fail-open
  fi
}

block_gate() {
  local gate="$1" reason="$2" fix="$3"
  write_event "wisc_gate" "{\"gate\":\"$gate\",\"action\":\"block\",\"detail\":\"${reason:0:200}\"}" 2>/dev/null || true
  echo "" >&2
  echo "$D" >&2
  echo "🛡️  WISC GATE BLOCKED — $gate" >&2
  echo "$D" >&2
  echo "" >&2
  echo "  Lý do : $reason" >&2
  echo "  Fix   : $fix" >&2
  echo "" >&2
  echo "  Bypass: ghi wisc_gates.$gate.satisfied: true vào project_state.yaml" >&2
  echo "          (cần user approve — ghi lý do bypass vào wisc_gates.$gate.bypass_reason)" >&2
  echo "" >&2
  echo "$D" >&2
  echo "" >&2
  exit 2
}

# ── Read classification ──────────────────────────────────────────────────────
D5=$(yaml_get "$STATE" "last_task_classification.D5" | tr '[:upper:]' '[:lower:]')
D6=$(yaml_get "$STATE" "last_task_classification.D6" | tr '[:upper:]' '[:lower:]')

# No classification → no enforcement
[ -z "$D5" ] && [ -z "$D6" ] && exit 0

# ── GATE 1: WRITE — D5=vague ────────────────────────────────────────────────
if [ "$D5" = "vague" ]; then
  WRITE_SAT=$(yaml_get "$STATE" "wisc_gates.WRITE.satisfied" | tr '[:upper:]' '[:lower:]')
  if [ "$WRITE_SAT" != "true" ]; then
    ARTIFACT=$(yaml_get "$STATE" "wisc_gates.WRITE.artifact")
    FOUND=false
    for f in "$ROOT/${ARTIFACT:-spec.md}" "$ROOT/spec.md" "$ROOT/docs/spec.md" "$ROOT/.claude/memory/spec.md"; do
      [ -f "$f" ] && { FOUND=true; break; }
    done
    if [ "$FOUND" = "false" ]; then
      block_gate "WRITE" \
        "D5=vague — spec chưa rõ, nhưng chưa có spec.md" \
        "Viết spec.md trước khi code, sau đó ghi wisc_gates.WRITE.satisfied: true"
    fi
  fi
fi

# ── GATE 2: ISOLATE — D6=unknown|legacy ─────────────────────────────────────
case "$D6" in
  unknown|legacy-undocumented|cross-module)
    ISO_SAT=$(yaml_get "$STATE" "wisc_gates.ISOLATE.satisfied" | tr '[:upper:]' '[:lower:]')
    if [ "$ISO_SAT" != "true" ]; then
      SCOUT_FOUND=false
      for f in "$ROOT/.claude/memory"/scout_report*; do
        [ -f "$f" ] && { SCOUT_FOUND=true; break; }
      done
      ARTIFACT=$(yaml_get "$STATE" "wisc_gates.ISOLATE.artifact")
      [ -n "$ARTIFACT" ] && [ -f "$ROOT/$ARTIFACT" ] && SCOUT_FOUND=true
      if [ "$SCOUT_FOUND" = "false" ]; then
        block_gate "ISOLATE" \
          "D6=$D6 — codebase chưa quen, nhưng chưa có scout report" \
          "Chạy sub-agent scout trước khi code, hoặc ghi wisc_gates.ISOLATE.satisfied: true"
      fi
    fi
    ;;
esac

# ── GATE 3: COMPRESS — token > threshold ────────────────────────────────────
COMP_SAT=$(yaml_get "$STATE" "wisc_gates.COMPRESS.satisfied" | tr '[:upper:]' '[:lower:]')
if [ "$COMP_SAT" != "true" ]; then
  TOKEN_CACHE="$ROOT/.claude/cache/last_tokens.json"
  if [ -f "$TOKEN_CACHE" ]; then
    TOKENS=$(jq -r '.tokens // 0' "$TOKEN_CACHE" 2>/dev/null || echo "0")
    THRESHOLD=120000
    # Try to read from thresholds config
    THRESH_FILE="$ROOT/.claude/config/thresholds.json"
    [ -f "$THRESH_FILE" ] && THRESHOLD=$(jq -r '.rotate_threshold // 120000' "$THRESH_FILE" 2>/dev/null || echo "120000")
    if [ "$TOKENS" -gt "$THRESHOLD" ] 2>/dev/null; then
      block_gate "COMPRESS" \
        "Token count ($TOKENS) vượt threshold ($THRESHOLD)" \
        "Chạy /rotate để đóng session, hoặc /compact có focus"
    fi
  fi
fi

exit 0
