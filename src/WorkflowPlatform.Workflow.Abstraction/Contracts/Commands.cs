namespace WorkflowPlatform.Workflow.Abstraction.Contracts;

public sealed record StartProcessCommand(
    string ProcessDefinitionKey,
    string BusinessKey,
    IReadOnlyDictionary<string, ProcessVariable> Variables,
    string Initiator);

public sealed record CompleteTaskCommand(
    string BusinessKey,
    string TaskId,
    IReadOnlyDictionary<string, ProcessVariable> Variables,
    string Actor);

/// <summary>Định nghĩa quy trình dạng BPMN 2.0 canonical (điều kiện C1).</summary>
public sealed record CanonicalBpmn(string DefinitionKey, string Xml);

public sealed record ProcessStartedAck(string BusinessKey, string InstanceId);
