using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Application.Definitions;

namespace WorkflowPlatform.Infrastructure.Persistence;

public sealed class EfProcessDefinitionStore : IProcessDefinitionStore
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public EfProcessDefinitionStore(IDbContextFactory<AppDbContext> factory) => _factory = factory;

    public void Save(ProcessDefinitionSpec spec)
    {
        using var ctx = _factory.CreateDbContext();
        var json = JsonSerializer.Serialize(spec);
        var existing = ctx.ProcessDefinitions.Find(spec.Key);
        if (existing is null)
            ctx.ProcessDefinitions.Add(new ProcessDefinitionRecord { Key = spec.Key, Name = spec.Name, SpecJson = json });
        else { existing.Name = spec.Name; existing.SpecJson = json; }
        ctx.SaveChanges();
    }

    public ProcessDefinitionSpec? Get(string key)
    {
        using var ctx = _factory.CreateDbContext();
        var r = ctx.ProcessDefinitions.AsNoTracking().FirstOrDefault(x => x.Key == key);
        return r is null ? null : JsonSerializer.Deserialize<ProcessDefinitionSpec>(r.SpecJson);
    }

    public IReadOnlyList<ProcessDefinitionSpec> All()
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.ProcessDefinitions.AsNoTracking().ToList()
            .Select(r => JsonSerializer.Deserialize<ProcessDefinitionSpec>(r.SpecJson)!)
            .ToList();
    }
}
