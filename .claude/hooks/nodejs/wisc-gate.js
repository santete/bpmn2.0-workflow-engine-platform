#!/usr/bin/env node
// Hook: PreToolUse — Edit|Write|MultiEdit
// WISC Governance Gate — block code changes when WRITE/ISOLATE/COMPRESS gates not satisfied.
// Requires: Node.js >= 16 (zero npm dependencies, uses only built-in fs/path)
// Exit 0 = allow, Exit 2 = block. Fail-open on any error.
'use strict';
const fs = require('fs');
const path = require('path');

const D = '─'.repeat(58);
const SKIP_EXTS = new Set(['.yaml', '.yml', '.md', '.json', '.toml', '.gitignore', '.env']);
const SKIP_DIRS = ['.claude/', '.claude\\', 'docs/ai/', 'docs\\ai\\', 'node_modules/', '__pycache__/'];

function findRoot(start) {
  let p = start || process.cwd();
  while (p !== path.dirname(p)) {
    if (fs.existsSync(path.join(p, '.claude')) || fs.existsSync(path.join(p, '.git'))) return p;
    p = path.dirname(p);
  }
  return start || process.cwd();
}

function parseYaml(text) {
  // Minimal YAML parser for flat/nested key: value (no arrays, no multi-line)
  // Sufficient for reading project_state.yaml fields we need
  const result = {};
  const lines = text.split('\n');
  const stack = [{ indent: -1, obj: result }];
  for (const line of lines) {
    if (/^\s*#/.test(line) || !line.trim()) continue;
    const m = line.match(/^(\s*)([^:#\s][^:#]*):\s*(.*)/);
    if (!m) continue;
    const indent = m[1].length;
    const key = m[2].trim();
    let val = m[3].trim();
    // Pop stack to find parent
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) stack.pop();
    const parent = stack[stack.length - 1].obj;
    if (val === '' || val === '{}') {
      // Nested object
      const child = {};
      parent[key] = child;
      stack.push({ indent, obj: child });
    } else {
      // Strip quotes
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'")))
        val = val.slice(1, -1);
      if (val === 'true') val = true;
      else if (val === 'false') val = false;
      else if (/^\d+$/.test(val)) val = parseInt(val, 10);
      parent[key] = val;
    }
  }
  return result;
}

function deepGet(obj, dotPath) {
  return dotPath.split('.').reduce((o, k) => (o && typeof o === 'object' ? o[k] : undefined), obj);
}

function writeMetric(root, gate, action, detail) {
  try {
    const dir = path.join(root, '.claude', 'metrics');
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const ev = JSON.stringify({
      ts: Math.floor(Date.now() / 1000),
      event: 'wisc_gate',
      pattern: '?',
      data: { gate, action, detail: (detail || '').slice(0, 200) },
    });
    fs.appendFileSync(path.join(dir, 'events.jsonl'), ev + '\n', 'utf8');
  } catch {}
}

function block(root, gate, reason, fix) {
  writeMetric(root, gate, 'block', reason);
  process.stderr.write(`\n${D}\n`);
  process.stderr.write(`🛡️  WISC GATE BLOCKED — ${gate}\n`);
  process.stderr.write(`${D}\n\n`);
  process.stderr.write(`  Lý do : ${reason}\n`);
  process.stderr.write(`  Fix   : ${fix}\n\n`);
  process.stderr.write(`  Bypass: ghi wisc_gates.${gate}.satisfied: true vào project_state.yaml\n`);
  process.stderr.write(`          (cần user approve — ghi lý do bypass vào wisc_gates.${gate}.bypass_reason)\n`);
  process.stderr.write(`\n${D}\n\n`);
  process.exit(2);
}

// ── Main ────────────────────────────────────────────────────────────────────
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => { raw += c; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(raw || '{}');
    const toolInput = data.tool_input || {};
    const target = toolInput.file_path || toolInput.path || '';
    if (!target) process.exit(0);

    // Skip non-source files
    const tl = target.toLowerCase().replace(/\\/g, '/');
    if (SKIP_EXTS.has(path.extname(tl))) process.exit(0);
    if (SKIP_DIRS.some(d => tl.includes(d))) process.exit(0);

    const root = findRoot();
    const statePath = path.join(root, '.claude', 'memory', 'project_state.yaml');
    if (!fs.existsSync(statePath)) process.exit(0);

    const state = parseYaml(fs.readFileSync(statePath, 'utf8'));
    const cls = state.last_task_classification || {};
    if (!cls.D5 && !cls.D6) process.exit(0);

    const d5 = String(cls.D5 || '').toLowerCase();
    const d6 = String(cls.D6 || '').toLowerCase();
    const gates = state.wisc_gates || {};

    // ── GATE 1: WRITE ─────────────────────────────────────────────────────
    if (d5 === 'vague') {
      const wg = gates.WRITE || {};
      if (!wg.satisfied) {
        const artifact = wg.artifact || 'spec.md';
        const candidates = [
          path.join(root, artifact),
          path.join(root, 'spec.md'),
          path.join(root, 'docs', 'spec.md'),
          path.join(root, '.claude', 'memory', 'spec.md'),
        ];
        if (!candidates.some(f => fs.existsSync(f))) {
          block(root, 'WRITE',
            `D5=${d5} — spec chưa rõ, nhưng chưa có spec.md`,
            'Viết spec.md trước khi code, sau đó ghi wisc_gates.WRITE.satisfied: true');
        }
      }
    }

    // ── GATE 2: ISOLATE ───────────────────────────────────────────────────
    if (['unknown', 'legacy-undocumented', 'cross-module'].includes(d6)) {
      const ig = gates.ISOLATE || {};
      if (!ig.satisfied) {
        const memDir = path.join(root, '.claude', 'memory');
        let found = false;
        if (fs.existsSync(memDir)) {
          found = fs.readdirSync(memDir).some(f => f.startsWith('scout_report'));
        }
        if (ig.artifact && fs.existsSync(path.join(root, ig.artifact))) found = true;
        if (!found) {
          block(root, 'ISOLATE',
            `D6=${d6} — codebase chưa quen, nhưng chưa có scout report`,
            'Chạy sub-agent scout trước khi code, hoặc ghi wisc_gates.ISOLATE.satisfied: true');
        }
      }
    }

    // ── GATE 3: COMPRESS ──────────────────────────────────────────────────
    const cg = gates.COMPRESS || {};
    if (!cg.satisfied) {
      const tokenCache = path.join(root, '.claude', 'cache', 'last_tokens.json');
      if (fs.existsSync(tokenCache)) {
        try {
          const cached = JSON.parse(fs.readFileSync(tokenCache, 'utf8'));
          const tokens = parseInt(cached.tokens || 0, 10);
          let threshold = 120000;
          const threshFile = path.join(root, '.claude', 'config', 'thresholds.json');
          if (fs.existsSync(threshFile)) {
            try {
              const tc = JSON.parse(fs.readFileSync(threshFile, 'utf8'));
              threshold = parseInt(tc.rotate_threshold || 120000, 10);
            } catch {}
          }
          if (tokens > threshold) {
            block(root, 'COMPRESS',
              `Token count (${tokens.toLocaleString()}) vượt threshold (${threshold.toLocaleString()})`,
              'Chạy /rotate để đóng session, hoặc /compact có focus');
          }
        } catch {}
      }
    }

    process.exit(0);
  } catch {
    process.exit(0); // Fail-open
  }
});
