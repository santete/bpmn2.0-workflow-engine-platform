# 04 — Definition of Ready (DoR) & Definition of Done (DoD)

> Hai hợp đồng chất lượng: **DoR** = khi nào một hạng mục *đủ điều kiện để bắt đầu*; **DoD** = khi nào
> *được coi là xong*. Gắn thẳng vào Fitness Functions và RTM đã có, không phát minh tiêu chí mới.
> Trạng thái: `DRAFT` chờ adopt tại G0. Nguồn: Master Plan §6 (DoD 6 điểm) + `docs/architecture/02_nfr-quantified.md`.

---

## 1. Definition of Ready (đủ điều kiện đưa vào sprint)

Một user story / task **chưa Ready** nếu thiếu bất kỳ mục nào:

| # | Tiêu chí Ready | Vì sao |
|---|----------------|--------|
| R1 | Trace về ≥1 **REQ-ID** (`docs/architecture/01_requirements-catalog.md`) | Không làm việc mồ côi |
| R2 | Tiêu chí chấp nhận (AC) rõ ràng, kiểm chứng được | Tránh mơ hồ (D5=vague → STOP) |
| R3 | NFR liên quan được nêu (nếu có) + ngưỡng | Không "quên" phi chức năng |
| R4 | Phụ thuộc đã xác định (RAID / task-dep) | Không bị chặn giữa chừng |
| R5 | Tác động an ninh/độ mật đã sơ bộ đánh giá | Security-by-design |
| R6 | Nằm trong 1 bounded context rõ (hoặc ADR nếu liên context) | Giữ ranh giới |
| R7 | Đủ nhỏ để hoàn thành trong 1 sprint | Chia nhỏ atomic |

> Story chạm PH-5 / an ninh / NFR / breaking API → cần **ADR liên quan ở trạng thái ≥ Proposed** mới Ready.

---

## 2. Definition of Done (được coi là xong)

Kế thừa **6 điểm DoD** của Master Plan §6, cụ thể hóa bằng cơ chế kiểm chứng đã có:

| # | Tiêu chí Done | Kiểm bằng | Trace |
|---|---------------|-----------|-------|
| D1 | Đạt yêu cầu chức năng (AC pass) | Test chức năng xanh | REQ-F |
| D2 | Đạt NFR liên quan (tải, độ trễ, availability) | Fitness `FIT-003/004`… | REQ-N, `02_nfr` |
| D3 | Qua kiểm thử bảo mật, không lỗi nghiêm trọng | SAST/DAST (`09_devsecops`) | REQ-S, TM-### |
| D4 | Đã gắn observability (metrics/logs/traces) | `FIT-009` trace 100% | REQ-N-009 |
| D5 | Tài liệu + ADR + **RTM đã cập nhật** | Review + RTM diff | RTM |
| D6 | Fitness functions liên quan vẫn xanh | CI gate | `FIT-001…010` |

### 2.1 DoD bổ sung bắt buộc (từ pipeline `CLAUDE.md` + chuẩn nghề)
| # | Tiêu chí | Kiểm |
|---|---------|------|
| D7 | **TDD**: test viết trước, không sửa test để pass | Review lịch sử commit |
| D8 | **No-placeholder**: không TBD/TODO không ref, không debug code sót | Hook `post-write-check` |
| D9 | **Ranh giới File Map**: chỉ sửa file trong scope đã định | Review MR |
| D10 | Không import engine SDK trong domain (PH-5 isolation) | `FIT-007` |
| D11 | Commit/MR đúng convention (`docs/ai/GIT_CONVENTION.md`, tag `[AI]` nếu AI sinh) | CI lint |

---

## 3. DoD theo cấp (level-specific)

| Cấp hạng mục | DoD áp dụng |
|--------------|-------------|
| **Task / story** | D1–D11 |
| **Domain increment** (M4) | D1–D11 + interop test + threat model cập nhật + C4 L3 container |
| **Milestone gate** | Toàn bộ checklist gate tương ứng (G0…G8) + fitness suite xanh |
| **Release** | DoD domain + `FIT-003/004/010` (perf + engine-swap) + pentest (từ M6) |

---

## 4. Nguyên tắc thực thi

- DoD là **cổng cơ học** (fitness/hook chặn merge), không phải checklist thủ công dựa vào trí nhớ.
- "Xong" báo cáo phải **trung thực**: test fail → nói rõ; bước skip → ghi rõ (khớp Phase 5 report `CLAUDE.md`).
- DoR/DoD rà soát lại mỗi gate; thay đổi cần ADR nhẹ + ARB informed.
