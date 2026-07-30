#!/usr/bin/env node
/*
 * Hook: PreToolCall — Bash
 * Chặn các lệnh nguy hiểm. Hard stops trong CLAUDE.md.
 *
 * Exit 0 = cho phép Claude tiếp tục
 * Exit 2 = block Claude, hiển thị error
 */

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let cmd = '';
  try {
    cmd = JSON.parse(raw || '{}')?.tool_input?.command || '';
  } catch (_) {
    process.exit(0);
  }
  if (!cmd) process.exit(0);

  const block = (reason) => {
    // Telemetry (fail-open)
    try {
      const { writeEvent } = require('./metrics-writer');
      writeEvent('hook_block', {
        hook: 'block-dangerous',
        rule: reason,
        command: cmd.substring(0, 200),
        severity: 'BLOCKER',
      });
    } catch (_) {}
    console.error(`❌ BLOCKED (dangerous command): ${reason}`);
    console.error(`Lệnh: ${cmd}`);
    console.error('Nếu thực sự cần, user phải tự chạy thủ công.');
    process.exit(2);
  };

  const checks = [
    [/rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(\/|~|\$HOME|\*)/, 'rm -rf vào path nguy hiểm'],
    [/git\s+push.*--force([^-]|$).*(main|master|develop|prod)/, 'git push --force lên branch chung'],
    [/(psql|mysql).*-c.*(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE)/i, 'DROP / TRUNCATE qua DB CLI'],
    [/(--insecure|--no-check-certificate|GIT_SSL_NO_VERIFY)/, 'Disable SSL verification'],
    [/curl[^|]+\|\s*(sh|bash)/, 'curl | sh — không an toàn, phải xem script trước'],
    [/chmod\s+(-R\s+)?777/, 'chmod 777 — quá permissive'],
    [/(npm|pnpm|yarn)\s+(i|install|add)\s+(-g|--global)/, 'Install global package — phải hỏi user'],
    [/(DROP\s+TABLE|TRUNCATE\s+TABLE|ALTER\s+TABLE.*DROP)/i, 'Schema migration nguy hiểm — phải hỏi user'],
  ];

  for (const [re, msg] of checks) {
    if (re.test(cmd)) block(msg);
  }
  process.exit(0);
});
