using WorkflowPlatform.Domain.Abstractions;

namespace WorkflowPlatform.Domain.Cases.Events;

public sealed record CaseCreated(Guid CaseId, string Title, DateTimeOffset OccurredAt) : IDomainEvent;
