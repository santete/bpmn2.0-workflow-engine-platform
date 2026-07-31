namespace WorkflowPlatform.Infrastructure.Persistence;

/// <summary>Bản ghi persistence cho aggregate Case (tách khỏi domain để giữ domain sạch EF).</summary>
public sealed class CaseRecord
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Status { get; set; } = "Draft";
    public DateTimeOffset CreatedAt { get; set; }
}

public sealed class ReplayInstanceRecord
{
    public string BusinessKey { get; set; } = string.Empty;
    public string DefinitionKey { get; set; } = string.Empty;
    public bool IsCancelled { get; set; }
}

public sealed class ReplayCompletionRecord
{
    public long Id { get; set; }
    public string BusinessKey { get; set; } = string.Empty;
    public int Seq { get; set; }
    public string TaskId { get; set; } = string.Empty;
    public string? Decision { get; set; }
}

/// <summary>Định nghĩa quy trình (spec) lưu dạng JSON — cho phép tạo/sửa workflow lúc chạy.</summary>
public sealed class ProcessDefinitionRecord
{
    public string Key { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string SpecJson { get; set; } = string.Empty;
}

/// <summary>Một dòng lịch sử bất biến của hồ sơ — audit trail (BC-7).</summary>
public sealed class CaseHistoryRecord
{
    public long Id { get; set; }
    public string CaseId { get; set; } = string.Empty;
    public string Kind { get; set; } = string.Empty;
    public string? TaskId { get; set; }
    public string? TaskName { get; set; }
    public string? Actor { get; set; }
    public string? Decision { get; set; }
    public DateTimeOffset OccurredAt { get; set; }
}
