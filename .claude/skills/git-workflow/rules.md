# Skill: Git Workflow

> Condensed git conventions. Full rules: `docs/ai/GIT_CONVENTION.md`, `internal_rules/01_MR_Compliance.md`.

## Branch Naming
- Format: `<type>/<ticket>-<short-description>`
- Types: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`, `test/`
- Example: `feat/SP-123-add-search-api`

## Commit Format (Conventional Commits)
```
<type>(<scope>): <description> [AI]

<body — optional>
```
- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `ci`
- `[AI]` tag mandatory khi code do AI sinh
- Description: imperative mood, lowercase, no period

## MR Checklist (6 items)
1. Branch naming follows convention
2. Commit messages follow Conventional Commits
3. AI disclosure tag present (if AI-generated)
4. Tests pass (CI green)
5. No debug code / hardcoded secrets
6. Self-review completed (Phase 4)

## AI Disclosure
- `[AI]` in commit subject = code generated/modified by AI
- MR description: mutually exclusive — either "AI-assisted" or "Human-written"
- Nếu cả hai: ghi "AI-assisted, human-reviewed"
