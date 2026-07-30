#!/usr/bin/env python3
"""
Framework Benchmark Suite
Measure overhead, quality impact, and feature effectiveness.

Usage:
    python .claude/scripts/benchmark.py --overhead     # Measure framework token overhead
    python .claude/scripts/benchmark.py --metrics      # Analyze metrics from events.jsonl
    python .claude/scripts/benchmark.py --compare      # Compare with-framework vs baseline
    python .claude/scripts/benchmark.py --all          # Run all benchmarks
    python .claude/scripts/benchmark.py --export csv   # Export results to CSV
"""
import io
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows fix
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def find_root() -> Path:
    """Find project root containing .claude/ AND CLAUDE.md (framework root).

    Also checks core/ subdirectory for template repo structure.
    """
    p = Path.cwd()
    for _ in range(10):
        if (p / '.claude').is_dir() and (p / 'CLAUDE.md').is_file():
            return p
        if (p / 'core' / '.claude').is_dir() and (p / 'core' / 'CLAUDE.md').is_file():
            return p / 'core'
        p = p.parent
    return Path.cwd()


# ── Benchmark 1: Framework Overhead ──────────────────────────────────────────

def measure_overhead(root: Path) -> dict:
    """Measure token overhead of framework configuration files.

    Estimates tokens consumed by eager-load files (always loaded at session start)
    and lazy-load files (loaded on demand).
    """
    # Rough token estimation: 1 token ≈ 4 chars for English, ~3 chars for mixed
    CHARS_PER_TOKEN = 3.5

    eager_files = [
        'docs/ai/PROJECT_MAP.md',
        '.claude/memory/project_state.yaml',
        'docs/ai/HALLUCINATION_RULES.md',
    ]

    # Check if internal_rules exists
    if (root / 'docs/ai/internal_rules/00_INDEX.md').exists():
        eager_files.append('docs/ai/internal_rules/00_INDEX.md')

    lazy_files = [
        '.claude/memory/schema_snapshot.yaml',
        '.claude/memory/task_tracker.yaml',
        '.claude/memory/agent_mail.yaml',
        'docs/ai/CODING_RULES.md',
        'docs/ai/GIT_CONVENTION.md',
        'docs/ai/API_RULES.md',
        'docs/ai/DB_RULES.md',
        'docs/ai/SECURITY_RULES.md',
        'docs/ai/TESTING_RULES.md',
        'docs/ai/ROUTING_MATRIX.md',
    ]

    # CLAUDE.md is always loaded (it's the main orchestrator)
    claude_md = root / 'CLAUDE.md'

    skills_files = list((root / '.claude/skills').rglob('rules.md')) if (root / '.claude/skills').exists() else []

    results = {
        'claude_md': {'chars': 0, 'tokens': 0, 'file': 'CLAUDE.md'},
        'eager_load': [],
        'lazy_load': [],
        'skills': [],
        'totals': {},
    }

    # CLAUDE.md
    if claude_md.exists():
        chars = len(claude_md.read_text(encoding='utf-8', errors='ignore'))
        results['claude_md'] = {
            'file': 'CLAUDE.md',
            'chars': chars,
            'tokens': int(chars / CHARS_PER_TOKEN),
        }

    # Eager files
    eager_total = results['claude_md']['tokens']
    for f in eager_files:
        fp = root / f
        if fp.exists():
            chars = len(fp.read_text(encoding='utf-8', errors='ignore'))
            tokens = int(chars / CHARS_PER_TOKEN)
            results['eager_load'].append({'file': f, 'chars': chars, 'tokens': tokens})
            eager_total += tokens

    # Lazy files
    lazy_total = 0
    for f in lazy_files:
        fp = root / f
        if fp.exists():
            chars = len(fp.read_text(encoding='utf-8', errors='ignore'))
            tokens = int(chars / CHARS_PER_TOKEN)
            results['lazy_load'].append({'file': f, 'chars': chars, 'tokens': tokens})
            lazy_total += tokens

    # Skills
    skills_total = 0
    for fp in skills_files:
        chars = len(fp.read_text(encoding='utf-8', errors='ignore'))
        tokens = int(chars / CHARS_PER_TOKEN)
        rel = str(fp.relative_to(root))
        results['skills'].append({'file': rel, 'chars': chars, 'tokens': tokens})
        skills_total += tokens

    # Internal rules (lazy)
    internal_total = 0
    internal_dir = root / 'docs/ai/internal_rules'
    if internal_dir.exists():
        for fp in internal_dir.glob('*.md'):
            if fp.name == '00_INDEX.md':
                continue  # already in eager
            chars = len(fp.read_text(encoding='utf-8', errors='ignore'))
            tokens = int(chars / CHARS_PER_TOKEN)
            internal_total += tokens

    results['totals'] = {
        'eager_baseline': eager_total,
        'lazy_pool': lazy_total,
        'skills_pool': skills_total,
        'internal_rules': internal_total,
        'max_possible': eager_total + lazy_total + skills_total + internal_total,
        'typical_session': eager_total + int(lazy_total * 0.3) + int(skills_total * 0.4),
    }

    return results


def print_overhead(results: dict):
    """Pretty-print overhead benchmark results."""
    print("\n" + "=" * 60)
    print("BENCHMARK 1: Framework Token Overhead")
    print("=" * 60)

    t = results['totals']
    print(f"\nCLAUDE.md (always loaded):  {results['claude_md']['tokens']:>6,} tokens")
    print(f"\nEager-load files (Phase 0, every session):")
    for f in results['eager_load']:
        print(f"  {f['file']:<50} {f['tokens']:>5,} tokens")
    print(f"  {'TOTAL EAGER BASELINE':<50} {t['eager_baseline']:>5,} tokens")

    print(f"\nLazy-load files (on demand, ~30% loaded per session):")
    for f in results['lazy_load']:
        print(f"  {f['file']:<50} {f['tokens']:>5,} tokens")
    print(f"  {'TOTAL LAZY POOL':<50} {t['lazy_pool']:>5,} tokens")

    if results['skills']:
        print(f"\nSkills (progressive disclosure, ~40% loaded per session):")
        for f in results['skills']:
            print(f"  {f['file']:<50} {f['tokens']:>5,} tokens")
        print(f"  {'TOTAL SKILLS POOL':<50} {t['skills_pool']:>5,} tokens")

    if t['internal_rules'] > 0:
        print(f"\nInternal rules (lazy):       {t['internal_rules']:>5,} tokens")

    print(f"\n--- Summary ---")
    print(f"Eager baseline (every session):   {t['eager_baseline']:>6,} tokens")
    print(f"Typical session (~30% lazy):      {t['typical_session']:>6,} tokens")
    print(f"Max possible (all loaded):        {t['max_possible']:>6,} tokens")
    print(f"Context budget 120k:              {120_000:>6,} tokens")
    print(f"Overhead % (typical/120k):        {t['typical_session']/1200:.1f}%")
    print(f"Overhead % (max/120k):            {t['max_possible']/1200:.1f}%")


# ── Benchmark 2: Metrics Analysis ────────────────────────────────────────────

def analyze_metrics(root: Path, days: int = 30) -> dict:
    """Analyze events.jsonl for quality and productivity metrics."""
    events_path = root / '.claude/metrics/events.jsonl'
    if not events_path.exists():
        return {'error': 'No events.jsonl found. Run some sessions first.'}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events = []
    try:
        for line in events_path.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = e.get('ts', e.get('timestamp', ''))
                if ts and ts >= cutoff.isoformat():
                    events.append(e)
            except json.JSONDecodeError:
                continue
    except Exception:
        return {'error': f'Failed to read {events_path}'}

    if not events:
        return {'error': f'No events in last {days} days. Run some sessions first.'}

    # Categorize events
    sessions = [e for e in events if e.get('event') == 'session_end']
    hrs_scores = [e for e in events if e.get('event') == 'halluc_score']
    hook_blocks = [e for e in events if e.get('event') == 'hook_block']
    loop_retries = [e for e in events if e.get('event') == 'loop_retry']
    classifies = [e for e in events if e.get('event') == 'classify']
    task_warnings = [e for e in events if e.get('event') == 'task_in_progress_at_end']

    results = {
        'period_days': days,
        'total_events': len(events),
        'sessions': {
            'count': len(sessions),
            'avg_tokens': 0,
            'rotate_rate': 0,
        },
        'quality': {
            'hrs_count': len(hrs_scores),
            'avg_hrs': 0,
            'hrs_green_pct': 0,
            'hrs_red_pct': 0,
            'hook_blocks': len(hook_blocks),
            'blocks_per_session': 0,
            'top_block_rules': [],
        },
        'productivity': {
            'loop_retries': len(loop_retries),
            'avg_retries_per_session': 0,
            'task_warnings': len(task_warnings),
        },
    }

    # Session analysis
    if sessions:
        tokens = [s.get('data', {}).get('final_tokens', 0) for s in sessions]
        rotated = [s for s in sessions if s.get('data', {}).get('rotated')]

        results['sessions']['avg_tokens'] = int(sum(tokens) / len(tokens)) if tokens else 0
        results['sessions']['rotate_rate'] = round(len(rotated) / len(sessions) * 100, 1)

    # HRS analysis
    if hrs_scores:
        scores = [h.get('data', {}).get('hrs', 0) for h in hrs_scores]
        colors = [h.get('data', {}).get('color', '') for h in hrs_scores]
        results['quality']['avg_hrs'] = round(sum(scores) / len(scores), 3)
        results['quality']['hrs_green_pct'] = round(colors.count('GREEN') / len(colors) * 100, 1)
        results['quality']['hrs_red_pct'] = round(colors.count('RED') / len(colors) * 100, 1)

    # Hook block analysis
    if hook_blocks and sessions:
        results['quality']['blocks_per_session'] = round(len(hook_blocks) / max(len(sessions), 1), 2)
        rule_counts = {}
        for b in hook_blocks:
            rule = b.get('data', {}).get('rule', 'unknown')
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
        results['quality']['top_block_rules'] = sorted(rule_counts.items(), key=lambda x: -x[1])[:5]

    # Productivity
    if loop_retries and sessions:
        results['productivity']['avg_retries_per_session'] = round(
            len(loop_retries) / max(len(sessions), 1), 2)

    return results


def print_metrics(results: dict):
    """Pretty-print metrics analysis."""
    print("\n" + "=" * 60)
    print("BENCHMARK 2: Quality & Productivity Metrics")
    print("=" * 60)

    if 'error' in results:
        print(f"\n  {results['error']}")
        return

    s = results['sessions']
    q = results['quality']
    p = results['productivity']

    print(f"\nPeriod: last {results['period_days']} days ({results['total_events']} events)")

    print(f"\n--- Sessions ({s['count']}) ---")
    print(f"  Avg tokens:      {s['avg_tokens']:>8,}")
    print(f"  Rotate rate:      {s['rotate_rate']}%")

    print(f"\n--- Quality ---")
    print(f"  HRS scores:       {q['hrs_count']} measurements")
    print(f"  Avg HRS:          {q['avg_hrs']:.3f} {'(GREEN)' if q['avg_hrs'] < 0.3 else '(YELLOW)' if q['avg_hrs'] < 0.5 else '(RED)'}")
    print(f"  GREEN rate:       {q['hrs_green_pct']}%")
    print(f"  RED rate:         {q['hrs_red_pct']}%")
    print(f"  Hook blocks:      {q['hook_blocks']} total ({q['blocks_per_session']}/session)")
    if q['top_block_rules']:
        print(f"  Top block rules:")
        for rule, count in q['top_block_rules']:
            print(f"    {rule}: {count}")

    print(f"\n--- Productivity ---")
    print(f"  Loop retries:     {p['loop_retries']} total ({p['avg_retries_per_session']}/session)")
    print(f"  Task warnings:    {p['task_warnings']} (unclosed tasks at session end)")


# ── Benchmark 3: Feature Comparison ──────────────────────────────────────────

def compare_features(root: Path) -> dict:
    """Compare framework features: token cost vs value."""
    results = {
        'features': [],
        'summary': {},
    }

    # Feature: Skills vs Full Rules
    skills_dir = root / '.claude/skills'
    rules_dir = root / 'docs/ai'
    if skills_dir.exists() and rules_dir.exists():
        skill_tokens = 0
        full_tokens = 0
        for skill_rules in skills_dir.rglob('rules.md'):
            chars = len(skill_rules.read_text(encoding='utf-8', errors='ignore'))
            skill_tokens += int(chars / 3.5)

        for rule_file in rules_dir.glob('*.md'):
            if rule_file.name == 'PROJECT_MAP.md':
                continue
            chars = len(rule_file.read_text(encoding='utf-8', errors='ignore'))
            full_tokens += int(chars / 3.5)

        savings = full_tokens - skill_tokens if full_tokens > skill_tokens else 0
        results['features'].append({
            'name': 'Skills Progressive Disclosure',
            'description': 'Load condensed skill rules vs full rule files',
            'cost_tokens': skill_tokens,
            'baseline_tokens': full_tokens,
            'savings_tokens': savings,
            'savings_pct': round(savings / max(full_tokens, 1) * 100, 1),
        })

    # Feature: Code Graph vs File Reading
    graph_path = root / '.claude/memory/code_graph.json'
    if graph_path.exists():
        graph_data = json.loads(graph_path.read_text(encoding='utf-8'))
        meta = graph_data.get('meta', {})
        graph_tokens = int(len(graph_path.read_text(encoding='utf-8')) / 3.5)
        # Estimate: reading 15 files avg 200 lines each ≈ 15 * 200 * 40 chars / 3.5
        estimated_file_read = int(meta.get('files_scanned', 15) * 200 * 40 / 3.5)
        # A graph query returns ~500 chars ≈ 143 tokens
        query_cost = 143

        results['features'].append({
            'name': 'Code Knowledge Graph',
            'description': 'Query graph vs reading source files',
            'cost_tokens': query_cost,
            'baseline_tokens': estimated_file_read,
            'savings_tokens': estimated_file_read - query_cost,
            'savings_pct': round((estimated_file_read - query_cost) / max(estimated_file_read, 1) * 100, 1),
            'note': f'Graph: {meta.get("symbols_count", 0)} symbols, {meta.get("edges_count", 0)} edges from {meta.get("files_scanned", 0)} files',
        })

    # Feature: 6D Classification overhead
    routing_matrix = root / 'docs/ai/ROUTING_MATRIX.md'
    if routing_matrix.exists():
        chars = len(routing_matrix.read_text(encoding='utf-8', errors='ignore'))
        tokens = int(chars / 3.5)
        results['features'].append({
            'name': '6D Task Classification',
            'description': 'One-time cost per task to choose correct methodology',
            'cost_tokens': tokens,
            'baseline_tokens': 0,
            'savings_tokens': 0,
            'savings_pct': 0,
            'note': 'Prevents wrong methodology choice (spec says wrong method = highest waste)',
        })

    # Feature: Task Tracker overhead
    tracker = root / '.claude/memory/task_tracker.yaml'
    if tracker.exists():
        chars = len(tracker.read_text(encoding='utf-8', errors='ignore'))
        tokens = int(chars / 3.5)
        results['features'].append({
            'name': 'Task Tracker (Beads-compatible)',
            'description': 'Persistent task state vs context-only tracking',
            'cost_tokens': tokens,
            'baseline_tokens': 0,
            'savings_tokens': 0,
            'savings_pct': 0,
            'note': 'Prevents Agent Amnesia — state survives compact/rotate',
        })

    return results


def print_comparison(results: dict):
    """Pretty-print feature comparison."""
    print("\n" + "=" * 60)
    print("BENCHMARK 3: Feature Token Cost vs Value")
    print("=" * 60)

    for f in results['features']:
        print(f"\n--- {f['name']} ---")
        print(f"  {f['description']}")
        print(f"  Cost:      {f['cost_tokens']:>6,} tokens")
        if f['baseline_tokens'] > 0:
            print(f"  Baseline:  {f['baseline_tokens']:>6,} tokens (without feature)")
            print(f"  Savings:   {f['savings_tokens']:>6,} tokens ({f['savings_pct']}%)")
        if f.get('note'):
            print(f"  Note: {f['note']}")


# ── Export ───────────────────────────────────────────────────────────────────

def export_csv(overhead: dict, metrics: dict, comparison: dict, root: Path):
    """Export benchmark results to CSV."""
    output = root / '.claude/metrics'
    output.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime('%Y-%m-%d')
    path = output / f'benchmark_{ts}.csv'

    lines = ['category,metric,value,unit']

    # Overhead
    t = overhead['totals']
    lines.append(f'overhead,eager_baseline,{t["eager_baseline"]},tokens')
    lines.append(f'overhead,typical_session,{t["typical_session"]},tokens')
    lines.append(f'overhead,max_possible,{t["max_possible"]},tokens')
    lines.append(f'overhead,overhead_pct_typical,{t["typical_session"]/1200:.1f},%')

    # Metrics
    if 'error' not in metrics:
        s = metrics['sessions']
        q = metrics['quality']
        lines.append(f'sessions,count,{s["count"]},count')
        lines.append(f'sessions,avg_tokens,{s["avg_tokens"]},tokens')
        lines.append(f'quality,avg_hrs,{q["avg_hrs"]},score')
        lines.append(f'quality,hrs_green_pct,{q["hrs_green_pct"]},%')
        lines.append(f'quality,hook_blocks_per_session,{q["blocks_per_session"]},count')

    # Comparison
    for f in comparison['features']:
        name = f['name'].lower().replace(' ', '_')
        lines.append(f'feature,{name}_cost,{f["cost_tokens"]},tokens')
        if f['savings_tokens'] > 0:
            lines.append(f'feature,{name}_savings,{f["savings_tokens"]},tokens')

    path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nExported to: {path}")


# ── Benchmark Scenarios ──────────────────────────────────────────────────────

def print_scenarios():
    """Print manual benchmark scenarios for A/B testing."""
    print("\n" + "=" * 60)
    print("BENCHMARK SCENARIOS — Manual A/B Testing Guide")
    print("=" * 60)

    print("""
Run each scenario WITH framework (A) and WITHOUT framework (B).
Record: tokens used, time, hallucination count, code quality issues.

SCENARIO 1 — Small Bug Fix (2a, ~30 min)
  Task: "Fix login validation — wrong error message for expired token"
  Measure: tokens, HRS score, hook blocks, time to resolve
  Expected: A uses fewer tokens (focused context), fewer hallucinations

SCENARIO 2 — Medium Feature (2a, ~2 hours)
  Task: "Add search by product code — API endpoint + service + tests"
  Measure: tokens, test coverage, retry loops, placeholder count
  Expected: A has TDD-first (tests exist), no placeholders, fewer loops

SCENARIO 3 — Investigation (2a, ~1 hour)
  Task: "Why is /api/orders slow? Investigate and report"
  Measure: tokens, files read, accuracy of diagnosis
  Expected: A uses scout isolation (fewer tokens for same insight)

SCENARIO 4 — Large Epic (2b, multi-session)
  Task: "8-task feature: search + filter + sort + pagination + tests"
  Measure: task completion rate, state preservation across sessions, dependency correctness
  Expected: A preserves state via task tracker, B loses context on rotate

SCENARIO 5 — Legacy Codebase (2a, unknown code)
  Task: "Add feature to module you haven't seen before"
  Measure: tokens, time to first correct code, hallucination count
  Expected: A uses code graph + scout, fewer hallucinations about non-existent APIs

SCORING MATRIX:
  | Metric              | Weight | How to measure                          |
  |---------------------|--------|-----------------------------------------|
  | Token efficiency    | 25%    | Total tokens used for same output       |
  | Code quality        | 25%    | HRS score + hook block count            |
  | Completion rate     | 20%    | % of task completed correctly           |
  | Time to complete    | 15%    | Wall clock time                         |
  | State preservation  | 15%    | Context retained after rotate (2b only) |
""")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Framework Benchmark Suite')
    parser.add_argument('--overhead', action='store_true', help='Measure token overhead')
    parser.add_argument('--metrics', action='store_true', help='Analyze metrics from events.jsonl')
    parser.add_argument('--compare', action='store_true', help='Compare feature cost vs value')
    parser.add_argument('--scenarios', action='store_true', help='Print A/B test scenarios')
    parser.add_argument('--all', action='store_true', help='Run all benchmarks')
    parser.add_argument('--export', choices=['csv'], help='Export results')
    parser.add_argument('--days', type=int, default=30, help='Metrics analysis period (days)')
    args = parser.parse_args()

    if not any([args.overhead, args.metrics, args.compare, args.scenarios, args.all]):
        args.all = True

    root = find_root()
    overhead = metrics = comparison = None

    if args.overhead or args.all:
        overhead = measure_overhead(root)
        print_overhead(overhead)

    if args.metrics or args.all:
        metrics = analyze_metrics(root, args.days)
        print_metrics(metrics)

    if args.compare or args.all:
        comparison = compare_features(root)
        print_comparison(comparison)

    if args.scenarios or args.all:
        print_scenarios()

    if args.export == 'csv' and overhead and comparison:
        export_csv(overhead, metrics or {}, comparison, root)

    print("\n" + "=" * 60)
    print("Done. Run /beads-doctor to verify framework health.")
    print("=" * 60)


if __name__ == '__main__':
    main()
