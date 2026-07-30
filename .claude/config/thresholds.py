#!/usr/bin/env python3
"""Load framework runtime thresholds with fallback to defaults.

Used by statusline + Python hooks. If `.claude/config/thresholds.json` is
missing or malformed, hardcoded DEFAULTS apply — framework keeps working.

Override only the keys you need; unspecified keys retain default values.
"""
import json
from pathlib import Path

DEFAULTS = {
    "rotate_threshold": 120_000,
    "recent_drop_reset": 10_000,
    "metrics_tok_warn": 90_000,
    "pattern_budgets": {
        "A": {"working": 100_000, "total": 120_000},
        "B": {"working": 120_000, "total": 140_000},
        "C": {"working": 120_000, "total": 190_000},
    },
    "hrs_weights": {
        "cite_coverage": 0.25,
        "schema_match": 0.25,
        "confidence_density": 0.10,
        "static_errors": 0.20,
        "context_drift": 0.10,
        "failures": 0.05,
        "schema_staleness": 0.05,
    },
    "loop_budgets": {
        "typecheck": 3,
        "lint_auto": 1,
        "lint_manual": 2,
        "test": 2,
    },
    "metrics_retention_days": 90,
    "metrics_max_size_mb": 100,
}


def _find_root() -> Path:
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / ".claude").is_dir() or (p / ".git").is_dir():
            return p
    return cwd


def load(root: Path | None = None) -> dict:
    root = root or _find_root()
    cfg_path = root / ".claude" / "config" / "thresholds.json"
    cfg = {**DEFAULTS, "pattern_budgets": {**DEFAULTS["pattern_budgets"]}}
    if not cfg_path.exists():
        return cfg
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return cfg
        for k, v in data.items():
            if k.startswith("_"):
                continue
            cfg[k] = v
        if isinstance(data.get("pattern_budgets"), dict):
            cfg["pattern_budgets"] = {
                **DEFAULTS["pattern_budgets"],
                **data["pattern_budgets"],
            }
    except Exception:
        pass
    return cfg
