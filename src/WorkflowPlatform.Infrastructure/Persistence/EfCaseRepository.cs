using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Domain.Cases;

namespace WorkflowPlatform.Infrastructure.Persistence;

/// <summary>ICaseRepository trên EF Core. Dùng IDbContextFactory vì repo là singleton (DbContext là scoped).</summary>
public sealed class EfCaseRepository : ICaseRepository
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public EfCaseRepository(IDbContextFactory<AppDbContext> factory) => _factory = factory;

    public void Add(Case @case)
    {
        using var ctx = _factory.CreateDbContext();
        ctx.Cases.Add(ToRecord(@case));
        ctx.SaveChanges();
    }

    public void Save(Case @case)
    {
        using var ctx = _factory.CreateDbContext();
        var record = ctx.Cases.Find(@case.Id);
        if (record is null) { ctx.Cases.Add(ToRecord(@case)); }
        else
        {
            record.Title = @case.Title;
            record.Content = @case.Content;
            record.Status = @case.Status.ToString();
        }
        ctx.SaveChanges();
    }

    public Case? Get(Guid id)
    {
        using var ctx = _factory.CreateDbContext();
        var r = ctx.Cases.AsNoTracking().FirstOrDefault(x => x.Id == id);
        return r is null ? null : ToDomain(r);
    }

    public IReadOnlyList<Case> All()
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.Cases.AsNoTracking().ToList().Select(ToDomain).ToList();
    }

    private static CaseRecord ToRecord(Case c) => new()
    {
        Id = c.Id, Title = c.Title, Content = c.Content, Status = c.Status.ToString(), CreatedAt = c.CreatedAt
    };

    private static Case ToDomain(CaseRecord r)
        => Case.Rehydrate(r.Id, r.Title, r.Content, Enum.Parse<CaseStatus>(r.Status), r.CreatedAt);
}
