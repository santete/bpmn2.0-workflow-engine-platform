using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Infrastructure.Persistence;

public sealed class EfCaseReadStore : ICaseReadStore
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public EfCaseReadStore(IDbContextFactory<AppDbContext> factory) => _factory = factory;

    public void Upsert(CaseView view)
    {
        using var ctx = _factory.CreateDbContext();
        var existing = ctx.CaseViews.Find(view.Id);
        if (existing is null)
        {
            ctx.CaseViews.Add(view);
        }
        else
        {
            existing.Title = view.Title;
            existing.BusinessStatus = view.BusinessStatus;
            existing.WorkflowStatus = view.WorkflowStatus;
            existing.CurrentTaskId = view.CurrentTaskId;
            existing.CurrentTaskName = view.CurrentTaskName;
        }
        ctx.SaveChanges();
    }

    public CaseView? Get(Guid id)
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.CaseViews.AsNoTracking().FirstOrDefault(v => v.Id == id);
    }

    public IReadOnlyList<CaseView> All()
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.CaseViews.AsNoTracking().ToList();
    }
}
