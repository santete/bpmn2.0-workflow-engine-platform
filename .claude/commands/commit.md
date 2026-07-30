---
description: Tạo commit theo Git Convention của project
---

Bạn đang đóng vai git committer cho project này. Quy trình:

## Bước 1: Inspect
- Chạy `git status` để xem trạng thái
- Chạy `git diff --staged` để xem changes đã staged
- Nếu CHƯA có file nào staged: chạy `git diff` để xem tất cả thay đổi, rồi HỎI user có muốn `git add -A` không

## Bước 2: Analyze
Phân tích diff để xác định:
- **Type** phù hợp (feat / fix / docs / refactor / ...) — xem `@docs/ai/GIT_CONVENTION.md`
- **Scope** chính xác theo module bị ảnh hưởng
- **Subject** ngắn gọn ≤ 72 ký tự, viết thường, imperative mood, KHÔNG dấu chấm cuối

## Bước 3: Check atomicity
Nếu diff gồm **nhiều logical changes khác nhau** (vd: vừa fix bug auth vừa thêm feature payment):
- Đề xuất tách thành nhiều commit riêng
- HỎI user có muốn tách không trước khi proceed

## Bước 4: Verify locally (nếu chưa chạy)
Đề xuất chạy:
- `<lint-cmd>`
- `<typecheck-cmd>`
- Test liên quan đến file đã đổi

(Lấy command thật từ `@docs/ai/PROJECT_MAP.md`)

## Bước 5: Propose & Wait
Đề xuất commit message hoàn chỉnh theo format:
```
<type>(<scope>): <subject>

<body nếu cần giải thích vì sao>

<footer: Refs/Closes #ticket nếu có>
```

**CHỜ user xác nhận** trước khi chạy `git commit`. KHÔNG tự commit.

## Bước 6: Execute
Sau khi user OK:
- Chạy `git commit -m "..."` (hoặc dùng heredoc cho message nhiều dòng)
- Verify bằng `git log -1 --stat`
- Báo lại kết quả theo format Phase 5 trong `@CLAUDE.md`

## Tham khảo
- Convention: `@docs/ai/GIT_CONVENTION.md`
- Pipeline tổng: `@CLAUDE.md`
