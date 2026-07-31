using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Infrastructure.Persistence;

public sealed class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<CaseRecord> Cases => Set<CaseRecord>();
    public DbSet<CaseView> CaseViews => Set<CaseView>();
    public DbSet<ReplayInstanceRecord> ReplayInstances => Set<ReplayInstanceRecord>();
    public DbSet<ReplayCompletionRecord> ReplayCompletions => Set<ReplayCompletionRecord>();
    public DbSet<ProcessDefinitionRecord> ProcessDefinitions => Set<ProcessDefinitionRecord>();
    public DbSet<CaseHistoryRecord> CaseHistories => Set<CaseHistoryRecord>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<CaseRecord>().HasKey(x => x.Id);
        b.Entity<CaseView>().HasKey(x => x.Id);                 // read model persist trực tiếp
        b.Entity<ReplayInstanceRecord>().HasKey(x => x.BusinessKey);
        b.Entity<ReplayCompletionRecord>().HasKey(x => x.Id);
        b.Entity<ReplayCompletionRecord>().HasIndex(x => new { x.BusinessKey, x.Seq });
        b.Entity<ProcessDefinitionRecord>().HasKey(x => x.Key);
        b.Entity<CaseHistoryRecord>().HasKey(x => x.Id);
        b.Entity<CaseHistoryRecord>().HasIndex(x => new { x.CaseId, x.Id });
    }
}
