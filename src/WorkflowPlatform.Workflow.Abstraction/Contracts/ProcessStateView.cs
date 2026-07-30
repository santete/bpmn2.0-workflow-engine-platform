namespace WorkflowPlatform.Workflow.Abstraction.Contracts;

public enum ProcessStatus
{
    NotFound,
    Running,
    Completed,
    Cancelled
}

public sealed record TaskView(string TaskId, string Name);

/// <summary>
/// Chỉ TRẠNG THÁI TIẾN TRÌNH + correlation — KHÔNG có field nào chứa nội dung hồ sơ (REQ-F-003).
/// </summary>
public sealed record ProcessStateView(
    string BusinessKey,
    string DefinitionKey,
    ProcessStatus Status,
    IReadOnlyList<TaskView> ActiveTasks);
