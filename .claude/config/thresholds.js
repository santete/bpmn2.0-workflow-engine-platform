// Load framework runtime thresholds with fallback to defaults.
// Used by Node hooks. If .claude/config/thresholds.json is missing or
// malformed, hardcoded DEFAULTS apply — framework keeps working.
const fs = require('fs');
const path = require('path');

const DEFAULTS = {
  rotate_threshold: 120_000,
  recent_drop_reset: 10_000,
  metrics_tok_warn: 90_000,
  pattern_budgets: {
    A: { working: 100_000, total: 120_000 },
    B: { working: 120_000, total: 140_000 },
    C: { working: 120_000, total: 190_000 },
  },
};

function findRoot() {
  let p = process.cwd();
  while (p !== path.dirname(p)) {
    if (fs.existsSync(path.join(p, '.claude')) || fs.existsSync(path.join(p, '.git'))) return p;
    p = path.dirname(p);
  }
  return process.cwd();
}

function load(root) {
  root = root || findRoot();
  const cfgPath = path.join(root, '.claude', 'config', 'thresholds.json');
  const out = {
    ...DEFAULTS,
    pattern_budgets: { ...DEFAULTS.pattern_budgets },
  };
  if (!fs.existsSync(cfgPath)) return out;
  try {
    const data = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
    if (!data || typeof data !== 'object') return out;
    for (const [k, v] of Object.entries(data)) {
      if (k.startsWith('_')) continue;
      out[k] = v;
    }
    if (data.pattern_budgets && typeof data.pattern_budgets === 'object') {
      out.pattern_budgets = { ...DEFAULTS.pattern_budgets, ...data.pattern_budgets };
    }
  } catch { /* fall back to defaults */ }
  return out;
}

module.exports = { load, DEFAULTS };
