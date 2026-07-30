#!/usr/bin/env bash
# Hallucination Risk Score (HRS) — Bash version (lite)
# Trigger-only — KHÔNG chạy tự động trong PreToolUse/PostToolUse
#
# Lưu ý: bản Bash là LITE (không parse YAML schema sâu, không gọi mypy/tsc).
# Để full feature, dùng Python: .claude/hooks/python/halluc-score.py
#
# Usage:
#   bash .claude/hooks/bash/halluc-score.sh [--tokens N] [--threshold 0.7] [--json]
#
# Exit:
#   0 = HRS < threshold
#   1 = HRS >= threshold

set -uo pipefail

THRESHOLD=0.7
TOKENS=0
JSON=0
FILES=""
SAVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tokens)    TOKENS="$2"; shift 2 ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    --files)     FILES="$2"; shift 2 ;;
    --json)      JSON=1; shift ;;
    --save)      SAVE=1; shift ;;
    *) shift ;;
  esac
done

# ── Find project root ────────────────────────────────────────────────────
ROOT="$(pwd)"
while [[ "$ROOT" != "/" ]]; do
  [[ -d "$ROOT/.claude" || -d "$ROOT/.git" ]] && break
  ROOT="$(dirname "$ROOT")"
done

SCHEMA="$ROOT/.claude/memory/schema_snapshot.yaml"
STATE="$ROOT/.claude/memory/project_state.yaml"

# Runtime thresholds (override via .claude/config/thresholds.json)
if [[ -f "$ROOT/.claude/config/thresholds.sh" ]]; then
  # shellcheck source=/dev/null
  source "$ROOT/.claude/config/thresholds.sh"
fi
: "${THRESHOLDS_ROTATE:=120000}"

# ── Get modified files ───────────────────────────────────────────────────
if [[ -z "$FILES" ]]; then
  if git -C "$ROOT" rev-parse --git-dir &>/dev/null; then
    FILES="$(git -C "$ROOT" diff --name-only HEAD 2>/dev/null | head -20 | tr '\n' ',' | sed 's/,$//')"
  fi
fi

# ── Build content blob ───────────────────────────────────────────────────
CONTENT=""
FILE_COUNT=0
if [[ -n "$FILES" ]]; then
  IFS=',' read -ra ARR <<< "$FILES"
  for f in "${ARR[@]}"; do
    full="$f"
    [[ "$full" != /* ]] && full="$ROOT/$f"
    if [[ -f "$full" ]]; then
      CONTENT+="$(cat "$full" 2>/dev/null)"$'\n'
      FILE_COUNT=$((FILE_COUNT + 1))
    fi
  done
fi

# Estimate tokens if not given
if [[ "$TOKENS" -eq 0 ]]; then
  CHAR_COUNT=${#CONTENT}
  TOKENS=$((CHAR_COUNT / 4))
fi

# ── Signal 1: Cite coverage ──────────────────────────────────────────────
# Heuristic: count "Based on `path:line`" or "Based on `schema_snapshot.yaml#"
CITED=$(echo "$CONTENT" | grep -oE 'Based on \`[^`]+:[0-9]+\`|Based on \`schema_snapshot\.yaml#' | wc -l | tr -d ' ')
# Total refs: distinct method calls (excluding common builtins)
TOTAL_REFS=$(echo "$CONTENT" | grep -oE '[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\(' \
  | grep -vE '\.(get|set|append|pop|keys|values|items|split|join|strip|replace|format|len|push|forEach|map|filter)\(' \
  | sort -u | wc -l | tr -d ' ')
if [[ "$TOTAL_REFS" -eq 0 ]]; then
  CITE_SCORE="1.0"
else
  CITE_SCORE=$(awk "BEGIN { v = $CITED / $TOTAL_REFS; if (v > 1) v = 1; printf \"%.3f\", v }")
fi

# ── Signal 2: Schema match (lite — text grep only) ───────────────────────
SCH_BLOCKED=0
SCH_TOTAL=0
SCH_MATCHED=0
SCHEMA_SCORE="1.0"
if [[ -f "$SCHEMA" && -n "$CONTENT" ]]; then
  # Extract candidate field refs: response.X, data.X, result.X
  CAND=$(echo "$CONTENT" | grep -oE '(response|data|result|row|record|payload)\.[a-zA-Z_][a-zA-Z0-9_]*' \
    | awk -F. '{print $2}' | sort -u)
  SCH_TOTAL=$(echo "$CAND" | grep -c . || echo 0)

  # Extract NOT_available list from schema (very rough YAML scan)
  NOT_AVAIL=$(grep -A 50 'NOT_available\|not_in_response\|NOT_in_response' "$SCHEMA" 2>/dev/null \
    | grep -oE '^\s*-\s+[a-zA-Z_][a-zA-Z0-9_]*' | awk '{print $2}' | sort -u)

  if [[ -n "$CAND" && -n "$NOT_AVAIL" ]]; then
    while IFS= read -r ref; do
      [[ -z "$ref" ]] && continue
      if echo "$NOT_AVAIL" | grep -qx "$ref"; then
        SCH_BLOCKED=$((SCH_BLOCKED + 1))
      fi
    done <<< "$CAND"
  fi

  if [[ "$SCH_BLOCKED" -gt 0 ]]; then
    SCHEMA_SCORE="0.0"
  fi
fi

# ── Signal 3: Confidence density ─────────────────────────────────────────
CONF_COUNT=$(echo "$CONTENT" | grep -ciE '\b(I believe|probably|should work|I think|might be|seems like|likely|presumably|maybe|perhaps|in theory|I assume|I guess)\b' | tr -d ' ')
WORD_COUNT=$(echo "$CONTENT" | wc -w | tr -d ' ')
[[ "$WORD_COUNT" -lt 1 ]] && WORD_COUNT=1
CONF_DENSITY=$(awk "BEGIN { printf \"%.3f\", $CONF_COUNT / ($WORD_COUNT / 1000.0) }")

# ── Signal 4: Static errors (lite — only py syntax) ──────────────────────
STATIC_ERRORS=0
STATIC_CHECKED=0
if [[ -n "$FILES" ]]; then
  IFS=',' read -ra ARR <<< "$FILES"
  for f in "${ARR[@]}"; do
    full="$f"
    [[ "$full" != /* ]] && full="$ROOT/$f"
    if [[ -f "$full" && "$full" == *.py ]]; then
      STATIC_CHECKED=$((STATIC_CHECKED + 1))
      if ! python -c "import ast; ast.parse(open(r'$full').read())" 2>/dev/null; then
        STATIC_ERRORS=$((STATIC_ERRORS + 1))
      fi
    fi
  done
fi

# ── Signal 5: Context drift ──────────────────────────────────────────────
DRIFT=$(awk "BEGIN { v = $TOKENS / ${THRESHOLDS_ROTATE}.0; if (v > 1) v = 1; printf \"%.3f\", v }")

# ── Signal 6: Consecutive failures ───────────────────────────────────────
FAILURES=0
if [[ -f "$STATE" ]]; then
  FAILURES=$(grep -E '^consecutive_failures:' "$STATE" 2>/dev/null | head -1 | awk '{print $2}' | grep -oE '[0-9]+' || echo 0)
  [[ -z "$FAILURES" ]] && FAILURES=0
fi

# ── Signal 7: Schema staleness (days) ────────────────────────────────────
STALENESS=0
if [[ -f "$SCHEMA" ]]; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    SCHEMA_MTIME=$(stat -f %m "$SCHEMA" 2>/dev/null || echo 0)
  else
    SCHEMA_MTIME=$(stat -c %Y "$SCHEMA" 2>/dev/null || echo 0)
  fi
  NOW=$(date +%s)
  STALENESS=$(( (NOW - SCHEMA_MTIME) / 86400 ))
fi

# ── Composite ────────────────────────────────────────────────────────────
HRS=$(awk "BEGIN {
  hrs = 0.25 * (1 - $CITE_SCORE) \
      + 0.25 * (1 - $SCHEMA_SCORE) \
      + 0.10 * ($CONF_DENSITY > 3 ? 1 : $CONF_DENSITY / 3) \
      + 0.20 * ($STATIC_ERRORS > 3 ? 1 : $STATIC_ERRORS / 3) \
      + 0.10 * $DRIFT \
      + 0.05 * ($FAILURES > 4 ? 1 : $FAILURES / 4) \
      + 0.05 * ($STALENESS > 30 ? 1 : $STALENESS / 30)
  printf \"%.3f\", hrs
}")

# Color
COLOR=$(awk "BEGIN {
  t = $THRESHOLD
  h = $HRS
  if (h >= t)             print \"RED\"
  else if (h >= t - 0.2)  print \"ORANGE\"
  else if (h >= t - 0.4)  print \"YELLOW\"
  else                    print \"GREEN\"
}")

# Output
if [[ "$JSON" -eq 1 ]]; then
  cat <<EOF
{
  "hrs": $HRS,
  "color": "$COLOR",
  "threshold": $THRESHOLD,
  "signals": {
    "cite_coverage": $CITE_SCORE,
    "schema_match": $SCHEMA_SCORE,
    "confidence_density": $CONF_DENSITY,
    "static_errors": $STATIC_ERRORS,
    "context_drift": $DRIFT,
    "failures": $FAILURES,
    "schema_staleness": $STALENESS
  },
  "details": {
    "cite_total": $TOTAL_REFS,
    "cite_cited": $CITED,
    "schema_total": $SCH_TOTAL,
    "schema_blocked": $SCH_BLOCKED,
    "confidence_count": $CONF_COUNT,
    "static_files_checked": $STATIC_CHECKED,
    "token_count": $TOKENS,
    "files_count": $FILE_COUNT
  }
}
EOF
else
  case "$COLOR" in
    GREEN)  EMOJI="🟢" ;;
    YELLOW) EMOJI="🟡" ;;
    ORANGE) EMOJI="🟠" ;;
    RED)    EMOJI="🔴" ;;
  esac
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "  HALLUCINATION RISK SCORE (Bash lite)"
  echo "════════════════════════════════════════════════════════════"
  echo "  Overall: $HRS  $EMOJI $COLOR"
  echo "  Threshold: $THRESHOLD  |  Files: $FILE_COUNT  |  Tokens: $TOKENS"
  echo ""
  echo "  Signals:"
  echo "    [1] Cite coverage:     $CITE_SCORE   ($CITED/$TOTAL_REFS)"
  echo "    [2] Schema match:      $SCHEMA_SCORE   ($SCH_BLOCKED blocked)"
  echo "    [3] Confidence dens:   $CONF_DENSITY/k  ($CONF_COUNT matches)"
  echo "    [4] Static errors:     $STATIC_ERRORS  ($STATIC_CHECKED checked)"
  echo "    [5] Context drift:     $DRIFT       ($TOKENS/$((THRESHOLDS_ROTATE/1000))k)"
  echo "    [6] Consec failures:   $FAILURES"
  echo "    [7] Schema staleness:  ${STALENESS}d"
  echo ""
  echo "  Recommendation:"
  case "$COLOR" in
    RED)    echo "    🔴 HALT — recovery protocol (HALLUCINATION_RULES.md)" ;;
    ORANGE) echo "    🟠 Halt Phase 2 — /schema-check + load actual source" ;;
    YELLOW) echo "    🟡 Warning — verify thêm trước khi proceed" ;;
    GREEN)  echo "    🟢 Continue normally" ;;
  esac
  echo "════════════════════════════════════════════════════════════"
  echo ""
  if [[ "$SAVE" -eq 1 ]]; then
    echo "  ⚠️  --save not supported in Bash version. Use Python for history."
    echo ""
  fi
fi

# Exit code
awk "BEGIN { exit ($HRS >= $THRESHOLD) ? 1 : 0 }"
