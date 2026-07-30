namespace WorkflowPlatform.Domain.Cases;

/// <summary>
/// Aggregate Hồ sơ/Vụ việc (BC-1). Giữ DỮ LIỆU NGHIỆP VỤ (Title, Content) và trạng thái nghiệp vụ.
/// KHÔNG biết gì về workflow engine — tách bạch state theo REQ-F-003.
/// </summary>
public sealed class Case
{
    public Guid Id { get; }
    public string Title { get; private set; }
    public string Content { get; private set; }
    public CaseStatus Status { get; private set; }
    public DateTimeOffset CreatedAt { get; }

    private Case(Guid id, string title, string content, DateTimeOffset createdAt)
    {
        Id = id;
        Title = title;
        Content = content;
        CreatedAt = createdAt;
        Status = CaseStatus.Draft;
    }

    public static Case Create(string title, string content)
    {
        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("Tiêu đề hồ sơ không được rỗng.", nameof(title));

        return new Case(Guid.NewGuid(), title, content ?? string.Empty, DateTimeOffset.UtcNow);
    }

    /// <summary>Dựng lại aggregate từ dữ liệu đã lưu (persistence). Không dùng cho tạo mới.</summary>
    public static Case Rehydrate(Guid id, string title, string content, CaseStatus status, DateTimeOffset createdAt)
        => new(id, title, content, createdAt) { Status = status };

    public void MarkInReview()
    {
        if (Status == CaseStatus.Draft)
            Status = CaseStatus.InReview;
    }

    public void Approve() => Status = CaseStatus.Approved;
    public void Reject() => Status = CaseStatus.Rejected;
}
