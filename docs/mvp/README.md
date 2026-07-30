# MVP — Walking Skeleton (.NET)

> Lát cắt E2E chứng minh **lõi PH-5**: domain điều phối BPMN **chỉ qua `IProcessPort`**, engine sau adapter,
> giao tiếp bằng **event**. Trạng thái: ✅ build sạch · **19/19 test** · chạy thật trên Kestrel + SQLite.

## Chạy

```bash
dotnet test                                   # 19 test
dotnet run --project src/WorkflowPlatform.Api # UI + API tại http://localhost:5xxx
```

Mở `http://localhost:<port>/` → UI: tạo hồ sơ, bấm **Hoàn thành thẩm định** → **Phê duyệt / Từ chối**.

Cấu hình (env hoặc appsettings):
| Key | Giá trị | Ý nghĩa |
|-----|---------|---------|
| `PERSISTENCE` | `sqlite` (mặc định) \| `inmemory` | Lưu trữ. sqlite ⇒ dùng engine Replay (persist được). |
| `WF_ENGINE` | `simple` (mặc định) \| `replay` | Chọn engine khi `inmemory` (chứng minh swap). |
| `DB_PATH` | đường dẫn | File SQLite (mặc định `workflow.db`). |

## Bản đồ project ↔ kiến trúc

| Project | Vai trò | Phân hệ |
|---------|---------|---------|
| `Domain` | Aggregate `Case`. **Không tham chiếu workflow/engine.** | PH-4 |
| `Workflow.Abstraction` | `IProcessPort` + `IEngineAdapter` (SPI) + DTO canonical + event | **PH-5** |
| `Workflow.Bpmn` | Parse/mô hình BPMN 2.0 (dùng chung mọi adapter) | PH-5 |
| `Workflow.Adapter.Simple` | Engine #1 — **stored-cursor** | PH-5 |
| `Workflow.Adapter.Replay` | Engine #2 — **replay/recompute** (nhật ký persist được) | PH-5 |
| `Application` | Read model (CQRS) + `CaseProjector` | PH-7 |
| `Infrastructure` | EF Core + SQLite (repo, read store, replay log) | PH-7 |
| `Api` | Minimal API + in-process event bus + UI tĩnh | PH-1/6 |

## Bốn năng lực đã bổ sung (sau walking skeleton gốc)

1. **Engine thứ 2 + engine-swap (FIT-010).** `Simple` (con trỏ) và `Replay` (replay nhật ký) là hai mô hình
   thực thi khác hẳn nhau nhưng qua **cùng contract** `IEngineAdapter`. Bộ `EngineContractTestsBase` chạy trên
   cả hai; E2E chạy trên cả hai chỉ bằng đổi `WF_ENGINE`. Đây là bằng chứng "tháo lắp" — đổi engine không đụng domain/API.
2. **Persistence thật (EF Core + SQLite).** `Case` + read model + nhật ký tiến trình lưu SQLite.
   `PersistenceIntegrationTests` chứng minh dữ liệu **và vị trí tiến trình sống sót qua restart**.
3. **Branch/gateway.** BPMN có `exclusiveGateway` sau bước Phê duyệt: `decision=APPROVED→Hoàn tất`,
   `decision=REJECTED→Từ chối`. Cả hai engine giải nhánh theo điều kiện; phát `ProcessRejected`/`ProcessCompleted`.
4. **UI mỏng.** `wwwroot/index.html` (vanilla JS) gọi JSON endpoints — tạo hồ sơ + thao tác duyệt/từ chối.

## Ba điều kiện tháo lắp — kiểm cơ học

- **C1 (BPMN 2.0):** `BpmnParser` đọc XML 2.0 thật (`Api/Workflow/case-approval.bpmn`).
- **C2 (tách dữ liệu):** engine chỉ giữ process state + `businessKey`; `ProcessVariable` chỉ scalar/enum/ref.
- **C3 (event-driven):** domain↔engine chỉ qua `WorkflowEvent`.
- `ArchitectureIsolationTests` = mini **FIT-007** → chặn nếu Domain lỡ tham chiếu workflow/engine.

## Ngoài phạm vi MVP (post-MVP)

Adapter engine ngoài thật (Camunda/Flowable), message broker thật (PH-6), Zero Trust/IAM, X-Road interop,
HA/DR, parallel gateway/sub-process. Thiết kế đầy đủ: `docs/architecture/`.
