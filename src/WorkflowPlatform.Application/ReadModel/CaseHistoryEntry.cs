namespace WorkflowPlatform.Application.ReadModel;

public enum CaseHistoryKind { TaskCompleted, ProcessCompleted, ProcessRejected, ProcessCancelled }

/// <summary>
/// Một dòng lịch sử bất biến của hồ sơ (append-only): ai hoàn thành task nào, quyết định gì, lúc nào;
/// hoặc kết quả kết thúc tiến trình. Nền của audit trail (BC-7) ở các increment sau.
/// </summary>
public sealed record CaseHistoryEntry(
    Guid CaseId,
    CaseHistoryKind Kind,
    string? TaskId,
    string? TaskName,
    string? Actor,
    string? Decision,
    DateTimeOffset OccurredAt);
