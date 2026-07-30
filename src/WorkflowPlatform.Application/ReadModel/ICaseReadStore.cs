namespace WorkflowPlatform.Application.ReadModel;

public interface ICaseReadStore
{
    void Upsert(CaseView view);
    CaseView? Get(Guid id);
    IReadOnlyList<CaseView> All();
}
