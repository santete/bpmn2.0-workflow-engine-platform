namespace WorkflowPlatform.Workflow.Abstraction.Events;

/// <summary>
/// Sự kiện tiến trình CANONICAL (không mang tên engine cụ thể). Là kênh giao tiếp duy nhất
/// giữa workflow và domain (điều kiện C3 — event-driven, không call đồng bộ hai chiều).
/// </summary>
public abstract record WorkflowEvent(string BusinessKey, DateTimeOffset OccurredAt);

public sealed record ProcessStarted(string BusinessKey, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);

public sealed record TaskCreated(string BusinessKey, string TaskId, string TaskName, string? Assignee, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);

public sealed record TaskCompleted(string BusinessKey, string TaskId, string TaskName, string? Actor, string? Decision, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);

public sealed record ProcessCompleted(string BusinessKey, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);

/// <summary>Tiến trình kết thúc theo nhánh từ chối (exclusiveGateway → end reject).</summary>
public sealed record ProcessRejected(string BusinessKey, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);

/// <summary>Tiến trình bị hủy bởi người dùng (không phải kết thúc BPMN tự nhiên).</summary>
public sealed record ProcessCancelled(string BusinessKey, DateTimeOffset OccurredAt)
    : WorkflowEvent(BusinessKey, OccurredAt);
