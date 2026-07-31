using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;

namespace WorkflowPlatform.Workflow.Abstraction;

/// <summary>
/// Driven port (SPI) — mỗi engine BPMN hiện thực interface này. Đổi engine = viết adapter mới,
/// domain bất biến. Adapter chịu trách nhiệm dịch (ACL) mô hình/ lỗi engine ↔ canonical.
/// </summary>
public interface IEngineAdapter
{
    /// <summary>Tên engine (phục vụ chẩn đoán / kiểm chứng engine-swap).</summary>
    string EngineName { get; }

    void Deploy(CanonicalBpmn bpmn);

    /// <summary>Khởi tạo tiến trình; trả về các sự kiện canonical phát sinh.</summary>
    IReadOnlyList<WorkflowEvent> Start(StartProcessCommand command);

    /// <summary>Hoàn thành user task; trả về các sự kiện canonical phát sinh.</summary>
    IReadOnlyList<WorkflowEvent> CompleteTask(CompleteTaskCommand command);

    /// <summary>Hủy tiến trình đang chạy; trả về sự kiện ProcessCancelled.</summary>
    IReadOnlyList<WorkflowEvent> Cancel(string businessKey);

    ProcessStateView GetState(string businessKey);
}
