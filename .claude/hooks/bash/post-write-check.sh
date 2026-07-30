#!/usr/bin/env bash
# Hook: PostToolCall — Write|Edit|MultiEdit (Code quality scan)
# Requires: bash >= 4, jq >= 1.6
set -euo pipefail

D="────────────────────────────────────────────────────────────"
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // ""' 2>/dev/null || echo "")
FILE_TEXT=$(echo "$INPUT" | jq -r '.tool_input.file_text // empty' 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in *.py|*.js|*.ts|*.jsx|*.tsx|*.java|*.go|*.rb|*.php|*.cs) ;;
  *) exit 0 ;; esac

case "$FILE_PATH" in *test*|*spec*|*vendor*|*node_modules*|*__pycache__*|*.venv*) exit 0 ;; esac

# Source for grep: inline file_text (preferred, parity with Python/Node) or disk file
SCAN_TARGET=""
TMP_SCAN=""
if [ -n "$FILE_TEXT" ]; then
  TMP_SCAN=$(mktemp -t pwc-scan-XXXXXX)
  printf '%s' "$FILE_TEXT" > "$TMP_SCAN"
  SCAN_TARGET="$TMP_SCAN"
elif [ -f "$FILE_PATH" ]; then
  SCAN_TARGET="$FILE_PATH"
else
  exit 0
fi
trap '[ -n "$TMP_SCAN" ] && rm -f "$TMP_SCAN"' EXIT

BLOCKERS=(); WARNS=()
SHORT="${FILE_PATH/#$HOME/~}"

scan() { grep -nE "$1" "$SCAN_TARGET" 2>/dev/null || true; }

# BLOCKERS: Debug statements
while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
  echo "$ltxt" | grep -qE "^(#|//|\*)" && continue
  BLOCKERS+=("  L$(printf '%4s' $lnum): console.log/debug  →  ${ltxt:0:70}")
done < <(scan 'console\.(log|debug|warn)\s*\(')

while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
  echo "$ltxt" | grep -qE "^(#|//|import|from|require)" && continue
  BLOCKERS+=("  L$(printf '%4s' $lnum): print()  →  ${ltxt:0:70}")
done < <(scan '\bprint\s*\(')

while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1)
  BLOCKERS+=("  L$(printf '%4s' $lnum): debugger / pdb.set_trace()")
done < <(scan '\b(debugger|pdb\.set_trace|breakpoint)\s*(\(\))?')

# BLOCKERS: Hardcoded secrets
SECRET_FOUND=false
while IFS= read -r m; do
  $SECRET_FOUND && break
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
  echo "$ltxt" | grep -qiE "(os\.environ|os\.getenv|process\.env)" && continue
  BLOCKERS+=("  L$(printf '%4s' $lnum): 🔴 Possible hardcoded secret  →  ${ltxt:0:60}")
  SECRET_FOUND=true
done < <(grep -niE '(password|api_key|secret)\s*=\s*["\x27][^\s"'\'']{4,}' "$SCAN_TARGET" 2>/dev/null || true)

while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1)
  BLOCKERS+=("  L$(printf '%4s' $lnum): 🔴 Token hardcoded in source")
done < <(scan '(glpat-[A-Za-z0-9_-]{20}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{32})')

# BLOCKERS: SQL injection — 3 patterns parity với Python/Node
sql_seen=""
add_sql_match() {
  local pat="$1"
  while IFS= read -r m; do
    [ -z "$m" ] && continue
    lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
    [[ ",$sql_seen," == *",$lnum,"* ]] && continue
    sql_seen="$sql_seen,$lnum"
    BLOCKERS+=("  L$(printf '%4s' $lnum): SQL injection risk  →  ${ltxt:0:70}")
  done < <(grep -niE "$pat" "$SCAN_TARGET" 2>/dev/null || true)
}
# 1) f-string với SELECT/INSERT/... và placeholder {...}
add_sql_match 'f["'"'"'].*(SELECT|INSERT|UPDATE|DELETE).*\{'
# 2) string concat: "...SELECT/WHERE..." +
add_sql_match '".*(SELECT|WHERE).*"[[:space:]]*\+'
# 3) JS template literal: `...SELECT/WHERE...${...}
add_sql_match '`.*(SELECT|WHERE).*\$\{'

# BLOCKERS: PCI DSS — PAN/CVV logging
while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
  echo "$ltxt" | grep -qE "^(#|//|\*)" && continue
  BLOCKERS+=("  L$(printf '%4s' $lnum): 🔴 PAN/CVV logging — PCI DSS violation  →  ${ltxt:0:60}")
done < <(grep -niE '\b(log|logger|print)\b.*\b(pan|card_number|cvv|cvc|track2)\b' "$SCAN_TARGET" 2>/dev/null || true)

# WARNINGS: TODO/FIXME without ticket
while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2-)
  echo "$ltxt" | grep -qE "(#[0-9]+|[A-Z]{2,}-[0-9]+)" && continue
  WARNS+=("  L$(printf '%4s' $lnum): TODO/FIXME without ticket  →  ${ltxt:0:60}")
done < <(scan '\b(TODO|FIXME|HACK|XXX)\b')

# WARNINGS: PII in logs
while IFS= read -r m; do
  [ -z "$m" ] && continue
  lnum=$(echo "$m" | cut -d: -f1); ltxt=$(echo "$m" | cut -d: -f2- | xargs)
  WARNS+=("  L$(printf '%4s' $lnum): PII possibly logged  →  ${ltxt:0:70}")
done < <(grep -niE '\b(log|logger)\b.*(email|password|token|card|phone)' "$SCAN_TARGET" 2>/dev/null || true)

[ ${#BLOCKERS[@]} -eq 0 ] && [ ${#WARNS[@]} -eq 0 ] && exit 0

echo ""; echo "$D"
if [ ${#BLOCKERS[@]} -gt 0 ]; then
  echo "🔴  BLOCKER(s) — $SHORT"; echo "$D"
  echo "  Fix before MR submission:"; echo ""
  for b in "${BLOCKERS[@]}"; do echo "$b"; done
fi
if [ ${#WARNS[@]} -gt 0 ]; then
  [ ${#BLOCKERS[@]} -gt 0 ] && echo ""
  [ ${#BLOCKERS[@]} -eq 0 ] && { echo "⚠️   WARNINGS — $SHORT"; echo "$D"; }
  for w in "${WARNS[@]}"; do echo "$w"; done
fi
echo ""; echo "$D"; echo ""

# Telemetry: log block events (fail-open)
if [ ${#BLOCKERS[@]} -gt 0 ]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  source "$SCRIPT_DIR/metrics-writer.sh" 2>/dev/null || true
  for b in "${BLOCKERS[@]}"; do
    rule=$(echo "$b" | sed -n 's/.*L[[:space:]]*[0-9]*:[[:space:]]*\(🔴[[:space:]]*\)\?\([^→]*\).*/\2/p' | head -c 40 | xargs)
    write_event "hook_block" "{\"hook\":\"post-write-check\",\"rule\":\"${rule:-unknown}\",\"file\":\"$FILE_PATH\",\"severity\":\"BLOCKER\"}" 2>/dev/null || true
  done
fi

[ ${#BLOCKERS[@]} -gt 0 ] && exit 1 || exit 0
