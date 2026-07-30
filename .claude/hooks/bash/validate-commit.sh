#!/bin/bash
# .claude/hooks/validate-commit.sh
# Chặn Claude Code commit không đúng convention
# Spec: docs/ai/GIT_CONVENTION.md

set -euo pipefail

COMMAND=$(jq -r '.tool_input.command // ""' < /dev/stdin)

# Chỉ check khi là git commit
if echo "$COMMAND" | grep -qE 'git[[:space:]]+commit'; then
  
  # Extract message từ -m "..." hoặc -m '...'
  MSG=$(echo "$COMMAND" | sed -n "s/.*-m[[:space:]]*['\"]\\([^'\"]*\\)['\"].*/\\1/p" | head -1)
  
  if [ -n "$MSG" ]; then
    # Conventional Commits pattern
    PATTERN='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([a-z0-9-]+\))?!?: .{1,72}$'
    
    if ! echo "$MSG" | grep -qE "$PATTERN"; then
      cat >&2 <<EOF
❌ BLOCKED: Commit message không đúng convention.

Format yêu cầu: <type>(<scope>): <subject>

Type hợp lệ: feat | fix | docs | style | refactor | test | chore | perf | ci | build | revert
Scope: lowercase, kebab-case (optional)
Subject: ≤ 72 ký tự, viết thường, không dấu chấm cuối

Bạn vừa thử:
  $MSG

Xem chi tiết: docs/ai/GIT_CONVENTION.md
EOF
      exit 1
    fi
  fi
  
  # Chặn commit trực tiếp vào branch protected
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
  case "$CURRENT_BRANCH" in
    main|master|develop|prod|production)
      cat >&2 <<EOF
❌ BLOCKED: Không được commit trực tiếp vào branch '$CURRENT_BRANCH'.

Tạo feature branch trước:
  git checkout -b feature/<ticket-id>-<short-desc>
EOF
      exit 1
      ;;
  esac
fi

exit 0
