namespace WorkflowPlatform.Application.Definitions;

public interface IProcessDefinitionStore
{
    void Save(ProcessDefinitionSpec spec);
    ProcessDefinitionSpec? Get(string key);
    IReadOnlyList<ProcessDefinitionSpec> All();
}
