# Skill: Code Review

> Condensed review checklist. Full rules: `docs/ai/CODING_RULES.md`, `SECURITY_RULES.md`, `HALLUCINATION_RULES.md`.

## 7-Point Review Checklist

1. **Spec compliance** — code does what spec/architect says? Missing feature? Extra feature?
2. **Hallucination check** — every external ref has cite source (`file:line` or `schema#key`)? Any invented API/method?
3. **Code quality** — naming consistent, error handling present, type hints, edge cases covered
4. **Security** — no hardcoded secrets, no SQL injection, input validated, auth checked
5. **No-Placeholder** — no TBD, "add later", "similar to", "will implement" in code
6. **TDD-first** — every new function/class has corresponding test? Test written before implementation?
7. **File Map boundary** — changes within declared File Map scope? No file modified outside boundary?

## Severity Levels

- **BLOCKER** — must fix before merge: hallucination, security vulnerability, spec violation
- **WARNING** — should fix: code quality, missing edge case
- **NOTE** — nice to have: naming improvement, refactoring suggestion

## Output Format

```
Status: APPROVE | REJECT
BLOCKER: <count>
WARNING: <count>

Findings:
- L<line>: <issue> → <severity> (<category>)
```
