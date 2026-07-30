# /stdin-schema — Analyze captured stdin from Claude Code runtime

Analyze `.claude/cache/stdin_capture.jsonl` to understand what data Claude Code
actually passes to statusline via stdin.

## Steps

1. Read `.claude/cache/stdin_capture.jsonl`
2. If file is empty or missing → report "No data captured yet. Run a few turns
   to collect samples, then re-run /stdin-schema."
3. Aggregate across all entries:
   - **All top-level keys** seen (with frequency count)
   - **`context_window` sub-keys** (with frequency + sample values)
   - **`context_window.current_usage` sub-keys** (with frequency + sample values + min/max)
   - **`model` sub-keys** (with frequency + sample values)
   - **Any unexpected/undocumented keys** not currently used by statusline.py
4. Compare discovered schema against what `statusline.py` currently reads:
   - `context_window.current_usage.input_tokens`
   - `context_window.current_usage.cache_read_input_tokens`
   - `context_window.current_usage.cache_creation_input_tokens`
   - `context_window.current_usage.output_tokens`
   - `context_window.used_percentage`
   - `context_window.max_tokens`
   - `model.display_name` / `model.id`
   - `cwd`
5. Output a report:

```
=== Claude Code Stdin Schema (N samples) ===

Top-level keys:
  cwd                          N/N  sample: "/home/user/project"
  model                        N/N
  context_window               N/N

context_window:
  used_percentage              N/N  range: 10–85    ← statusline reads this
  max_tokens                   N/N  sample: 200000
  current_usage                N/N

current_usage fields:
  input_tokens                 0/N  ← MISSING — statusline expects this
  cache_read_input_tokens      0/N  ← MISSING
  ...

Unmapped keys (statusline ignores these):
  context_window.foo_bar       N/N  sample: "..."

Recommendation:
  - Field X is available → statusline should use it
  - Field Y is missing → current fallback is correct
```

6. If findings suggest statusline field mapping needs fixing, list specific
   code changes needed in `statusline.py` with line numbers.
