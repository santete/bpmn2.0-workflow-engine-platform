namespace WorkflowPlatform.Application.Definitions;

public sealed class StepSpec
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Assignee { get; set; }
}

/// <summary>
/// Mô tả quy trình do người dùng định nghĩa (bước + có bước quyết định cuối). Lưu được, dùng để sinh BPMN.
/// </summary>
public sealed class ProcessDefinitionSpec
{
    public string Key { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public List<StepSpec> Steps { get; set; } = new();
    public bool EndsWithDecision { get; set; }
}
