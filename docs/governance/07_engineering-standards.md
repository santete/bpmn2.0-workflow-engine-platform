# 07 — Engineering Standards Baseline

> Chuẩn code & chuẩn bảo mật cho G0-8. **Không viết lại** — repo đã có bộ chuẩn kỹ thuật đầy đủ trong
> `docs/ai/*`. Tài liệu này **adopt chính thức** + tổng hợp điểm chốt + trỏ nguồn. Trạng thái: `DRAFT` chờ ARB adopt.

---

## 1. Nguồn chuẩn đã có (adopt as-is)

| Lĩnh vực | Chuẩn (nguồn) | ARB adopt |
|----------|---------------|:---------:|
| Coding convention chung | `docs/ai/CODING_RULES.md` | ☐ |
| Coding convention chi tiết (.NET ưu tiên) | `docs/ai/internal_rules/06_Coding_Convention.md` | ☐ |
| Git / branch / commit / MR | `docs/ai/GIT_CONVENTION.md` + `internal_rules/01_MR_Compliance.md` | ☐ |
| Naming service/DB/event | `docs/ai/internal_rules/02_Naming_Microservice.md` | ☐ |
| API design & naming | `docs/ai/API_RULES.md` + `internal_rules/03_API_Naming.md` | ☐ |
| API response & error | `docs/ai/internal_rules/04_API_Response_and_Error.md` | ☐ |
| API timeout / retry / cancellation | `docs/ai/internal_rules/05_API_Timeout.md` | ☐ |
| DB / migration | `docs/ai/DB_RULES.md` | ☐ |
| Security | `docs/ai/SECURITY_RULES.md` | ☐ |
| Testing | `docs/ai/TESTING_RULES.md` | ☐ |
| Pipeline làm việc AI-agent | `CLAUDE.md` (6-phase) | ☐ |
| BLOCKER tuyệt đối (compliance) | `docs/ai/internal_rules/00_INDEX.md` | ☐ |

> ARB tick từng dòng tại G0 = hành vi "adopt". Không cần chép nội dung sang đây — tránh drift 2 nguồn.

---

## 2. Điểm chốt bắt buộc (non-negotiable — trích, để nhìn nhanh)

| # | Chuẩn | Thực thi bằng |
|---|-------|---------------|
| S1 | Không hardcode secret/khóa — dùng vault | Secret scan CI (`09_devsecops`), REQ-S-007 |
| S2 | Mã hóa in-transit (TLS/mTLS) + at-rest | IaC scan, review |
| S3 | Không `as any` / `@ts-ignore` / `# type: ignore` để qua typecheck | Lint gate, `CLAUDE.md` |
| S4 | Không disable/skip test để pass | Review + CI |
| S5 | Domain không import engine SDK (PH-5 isolation) | `FIT-007` |
| S6 | Trace-id 100% qua biên service | `FIT-009`, REQ-N-009 |
| S7 | Conventional Commits + tag `[AI]` nếu AI sinh | CI lint, `GIT_CONVENTION.md` |
| S8 | Không log PAN/CVV/dữ liệu mật | Hook `post-write-check`, REQ-S-009 |
| S9 | TDD: test trước, không sửa test để pass | Review lịch sử commit |

---

## 3. Quét & cổng chất lượng (khớp `09_devsecops-and-delivery.md`)

| Loại | Công cụ (Proposed) | Cổng |
|------|--------------------|------|
| Typecheck / Lint | theo stack (chốt M2) | block merge |
| SAST | static analyzer | block merge nếu nghiêm trọng |
| SCA (dependency/CVE/license) | scanner | block merge |
| Secret scan | pre-commit + CI | block merge |
| IaC scan | policy-as-code | block merge |
| Arch fitness | ArchUnit-style | block merge (`FIT-007/009`) |
| DAST / Perf | staging | block release |

---

## 4. Quản lý phụ thuộc & license (chủ quyền số)

| Quy tắc | Trace |
|---------|-------|
| Lock version mọi dependency mới; kiểm license + kích thước + maintenance | `CLAUDE.md` Hard Stop |
| Ưu tiên OSS kiểm soát được; air-gap registry cho hệ mật | REQ-O-006, REQ-S-011 |
| Thêm dependency mới = quyết định cần xác nhận (không tự ý) | Hard Stop |

---

## 5. Điều kiện adopt (G0-8)

G0-8 đạt khi: (a) ARB tick toàn bộ §1; (b) §2 được cấu hình thành cổng CI thực tế ở M3 (không chỉ trên
giấy); (c) mọi thành viên đội xác nhận đã đọc. Chuẩn thay đổi → ADR nhẹ + ARB informed.
