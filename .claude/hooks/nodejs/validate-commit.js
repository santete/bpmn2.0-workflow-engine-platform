#!/usr/bin/env node
// Hook: PreToolCall — Bash (Conventional Commits gate)
// Requires: Node.js >= 16 (zero dependencies)
'use strict';
const TYPES = 'feat|fix|hotfix|refactor|test|docs|ci|chore|perf|security';
const D = '─'.repeat(60);
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => { raw += c; });
process.stdin.on('end', () => {
  let data = {};
  try { data = JSON.parse(raw); } catch { process.exit(0); }
  const cmd = data?.tool_input?.command ?? '';
  if (!cmd.includes('git commit')) process.exit(0);

  let msg = '';
  const dq = cmd.match(/-m\s+"((?:[^"\\]|\\.)*)"/);
  const sq = cmd.match(/-m\s+'((?:[^'\\]|\\.)*)'/);
  if (dq) msg = dq[1].replace(/\\"/g, '"');
  else if (sq) msg = sq[1].replace(/\\'/g, "'");
  if (!msg) process.exit(0);

  const subject = msg.split('\n')[0].trim();
  const errors = [], warnings = [];

  const CC = new RegExp(`^(\\[AI\\] )?(${TYPES})(\\([^)]+\\))?!?: .+`);
  if (!CC.test(subject)) {
    errors.push(`❌  Wrong format: '${subject}'`);
    errors.push(`    Expected: feat(scope): desc  |  Types: ${TYPES}`);
  }
  if (subject.length > 72) errors.push(`❌  Subject too long (${subject.length}/72)`);
  if (msg.length > 500)    errors.push(`❌  Message exceeds 500 chars (${msg.length})`);
  if (/^(fix bug|fixed|update|wip|temp|minor|changes|\.+)$/i.test(subject))
    errors.push(`❌  Generic message: '${subject}'`);

  const bang = new RegExp(`^(\\[AI\\] )?(${TYPES})(\\([^)]+\\))?!:`).test(subject);
  if (bang && !msg.includes('BREAKING CHANGE:'))
    warnings.push('⚠️   Breaking change (!) — add BREAKING CHANGE: footer');

  if (errors.length) {
    console.log(`\n${D}\n🚫  COMMIT BLOCKED\n${D}`);
    errors.forEach(e => console.log(e));
    if (warnings.length) { console.log(''); warnings.forEach(w => console.log(w)); }
    console.log(`\n${D}\n`);
    process.exit(1);
  }
  if (warnings.length) {
    console.log(`\n${D}\n⚠️   WARNING\n${D}`);
    warnings.forEach(w => console.log(w));
    console.log(`\n${D}\n`);
  }
  console.log(`✅  Commit OK: '${subject}'`);
  process.exit(0);
});
