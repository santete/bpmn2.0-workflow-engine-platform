# /check-drift — manual drift inspection

Detects whether the codebase has diverged from the memory baseline recorded
in `.claude/memory/_sync_state.yaml`.

When you run `/check-drift`, Claude:

1. Reads `.claude/memory/_sync_state.yaml` to get `synced_at_commit` and the
   `watched_paths` / `ignored_paths` globs.
2. Runs `python .claude/hooks/python/drift_check.py --verbose` from project root.
3. Renders the grouped report (source / schema / manifest / other) to the user.

## When to use

- After pulling new commits — quickly see if memory files are stale.
- Before starting a non-trivial task — confirm Phase 0 grounding still matches reality.
- When SessionStart's 1-line drift warning shows up and you want detail.
- After a long session — confirm `/done` actually re-stamped the baseline.

## Modes

Plain `/check-drift`
- Verbose grouped report. This is the default user-facing mode.

`/check-drift --baseline`
- **Mutating**. Stamps current HEAD as the new sync point. Use when:
  - You've manually reconciled memory files with the codebase and want to clear drift.
  - The baseline commit is missing (rebase/squash erased it) and you need to re-anchor.
  - Memory files have been hand-edited and you want to declare them in-sync as-of-now.
- *Do not* run `--baseline` to silence drift you haven't actually addressed. The
  point is consistency — re-stamping without reconciliation just moves the
  goalposts and Dev B will inherit a baseline that doesn't match reality.

`/check-drift --json`
- JSON output for tooling. Same shape as `drift_check.py --json`.

## Output statuses

| Status             | Meaning                                                       |
|--------------------|---------------------------------------------------------------|
| `clean`            | No watched files changed since baseline. Memory is in sync.   |
| `drift`            | One or more watched files changed. Report lists them grouped. |
| `baseline_missing` | `synced_at_commit` is empty or refers to a commit not in repo (rebased / squashed). Re-baseline with `/check-drift --baseline`. |
| `no_sync_state`    | `_sync_state.yaml` doesn't exist — project hasn't been classified yet. Run `/classify` first. |

## Fail-open invariant

`drift_check.py` always exits 0 — even on internal errors. Drift detection is
informational, never a blocker. If the script crashes, your workflow continues
as if nothing happened. Crashes show up in metrics (`drift_nudge` events with
empty payload), not in your face.

## Related

- `/classify` — stamps the initial baseline at Bước 5 step 6.
- `/done` — re-stamps the baseline after a successful task.
- `_sync_state.yaml` — the file this command reads/writes.
- `core/EVOLUTION.md#m6--context-consistency` — why this exists.
