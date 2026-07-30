namespace WorkflowPlatform.Domain.Abstractions;

/// <summary>Sự kiện nghiệp vụ phát ra từ domain. Không mang dấu vết hạ tầng.</summary>
public interface IDomainEvent
{
    DateTimeOffset OccurredAt { get; }
}
