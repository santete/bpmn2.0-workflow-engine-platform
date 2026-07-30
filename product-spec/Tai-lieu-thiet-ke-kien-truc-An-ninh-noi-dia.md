# TÀI LIỆU THIẾT KẾ KIẾN TRÚC TỔNG THỂ
## Hệ thống Số hóa Toàn trình — An ninh Nội địa Quốc gia

> **Tài liệu thiết kế chuẩn (Reference Architecture)** — phiên bản tổng hợp cấp cao (high-level).
> Mục tiêu: gom cụm toàn bộ yêu cầu và đặc tính kỹ thuật thành một hệ thống nhất quán, không xung đột tính năng, phân rã rõ ràng theo phân hệ, kèm ma trận truy vết yêu cầu và cơ chế giải quyết xung đột.

---

## 0. Phạm vi & cách đọc tài liệu

Tài liệu chia làm 8 phần theo logic từ trên xuống:

| Phần | Nội dung | Trả lời câu hỏi |
|------|----------|-----------------|
| 1 | Tổng hợp & gom cụm yêu cầu | *Hệ thống phải làm được gì?* |
| 2 | Nguyên tắc kiến trúc nền tảng | *Toàn hệ thống tuân theo triết lý nào?* |
| 3 | Bản đồ phân hệ | *Hệ thống gồm những khối nào?* |
| 4 | Chi tiết phân hệ chức năng | *Mỗi khối làm gì, bằng công nghệ gì?* |
| 5 | Nền tảng & thuộc tính xuyên suốt | *Chất lượng hệ thống được đảm bảo thế nào?* |
| 6 | Ma trận truy vết yêu cầu | *Mỗi yêu cầu được phân hệ nào đáp ứng?* |
| 7 | Giải quyết xung đột tính năng | *Các yêu cầu mâu thuẫn được hóa giải ra sao?* |
| 8 | Quản trị, con người & lộ trình | *Làm sao triển khai không thất bại?* |
| Phụ lục A | Bảng thuật ngữ (Glossary) | *Các keyword & viết tắt nghĩa là gì?* |

---

## 1. Tổng hợp & gom cụm yêu cầu

Toàn bộ keyword/đặc tính được gom về **6 nhóm mục tiêu**. Việc gom cụm này là bước đầu tiên để đảm bảo không có yêu cầu nào bị bỏ sót và không có hai yêu cầu nào xung đột ngầm.

| Nhóm mục tiêu | Keyword / đặc tính đã tổng hợp | Nguồn |
|---|---|---|
| **G1. Điều phối quy trình** | BPMN workflow engine; tầng workflow biệt lập; tháo lắp được (open source / enterprise / tự xây); ports & adapters; anti-corruption layer; tách trạng thái tiến trình khỏi dữ liệu nghiệp vụ; BPMN 2.0 chuẩn hóa | Yêu cầu + Phân tích |
| **G2. An toàn thông tin** | Security đặt hàng đầu; Zero Trust; Defense in Depth; IAM (RBAC/ABAC); MFA; phân quyền mức bản ghi/trường; mã hóa at-rest & in-transit; quản lý secret/khóa; phân loại độ mật; audit log bất biến; break-glass; insider threat; separation of duties; nguyên tắc bốn mắt; tuân thủ Luật ATTT mạng & NĐ 85/2016 (cấp độ 4/5) | Yêu cầu + Phân tích + Research |
| **G3. Chịu tải & thời gian thực** | Chịu tải cao; nhiều user cập nhật đồng thời; hiển thị tức thời; CQRS; WebSocket/SSE push; optimistic concurrency; stateless; load balancing; autoscaling; message broker (bể giảm chấn); multi-level cache; read replica; sharding | Yêu cầu + Phân tích |
| **G4. Sẵn sàng & tin cậy** | Availability; Reliability; no single point of failure; redundancy; clustering; multi-AZ/DC; active-active/passive; circuit breaker; bulkhead; graceful degradation; DR (RPO/RTO); backup; chaos engineering; diễn tập phục hồi | Yêu cầu + Phân tích + Research |
| **G5. Dữ liệu & tích hợp** | Dữ liệu phân tán (không kho trung tâm — mô hình X-Road); interoperability layer; once-only principle; federation; Data Mesh; data classification; retention policy; Event Sourcing; polyglot persistence | Phân tích + Research |
| **G6. Big System & vận hành** | Scalability; Capability (khả năng mở rộng chức năng); DDD + bounded context; microservices; event-driven; modular monolith khởi đầu; CI/CD; DevSecOps; blue-green/canary (không gián đoạn); API versioning; digital sovereignty; chống nợ kỹ thuật; hiện đại hóa tăng dần (no rip-and-replace); quản lý thay đổi tổ chức; dashboard giám sát realtime; observability (metrics/logs/traces) | Yêu cầu + Phân tích + Research |

---

## 2. Nguyên tắc kiến trúc nền tảng

7 nguyên tắc bất biến. Mọi phân hệ và quyết định thiết kế đều phải nhất quán với các nguyên tắc này.

| # | Nguyên tắc | Nội dung cốt lõi | Phục vụ nhóm |
|---|-----------|------------------|--------------|
| **P1** | **Phân tầng + hướng sự kiện** | Giao tiếp ưu tiên bất đồng bộ qua event bus thay vì gọi trực tiếp; tách rời (decoupling) để chịu tải và chống lỗi dây chuyền | G3, G4, G6 |
| **P2** | **Domain-Driven Design** | Mỗi nghiệp vụ là một bounded context độc lập; khởi đầu bằng modular monolith, tách microservice theo điểm nghẽn thực tế | G6 |
| **P3** | **Dữ liệu phân tán, không kho chung** | Dữ liệu do đơn vị chủ quản nắm giữ; trao đổi qua tầng interoperability chuẩn hóa; tránh single point of failure ở tầng dữ liệu | G5, G4 |
| **P4** | **Tháo lắp được (pluggable)** | Thành phần chiến lược (đặc biệt workflow engine) nằm sau tầng trừu tượng + adapter; chuẩn mở đảm bảo khả chuyển | G1, G6 |
| **P5** | **Security-by-design / Zero Trust** | Không tin tưởng mặc định bất kỳ request nào; xác thực & phân quyền lại ở mọi tầng; nhiều lớp phòng thủ | G2 |
| **P6** | **Chủ quyền số (digital sovereignty)** | Ưu tiên chuẩn mở & mã nguồn mở kiểm soát được; tránh khóa cứng nhà cung cấp; dữ liệu không ra khỏi biên giới | G2, G5, G6 |
| **P7** | **Hiện đại hóa tăng dần** | Không "đập đi xây lại"; xây từng phần, rút kinh nghiệm, mở rộng; cải tiến liên tục không gián đoạn dịch vụ | G4, G6 |

---

## 3. Bản đồ phân hệ (tổng quan)

Hệ thống gồm **8 phân hệ chức năng** (functional subsystems — lát cắt dọc) và **5 nền tảng xuyên suốt** (cross-cutting platforms — lát cắt ngang bao trùm mọi phân hệ).

```
                    NGƯỜI DÙNG NGHIỆP VỤ / HIỆN TRƯỜNG
                                  │
  ┌───────────────────────────────────────────────────────────────┐
  │  PH-1  Truy cập & Trải nghiệm (Web / Mobile / Dashboard)       │
  ├───────────────────────────────────────────────────────────────┤
  │  PH-2  Cổng bảo mật biên (API Gateway + WAF)                   │
  │  PH-3  Định danh & Kiểm soát truy cập (IAM)                    │
  ├───────────────────────────────────────────────────────────────┤
  │  PH-4  Dịch vụ nghiệp vụ (Domain Microservices)               │
  ├───────────────────────────────────────────────────────────────┤
  │  PH-5  Điều phối quy trình — BIỆT LẬP (Workflow Abstraction)  │ ★
  ├───────────────────────────────────────────────────────────────┤
  │  PH-6  Hạ tầng sự kiện & Tích hợp (Event Bus + Interop)       │
  ├───────────────────────────────────────────────────────────────┤
  │  PH-7  Quản trị dữ liệu (Polyglot + CQRS + Audit)            │
  │  PH-8  Giám sát & Quan sát (Business + Technical + SOC)       │
  └───────────────────────────────────────────────────────────────┘

  XUYÊN SUỐT: NT-1 An toàn thông tin · NT-2 Sẵn sàng & Chống chịu
              NT-3 Mở rộng & Hiệu năng · NT-4 DevSecOps
              NT-5 Quan sát kỹ thuật
```

---

## 4. Chi tiết các phân hệ chức năng

Mỗi phân hệ nêu **Tính năng chính** (in đậm — điểm nhấn), đặc tính kỹ thuật, và ranh giới trách nhiệm.

### PH-1 — Phân hệ Truy cập & Trải nghiệm

**★ Tính năng chính: là điểm tương tác duy nhất của người dùng và là nơi nhận dữ liệu realtime được đẩy xuống (không hỏi vòng — no polling).**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | Cổng nghiệp vụ (web portal), ứng dụng hiện trường (mobile), dashboard giám sát realtime |
| Đặc tính kỹ thuật | Kênh đẩy dữ liệu WebSocket/SSE; giao diện tách biệt theo vai trò; không giữ logic nghiệp vụ (chỉ trình bày) |
| Ranh giới | Chỉ nói chuyện với PH-2; không truy cập trực tiếp dữ liệu hay service |

### PH-2 — Phân hệ Cổng bảo mật biên

**★ Tính năng chính: điểm chặn bảo mật duy nhất — thực thi Zero Trust tại biên, xác thực token một lần và chống quá tải trước khi request chạm vào hệ thống.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | API Gateway, WAF, rate limiter, TLS termination |
| Đặc tính kỹ thuật | Kiểm tra & xác thực token tập trung; giới hạn tần suất; chặn tấn công tầng ứng dụng; định tuyến tới domain service |
| Ranh giới | Không chứa logic nghiệp vụ; ủy quyền xác thực cho PH-3 |

### PH-3 — Phân hệ Định danh & Kiểm soát truy cập (IAM)

**★ Tính năng chính: nguồn chân lý duy nhất về "ai là ai, ai được làm gì, ai được xem gì" — thực thi đặc quyền tối thiểu tới mức trường dữ liệu.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | IAM tập trung, quản lý phiên, cơ chế break-glass |
| Đặc tính kỹ thuật | RBAC + ABAC; phân quyền mức bản ghi/trường (data-level authorization); MFA bắt buộc; separation of duties; nguyên tắc bốn mắt cho thao tác nhạy cảm; truy cập khẩn cấp break-glass luôn để lại dấu vết |
| Ranh giới | Không lưu dữ liệu nghiệp vụ; cung cấp quyết định phân quyền cho các phân hệ khác |

### PH-4 — Phân hệ Dịch vụ nghiệp vụ

**★ Tính năng chính: chứa toàn bộ logic nghiệp vụ, mỗi domain là một đơn vị độc lập triển khai và mở rộng riêng (đảm bảo Capability & Scalability).**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | Các microservice theo bounded context: quản lý hồ sơ/vụ việc, nghiệp vụ chuyên môn, tra cứu & phân tích, báo cáo & thống kê |
| Đặc tính kỹ thuật | Stateless để scale ngang; giao tiếp bất đồng bộ qua PH-6; sở hữu dữ liệu riêng (database-per-service); khởi đầu dạng modular monolith |
| Ranh giới | Không gọi trực tiếp workflow engine — chỉ qua tầng trừu tượng PH-5 |

### PH-5 — Phân hệ Điều phối quy trình *(BIỆT LẬP)* ★

**★ Tính năng chính: điều phối toàn bộ quy trình nghiệp vụ theo BPMN, đồng thời cô lập engine để có thể thay thế (open source / enterprise / tự xây) mà không đụng tới nghiệp vụ.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | **Workflow Abstraction Layer** (interface trung lập) + các **Adapter** cho từng engine + engine BPMN thực thi phía sau |
| Đặc tính kỹ thuật | Ports & adapters + anti-corruption layer; quy trình chuẩn hóa theo **BPMN 2.0** (đảm bảo khả chuyển); **tách trạng thái tiến trình** (do engine giữ) **khỏi dữ liệu nghiệp vụ** (do PH-4 giữ); giao tiếp với domain **qua sự kiện** trên PH-6, không gọi đồng bộ hai chiều |
| Điều kiện để "tháo lắp được" | (1) chuẩn hóa BPMN 2.0 ở mức định nghĩa; (2) tách bạch dữ liệu; (3) giao tiếp hướng sự kiện. Đủ 3 điều kiện → đổi engine chỉ cần viết lại adapter |
| Ranh giới | Không chứa logic nghiệp vụ chi tiết; chỉ điều phối "khi nào, ai, bước nào" |

### PH-6 — Phân hệ Hạ tầng sự kiện & Tích hợp

**★ Tính năng chính: xương sống giao tiếp bất đồng bộ của toàn hệ thống — vừa là "bể giảm chấn" chống nghẽn tải, vừa là tầng trao đổi dữ liệu liên đơn vị kiểu X-Road.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | Message broker / event streaming; tầng interoperability chuẩn hóa |
| Đặc tính kỹ thuật | Hấp thụ đỉnh tải bằng xử lý bất đồng bộ; phát/tiêu thụ sự kiện giữa các phân hệ; **once-only principle** (dữ liệu cung cấp một lần, tái sử dụng); **federation** (liên kết hệ sinh thái khi mở rộng liên ngành/liên vùng); kênh trao đổi mã hóa & xác thực hai chiều |
| Ranh giới | Không xử lý logic; chỉ vận chuyển & định tuyến sự kiện/dữ liệu |

### PH-7 — Phân hệ Quản trị dữ liệu

**★ Tính năng chính: lưu trữ phân tán (không kho trung tâm), tối ưu đọc/ghi tách biệt, và giữ nhật ký kiểm toán bất biến làm bằng chứng.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | CSDL nghiệp vụ (giao dịch), read model (CQRS), audit log bất biến, kho time-series & search |
| Đặc tính kỹ thuật | **CQRS** tách đường ghi/đọc; cân nhắc **Event Sourcing** cho domain trọng yếu (lịch sử sự kiện = audit trail); polyglot persistence; **Data Mesh** (mỗi đơn vị sở hữu "data product", quản trị chung); **phân loại độ mật** + **chính sách lưu trữ/hủy**; read replica & sharding cho tải cao |
| Ranh giới | Dữ liệu do đơn vị chủ quản sở hữu; audit log tách khỏi business data |

### PH-8 — Phân hệ Giám sát & Quan sát

**★ Tính năng chính: cung cấp bức tranh realtime kép — tình hình nghiệp vụ (cho lãnh đạo) và sức khỏe kỹ thuật (cho vận hành) — đồng thời phát hiện mối đe dọa nội bộ.**

| Hạng mục | Nội dung |
|---|---|
| Thành phần | Dashboard nghiệp vụ realtime; nền tảng observability kỹ thuật; SOC (trung tâm giám sát an ninh) |
| Đặc tính kỹ thuật | Giám sát nghiệp vụ qua read model realtime (hồ sơ tồn đọng ở khâu nào…); giám sát kỹ thuật qua 3 trụ cột **metrics/logs/traces**; **giám sát hành vi & phát hiện bất thường nội bộ** (insider threat); cảnh báo tự động |
| Ranh giới | Chỉ quan sát; không can thiệp dữ liệu nghiệp vụ |

---

## 5. Nền tảng & thuộc tính xuyên suốt

Bao trùm mọi phân hệ, đảm bảo các "-ilities".

| Nền tảng | Tính năng chính | Cơ chế then chốt |
|---|---|---|
| **NT-1 An toàn thông tin** | Bảo vệ nhiều lớp, tuân thủ pháp lý | Zero Trust; Defense in Depth; mã hóa at-rest & in-transit; quản lý secret/khóa tập trung; audit bất biến; tuân thủ Luật ATTT mạng & NĐ 85/2016 (cấp độ 4/5) |
| **NT-2 Sẵn sàng & Chống chịu** | Không điểm chết, phục hồi được | No SPOF; redundancy; clustering; multi-AZ/DC (active-active/passive); circuit breaker; bulkhead; graceful degradation; DR với RPO/RTO rõ ràng; backup; **chaos engineering + diễn tập phục hồi định kỳ** |
| **NT-3 Mở rộng & Hiệu năng** | Chịu tải cao, co giãn theo nhu cầu | Service stateless; load balancing; autoscaling; multi-level cache; message broker giảm chấn; read replica & sharding |
| **NT-4 DevSecOps & Nền tảng vận hành** | Triển khai liên tục, không gián đoạn | CI/CD; quét bảo mật tự động trong pipeline; **blue-green/canary deployment**; Infrastructure as Code; API versioning tương thích ngược; quản lý cấu hình theo môi trường |
| **NT-5 Quan sát kỹ thuật** | Phát hiện sự cố sớm | Metrics, logs, traces thống nhất; truy vết phân tán qua nhiều service |

---

## 6. Ma trận truy vết đáp ứng yêu cầu

Chứng minh **mọi yêu cầu đều được phủ** và chỉ rõ phân hệ/cơ chế chịu trách nhiệm. Đây là công cụ kiểm tra "không bỏ sót".

| Yêu cầu gốc | Phân hệ / nền tảng đáp ứng | Cơ chế cụ thể |
|---|---|---|
| BPMN workflow engine | PH-5 | Engine BPMN 2.0 sau tầng trừu tượng |
| Workflow engine biệt lập, tháo lắp được | PH-5 | Abstraction layer + adapter + tách state + event-based |
| Big System | P2, PH-4, NT-4 | DDD, microservices, CI/CD, modular monolith → tách dần |
| Availability | NT-2 | No SPOF, multi-AZ, active-active |
| Capability (mở rộng chức năng) | PH-4, P2 | Bounded context độc lập, thêm domain không ảnh hưởng phần khác |
| Scalability | NT-3, PH-4 | Stateless + autoscaling + load balancing |
| Reliability | NT-2 | Circuit breaker, bulkhead, graceful degradation, DR |
| Security hàng đầu | NT-1, PH-2, PH-3 | Zero Trust, IAM, mã hóa, audit bất biến, tuân thủ pháp lý |
| Chịu tải cao | NT-3, PH-6 | Message broker giảm chấn, cache, read replica |
| Nhiều user cập nhật đồng thời | PH-7 | Optimistic concurrency + conflict resolution |
| Hiển thị tức thời | PH-1, PH-7 | CQRS read model + WebSocket/SSE push |
| Dashboard monitor realtime | PH-8, PH-1 | Read model realtime + kênh đẩy |
| Dữ liệu chủ động, không phụ thuộc | P3, P6, PH-7 | Dữ liệu phân tán, chuẩn mở, chủ quyền số |

---

## 7. Giải quyết xung đột tính năng

Phần quan trọng nhất với yêu cầu "không xung đột tính năng". Mỗi cặp yêu cầu có khả năng mâu thuẫn được nêu rõ và chỉ ra cơ chế hóa giải.

| # | Cặp mâu thuẫn tiềm ẩn | Vấn đề | Cơ chế hóa giải |
|---|---|---|---|
| **X1** | Zero Trust / mã hóa **⟷** Realtime & hiệu năng | Xác thực & mã hóa mọi request làm tăng độ trễ | Xác thực token **một lần tại PH-2** (không lặp lại downstream); cache quyết định phân quyền; TLS offload tại gateway; đọc từ read model đã tối ưu |
| **X2** | Nhất quán mạnh **⟷** Sẵn sàng cao (định lý CAP) | Không thể vừa nhất quán tuyệt đối vừa luôn sẵn sàng khi phân tán | **Strong consistency** cho đường ghi giao dịch; **eventual consistency** cho read model/dashboard — chấp nhận độ trễ mili-giây để đổi lấy sẵn sàng |
| **X3** | Dữ liệu phân tán, không kho chung **⟷** Dashboard tổng hợp toàn cục | Không có kho trung tâm thì lấy gì để tổng hợp realtime | Tổng hợp **qua sự kiện** (PH-6) vào một **read model chuyên cho dashboard** (PH-7); dữ liệu gốc vẫn phân tán |
| **X4** | Microservices tự chủ **⟷** Nhất quán dữ liệu liên service | Không dùng transaction phân tán qua nhiều service | **Saga pattern** + event choreography; bù trừ (compensation) khi lỗi thay vì khóa toàn cục |
| **X5** | Audit bất biến (giữ vĩnh viễn) **⟷** Chính sách lưu trữ/hủy dữ liệu | Yêu cầu giữ dấu vết mãi mâu thuẫn với yêu cầu hủy dữ liệu hết hạn | **Tách audit (metadata thao tác, bất biến) khỏi business data (có retention)**; ẩn danh hóa thay vì xóa khi cần giữ dấu vết |
| **X6** | Workflow engine biệt lập **⟷** Hiệu năng gọi engine | Thêm tầng trừu tượng có thể thêm độ trễ | Giao tiếp **bất đồng bộ qua event bus** + tách state → engine không nằm trên đường request đồng bộ nóng |
| **X7** | Nhiều user sửa đồng thời **⟷** Không mất dữ liệu | Khóa cứng gây nghẽn; không khóa gây mất dữ liệu | **Optimistic concurrency control**: phát hiện xung đột theo phiên bản, xử lý va chạm — giữ throughput cao mà không mất dữ liệu |
| **X8** | Mã nguồn mở / chủ quyền **⟷** Tính năng enterprise mạnh | Sợ mất tính năng khi tự chủ | Abstraction layer (PH-5) cho phép **đổi engine linh hoạt**; chuẩn mở BPMN đảm bảo không khóa cứng — có thể bắt đầu enterprise rồi chuyển open source hoặc ngược lại |
| **X9** | Modular monolith khởi đầu **⟷** Microservices để scale | Sợ phải viết lại khi tách | Vẽ **ranh giới bounded context chuẩn từ đầu**; tách microservice dần theo điểm nghẽn thực tế — không viết lại, chỉ tách |

---

## 8. Quản trị, con người & lộ trình

Các nghiên cứu về hệ thống chính phủ lớn đều chỉ ra: dự án thường thất bại vì lý do **phi kỹ thuật**. Phần này bắt buộc phải nằm trong tài liệu thiết kế chuẩn.

| Hạng mục | Nội dung | Rủi ro nếu bỏ qua |
|---|---|---|
| **Quản lý thay đổi tổ chức** | Lãnh đạo cấp cao tham gia; "truyền thông quá mức"; đào tạo người dùng nghiệp vụ | Hệ thống xây xong không ai dùng |
| **Chống nợ kỹ thuật** | Kiểm toán hệ thống định kỳ; đào tạo & giữ đội ngũ nội bộ (đặc biệt với hệ mật) | Hệ thống xuống cấp, không nâng cấp nổi |
| **Hiện đại hóa tăng dần** | Không rip-and-replace; làm từng phần, rút kinh nghiệm, mở rộng | Rủi ro vận hành & chính trị cao khi làm "một cú lớn" |
| **Tuân thủ pháp lý** | Xác định sớm cấp độ an toàn (NĐ 85/2016), yêu cầu on-premise/air-gap, dữ liệu trong biên giới | Phải làm lại hạ tầng khi audit tuân thủ |
| **Vận hành an ninh** | SOC, insider threat, break-glass, chaos/DR drill định kỳ | Availability & security chỉ là lời hứa trên giấy |

---

## Phụ lục A — Bảng thuật ngữ (Glossary)

Giải thích toàn bộ keyword công nghệ và thuật ngữ viết tắt xuất hiện trong tài liệu, gom theo nhóm để dễ tra cứu. Với các từ viết tắt, phần giải thích luôn bắt đầu bằng dạng đầy đủ.

### A.1 — Kiến trúc & thiết kế phần mềm

| Thuật ngữ | Giải thích |
|---|---|
| **DDD** | *Domain-Driven Design* — Thiết kế hướng miền nghiệp vụ: mô hình phần mềm bám sát cách nghiệp vụ thực tế vận hành, thay vì bám theo công nghệ. |
| **Bounded Context** | Ranh giới ngữ cảnh: một vùng nghiệp vụ khép kín, có mô hình dữ liệu và ngôn ngữ riêng, không lẫn với vùng khác. Là đơn vị để tách microservice. |
| **Microservices** | Kiến trúc chia ứng dụng thành nhiều dịch vụ nhỏ, độc lập triển khai và mở rộng riêng, giao tiếp qua mạng. |
| **Modular Monolith** | Khối liền mạch có mô-đun hóa: một ứng dụng triển khai chung nhưng bên trong chia mô-đun ranh giới rõ ràng — bước khởi đầu an toàn trước khi tách microservice. |
| **Event-Driven Architecture** | Kiến trúc hướng sự kiện: các thành phần giao tiếp bằng cách phát/nhận "sự kiện" bất đồng bộ thay vì gọi trực tiếp, giúp tách rời và chịu tải tốt hơn. |
| **Ports & Adapters** | (còn gọi *Hexagonal Architecture*) Mẫu thiết kế đặt lõi nghiệp vụ ở trung tâm, mọi thứ bên ngoài (DB, engine, UI) cắm vào qua "cổng" chuẩn hóa — giúp thay thế thành phần ngoài mà không đụng lõi. |
| **Anti-Corruption Layer** | Lớp chống "nhiễm bẩn": tầng dịch trung gian ngăn đặc thù của hệ thống ngoài (ví dụ engine cụ thể) lọt vào và làm hỏng mô hình nghiệp vụ. |
| **Saga Pattern** | Mẫu xử lý giao dịch trải trên nhiều service: thực hiện từng bước, nếu một bước lỗi thì chạy hành động bù trừ (compensation) để quay lui — thay cho khóa toàn cục. |
| **Conway's Law** | Quy luật quan sát: cấu trúc hệ thống có xu hướng phản chiếu cấu trúc tổ chức đội ngũ. Hàm ý: nên chia service khớp ranh giới đội để các đội tự chủ. |

### A.2 — Quy trình & workflow

| Thuật ngữ | Giải thích |
|---|---|
| **BPMN 2.0** | *Business Process Model and Notation* — Chuẩn quốc tế để mô hình hóa quy trình nghiệp vụ bằng ký hiệu đồ họa. Là "ngôn ngữ chung" giúp quy trình khả chuyển giữa các engine. |
| **Workflow Engine** | Phần mềm thực thi quy trình: điều phối "bước nào, ai làm, khi nào, điều kiện gì" theo định nghĩa BPMN. |
| **Workflow Abstraction Layer** | Tầng trừu tượng workflow: tập interface trung lập mà nghiệp vụ chỉ nói chuyện với nó, che giấu engine cụ thể phía sau — điều kiện để "tháo lắp" engine. |
| **Adapter** | Bộ chuyển đổi: đoạn mã dịch giữa interface trung lập và API của một engine cụ thể. Đổi engine = viết lại adapter. |
| **Orchestration / Choreography** | Hai kiểu điều phối: *orchestration* có một "nhạc trưởng" ra lệnh từng bước; *choreography* các service tự phản ứng theo sự kiện, không có trung tâm điều khiển. |

### A.3 — An toàn thông tin & định danh

| Thuật ngữ | Giải thích |
|---|---|
| **Zero Trust** | "Không tin tưởng mặc định": mọi request đều phải xác thực và phân quyền lại, kể cả từ nội bộ mạng. |
| **Defense in Depth** | Phòng thủ nhiều lớp: xếp chồng nhiều lớp bảo mật (mạng, ứng dụng, dữ liệu) để một lớp thủng không mất tất cả. |
| **IAM** | *Identity and Access Management* — Quản lý định danh và truy cập: hệ thống trung tâm quản lý "ai là ai" và "ai được làm gì". |
| **RBAC** | *Role-Based Access Control* — Phân quyền theo vai trò: gán quyền qua vai trò (ví dụ "điều tra viên") thay vì gán trực tiếp cho từng người. |
| **ABAC** | *Attribute-Based Access Control* — Phân quyền theo thuộc tính: quyết định truy cập dựa trên thuộc tính (đơn vị, độ mật, thời điểm…), linh hoạt hơn RBAC. |
| **MFA** | *Multi-Factor Authentication* — Xác thực đa yếu tố: yêu cầu nhiều bằng chứng (mật khẩu + mã OTP/thiết bị…) để đăng nhập. |
| **SSO** | *Single Sign-On* — Đăng nhập một lần: dùng một lần đăng nhập cho nhiều hệ thống. |
| **WAF** | *Web Application Firewall* — Tường lửa ứng dụng web: chặn các tấn công ở tầng ứng dụng (SQL injection, XSS…) trước khi chạm hệ thống. |
| **TLS** | *Transport Layer Security* — Giao thức mã hóa dữ liệu khi truyền trên mạng (nền tảng của HTTPS). |
| **TLS termination / offload** | Điểm giải mã TLS: gateway đảm nhận việc giải mã, giảm tải cho các service phía sau. |
| **Rate limiting** | Giới hạn tần suất: chặn số lượng request quá mức từ một nguồn để chống quá tải và lạm dụng. |
| **Break-glass access** | Truy cập khẩn cấp "đập kính": cơ chế cấp quyền đặc biệt trong tình huống khẩn, luôn để lại dấu vết bất biến. |
| **Insider threat** | Mối đe dọa nội bộ: rủi ro từ chính người có quyền hợp pháp bên trong hệ thống. |
| **Separation of Duties** | Tách biệt trách nhiệm: chia một thao tác nhạy cảm cho nhiều người, không ai đủ quyền tự làm trọn. |
| **Nguyên tắc bốn mắt** | *Four-eyes principle* — Thao tác quan trọng cần ít nhất hai người phê duyệt. |
| **Secret / Key management** | Quản lý bí mật/khóa: lưu trữ và cấp phát tập trung các mật khẩu, khóa mã hóa, chứng thư — không nhúng cứng trong mã. |
| **Encryption at-rest / in-transit** | Mã hóa khi lưu trữ (at-rest) và khi truyền (in-transit) — hai trạng thái dữ liệu cần được bảo vệ. |
| **Audit log (immutable)** | Nhật ký kiểm toán bất biến: bản ghi mọi thao tác, không thể sửa/xóa, dùng làm bằng chứng. |
| **Data classification** | Phân loại dữ liệu theo độ mật/độ nhạy, làm cơ sở cho kiểm soát truy cập và lưu trữ. |

### A.4 — Dữ liệu & nhất quán

| Thuật ngữ | Giải thích |
|---|---|
| **CQRS** | *Command Query Responsibility Segregation* — Tách trách nhiệm ghi/đọc: dùng mô hình ghi và mô hình đọc riêng biệt, cho phép tối ưu đường đọc (dashboard, tra cứu) độc lập với đường ghi. |
| **Event Sourcing** | Nguồn sự kiện: lưu trạng thái dưới dạng chuỗi sự kiện đã xảy ra thay vì chỉ giá trị hiện tại; bản thân lịch sử sự kiện là một audit trail hoàn chỉnh. |
| **Read Model** | Mô hình đọc: bản dữ liệu đã tổng hợp/tối ưu sẵn cho truy vấn nhanh, cập nhật qua sự kiện. |
| **Polyglot Persistence** | Đa dạng lưu trữ: dùng nhiều loại CSDL khác nhau cho các nhu cầu khác nhau (giao dịch, tìm kiếm, chuỗi thời gian…). |
| **Read Replica** | Bản sao chỉ-đọc của CSDL để san tải truy vấn đọc. |
| **Sharding** | Phân mảnh dữ liệu: chia CSDL thành nhiều mảnh theo khóa để mở rộng ngang. |
| **Data Mesh** | Kiến trúc dữ liệu phi tập trung: mỗi đơn vị sở hữu và cung cấp "data product" của mình dưới quản trị chung, thay vì gom về một kho trung tâm. |
| **Data Product** | Sản phẩm dữ liệu: một tập dữ liệu được một đơn vị sở hữu, quản lý chất lượng và cung cấp như một dịch vụ tin cậy. |
| **Retention policy** | Chính sách lưu trữ/hủy: quy định giữ dữ liệu bao lâu và khi nào hủy. |
| **Strong / Eventual Consistency** | Nhất quán mạnh (mọi nơi thấy dữ liệu giống nhau ngay lập tức) và nhất quán cuối cùng (chấp nhận trễ ngắn để đổi lấy sẵn sàng cao). |
| **CAP theorem** | Định lý CAP: hệ phân tán không thể đồng thời đạt tối đa cả ba: nhất quán (Consistency), sẵn sàng (Availability), chịu phân vùng mạng (Partition tolerance) — buộc phải đánh đổi. |
| **Optimistic Concurrency Control** | Kiểm soát tương tranh lạc quan: cho nhiều người cùng sửa, phát hiện xung đột theo phiên bản khi lưu — thay cho khóa cứng gây nghẽn. |

### A.5 — Chịu tải & hiệu năng

| Thuật ngữ | Giải thích |
|---|---|
| **Stateless** | Không lưu trạng thái phiên bên trong service, nhờ đó nhân bản và co giãn tùy ý. |
| **Load Balancing** | Cân bằng tải: phân phối request đều cho nhiều bản service. |
| **Autoscaling** | Tự động co giãn: tăng/giảm số lượng bản service theo tải thực tế. |
| **Message Broker** | Trung gian tin nhắn: thành phần nhận và chuyển tiếp sự kiện/tin nhắn giữa các service; đóng vai trò "bể giảm chấn" hấp thụ đỉnh tải. |
| **Event Streaming** | Luồng sự kiện: dòng sự kiện liên tục, cho phép nhiều bên tiêu thụ theo thời gian thực. |
| **Multi-level Cache** | Bộ nhớ đệm nhiều tầng: lưu tạm dữ liệu hay dùng ở nhiều lớp để giảm tải và tăng tốc. |
| **WebSocket** | Kênh kết nối hai chiều bền vững giữa client và server, cho phép server đẩy dữ liệu tức thời. |
| **SSE** | *Server-Sent Events* — Kênh một chiều để server đẩy sự kiện liên tục xuống client (nhẹ hơn WebSocket khi chỉ cần đẩy xuống). |
| **Polling / no-polling** | *Polling* là client hỏi server liên tục để lấy dữ liệu mới (tốn tài nguyên); "no-polling" nghĩa là dùng cơ chế đẩy (WebSocket/SSE) thay thế. |

### A.6 — Sẵn sàng & chống chịu

| Thuật ngữ | Giải thích |
|---|---|
| **Availability** | Tính sẵn sàng: tỷ lệ thời gian hệ thống hoạt động và phục vụ được. |
| **Reliability** | Độ tin cậy: khả năng hệ thống hoạt động đúng và ổn định theo thời gian. |
| **SPOF** | *Single Point of Failure* — Điểm chết đơn lẻ: một thành phần mà nếu hỏng sẽ kéo sập cả hệ thống; kiến trúc tốt phải loại bỏ. |
| **Redundancy** | Dự phòng: nhân bản thành phần để một cái hỏng vẫn còn cái khác. |
| **Clustering** | Cụm: nhóm nhiều máy/nút hoạt động cùng nhau như một khối, chia tải và dự phòng lẫn nhau. |
| **AZ / DC** | *Availability Zone / Data Center* — Vùng sẵn sàng / Trung tâm dữ liệu: triển khai trên nhiều vùng/trung tâm để chịu được sự cố cục bộ. |
| **Active-Active / Active-Passive** | Hai mô hình dự phòng: *active-active* nhiều cụm cùng chạy chia tải; *active-passive* một cụm chạy, một cụm chờ tiếp quản khi lỗi. |
| **Circuit Breaker** | Cầu dao ngắt mạch: tự động ngắt lời gọi tới một service đang lỗi để tránh lỗi lan dây chuyền. |
| **Bulkhead** | Vách ngăn: cô lập tài nguyên theo phần, để một phần quá tải không kéo sập phần còn lại (ví như khoang kín trên tàu). |
| **Graceful Degradation** | Suy giảm có kiểm soát: khi quá tải/lỗi, hy sinh tính năng phụ để giữ tính năng lõi thay vì sập hoàn toàn. |
| **DR** | *Disaster Recovery* — Phục hồi thảm họa: kế hoạch và hạ tầng để khôi phục hệ thống sau sự cố lớn. |
| **RPO** | *Recovery Point Objective* — Mức mất dữ liệu tối đa chấp nhận được (tính bằng thời gian): "được phép mất bao nhiêu dữ liệu?" |
| **RTO** | *Recovery Time Objective* — Thời gian khôi phục tối đa chấp nhận được: "được phép ngừng bao lâu?" |
| **Chaos Engineering** | Kỹ thuật hỗn loạn: chủ động gây lỗi có kiểm soát trong môi trường thật để kiểm chứng khả năng chống chịu. |
| **Backup** | Sao lưu dữ liệu định kỳ để phục hồi khi mất mát. |

### A.7 — Tích hợp & dữ liệu phân tán

| Thuật ngữ | Giải thích |
|---|---|
| **Interoperability** | Khả năng liên thông: các hệ thống độc lập trao đổi và dùng chung dữ liệu một cách chuẩn hóa. |
| **X-Road** | Nền tảng trao đổi dữ liệu phi tập trung của Estonia (mã nguồn mở), được coi là chuẩn mực thế giới; kết nối các CSDL độc lập mà không gom về kho trung tâm. |
| **Once-only principle** | Nguyên tắc "một lần": đối tượng chỉ cung cấp một thông tin một lần, các hệ thống tái sử dụng lại thay vì nhập trùng. |
| **Federation** | Liên kết: nối hai hệ sinh thái trao đổi dữ liệu để dùng chung dịch vụ như thể cùng một hệ thống (phục vụ liên ngành/liên vùng). |
| **Digital Sovereignty** | Chủ quyền số: khả năng tự chủ hoàn toàn về công nghệ, dữ liệu và hạ tầng, không lệ thuộc bên ngoài. |
| **Vendor lock-in** | Khóa cứng nhà cung cấp: bị phụ thuộc vào một hãng đến mức khó/đắt để đổi — điều cần tránh. |

### A.8 — Vận hành & phát triển

| Thuật ngữ | Giải thích |
|---|---|
| **CI/CD** | *Continuous Integration / Continuous Delivery* — Tích hợp & phân phối liên tục: tự động hóa build–kiểm thử–triển khai để ra phiên bản nhanh và an toàn. |
| **DevSecOps** | Tích hợp bảo mật vào quy trình phát triển–vận hành (Dev + Sec + Ops); bảo mật được kiểm tra tự động ngay trong pipeline. |
| **Blue-green deployment** | Triển khai xanh-lam: chạy song song hai môi trường, chuyển đổi tức thời sang bản mới, quay lui nhanh nếu lỗi — không gián đoạn dịch vụ. |
| **Canary deployment** | Triển khai kiểu "chim hoàng yến": đưa bản mới cho một phần nhỏ người dùng trước, theo dõi rồi mới mở rộng. |
| **IaC** | *Infrastructure as Code* — Hạ tầng dạng mã: định nghĩa hạ tầng bằng mã để tái lập, kiểm soát phiên bản và tự động hóa. |
| **API** | *Application Programming Interface* — Giao diện lập trình: hợp đồng để các phần mềm gọi và trao đổi với nhau. |
| **API versioning** | Quản lý phiên bản API sao cho tương thích ngược, không làm hỏng bên đang dùng khi nâng cấp. |
| **Technical debt** | Nợ kỹ thuật: chi phí tích lũy do các quyết định tạm bợ, cần "trả" bằng tái cấu trúc để tránh hệ thống xuống cấp. |
| **Rip-and-replace** | "Đập đi xây lại" toàn bộ cùng lúc — cách làm rủi ro cao, tài liệu này khuyến nghị tránh. |

### A.9 — Giám sát

| Thuật ngữ | Giải thích |
|---|---|
| **Observability** | Khả năng quan sát: mức độ có thể suy ra trạng thái bên trong hệ thống từ dữ liệu nó phát ra. |
| **Metrics / Logs / Traces** | Ba trụ cột quan sát: *metrics* (chỉ số đo lường), *logs* (nhật ký sự kiện), *traces* (dấu vết một request đi qua nhiều service). |
| **SOC** | *Security Operations Center* — Trung tâm điều hành an ninh: nơi giám sát, phát hiện và ứng phó sự cố an ninh liên tục. |
| **Dashboard** | Bảng điều khiển trực quan hóa dữ liệu để theo dõi tình hình theo thời gian thực. |

### A.10 — Viết tắt tiếng Việt & pháp lý

| Thuật ngữ | Giải thích |
|---|---|
| **ATTT** | An toàn thông tin. |
| **NĐ** | Nghị định (văn bản quy phạm pháp luật của Chính phủ). |
| **NĐ 85/2016** | Nghị định về bảo đảm an toàn hệ thống thông tin theo cấp độ — cơ sở pháp lý phân loại và yêu cầu bảo vệ hệ thống ở Việt Nam. |
| **Cấp độ (an toàn HTTT)** | Mức phân loại hệ thống thông tin theo mức độ quan trọng (từ 1 đến 5); cấp độ càng cao yêu cầu bảo vệ càng nghiêm ngặt. |
| **Air-gap** | Cách ly vật lý: tách hoàn toàn một mạng/hệ thống nhạy cảm khỏi mạng ngoài để tăng bảo mật. |
| **PH- / NT-** | Ký hiệu nội bộ trong tài liệu: *PH* = Phân hệ chức năng, *NT* = Nền tảng xuyên suốt. |

---

### Ghi chú phiên bản

Tài liệu này là bản **high-level reference architecture** — chưa chốt tech stack cụ thể theo đúng yêu cầu. Các bước tiếp theo khả dĩ: (a) chi tiết hóa PH-5 (đặc tả interface + tiêu chí chọn engine); (b) thiết kế tầng interoperability PH-6 kiểu X-Road cho bối cảnh Việt Nam; (c) khung quản trị dữ liệu PH-7 (Data Mesh + phân loại độ mật + retention); (d) mô hình vận hành an ninh PH-8/NT-1 (SOC, insider threat, break-glass, chaos/DR).
