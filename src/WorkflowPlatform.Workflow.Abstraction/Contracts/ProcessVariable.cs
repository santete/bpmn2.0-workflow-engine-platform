namespace WorkflowPlatform.Workflow.Abstraction.Contracts;

/// <summary>
/// Loại biến điều phối. Ràng buộc C2 (tách dữ liệu): CHỈ scalar/enum/tham chiếu thực thể —
/// KHÔNG nhồi payload nghiệp vụ vào process variable.
/// </summary>
public enum VariableKind
{
    Scalar,
    Enum,
    EntityRef
}

/// <summary>Biến điều phối trung lập. Value luôn là chuỗi (ref/scalar), không phải object nghiệp vụ.</summary>
public sealed record ProcessVariable(VariableKind Kind, string Value)
{
    public static ProcessVariable Scalar(string value) => new(VariableKind.Scalar, value);
    public static ProcessVariable Enum(string value) => new(VariableKind.Enum, value);

    /// <summary>Con trỏ tới business data ở PH-4 (vd "case:{guid}") — KHÔNG phải bản thân dữ liệu.</summary>
    public static ProcessVariable Ref(string domain, string id) => new(VariableKind.EntityRef, $"{domain}:{id}");
}
