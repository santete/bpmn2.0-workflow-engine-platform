# KẾ HOẠCH TỔNG THỂ TRIỂN KHAI
## Hệ thống Số hóa Toàn trình — An ninh Nội địa Quốc gia

> **Master Delivery Plan** — lập theo phương pháp Solution Architect chuẩn doanh nghiệp.
> Đi kèm: *Tài liệu thiết kế kiến trúc tổng thể* (reference architecture) và *C4 Container diagram*.
> Nguyên tắc: kiến trúc dẫn đường, khử rủi ro cao nhất trước, giao hàng gia tăng (không big-bang), mọi quyết định truy vết được, chất lượng chốt bằng cổng kiểm soát (gate).

---

## 0. Cách làm việc của Solution Architect (nguyên tắc xuyên suốt)

Kế hoạch này không phải một danh sách công việc tuyến tính, mà vận hành theo 7 nguyên tắc nghề nghiệp:

| # | Nguyên tắc | Áp dụng cụ thể |
|---|-----------|----------------|
| 1 | **Architecture-first** | Chốt kiến trúc nền & NFR định lượng trước khi viết dòng code sản xuất nào |
| 2 | **Risk-driven sequencing** | Spike/PoC những rủi ro kiến trúc cao nhất *sớm nhất* (M2), không để dồn về cuối |
| 3 | **Incremental delivery** | Bắt đầu modular monolith → tách microservice theo điểm nghẽn thật; không "đập đi xây lại" |
| 4 | **Walking skeleton** | Dựng một lát cắt xuyên suốt mỏng qua *mọi tầng* trước, rồi mới đắp thịt |
| 5 | **Decisions as ADR** | Mọi quyết định kiến trúc/công nghệ ghi thành Architecture Decision Record có lý do & phương án loại bỏ |
| 6 | **Traceability** | Mọi hạng mục truy ngược về yêu cầu qua Requirements Traceability Matrix (RTM) |
| 7 | **Fitness functions & gates** | Chất lượng kiến trúc (độ trễ, coupling, bảo mật) được kiểm thử tự động; mỗi milestone có cổng nghiệm thu |

---

## 1. Bản đồ milestone tổng thể

> **Giả định thời lượng:** ước tính chỉ định cho một đội đa chức năng cỡ trung, sprint 2 tuần. Con số cần tinh chỉnh theo năng lực đội, ngân sách và mức độ tuân thủ thực tế — đây là *thứ tự và trọng số*, không phải cam kết lịch.

| MS | Tên milestone | Mục tiêu cốt lõi | Cổng nghiệm thu (Gate) | Thời lượng chỉ định |
|----|---------------|------------------|------------------------|---------------------|
| **M0** | Khởi động & Quản trị | Dựng bộ máy quản trị & chuẩn làm việc | G0: ARB & chuẩn được duyệt | 2–3 tuần |
| **M1** | Khám phá & Kiến trúc nền | Chốt miền, NFR định lượng, tuân thủ | G1: Kiến trúc nền & NFR được ký | 4–6 tuần |
| **M2** | Quyết định công nghệ & PoC | Chốt tech stack *dựa trên bằng chứng* | G2: Tech stack duyệt qua PoC | 4–6 tuần |
| **M3** | Nền tảng & Khung xương | Dựng nền tảng xuyên suốt + walking skeleton | G3: Lát cắt E2E chạy + pipeline xanh | 6–8 tuần |
| **M4** | Phát triển gia tăng theo domain | Bàn giao lần lượt từng bounded context | G4 (lặp): mỗi domain đạt DoD | Theo số domain |
| **M5** | Chịu tải, HA & Chống chịu | Đạt & đo được NFR phi chức năng | G5: NFR đạt + DR drill thành công | 4–6 tuần |
| **M6** | Kiểm định an ninh & Tuân thủ | Chứng nhận an ninh & pháp lý | G6: Đạt pentest & tuân thủ cấp độ | 3–5 tuần |
| **M7** | Go-live, Vận hành & Chuyển giao | Vận hành an toàn, không gián đoạn | G7: Hypercare đạt SLA, nghiệm thu | 3–4 tuần + hypercare |
| **M8** | Cải tiến liên tục | Tiến hóa bền vững, chứng minh tháo lắp | G8 (định kỳ): fitness functions xanh | Liên tục |

Lưu ý: M3–M4 có thể chồng lấn; nền tảng (M3) và các domain đầu (M4) chạy song song một phần. M5–M6 áp dụng liên tục ở mức nhỏ trong M4 rồi tổng lực trước go-live.

---

## 2. Chi tiết từng milestone

### M0 — Khởi động & Thiết lập quản trị

**Mục tiêu:** đặt nền tảng ra quyết định và đồng thuận trước khi đụng vào kỹ thuật — bài học số 1 từ các dự án chính phủ lớn.

Công việc chính:
- Thành lập **Architecture Review Board (ARB)**; xác định **RACI** cho các quyết định
- Thiết lập quy trình **ADR** (mẫu, nơi lưu, cách duyệt)
- Định nghĩa **Definition of Done / Definition of Ready**, chuẩn code & chuẩn bảo mật
- Xác định **executive sponsor**; khởi động **kế hoạch quản lý thay đổi & truyền thông** (bắt đầu sớm, "truyền thông quá mức")
- Chọn bộ công cụ: repo, CI/CD, quản lý backlog, tài liệu kiến trúc sống (C4), **RAID log**

Sản phẩm bàn giao: Điều lệ ARB · Mẫu & kho ADR · RACI · Kế hoạch change management · Bộ chuẩn kỹ thuật.

**Gate G0:** bộ máy quản trị và chuẩn làm việc được phê duyệt.

*Trục phủ:* **G6** (quản trị, con người) — nền tảng cho mọi trục còn lại.

---

### M1 — Khám phá & Kiến trúc nền

**Mục tiêu:** biến yêu cầu mơ hồ thành mô hình miền rõ ràng và **NFR định lượng** — không có số thì không thể nghiệm thu về sau.

Công việc chính:
- **Event Storming / DDD workshops** → chốt bounded contexts & context map (đầu vào cho việc tách service sau này)
- **Định lượng NFR:** mục tiêu tải (RPS, số user đồng thời), **RPO/RTO**, % availability/SLA, ngưỡng độ trễ đẩy realtime
- Xác định **cấp độ an toàn HTTT theo NĐ 85/2016** (cấp 4 hay 5) → lập hồ sơ tuân thủ; xác định yêu cầu on-premise/air-gap/dữ liệu trong biên giới
- **Threat modeling** sơ bộ (STRIDE); **phân loại dữ liệu** theo độ mật
- Hoàn thiện **Reference Architecture** + **C4 Level 1/L2**; ghi các ADR nền tảng
- Khởi tạo **Requirements Traceability Matrix (RTM)**

Sản phẩm bàn giao: Context map · NFR định lượng (đã ký) · Hồ sơ phân loại & tuân thủ · Threat model v1 · C4 L1/L2 · RTM.

**Gate G1:** ARB duyệt kiến trúc nền & NFR; stakeholder ký cam kết NFR.

*Trục phủ:* **G1** (định nghĩa quy trình nghiệp vụ) · **G2** (phân loại, tuân thủ, threat model) · **G3/G4** (NFR định lượng) · **G5** (mô hình dữ liệu) · **G6** (DDD, RTM).

---

### M2 — Quyết định công nghệ & PoC / Spike

**Mục tiêu:** đây là điểm mở khóa tech stack (trước đó cố tình để trống). Quyết định **dựa trên bằng chứng**, không dựa trên sở thích.

Công việc chính:
- Lập **tiêu chí đánh giá & chọn** cho từng trục: workflow engine (OSS như Camunda/Flowable *vs* enterprise *vs* tự xây) — đo qua khả năng ghép vào Abstraction Layer; event backbone; datastore; IAM; interop
- **Architecture spikes** cho rủi ro cao: đẩy realtime ở tải lớn (WebSocket/SSE), CQRS + eventual consistency, optimistic concurrency, event replay/Event Sourcing, liên thông kiểu X-Road
- **PoC tầng Workflow Abstraction + ≥1 adapter** — chứng minh "tháo lắp được" ngay từ sớm, không để là lời hứa suông
- Định nghĩa **fitness functions v1** (kiểm thử kiến trúc tự động: độ trễ, coupling, cổng bảo mật)
- Ghi **ADR** cho từng quyết định công nghệ (kèm phương án bị loại & lý do)

Sản phẩm bàn giao: Bảng đánh giá & ADR quyết định từng trục · Kết quả PoC/spike · Fitness functions v1.

**Gate G2:** ARB duyệt tech stack dựa trên bằng chứng PoC (không duyệt trên slide).

*Trục phủ:* **G1** (chọn engine + chứng minh abstraction) · **G3** (PoC realtime/concurrency) · **G5** (PoC interop) · **G6** (fitness functions).

---

### M3 — Nền tảng & Khung xương (Architecture Runway + Walking Skeleton)

**Mục tiêu:** dựng "đường băng kiến trúc" và một lát cắt xuyên suốt mỏng — để mọi domain sau này chạy trên nền có sẵn.

Công việc chính:
- **Nền tảng xuyên suốt trước:** IAM (Zero Trust cơ sở), API Gateway + WAF, event backbone, observability (metrics/logs/traces), quản lý secret/khóa, audit log bất biến
- **CI/CD + DevSecOps pipeline** (quét bảo mật tự động trong pipeline), **IaC**, quản lý cấu hình theo môi trường
- **Walking skeleton:** một luồng mỏng chạy end-to-end qua *mọi tầng* — client → gateway → 1 domain (dạng modular monolith) → workflow abstraction + 1 engine → event bus → read model → dashboard realtime
- Dựng môi trường dev/test/staging + kiểm soát bảo mật cơ sở

Sản phẩm bàn giao: Nền tảng vận hành được · Pipeline CI/CD · Walking skeleton chạy E2E · Observability dashboard.

**Gate G3:** lát cắt xuyên suốt chạy được + pipeline xanh + kiểm soát bảo mật cơ sở đạt.

*Trục phủ:* **G2** (IAM, audit, secret, Zero Trust cơ sở) · **G3** (event backbone, realtime skeleton) · **G6** (CI/CD, DevSecOps, IaC, monolith mô-đun) · nền **NT-5** (observability).

---

### M4 — Phát triển gia tăng theo domain

**Mục tiêu:** phủ nghiệp vụ thực bằng cách bàn giao *lần lượt* từng bounded context; tách microservice có kỷ luật.

Công việc chính (lặp cho mỗi domain):
- Mỗi increment gồm: domain service + **quy trình BPMN** + read model + lát dashboard + **phân quyền mức dữ liệu (ABAC)**
- Áp **optimistic concurrency** cho cập nhật đồng thời; **saga** cho giao dịch liên service
- **Tách microservice khỏi monolith khi có bằng chứng điểm nghẽn** — không tách sớm
- Triển khai **interop layer** gia tăng: once-only, federation khi cần liên ngành
- **Kiểm thử bảo mật liên tục (SAST/DAST)** mỗi increment; cập nhật threat model
- Cập nhật **RTM & C4 L3** cho từng container hoàn thành

Sản phẩm bàn giao: Các domain hoàn thiện theo lô · Quy trình BPMN vận hành · Interop liên thông · RTM & C4 L3 cập nhật.

**Gate G4 (lặp):** một domain phải đạt DoD (chức năng + NFR + bảo mật + test) trước khi mở domain kế tiếp.

*Trục phủ:* **G1** (quy trình BPMN thực) · **G2** (ABAC, security testing liên tục) · **G3** (concurrency) · **G5** (interop, once-only, federation, database-per-service) · **G6** (tách microservice có kỷ luật).

---

### M5 — Chịu tải, HA & Chống chịu

**Mục tiêu:** biến các NFR phi chức năng từ lời hứa thành **số đo được**.

Công việc chính:
- **Load / stress / soak testing** đến mục tiêu; tối ưu cache đa tầng, read replica, sharding, autoscaling
- Triển khai **HA:** cluster, multi-AZ/DC, active-active/passive; **kiểm thử failover**
- Cấu hình **DR** đạt RPO/RTO; **diễn tập phục hồi thảm họa thật** (không chỉ trên giấy)
- **Chaos engineering:** chủ động gây lỗi, kiểm chứng circuit breaker / bulkhead / graceful degradation
- Kiểm thử **tương tranh cao** (nhiều user đồng thời) & độ trễ đẩy realtime

Sản phẩm bàn giao: Báo cáo tải đạt mục tiêu · Cấu hình HA/DR · Báo cáo DR drill & chaos · Bản tinh chỉnh.

**Gate G5:** NFR về Availability/Reliability/Scalability đạt & được đo; DR drill thành công.

*Trục phủ:* **G3** (tải, realtime) · **G4** (HA, DR, resilience, chaos) · nền **NT-2/NT-3**.

---

### M6 — Kiểm định an ninh & Tuân thủ

**Mục tiêu:** vượt qua kiểm định an ninh & pháp lý — điều kiện *bắt buộc* để go-live với hệ thống an ninh quốc gia.

Công việc chính:
- **Penetration testing** bởi bên thứ ba độc lập; vá & tái kiểm
- **Kiểm toán bảo mật** đầy đủ; xác minh **audit trail bất biến** hoạt động đúng
- Hoàn thiện & **kiểm thử** kiểm soát: insider threat, separation of duties, nguyên tắc bốn mắt, **break-glass**
- **Đánh giá & hồ sơ tuân thủ theo cấp độ NĐ 85/2016**; xác minh dữ liệu trong biên giới, air-gap nếu áp dụng
- Threat model cuối; **đánh giá chủ quyền số** (kiểm tra không bị khóa cứng nhà cung cấp)

Sản phẩm bàn giao: Báo cáo pentest + khắc phục · Hồ sơ tuân thủ cấp độ · Chứng nhận an ninh nội bộ.

**Gate G6:** đạt kiểm định an ninh & tuân thủ pháp lý (điều kiện chặn go-live).

*Trục phủ:* **G2** (toàn diện) · **G5** (chủ quyền dữ liệu) · **G6** (digital sovereignty).

---

### M7 — Go-live, Vận hành & Chuyển giao

**Mục tiêu:** đưa vào vận hành an toàn, không gián đoạn, và chuyển giao năng lực cho đội vận hành.

Công việc chính:
- Thiết lập **SOC** (giám sát an ninh liên tục), **runbook**, quy trình on-call & ứng cứu sự cố
- **Go-live theo blue-green/canary**; kế hoạch rollback rõ ràng
- **Đào tạo** người dùng nghiệp vụ & vận hành; **truyền thông rollout** (thực thi change management)
- Chuyển giao tri thức, tài liệu vận hành, SLA/OLA

Sản phẩm bàn giao: SOC vận hành · Hệ thống go-live · Tài liệu vận hành & runbook · Chương trình đào tạo.

**Gate G7:** vận hành ổn định giai đoạn hypercare, đạt SLA; nghiệm thu chính thức.

*Trục phủ:* **G2** (SOC) · **G4** (vận hành HA thực tế) · **G6** (blue-green/canary, change management, đào tạo).

---

### M8 — Cải tiến liên tục & Chứng minh khả năng tháo lắp

**Mục tiêu:** duy trì tiến hóa bền vững và *chứng minh* giá trị của các quyết định kiến trúc.

Công việc chính:
- Vòng phản hồi & cải tiến liên tục; **kiểm toán kiến trúc định kỳ**; **quản lý nợ kỹ thuật**
- Diễn tập DR/chaos định kỳ; cập nhật threat model theo chu kỳ
- **Bài kiểm chứng "engine swap":** thử thay workflow engine qua adapter để xác nhận Abstraction Layer thực sự tháo lắp được — đây là bằng chứng sống cho yêu cầu cốt lõi của dự án
- Định kỳ đánh giá lại chủ quyền số & mức phụ thuộc nhà cung cấp

Sản phẩm bàn giao: Nhịp cải tiến · Báo cáo kiểm toán định kỳ · Kết quả engine-swap drill.

**Gate G8 (định kỳ):** fitness functions vẫn xanh; nợ kỹ thuật trong ngưỡng cho phép.

*Trục phủ:* **G1** (chứng minh tháo lắp) · **G4** (chaos/DR định kỳ) · **G6** (tech debt, sovereignty, cải tiến liên tục).

---

## 3. Ma trận phủ trục công nghệ

Bảng chứng minh **mọi trục đều được phủ** và chỉ rõ milestone nào *chốt chính* (●) và milestone nào *chạm tới* (○) trục đó. Không cột nào được để trống.

| Trục công nghệ | M0 | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **G1 — Điều phối quy trình (BPMN, workflow biệt lập)** | | ○ | ● | ○ | ● | | | | ● |
| **G2 — An toàn thông tin** | ○ | ○ | | ● | ● | | ● | ○ | |
| **G3 — Chịu tải & thời gian thực** | | ○ | ● | ○ | ○ | ● | | | |
| **G4 — Sẵn sàng & tin cậy** | | ○ | | ○ | | ● | | ○ | ○ |
| **G5 — Dữ liệu & tích hợp** | | ● | ○ | | ● | | ○ | | |
| **G6 — Big System & vận hành** | ● | ○ | ○ | ● | ● | | ○ | ● | ● |

Đọc theo hàng: mỗi trục có ít nhất một milestone "chốt chính" (●) và được nuôi dưỡng qua nhiều giai đoạn. Đọc theo cột: không milestone nào chỉ phục vụ một trục đơn lẻ — đảm bảo tính tích hợp.

---

## 4. Quản trị kiến trúc & nhịp làm việc

| Cơ chế | Nội dung | Tần suất |
|---|---|---|
| **Architecture Review Board (ARB)** | Duyệt ADR lớn & cổng milestone | Theo gate + định kỳ 2 tuần |
| **ADR (Architecture Decision Record)** | Ghi mọi quyết định kiến trúc/công nghệ kèm lý do & phương án loại | Ngay khi có quyết định |
| **Requirements Traceability Matrix** | Truy vết yêu cầu ↔ thiết kế ↔ kiểm thử | Cập nhật mỗi increment |
| **Fitness functions** | Kiểm thử kiến trúc tự động (độ trễ, coupling, bảo mật) | Chạy trong CI mỗi commit |
| **RAID log** | Risks, Assumptions, Issues, Dependencies | Rà soát hàng tuần |
| **C4 living docs** | Sơ đồ L1–L3 luôn khớp thực tế | Cập nhật theo container hoàn thành |

Vai trò chính (RACI): **Lead Solution Architect** (chủ trì kiến trúc & ARB) · Domain/Application Architects · **Security Architect** · **Data Architect** · Platform/DevSecOps Lead · Product/Business Owners · SRE/Ops · QA/Test Lead · **Change Manager**.

---

## 5. Rủi ro chính & giảm thiểu (trích RAID)

| Rủi ro | Tác động | Giảm thiểu | Xử lý tại |
|---|---|---|---|
| Tách microservice quá sớm | Phức tạp hóa vô ích, khó vận hành | Bắt đầu modular monolith, tách theo bằng chứng điểm nghẽn | M3–M4 |
| Khóa cứng vào workflow engine | Mất chủ động, đúng nỗi lo cốt lõi | Abstraction Layer + adapter + PoC tháo lắp sớm | M2, M8 |
| Realtime không đạt ở tải cao | Vỡ trải nghiệm & NFR | Spike sớm; CQRS + read model + đẩy WSS; load test | M2, M5 |
| Đánh giá sai cấp độ tuân thủ | Phải làm lại hạ tầng | Chốt cấp độ NĐ 85 ngay M1 | M1, M6 |
| Cám dỗ big-bang | Rủi ro vận hành/chính trị cao | Kỷ luật giao hàng gia tăng theo domain | Xuyên suốt |
| Người dùng không chịu dùng | Hệ thống xây xong bỏ không | Change management & truyền thông từ M0; đào tạo M7 | M0, M7 |
| Nợ kỹ thuật tích lũy | Hệ thống xuống cấp | Kiểm toán định kỳ, ngưỡng nợ trong fitness functions | M8 |
| Mối đe dọa nội bộ | Rò rỉ dữ liệu mật | Separation of duties, bốn mắt, break-glass, giám sát hành vi | M4, M6 |

---

## 6. Definition of Done (chuẩn nghiệm thu mỗi hạng mục)

Một hạng mục chỉ được coi là "xong" khi đồng thời: (1) đạt yêu cầu chức năng; (2) đạt NFR liên quan (tải, độ trễ, availability); (3) qua kiểm thử bảo mật (SAST/DAST) không lỗi nghiêm trọng; (4) đã gắn observability (metrics/logs/traces); (5) tài liệu, ADR và RTM đã cập nhật; (6) fitness functions liên quan vẫn xanh.

---

### Ghi chú phiên bản

Kế hoạch này là **master plan cấp cao**, độc lập với lịch tuyệt đối. Các con số thời lượng là chỉ định theo giả định đội ngũ và cần được thay bằng cam kết thực tế sau khi chốt năng lực đội, ngân sách và cấp độ tuân thủ (đầu ra của M0–M1). Kế hoạch chi tiết cấp sprint sẽ được sinh ra trong từng milestone theo backlog.
