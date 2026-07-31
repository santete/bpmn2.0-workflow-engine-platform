namespace WorkflowPlatform.Application.ReadModel;

public interface ICaseHistoryStore
{
    void Append(CaseHistoryEntry entry);
    IReadOnlyList<CaseHistoryEntry> List(Guid caseId);
    bool VerifyIntegrity(Guid caseId);
}
