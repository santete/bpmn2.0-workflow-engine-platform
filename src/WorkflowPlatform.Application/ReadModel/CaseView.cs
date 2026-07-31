namespace WorkflowPlatform.Application.ReadModel;

/// <summary>
/// Read model (CQRS - PH-7): kết hợp thông tin nghiệp vụ + trạng thái tiến trình. Cập nhật qua event.
/// </summary>
public sealed class CaseView
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string DefinitionKey { get; set; } = string.Empty;
    public string BusinessStatus { get; set; } = "Draft";
    public string WorkflowStatus { get; set; } = "Khoi tao";
    public string? CurrentTaskId { get; set; }
    public string? CurrentTaskName { get; set; }
    public string? CurrentTaskAssignee { get; set; }
    public Guid Version { get; set; } = Guid.Empty;
}
