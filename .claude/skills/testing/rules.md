# Skill: Testing

> Condensed testing rules. Full rules: `docs/ai/TESTING_RULES.md`.

## TDD-First Workflow (mandatory)
```
1. Write failing test (RED)     — define expected behavior
2. Implement minimal code       — just enough to pass
3. Verify test passes (GREEN)   — run test
4. Refactor if needed           — clean up, keep tests green
5. Commit                       — atomic: test + impl together
```

## Test Structure
- Test file mirrors source: `src/payment/stripe.py` → `tests/test_stripe.py`
- Test naming: `test_<function>_<scenario>_<expected>` (e.g., `test_process_payment_invalid_card_raises_error`)
- Arrange-Act-Assert pattern (AAA)

## What to Test
- Happy path (main flow works)
- Edge cases: null, empty, zero, max value, boundary
- Error paths: invalid input, timeout, external failure
- Security: auth required, input validation, SQL injection

## What NOT to Test
- Framework internals (trust the framework)
- Private methods directly (test through public interface)
- Trivial getters/setters

## Coverage Target
- 85% line coverage (framework target)
- 100% for critical paths (auth, payment, data mutation)
- Focus on branch coverage, not just line coverage
