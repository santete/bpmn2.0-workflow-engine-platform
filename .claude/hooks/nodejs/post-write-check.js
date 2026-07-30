#!/usr/bin/env node
// Hook: PostToolCall — Write|Edit|MultiEdit (Code quality scan)
// Requires: Node.js >= 16 (zero dependencies, uses only built-in fs)
'use strict';
const fs = require('fs'), path = require('path');
const D = '─'.repeat(60);
const SCAN_EXTS  = new Set(['.py','.js','.ts','.jsx','.tsx','.java','.go','.rb','.php','.cs']);
const SKIP_PATHS = ['test','spec','vendor','node_modules','__pycache__','.venv','dist','build'];
const HOME       = process.env.HOME || process.env.USERPROFILE || '';

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => { raw += c; });
process.stdin.on('end', () => {
  let data = {};
  try { data = JSON.parse(raw); } catch { process.exit(0); }
  const filePath = data?.tool_input?.path ?? '';
  if (!filePath) process.exit(0);
  if (!SCAN_EXTS.has(path.extname(filePath).toLowerCase())) process.exit(0);
  if (SKIP_PATHS.some(s => filePath.toLowerCase().includes(s))) process.exit(0);

  let content = data?.tool_input?.file_text ?? data?.tool_input?.new_str ?? '';
  if (!content && fs.existsSync(filePath)) {
    try { content = fs.readFileSync(filePath, 'utf8'); } catch { process.exit(0); }
  }
  if (!content) process.exit(0);
  const lines = content.split('\n');
  const blockers = [], warns = [];
  const pad = n => String(n).padStart(4,' ');
  const trim = (s,m=70) => s.length>m ? s.slice(0,m)+'…' : s;
  const isCmt = l => /^\s*(#|\/\/|\*|\/\*)/.test(l);

  const DEBUG_RE = [
    [/\bconsole\.(log|debug|warn)\s*\(/g, 'console.log/debug'],
    [/\bprint\s*\(/g, 'print()'],
    [/\bdebugger\b/g, 'debugger'],
    [/\bpdb\.set_trace\s*\(\)/g, 'pdb.set_trace()'],
    [/\bbreakpoint\s*\(\)/g, 'breakpoint()'],
  ];
  lines.forEach((line, i) => {
    if (isCmt(line)) return;
    DEBUG_RE.forEach(([re, label]) => {
      if (re.test(line)) blockers.push(`  L${pad(i+1)}: ${label}  →  ${trim(line.trim())}`);
      re.lastIndex = 0;
    });
  });

  const SECRET_RE = [
    [/password\s*=\s*['"][^'"]{4,}['"]/gi, 'Hardcoded password'],
    [/api_key\s*=\s*['"][^'"]{8,}['"]/gi,  'Hardcoded API key'],
    [/secret\s*=\s*['"][^'"]{8,}['"]/gi,   'Hardcoded secret'],
    [/glpat-[A-Za-z0-9_-]{20,}/g,          'GitLab PAT'],
    [/ghp_[A-Za-z0-9]{36}/g,               'GitHub token'],
    [/sk-[A-Za-z0-9]{32,}/g,               'OpenAI key'],
  ];
  let secretFound = false;
  lines.forEach((line, i) => {
    if (secretFound) return;
    if (/os\.environ|os\.getenv|process\.env|env\./.test(line)) return;
    SECRET_RE.forEach(([re, label]) => {
      if (!secretFound && re.test(line)) {
        blockers.push(`  L${pad(i+1)}: 🔴 ${label} — verify immediately`);
        secretFound = true;
      }
      re.lastIndex = 0;
    });
  });

  const SQL_RE = [
    /f['"][^'"]*(?:SELECT|INSERT|UPDATE|DELETE)[^'"]*\{/i,           // Python f-string
    /['"][^'"]*(?:SELECT|WHERE)[^'"]*['"]\s*\+/i,                    // string concat
    /`[^`]*(?:SELECT|WHERE)[^`]*\$\{/i,                              // JS template literal
  ];
  lines.forEach((line, i) => {
    for (const re of SQL_RE) {
      if (re.test(line)) {
        blockers.push(`  L${pad(i+1)}: SQL injection risk  →  ${trim(line.trim())}`);
        break;
      }
    }
  });

  const PAN_LOG_RE = /\b(log|logger|print)\b.*\b(pan|card_number|cvv|cvc|track2)\b/i;
  lines.forEach((line, i) => {
    if (isCmt(line)) return;
    if (PAN_LOG_RE.test(line))
      blockers.push(`  L${pad(i+1)}: 🔴 PAN/CVV logging — PCI DSS violation  →  ${trim(line.trim(), 60)}`);
  });

  const TICKET_RE = /(#\d+|[A-Z]{2,}-\d+)/;
  lines.forEach((line, i) => {
    if (/\b(TODO|FIXME|HACK|XXX)\b/i.test(line) && !TICKET_RE.test(line))
      warns.push(`  L${pad(i+1)}: TODO/FIXME without ticket  →  ${trim(line.trim())}`);
  });

  const PII_LOG = /\b(log|logger)\b.*(email|password|token|card|phone)/i;
  lines.forEach((line, i) => {
    if (PII_LOG.test(line))
      warns.push(`  L${pad(i+1)}: PII possibly logged  →  ${trim(line.trim())}`);
  });

  const EMPTY_CATCH = /catch\s*\([^)]*\)\s*\{\s*\}|except\s*:/;
  lines.forEach((line, i) => {
    if (EMPTY_CATCH.test(line))
      warns.push(`  L${pad(i+1)}: Empty catch / bare except  →  silent failure risk`);
  });

  if (!blockers.length && !warns.length) process.exit(0);

  const shortPath = filePath.replace(HOME, '~');
  console.log(`\n${D}`);
  if (blockers.length) {
    console.log(`🔴  BLOCKER(s) — ${shortPath}`);
    console.log(D); console.log('  Fix before MR submission:\n');
    blockers.forEach(b => console.log(b));
  }
  if (warns.length) {
    if (blockers.length) console.log('');
    else { console.log(`⚠️   WARNINGS — ${shortPath}`); console.log(D); }
    warns.forEach(w => console.log(w));
  }
  console.log(`\n${D}\n`);

  // Telemetry: log block events (fail-open)
  if (blockers.length) {
    try {
      const { writeEvent } = require('./metrics-writer');
      const ruleRe = /L\s*\d+:\s*(?:🔴\s*)?([^→\n]+?)(?:\s*→|\n|$)/;
      for (const b of blockers) {
        const m = b.match(ruleRe);
        const rule = m ? m[1].trim().substring(0, 40) : 'unknown';
        writeEvent('hook_block', { hook: 'post-write-check', rule, file: filePath, severity: 'BLOCKER' });
      }
    } catch (_) {}
  }

  process.exit(blockers.length > 0 ? 1 : 0);
});
