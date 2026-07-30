# Project Map

> "Bản đồ" để AI agent hiểu nhanh kiến trúc project. Đọc file này TRƯỚC khi
> đoán file ở đâu. Cập nhật khi cấu trúc thay đổi đáng kể.

---

## Tech Stack

> ⚠️ TODO khi customize: điền stack thật của project

- **Language**: <vd: TypeScript 5.x / Python 3.12 / Go 1.22>
- **Framework**: <vd: Next.js 15 / FastAPI / Gin>
- **Database**: <vd: PostgreSQL 16 + Prisma / MongoDB>
- **Cache / Queue**: <vd: Redis / BullMQ>
- **Test**: <vd: Vitest / Pytest>
- **Lint / Format**: <vd: Biome / ESLint+Prettier / Ruff>
- **Package manager**: <vd: pnpm / uv / go mod>

---

## Folder Structure

```
project-root/
├── src/                  # <mô tả>
│   ├── api/              # <mô tả>
│   ├── core/             # <mô tả>
│   ├── db/               # <mô tả>
│   └── utils/            # <mô tả>
├── tests/                # <mô tả>
├── docs/                 # <mô tả>
│   └── ai/               # Rule cho AI agent (file này)
├── scripts/              # <mô tả>
└── ...
```

> ⚠️ TODO: Cập nhật cấu trúc thật khi áp dụng vào project cụ thể.

---

## Key Modules / Domains

| Module      | Path             | Responsibility                  | Owner       |
|-------------|------------------|----------------------------------|-------------|
| auth        | `src/auth/`      | Login, JWT, session             | <team>      |
| payment     | `src/payment/`   | VNPay, Momo, refund             | <team>      |
| user        | `src/user/`      | Profile, preferences            | <team>      |
| ...         | ...              | ...                              | ...         |

---

## Important Files (đọc khi onboarding)

- `README.md`              — Hướng dẫn chạy local, deploy
- `package.json` / `pyproject.toml` — Scripts có thể chạy
- `<entrypoint file>`      — Khởi đầu app (vd: `src/main.ts`)
- `<config file>`          — Config (vd: `src/config/index.ts`)
- `<env example>`          — Env vars cần thiết (vd: `.env.example`)

---

## Build / Run / Test commands

> ⚠️ TODO: Điền command thật của project

```bash
# Setup
<install-cmd>             # vd: pnpm install

# Dev
<dev-cmd>                 # vd: pnpm dev

# Test
<test-cmd>                # vd: pnpm test
<test-watch-cmd>          # vd: pnpm test:watch
<test-file-cmd>           # vd: pnpm test path/to/file.test.ts

# Lint / Format
<lint-cmd>                # vd: pnpm lint
<lint-fix-cmd>            # vd: pnpm lint:fix
<format-cmd>              # vd: pnpm format

# Typecheck
<typecheck-cmd>           # vd: pnpm typecheck

# Build
<build-cmd>               # vd: pnpm build
```

---

## Architectural Decisions (gốc của các rule)

> Ghi ngắn gọn để AI agent (và người mới) hiểu vì sao project được thiết kế
> như hiện tại. Đừng để rule trông như "luật trời".

- **Vì sao chọn X thay vì Y**: <giải thích ngắn>
- **Pattern Z được dùng vì**: <giải thích ngắn>
- **Quyết định nổi bật khác**: <link tới ADR nếu có>

---

## Environments

| Env        | Branch       | URL                  | Deploy             |
|------------|--------------|----------------------|--------------------|
| local      | any          | localhost:3000       | manual             |
| staging    | `develop`    | <url>                | auto on merge      |
| production | `main`       | <url>                | manual + approval  |

---

## What NOT to touch (without asking)

- `prisma/migrations/` — chỉ tạo migration mới, KHÔNG sửa migration cũ
- `src/legacy/`        — code cũ giữ vì BC, đang phase out
- `infra/`             — Terraform / k8s, cần senior review
- ... <bổ sung theo project>
