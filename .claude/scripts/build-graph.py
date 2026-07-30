#!/usr/bin/env python3
"""
Code Knowledge Graph Builder — POC
Parse source files → extract symbols + relationships → JSON graph.

Usage:
    python .claude/scripts/build-graph.py [--root <path>] [--lang <py|js|ts|all>] [--output <path>]

Strategy:
    - Python: uses `ast` module (accurate, no external deps)
    - JS/TS: regex-based extraction (lightweight, good enough for POC)
    - Output: .claude/memory/code_graph.json

The graph is designed for agent queries like:
    "What does function X call?"
    "What imports module Y?"
    "What classes extend Z?"
"""
import ast
import io
import json
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Windows fix: force utf-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Configuration ────────────────────────────────────────────────────────────

SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'vendor', '__pycache__',
    '.venv', 'venv', '.claude', 'docs', '.next', 'coverage',
}

LANG_EXTENSIONS = {
    'py': ['.py'],
    'js': ['.js', '.jsx', '.mjs'],
    'ts': ['.ts', '.tsx'],
}

# ── Python AST Parser ────────────────────────────────────────────────────────

def parse_python(filepath: Path) -> dict:
    """Parse Python file using ast module. Returns symbols + edges."""
    try:
        source = filepath.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, ValueError):
        return {'symbols': [], 'edges': []}

    symbols = []
    edges = []
    module_name = filepath.stem

    for node in ast.walk(tree):
        # Functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                'name': node.name,
                'type': 'function',
                'line': node.lineno,
                'file': str(filepath),
            })
            # Extract calls inside this function
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    callee = _get_call_name(child)
                    if callee:
                        edges.append({
                            'from': f"{module_name}.{node.name}",
                            'to': callee,
                            'type': 'calls',
                        })

        # Classes
        elif isinstance(node, ast.ClassDef):
            symbols.append({
                'name': node.name,
                'type': 'class',
                'line': node.lineno,
                'file': str(filepath),
            })
            # Extract base classes
            for base in node.bases:
                base_name = _get_name(base)
                if base_name:
                    edges.append({
                        'from': f"{module_name}.{node.name}",
                        'to': base_name,
                        'type': 'extends',
                    })

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                edges.append({
                    'from': module_name,
                    'to': alias.name,
                    'type': 'imports',
                })

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    edges.append({
                        'from': module_name,
                        'to': f"{node.module}.{alias.name}",
                        'type': 'imports',
                    })

    return {'symbols': symbols, 'edges': edges}


def _get_call_name(node: ast.Call) -> str:
    """Extract function name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    elif isinstance(node.func, ast.Attribute):
        value = _get_name(node.func.value)
        if value:
            return f"{value}.{node.func.attr}"
        return node.func.attr
    return ''


def _get_name(node) -> str:
    """Extract name from AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        value = _get_name(node.value)
        if value:
            return f"{value}.{node.attr}"
        return node.attr
    return ''


# ── JS/TS Regex Parser ──────────────────────────────────────────────────────

# Patterns for JS/TS extraction (good enough for POC)
JS_FUNCTION_RE = re.compile(
    r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', re.MULTILINE)
JS_CLASS_RE = re.compile(
    r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', re.MULTILINE)
JS_IMPORT_RE = re.compile(
    r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
JS_ARROW_RE = re.compile(
    r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', re.MULTILINE)


def parse_js_ts(filepath: Path) -> dict:
    """Parse JS/TS file using regex. Returns symbols + edges."""
    try:
        source = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return {'symbols': [], 'edges': []}

    symbols = []
    edges = []
    module_name = filepath.stem

    # Functions
    for m in JS_FUNCTION_RE.finditer(source):
        symbols.append({
            'name': m.group(1),
            'type': 'function',
            'line': source[:m.start()].count('\n') + 1,
            'file': str(filepath),
        })

    # Arrow functions (const foo = () => ...)
    for m in JS_ARROW_RE.finditer(source):
        symbols.append({
            'name': m.group(1),
            'type': 'function',
            'line': source[:m.start()].count('\n') + 1,
            'file': str(filepath),
        })

    # Classes
    for m in JS_CLASS_RE.finditer(source):
        symbols.append({
            'name': m.group(1),
            'type': 'class',
            'line': source[:m.start()].count('\n') + 1,
            'file': str(filepath),
        })
        if m.group(2):  # extends
            edges.append({
                'from': f"{module_name}.{m.group(1)}",
                'to': m.group(2),
                'type': 'extends',
            })

    # Imports
    for m in JS_IMPORT_RE.finditer(source):
        edges.append({
            'from': module_name,
            'to': m.group(1),
            'type': 'imports',
        })

    return {'symbols': symbols, 'edges': edges}


# ── Graph Builder ────────────────────────────────────────────────────────────

def build_graph(root: Path, languages: list[str]) -> dict:
    """Scan source files and build the knowledge graph."""
    extensions = set()
    for lang in languages:
        extensions.update(LANG_EXTENSIONS.get(lang, []))

    if not extensions:
        # 'all' — use all known extensions
        for exts in LANG_EXTENSIONS.values():
            extensions.update(exts)

    all_symbols = []
    all_edges = []
    files_scanned = 0

    for filepath in root.rglob('*'):
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue
        if filepath.suffix not in extensions:
            continue
        if not filepath.is_file():
            continue

        files_scanned += 1

        if filepath.suffix == '.py':
            result = parse_python(filepath)
        elif filepath.suffix in ('.js', '.jsx', '.mjs', '.ts', '.tsx'):
            result = parse_js_ts(filepath)
        else:
            continue

        all_symbols.extend(result['symbols'])
        all_edges.extend(result['edges'])

    # Compute content hash for incremental update detection
    content = json.dumps({'symbols': all_symbols, 'edges': all_edges}, sort_keys=True)
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]

    return {
        'meta': {
            'built_at': datetime.now(timezone.utc).isoformat(),
            'root': str(root),
            'files_scanned': files_scanned,
            'symbols_count': len(all_symbols),
            'edges_count': len(all_edges),
            'content_hash': content_hash,
            'languages': languages,
        },
        'symbols': all_symbols,
        'edges': all_edges,
    }


# ── Query Helpers (used by /code-graph) ──────────────────────────────────────

def query_symbol(graph: dict, name: str) -> dict:
    """Query graph for a symbol and its relationships."""
    # Find matching symbols
    matches = [s for s in graph['symbols']
               if name.lower() in s['name'].lower()]

    # Find edges involving this symbol
    outgoing = [e for e in graph['edges']
                if name.lower() in e['from'].lower()]
    incoming = [e for e in graph['edges']
                if name.lower() in e['to'].lower()]

    return {
        'query': name,
        'symbols': matches[:20],  # limit for token efficiency
        'calls': [e for e in outgoing if e['type'] == 'calls'][:20],
        'called_by': [e for e in incoming if e['type'] == 'calls'][:20],
        'imports': [e for e in outgoing if e['type'] == 'imports'][:10],
        'imported_by': [e for e in incoming if e['type'] == 'imports'][:10],
        'extends': [e for e in outgoing if e['type'] == 'extends'][:10],
        'extended_by': [e for e in incoming if e['type'] == 'extends'][:10],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build code knowledge graph')
    parser.add_argument('--root', default='.', help='Project root directory')
    parser.add_argument('--lang', default='all', help='Languages: py, js, ts, all')
    parser.add_argument('--output', default='.claude/memory/code_graph.json',
                        help='Output path')
    parser.add_argument('--query', help='Query a symbol (skip build)')
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.query:
        # Query mode
        if not output_path.exists():
            print(f"Graph not found at {output_path}. Run without --query first.", file=sys.stderr)
            sys.exit(1)
        graph = json.loads(output_path.read_text(encoding='utf-8'))
        result = query_symbol(graph, args.query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Build mode
    root = Path(args.root).resolve()
    languages = [args.lang] if args.lang != 'all' else list(LANG_EXTENSIONS.keys())

    print(f"Scanning {root} for {', '.join(languages)}...")
    graph = build_graph(root, languages)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    meta = graph['meta']
    print(f"Done: {meta['files_scanned']} files, "
          f"{meta['symbols_count']} symbols, "
          f"{meta['edges_count']} edges → {output_path}")


if __name__ == '__main__':
    main()
