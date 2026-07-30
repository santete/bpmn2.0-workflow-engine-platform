# Skill: API Design

> Condensed API conventions. Full rules: `docs/ai/API_RULES.md`, `internal_rules/03-05`.

## Endpoint Naming
- RESTful: `/<resource>` (plural noun), no verbs in path
- HTTP method carries the action: GET (read), POST (create), PUT (update), DELETE (remove)
- Nested resources: `/<parent>/<id>/<child>` (max 2 levels)

## Response Format (4-field wrapper)
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "page": 1, "total": 100 }
}
```

## Error Handling
- Error response MUST include: `code` (machine-readable), `message` (human-readable), `details` (optional)
- HTTP status codes: 400 (bad input), 401 (auth), 403 (forbidden), 404 (not found), 422 (validation), 500 (server)
- Internal error codes: `<MODULE>-<NUMBER>` format (e.g., `AUTH-001`)

## Timeout & Retry
- All HTTP clients MUST have explicit timeout (default: 30s)
- Retry budget: max 3 retries with exponential backoff
- Cancellation: propagate cancellation tokens through call chain
- Log: request_id, duration, status for every external call
