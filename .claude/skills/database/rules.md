# Skill: Database

> Condensed DB conventions. Full rules: `docs/ai/DB_RULES.md`, `internal_rules/02_Naming_Microservice.md`.

## Table & Column Naming
- Tables: `snake_case`, plural (`users`, `order_items`)
- Columns: `snake_case`, no table prefix (`name` not `user_name`)
- Primary key: `id` (auto-generated)
- Foreign key: `<referenced_table_singular>_id` (e.g., `user_id`)
- Timestamps: `created_at`, `updated_at` (mandatory on all tables)

## Migration Rules
- One migration per schema change (atomic)
- Migration name: `<timestamp>_<verb>_<description>` (e.g., `20260611_add_phone_verified_to_users`)
- Always reversible: include `up()` and `down()`
- No data manipulation in schema migration (separate data migration)

## Nullable Handling (mandatory)
- Fields marked `nullable` in schema_snapshot → MUST handle in code:
  - Python: `.get("field")` or `Optional[T]` + None check
  - TypeScript: `?.` or `| undefined`
- NEVER access nullable field as non-null

## Query Patterns
- Use parameterized queries / ORM — NEVER string interpolation
- Index on foreign keys and frequently queried columns
- Paginate all list endpoints (default: 20 items)
- Use `SELECT <columns>` not `SELECT *`

## Engine Decision
- SQL (default) for structured data with relationships
- NoSQL only when: schema-less data, extreme write throughput, document-oriented
- Decision must be documented in `decisions[]` of project_state.yaml
