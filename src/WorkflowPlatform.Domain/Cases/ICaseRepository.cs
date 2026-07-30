namespace WorkflowPlatform.Domain.Cases;

public interface ICaseRepository
{
    void Add(Case @case);

    /// <summary>Lưu thay đổi trạng thái của aggregate (upsert). Cần cho persistence khi Get trả về bản tách rời.</summary>
    void Save(Case @case);

    Case? Get(Guid id);
    IReadOnlyList<Case> All();
}
