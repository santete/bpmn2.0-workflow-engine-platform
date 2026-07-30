# 06 — Stakeholder Register & Change Management Plan

> Dự án chính phủ lớn **thất bại vì lý do phi kỹ thuật** nhiều hơn kỹ thuật. Bắt đầu quản lý thay đổi &
> truyền thông **từ M0** ("truyền thông quá mức"). Trạng thái: `DRAFT` — điền tên/đơn vị tại G0.
> Chủ: Change Manager + Executive Sponsor. Trace: REQ-O-007, Master Plan §8.

---

## 1. Executive Sponsor (G0-6 — điều kiện chặn)

| Hạng mục | Nội dung |
|----------|----------|
| Vai trò | Người bảo trợ cấp cao, gỡ vướng chính trị/ngân sách, chủ trì phê duyệt gate lớn |
| Cam kết cần có | Tham gia định kỳ (không chỉ ký tên); "truyền thông quá mức" xuống tổ chức |
| Người | **Trần Quốc Bảo** *(minh họa — chốt tại G0 2026-07-10; thay khi triển khai thật)* |
| Cam kết đã ghi nhận | Tham gia phê duyệt gate + truyền thông xuống tổ chức (I-01 đóng) |
| Rủi ro nếu thiếu | I-01 (RAID) — hệ thống xây xong không ai dùng / mất hậu thuẫn |

---

## 2. Stakeholder Register

Phân loại theo **quyền lực × mức quan tâm** (power/interest) → quyết định chiến lược tương tác.

| Nhóm stakeholder | Quan tâm chính | Power | Interest | Chiến lược | Kênh/nhịp |
|------------------|----------------|:-----:|:--------:|-----------|-----------|
| Lãnh đạo cấp cao / Sponsor | Thành công tổng thể, tuân thủ, chính trị | C | C | **Quản lý sát** | Báo cáo mỗi gate |
| Cơ quan quản lý an ninh (NĐ 85) | Tuân thủ cấp độ, dữ liệu trong biên giới | C | TB | **Làm hài lòng** | Hồ sơ tuân thủ M1/M6 |
| Người dùng nghiệp vụ (cán bộ) | Dễ dùng, không gián đoạn công việc | TB | C | **Giữ thông tin + đào tạo** | Demo tăng dần, đào tạo M7 |
| Lãnh đạo đơn vị chủ quản dữ liệu | Chủ quyền dữ liệu, không mất kiểm soát | TB | C | Giữ thông tin | Interop workshop M2/M4 |
| Đội vận hành / SOC | Vận hành được, observability | TB | C | Tham gia thiết kế | ARB (OPS/SEC) |
| Đội phát triển | Ranh giới rõ, chuẩn ổn định | T | C | Giữ thông tin | Ways of Working |
| Đơn vị liên thông (NDXP) | Hợp đồng dịch vụ, bảo mật | TB | TB | Giám sát | Federation M4+ |
| Kiểm toán / thanh tra | Audit trail, bằng chứng | TB | TB | Làm hài lòng | Audit bất biến, M6 |

---

## 3. Change Management Plan (kế hoạch quản lý thay đổi)

Theo mô hình nhận thức → mong muốn → năng lực → củng cố:

| Giai đoạn | Mục tiêu | Hoạt động | Khi nào |
|-----------|----------|-----------|---------|
| **Nhận thức** | Mọi người biết vì sao đổi | Truyền thông tầm nhìn từ Sponsor; kick-off | M0 |
| **Mong muốn** | Muốn tham gia, giảm kháng cự | Lắng nghe cán bộ nghiệp vụ; nêu lợi ích cụ thể | M0–M1 |
| **Kiến thức** | Biết cách dùng | Đào tạo theo vai; tài liệu; demo tăng dần | M4, M7 |
| **Năng lực** | Dùng được thực tế | Hypercare, hỗ trợ tại chỗ, runbook | M7 |
| **Củng cố** | Duy trì thói quen mới | Phản hồi, cải tiến, ghi nhận | M7–M8 |

---

## 4. Kế hoạch truyền thông (Communication Plan)

| Đối tượng | Thông điệp | Kênh | Tần suất | Chủ |
|-----------|-----------|------|----------|-----|
| Sponsor / lãnh đạo | Tiến độ gate, rủi ro, quyết định cần | Báo cáo gate + dashboard | Mỗi gate | Lead SA |
| Người dùng nghiệp vụ | Cái gì sắp đổi, lợi ích, đào tạo | Họp đơn vị, demo, email | Mỗi increment | CM |
| Đội phát triển/vận hành | Chuẩn, quyết định kiến trúc, ADR | ARB, repo docs | 2 tuần | Lead SA |
| Đơn vị chủ quản dữ liệu | Chủ quyền, cách liên thông | Workshop | Theo mốc interop | DA |
| Cơ quan tuân thủ | Trạng thái hồ sơ cấp độ | Hồ sơ chính thức | M1, M6 | SEC |

> **Nguyên tắc "over-communicate":** thà lặp lại thừa còn hơn để khoảng trống thông tin sinh tin đồn/kháng cự.

---

## 5. Đo lường hiệu quả change management

| Chỉ số | Cách đo | Ngưỡng mong muốn |
|--------|---------|------------------|
| Mức độ chấp nhận người dùng | Khảo sát + tỷ lệ sử dụng thực | tăng dần qua các increment |
| Kháng cự / phản hồi tiêu cực | Kênh phản hồi + hỗ trợ | giảm dần sau đào tạo |
| Sẵn sàng go-live | Checklist đào tạo + hypercare | 100% vai trò cốt lõi trước M7 |
