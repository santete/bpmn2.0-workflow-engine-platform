#!/usr/bin/env node
/*
 * Hallucination Risk Score (HRS) — Node version
 * Trigger-only — KHÔNG chạy tự động trong PreToolUse/PostToolUse
 *
 * Usage:
 *   node .claude/hooks/nodejs/halluc-score.js [--files a,b] [--tokens N]
 *                                              [--threshold 0.7] [--json] [--save]
 *
 * Exit:
 *   0 = HRS < threshold
 *   1 = HRS >= threshold
 *
 * Note: --save requires `js-yaml` (npm i js-yaml). Without it, --save is no-op.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

let yaml = null;
try { yaml = require('js-yaml'); } catch { /* optional */ }

// Runtime thresholds (override via .claude/config/thresholds.json)
let ROTATE_THRESHOLD = 120_000;
try {
  const loader = require(path.join(__dirname, '..', '..', 'config', 'thresholds.js'));
  ROTATE_THRESHOLD = Number(loader.load().rotate_threshold) || 120_000;
} catch { /* fall back to default */ }

// ── Weights ───────────────────────────────────────────────────────────────
const W = {
  cite_coverage:      0.25,
  schema_match:       0.25,
  confidence_density: 0.10,
  static_errors:      0.20,
  context_drift:      0.10,
  failures:           0.05,
  schema_staleness:   0.05,
};

const CONFIDENCE_RE = /\b(I believe|probably|should work|I think|might be|seems like|likely|presumably|maybe|perhaps|in theory|I assume|I guess)\b/gi;

const BUILTINS = new Set([
  'get','set','append','pop','keys','values','items','split','join','strip',
  'replace','format','len','str','int','list','dict','map','filter','reduce',
  'forEach','push','shift','indexOf','slice','concat','toString',
]);

// ── Args ──────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = { threshold: 0.7, json: false, save: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--files')         args.files = argv[++i];
    else if (a === '--tokens')   args.tokens = parseInt(argv[++i], 10);
    else if (a === '--threshold') args.threshold = parseFloat(argv[++i]);
    else if (a === '--json')     args.json = true;
    else if (a === '--save')     args.save = true;
  }
  return args;
}

// ── Helpers ───────────────────────────────────────────────────────────────
function findRoot() {
  let p = process.cwd();
  while (p !== path.dirname(p)) {
    if (fs.existsSync(path.join(p, '.claude')) || fs.existsSync(path.join(p, '.git'))) return p;
    p = path.dirname(p);
  }
  return process.cwd();
}

function loadYaml(filePath) {
  if (!yaml || !fs.existsSync(filePath)) return {};
  try {
    return yaml.load(fs.readFileSync(filePath, 'utf8')) || {};
  } catch { return {}; }
}

function getModifiedFiles(root) {
  try {
    const out = execSync('git diff --name-only HEAD', {
      cwd: root, encoding: 'utf8', timeout: 10000, stdio: ['pipe','pipe','ignore']
    });
    return out.split('\n').filter(Boolean).map(f => path.join(root, f));
  } catch {
    // Fallback: recently modified source files
    const files = [];
    const cutoff = Date.now() - 3600 * 1000;
    const exts = ['.py','.js','.ts','.tsx','.go','.java'];
    function walk(dir) {
      if (files.length >= 20) return;
      let entries;
      try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
      for (const e of entries) {
        if (files.length >= 20) return;
        const skip = ['node_modules','.git','dist','build','.venv','__pycache__'];
        if (skip.includes(e.name)) continue;
        const full = path.join(dir, e.name);
        if (e.isDirectory()) walk(full);
        else if (exts.includes(path.extname(e.name))) {
          try {
            if (fs.statSync(full).mtimeMs > cutoff) files.push(full);
          } catch {}
        }
      }
    }
    walk(root);
    return files.slice(0, 20);
  }
}

function readContent(files) {
  const chunks = [];
  for (const f of files) {
    try { chunks.push(fs.readFileSync(f, 'utf8')); } catch {}
  }
  return chunks.join('\n');
}

// ── Signal 1: Cite coverage ───────────────────────────────────────────────
function signalCiteCoverage(content) {
  const calls = [...content.matchAll(/\b\w+\.(\w+)\s*\(/g)].map(m => m[1]);
  const fields = [...content.matchAll(/(?:response|data|result|payload)\s*[\.\[]\s*['"]?(\w+)/g)].map(m => m[1]);
  const refs = new Set([...calls, ...fields].filter(r => !BUILTINS.has(r)));
  const total = refs.size;
  if (total === 0) return { score: 1.0, total: 0, cited: 0 };
  const cited = (content.match(/Based on\s+`[^`]+:\d+`|Based on\s+`schema_snapshot\.yaml#/g) || []).length;
  return { score: Math.min(1, cited / total), total, cited };
}

// ── Signal 2: Schema match ────────────────────────────────────────────────
function signalSchemaMatch(content, schema) {
  if (!schema || Object.keys(schema).length === 0) {
    return { score: 1.0, total: 0, matched: 0, blocked: 0 };
  }
  const known = new Set();
  const notAvail = new Set();

  for (const cat of ['external_apis','internal_apis']) {
    const apis = schema[cat] || {};
    for (const api of Object.values(apis)) {
      if (typeof api !== 'object' || !api) continue;
      const ret = api.returns;
      if (ret && typeof ret === 'object') Object.keys(ret).forEach(k => known.add(k));
      (api.required || []).forEach(k => known.add(k));
      (api.optional || []).forEach(k => known.add(k));
      (api.not_in_response || []).forEach(k => notAvail.add(k));
      (api.NOT_available || []).forEach(k => notAvail.add(k));
    }
  }
  const db = schema.database || {};
  for (const t of Object.values(db)) {
    if (t && typeof t === 'object') (t.columns || []).forEach(c => known.add(c));
  }
  const events = schema.events || {};
  for (const ev of Object.values(events)) {
    if (ev && ev.payload && typeof ev.payload === 'object') {
      Object.keys(ev.payload).forEach(k => known.add(k));
    }
  }

  const refs = new Set();
  for (const m of content.matchAll(/(?:response|data|result|row|record|payload)\s*\.\s*(\w+)/g)) refs.add(m[1]);
  for (const m of content.matchAll(/(?:response|data|result|row|record|payload)\s*\[\s*['"](\w+)['"]/g)) refs.add(m[1]);

  if (refs.size === 0) return { score: 1.0, total: 0, matched: 0, blocked: 0 };
  if (known.size === 0) return { score: 1.0, total: 0, matched: 0, blocked: 0 };

  const blocked = [...refs].filter(r => notAvail.has(r));
  const matched = [...refs].filter(r => known.has(r));
  if (blocked.length > 0) return { score: 0.0, total: refs.size, matched: matched.length, blocked: blocked.length };
  return { score: Math.min(1, matched.length / refs.size), total: refs.size, matched: matched.length, blocked: 0 };
}

// ── Signal 3: Confidence density ──────────────────────────────────────────
function signalConfidenceDensity(content) {
  const matches = (content.match(CONFIDENCE_RE) || []).length;
  const words = Math.max(1, content.split(/\s+/).filter(Boolean).length);
  return { density: matches / (words / 1000), count: matches };
}

// ── Signal 4: Static errors (lite — JS/TS syntax only) ────────────────────
function signalStaticErrors(files) {
  let errors = 0, checked = 0;
  for (const f of files) {
    if (!fs.existsSync(f)) continue;
    const ext = path.extname(f).toLowerCase();
    try {
      if (ext === '.js' || ext === '.cjs' || ext === '.mjs') {
        checked++;
        try {
          const src = fs.readFileSync(f, 'utf8');
          // Use Function constructor as syntax check (won't execute)
          // Note: this throws on syntax error
          new Function(src);
        } catch { errors++; }
      } else if (ext === '.ts' || ext === '.tsx') {
        checked++;
        try {
          execSync(`npx --no-install tsc --noEmit --allowJs "${f}"`, {
            timeout: 20000, stdio: ['ignore','pipe','pipe']
          });
        } catch (e) {
          const out = (e.stdout || '').toString() + (e.stderr || '').toString();
          errors += (out.match(/Property '\w+' does not exist|Cannot find name/g) || []).length;
        }
      } else if (ext === '.py') {
        checked++;
        try {
          execSync(`python -c "import ast; ast.parse(open(r'${f}').read())"`, {
            timeout: 10000, stdio: 'ignore'
          });
        } catch { errors++; }
      }
    } catch {}
  }
  return { errors, checked };
}

// ── Signal 5/6/7 ──────────────────────────────────────────────────────────
const signalContextDrift = tokens => Math.min(1, tokens / ROTATE_THRESHOLD);
const signalFailures = state => parseInt(state.consecutive_failures || 0, 10) || 0;
function signalSchemaStaleness(schemaPath) {
  if (!fs.existsSync(schemaPath)) return 0;
  const ageDays = (Date.now() - fs.statSync(schemaPath).mtimeMs) / 86_400_000;
  return Math.floor(ageDays);
}

// ── Composite ─────────────────────────────────────────────────────────────
function computeHrs(s) {
  const hrs =
    W.cite_coverage      * (1 - s.cite_coverage) +
    W.schema_match       * (1 - s.schema_match) +
    W.confidence_density * Math.min(1, s.confidence_density / 3) +
    W.static_errors      * Math.min(1, s.static_errors / 3) +
    W.context_drift      * s.context_drift +
    W.failures           * Math.min(1, s.failures / 4) +
    W.schema_staleness   * Math.min(1, s.schema_staleness / 30);
  return Math.round(hrs * 1000) / 1000;
}

function colorFor(hrs, threshold) {
  if (hrs >= threshold)         return 'RED';
  if (hrs >= threshold - 0.2)   return 'ORANGE';
  if (hrs >= threshold - 0.4)   return 'YELLOW';
  return 'GREEN';
}

function dominantSignal(s) {
  const c = {
    cite_coverage:      W.cite_coverage      * (1 - s.cite_coverage),
    schema_match:       W.schema_match       * (1 - s.schema_match),
    confidence_density: W.confidence_density * Math.min(1, s.confidence_density / 3),
    static_errors:      W.static_errors      * Math.min(1, s.static_errors / 3),
    context_drift:      W.context_drift      * s.context_drift,
    failures:           W.failures           * Math.min(1, s.failures / 4),
    schema_staleness:   W.schema_staleness   * Math.min(1, s.schema_staleness / 30),
  };
  return Object.entries(c).sort((a, b) => b[1] - a[1])[0][0];
}

function appendHistory(statePath, hrs, signals, dominant) {
  if (!yaml) {
    console.error('WARN: --save requires js-yaml. Run: npm i js-yaml');
    return;
  }
  const state = loadYaml(statePath);
  const history = state.hallucination_history || [];
  history.push({
    date: new Date().toISOString().slice(0, 10),
    session: parseInt(state.session_count || 0, 10),
    hrs,
    dominant_signal: dominant,
    signals: Object.fromEntries(Object.entries(signals).map(([k, v]) =>
      [k, typeof v === 'number' ? Math.round(v * 1000) / 1000 : v]
    )),
  });
  state.hallucination_history = history.slice(-50);
  try {
    fs.writeFileSync(statePath, yaml.dump(state, { sortKeys: false, lineWidth: 120 }));
  } catch (e) {
    console.error(`WARN: Cannot save: ${e.message}`);
  }
}

// ── Main ──────────────────────────────────────────────────────────────────
function main() {
  const args = parseArgs(process.argv);
  const root = findRoot();
  const schemaPath = path.join(root, '.claude', 'memory', 'schema_snapshot.yaml');
  const statePath  = path.join(root, '.claude', 'memory', 'project_state.yaml');

  const schema = loadYaml(schemaPath);
  const state  = loadYaml(statePath);

  const files = args.files
    ? args.files.split(',').map(s => s.trim()).filter(Boolean)
    : getModifiedFiles(root);
  const content = files.length ? readContent(files) : '';

  const tokens = (args.tokens != null) ? args.tokens : Math.floor(content.length / 4);

  const cite   = signalCiteCoverage(content);
  const sch    = signalSchemaMatch(content, schema);
  const conf   = signalConfidenceDensity(content);
  const stat   = signalStaticErrors(files);
  const drift  = signalContextDrift(tokens);
  const fail   = signalFailures(state);
  const stale  = signalSchemaStaleness(schemaPath);

  const signals = {
    cite_coverage:      cite.score,
    schema_match:       sch.score,
    confidence_density: conf.density,
    static_errors:      stat.errors,
    context_drift:      drift,
    failures:           fail,
    schema_staleness:   stale,
  };

  const hrs = computeHrs(signals);
  const color = colorFor(hrs, args.threshold);
  const dom = dominantSignal(signals);

  if (args.json) {
    console.log(JSON.stringify({
      hrs, color, threshold: args.threshold, dominant_signal: dom, signals,
      details: {
        cite_total: cite.total, cite_cited: cite.cited,
        schema_total: sch.total, schema_matched: sch.matched, schema_blocked: sch.blocked,
        confidence_count: conf.count,
        static_files_checked: stat.checked,
        token_count: tokens, files_count: files.length,
      },
    }, null, 2));
  } else {
    const emoji = { GREEN: '🟢', YELLOW: '🟡', ORANGE: '🟠', RED: '🔴' }[color];
    console.log('');
    console.log('═'.repeat(60));
    console.log('  HALLUCINATION RISK SCORE');
    console.log('═'.repeat(60));
    console.log(`  Overall: ${hrs.toFixed(2)}  ${emoji} ${color}`);
    console.log(`  Threshold: ${args.threshold}  |  Dominant: ${dom}`);
    console.log(`  Files: ${files.length}  |  Tokens (est): ${tokens.toLocaleString()}`);
    console.log('');
    console.log('  Signals:');
    console.log(`    [1] Cite coverage:     ${(cite.score*100).toFixed(0).padStart(3)}%   (${cite.cited}/${cite.total})`);
    console.log(`    [2] Schema match:      ${(sch.score*100).toFixed(0).padStart(3)}%   (${sch.matched}/${sch.total}` + (sch.blocked ? `, ${sch.blocked} BLOCKED` : '') + ')');
    console.log(`    [3] Confidence dens:   ${conf.density.toFixed(2)}/k (${conf.count} matches)`);
    console.log(`    [4] Static errors:     ${stat.errors}    (${stat.checked} files checked)`);
    console.log(`    [5] Context drift:     ${drift.toFixed(2)}  (${tokens.toLocaleString()} / ${Math.floor(ROTATE_THRESHOLD/1000)}k)`);
    console.log(`    [6] Consec failures:   ${fail}`);
    console.log(`    [7] Schema staleness:  ${stale}d`);
    console.log('');
    console.log('  Recommendation:');
    if (color === 'RED') {
      console.log('    🔴 HALT — recovery protocol (HALLUCINATION_RULES.md)');
      console.log(`    🔴 Fix dominant signal: ${dom}`);
      if (sch.blocked) console.log(`    🔴 ${sch.blocked} ref(s) trong NOT_available — Type 1 hallucination`);
    } else if (color === 'ORANGE') {
      console.log('    🟠 Halt Phase 2 — /schema-check + load actual source');
      console.log(`    🟠 Re-verify dominant signal: ${dom}`);
    } else if (color === 'YELLOW') {
      console.log('    🟡 Warning — verify thêm trước khi proceed');
      console.log(`    🟡 Watch dominant signal: ${dom}`);
    } else {
      console.log('    🟢 Continue normally');
    }
    console.log('═'.repeat(60));
    console.log('');
  }

  if (args.save) {
    appendHistory(statePath, hrs, signals, dom);
    if (!args.json) console.log(`  📝 Appended to project_state.yaml\n`);
  }

  process.exit(hrs >= args.threshold ? 1 : 0);
}

main();
