#!/usr/bin/env node
/*
 * metrics_writer — append-only event log cho framework telemetry.
 * Node.js parity with Python metrics_writer.py.
 *
 * Fail-open invariant: KHÔNG bao giờ throw, KHÔNG bao giờ block caller.
 *
 * Usage:
 *   const { writeEvent } = require('./metrics-writer');
 *   writeEvent('hook_block', { hook: 'block-dangerous', rule: 'rm -rf' });
 */

const fs = require('fs');
const path = require('path');

function findProjectRoot(start) {
  let dir = start || process.cwd();
  while (dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, '.claude')) || fs.existsSync(path.join(dir, '.git'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  return process.cwd();
}

function readPattern(root) {
  try {
    const statePath = path.join(root, '.claude', 'memory', 'project_state.yaml');
    if (!fs.existsSync(statePath)) return '?';
    const text = fs.readFileSync(statePath, 'utf-8');
    const m = text.match(/^pattern:\s*([ABC])\b/m);
    return m ? m[1] : '?';
  } catch (_) {
    return '?';
  }
}

function writeEvent(eventType, data, root) {
  try {
    root = root || findProjectRoot();
    const metricsDir = path.join(root, '.claude', 'metrics');
    const logPath = path.join(metricsDir, 'events.jsonl');

    fs.mkdirSync(metricsDir, { recursive: true });

    const event = {
      ts: Math.floor(Date.now() / 1000),
      event: eventType,
      pattern: readPattern(root),
      data: data || {},
    };

    fs.appendFileSync(logPath, JSON.stringify(event) + '\n', 'utf-8');
    return true;
  } catch (_) {
    return false;
  }
}

module.exports = { findProjectRoot, writeEvent };
