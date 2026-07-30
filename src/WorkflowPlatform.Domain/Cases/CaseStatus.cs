namespace WorkflowPlatform.Domain.Cases;

/// <summary>Trạng thái NGHIỆP VỤ của hồ sơ (khác với trạng thái TIẾN TRÌNH do engine giữ).</summary>
public enum CaseStatus
{
    Draft,
    InReview,
    Approved,
    Rejected,
    Closed
}
