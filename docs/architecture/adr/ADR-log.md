# ADR Log — Architecture Decision Records

> **Decisions-as-ADR** (nguyên tắc #5 của Master Plan). Mỗi quyết định kiến trúc ghi lại kèm **bối cảnh,
> quyết định, hệ quả, phương án bị loại & lý do**. ADR đã `Accepted` **không sửa** — chỉ `Superseded` bằng ADR mới.
>
> Giai đoạn đầu để tất cả trong 1 log; khi > 15 ADR sẽ tách mỗi ADR 1 file `ADR-###-slug.md`.

**Trạng thái:** `Proposed` (chờ ARB) · `Accepted` · `Superseded by ADR-xxx` · `Deprecated`.

**Mẫu ADR:**
```
## ADR-XXX — <Tiêu đề>
- Status: Proposed | Accepted | Superseded
- Date / Deciders / Trace (REQ, X)
- Context: <lực đẩy, ràng buộc>
- Decision: <quyết định>
- Consequences: <hệ quả +/->
- Alternatives rejected: <phương án loại + lý do>
```

---

## ADR-001 — Cô lập Workflow Engine bằng Ports & Adapters + Anti-Corruption Layer
- **Status:** Proposed · **Trace:** REQ-F-001,002,003 · X8 · PH-5
- **Context:** Rủi ro cốt lõi của dự án là *khóa cứng vào một workflow engine*. Yêu cầu "tháo lắp được"
  (OSS/enterprise/tự xây) mà không đụng nghiệp vụ.
- **Decision:** Domain chỉ giao tiếp qua `ProcessPort` trung lập; mỗi engine có 1 Adapter hiện thực SPI
  `EngineAdapter`; ACL dịch 2 chiều; giao tiếp async qua event bus. Xem [`04_ph5`](../04_ph5-workflow-abstraction-layer.md).
- **Consequences:** (+) đổi engine = viết lại adapter, domain bất biến; kiểm chứng bằng FIT-010.
  (−) thêm 1 tầng trừu tượng (chi phí ban đầu); giải quyết độ trễ bằng async (X6) nên không nằm trên đường nóng.
- **Alternatives rejected:** *Gọi trực tiếp engine SDK từ domain* — nhanh hơn ban đầu nhưng khóa cứng, đúng
  nỗi lo cốt lõi → loại. *Chuẩn hóa qua chỉ REST engine* — vẫn rò rỉ ngữ nghĩa engine → loại.

## ADR-002 — Khởi đầu Modular Monolith, tách Microservice theo bằng chứng điểm nghẽn
- **Status:** Proposed · **Trace:** REQ-F-005, O-005 · X9 · P2
- **Context:** "Big System" cần scale & capability, nhưng tách microservice sớm gây phức tạp vận hành vô ích.
- **Decision:** Bắt đầu **modular monolith** với ranh giới bounded context rõ từ đầu; **tách microservice chỉ
  khi có bằng chứng điểm nghẽn** (tải, tần suất deploy, ranh giới đội — Conway's Law).
- **Consequences:** (+) giảm rủi ro vận hành sớm; không "đập đi xây lại" (chỉ tách). (−) cần kỷ luật giữ
  ranh giới module (thực thi bằng FIT-007 static coupling rule).
- **Alternatives rejected:** *Microservices từ đầu* — over-engineering, chi phí vận hành cao khi chưa có tải thật.

## ADR-003 — Event-driven async là kiểu tích hợp mặc định
- **Status:** Proposed · **Trace:** REQ-F-004 · X6 · P1 · PH-6
- **Context:** Cần chịu tải cao, chống lỗi dây chuyền, decoupling giữa domain và workflow.
- **Decision:** Giao tiếp giữa các phân hệ **ưu tiên bất đồng bộ qua message broker/event streaming**;
  message broker đóng vai "bể giảm chấn". Call đồng bộ chỉ dùng cho query đọc độ trễ thấp.
- **Consequences:** (+) hấp thụ đỉnh tải, tách rời; (−) eventual consistency → xử lý ở ADR-004; cần idempotency
  + outbox pattern để không mất/trùng event.
- **Alternatives rejected:** *REST đồng bộ khắp nơi* — coupling chặt, lỗi lan dây chuyền, không chịu đỉnh tải.

## ADR-004 — CQRS với read model eventual-consistent cho realtime
- **Status:** Proposed · **Trace:** REQ-F-007,012,013 · X2,X3 · PH-7
- **Context:** Vừa cần nhất quán mạnh khi ghi giao dịch, vừa cần dashboard realtime tổng hợp từ dữ liệu phân tán.
- **Decision:** Tách **command (ghi, strong consistency)** khỏi **query (đọc từ read model, eventual)**;
  read model cập nhật qua event; dashboard đọc read model + push WSS.
- **Consequences:** (+) tối ưu đường đọc độc lập, tổng hợp toàn cục dù dữ liệu phân tán (giải X3);
  (−) độ trễ mili-giây giữa ghi và đọc (chấp nhận được, giải X2); cần theo dõi projection lag.
- **Alternatives rejected:** *1 model đọc-ghi chung, strong consistency toàn cục* — không scale đọc, vi phạm CAP khi phân tán.

## ADR-005 — Saga + compensation cho giao dịch liên service
- **Status:** Proposed · **Trace:** REQ-F-011 · X4
- **Context:** Không dùng distributed transaction (2PC) qua nhiều service (khóa toàn cục, không scale).
- **Decision:** Dùng **Saga** (choreography ưu tiên; orchestration khi luồng phức tạp) với **hành động bù trừ**
  khi bước lỗi.
- **Consequences:** (+) không khóa toàn cục, chịu lỗi cục bộ; (−) phải thiết kế compensation cho mỗi bước;
  cần theo dõi saga dở dang.
- **Alternatives rejected:** *2PC/XA* — không scale, SPOF ở transaction coordinator.

## ADR-006 — Optimistic Concurrency Control cho cập nhật đồng thời
- **Status:** Proposed · **Trace:** REQ-F-008 · X7
- **Context:** Nhiều user sửa 1 hồ sơ đồng thời; khóa cứng gây nghẽn, không khóa gây mất dữ liệu.
- **Decision:** Dùng **versioning (optimistic lock)**: phát hiện xung đột theo phiên bản khi lưu; xử lý va chạm
  (merge/từ chối kèm thông báo).
- **Consequences:** (+) throughput cao, không nghẽn; (−) client phải xử lý conflict response.
- **Alternatives rejected:** *Pessimistic lock* — nghẽn khi tải cao; *last-write-wins* — mất dữ liệu.

## ADR-007 — Zero Trust: verify token 1 lần tại Gateway, authZ theo ngữ cảnh tại PDP
- **Status:** Proposed · **Trace:** REQ-S-001,002,010 · X1 · PH-2,PH-3
- **Context:** Zero Trust yêu cầu xác thực/phân quyền mọi tầng, nhưng lặp xác thực nặng làm hỏng NFR realtime.
- **Decision:** **Xác thực** token (nặng) làm **1 lần tại PH-2**; truyền identity context ký số (mTLS) xuống
  downstream; **phân quyền** (nhẹ, cache TTL ngắn) làm lại tại **PDP** với ABAC field-level.
- **Consequences:** (+) giữ Zero Trust mà không phá latency (giải X1); (−) cần bảo vệ identity context khỏi giả mạo
  (ký số + mTLS).
- **Alternatives rejected:** *Xác thực lại đầy đủ ở mọi service* — độ trễ cao, vi phạm REQ-N-003.

## ADR-008 — Audit bất biến tách khỏi business data; ẩn danh hóa thay vì xóa
- **Status:** Proposed · **Trace:** REQ-S-008 · X5 · TM-004,005
- **Context:** Audit phải giữ vĩnh viễn & bất biến; nhưng business data có chính sách hủy theo retention → xung đột.
- **Decision:** **Tách 2 kho:** audit = WORM/append-only/hash-chain (metadata thao tác, giữ lâu dài);
  business data = có retention/hủy. Khi cần hủy mà vẫn giữ dấu vết → **ẩn danh hóa** thay vì xóa audit.
- **Consequences:** (+) thỏa cả tuân thủ lẫn bằng chứng (giải X5); chống phi tang (TM-004); (−) 2 vòng đời dữ liệu để quản.
- **Alternatives rejected:** *Gộp audit vào business data* — hủy business data mất luôn dấu vết; *giữ tất cả mãi mãi* — vi phạm retention.

## ADR-009 — Liên thông dữ liệu phi tập trung kiểu X-Road (không kho trung tâm)
- **Status:** Proposed · **Trace:** REQ-F-009,010 · P3,P6 · PH-6
- **Context:** Dữ liệu do đơn vị chủ quản nắm giữ; cần liên thông nhưng tránh SPOF & giữ chủ quyền.
- **Decision:** Tầng interoperability kiểu **X-Road**: trao đổi P2P có xác thực 2 chiều + mã hóa, **once-only**,
  **federation** khi mở rộng; **không** gom về kho trung tâm.
- **Consequences:** (+) không SPOF tầng dữ liệu, giữ chủ quyền đơn vị; (−) tổng hợp toàn cục phải qua event→read
  model (giải X3, ADR-004), phức tạp hơn kho trung tâm.
- **Alternatives rejected:** *Data lake trung tâm* — SPOF, vi phạm mô hình dữ liệu phân tán & chủ quyền đơn vị.

## ADR-010 — Polyglot Persistence + Database-per-Service
- **Status:** Proposed · **Trace:** REQ-F-005, N-008 · PH-7
- **Context:** Nhu cầu lưu trữ khác nhau (giao dịch, tìm kiếm, time-series, read model).
- **Decision:** Mỗi service sở hữu DB riêng; chọn loại CSDL theo nhu cầu (RDBMS giao dịch, search engine,
  time-series, cache). Không service nào truy cập DB của service khác trực tiếp.
- **Consequences:** (+) tách rời, tối ưu theo nhu cầu, scale độc lập; (−) không JOIN xuyên service → dùng event + read model.
- **Alternatives rejected:** *1 CSDL dùng chung* — coupling chặt, SPOF, cản tách microservice sau này.

## ADR-011 — Lựa chọn Workflow Engine dựa trên bằng chứng PoC (chưa chốt)
- **Status:** Proposed (deferred → Gate G2) · **Trace:** REQ-F-001, O-006 · X8
- **Context:** Reference architecture cố ý để trống tech stack; chọn engine là quyết định lớn, cần bằng chứng.
- **Decision:** **Chưa chốt engine ở giai đoạn kiến trúc.** Dùng ma trận tiêu chí có trọng số ([`04_ph5` §6])
  + PoC tầng abstraction với ≥1 adapter tại M2; chốt tại **Gate G2 qua bằng chứng, không qua slide**.
  Khuyến nghị sơ bộ: ưu tiên OSS chín muồi (Camunda/Flowable) vì chủ quyền số + air-gap; "tự xây" chỉ khi PoC bác bỏ OSS.
- **Consequences:** (+) quyết định có bằng chứng, giảm rủi ro chọn sai; (−) hoãn chốt stack tới M2 (đúng thiết kế).
- **Alternatives rejected:** *Chốt engine ngay trên giấy* — rủi ro cao, trái nguyên tắc evidence-based của Master Plan.

## ADR-012 — Realtime transport: WebSocket chính, SSE dự phòng
- **Status:** Proposed · **Trace:** REQ-F-006, N-003 · PH-1
- **Context:** Cần đẩy dữ liệu realtime, no-polling; một số client/mạng hạn chế WebSocket.
- **Decision:** **WebSocket** cho kênh 2 chiều realtime chính; **SSE** fallback cho luồng chỉ-đẩy khi WS bị chặn;
  không dùng polling.
- **Consequences:** (+) độ trễ thấp, giảm tải server so với polling; (−) cần quản lý kết nối bền + fan-out ở scale (bulkhead).
- **Alternatives rejected:** *Long-polling* — tốn tài nguyên, độ trễ cao, không đạt REQ-N-003.

---

### Chỉ số ADR
12 ADR · phủ toàn bộ 9 xung đột X1–X9 (X1→007, X2→004, X3→004/009, X4→005, X5→008, X6→001/003, X7→006, X8→001/011, X9→002).
