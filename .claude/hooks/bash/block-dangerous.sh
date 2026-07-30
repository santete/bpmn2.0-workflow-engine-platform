#!/bin/bash
# .claude/hooks/block-dangerous.sh
# Chặn các lệnh nguy hiểm. Hard stops trong CLAUDE.md.

set -euo pipefail

COMMAND=$(jq -r '.tool_input.command // ""' < /dev/stdin)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/metrics-writer.sh" 2>/dev/null || true

block() {
  # Telemetry (fail-open)
  local cmd_short="${COMMAND:0:200}"
  write_event "hook_block" "{\"hook\":\"block-dangerous\",\"rule\":\"$1\",\"command\":\"$cmd_short\",\"severity\":\"BLOCKER\"}" 2>/dev/null || true
  echo "❌ BLOCKED (dangerous command): $1" >&2
  echo "Lệnh: $COMMAND" >&2
  echo "Nếu thực sự cần, user phải tự chạy thủ công." >&2
  exit 2
}

# rm -rf nguy hiểm (root, home, /, *)
if echo "$COMMAND" | grep -qE 'rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)[[:space:]]+(/|~|\$HOME|\*)'; then
  block "rm -rf vào path nguy hiểm"
fi

# Force push lên branch chung
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push.*--force([^-]|$)' && \
   echo "$COMMAND" | grep -qE '(main|master|develop|prod)'; then
  block "git push --force lên branch chung"
fi

# DROP / TRUNCATE qua psql / mysql CLI
if echo "$COMMAND" | grep -qiE '(psql|mysql).*-c.*(DROP[[:space:]]+(TABLE|DATABASE|SCHEMA)|TRUNCATE)'; then
  block "DROP / TRUNCATE qua DB CLI"
fi

# Disable SSL / cert verify
if echo "$COMMAND" | grep -qE '(--insecure|--no-check-certificate|GIT_SSL_NO_VERIFY)'; then
  block "Disable SSL verification"
fi

# Curl pipe sh (chạy script không kiểm tra)
if echo "$COMMAND" | grep -qE 'curl[^|]+\|[[:space:]]*(sh|bash)'; then
  block "curl | sh — không an toàn, phải xem script trước"
fi

# Chmod 777
if echo "$COMMAND" | grep -qE 'chmod[[:space:]]+(-R[[:space:]]+)?777'; then
  block "chmod 777 — quá permissive"
fi

# Global install không hỏi
if echo "$COMMAND" | grep -qE '(npm|pnpm|yarn)[[:space:]]+(i|install|add)[[:space:]]+(-g|--global)'; then
  block "Install global package — phải hỏi user"
fi

exit 0
