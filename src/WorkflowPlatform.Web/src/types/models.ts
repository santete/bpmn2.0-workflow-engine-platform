export interface ProcessDefinitionSpec {
  key: string;
  name: string;
  steps: StepSpec[];
  endsWithDecision: boolean;
}

export interface StepSpec {
  id: string;
  name: string;
  assignee?: string;
  counterSigner?: string;
}

export interface CaseView {
  id: string;
  title: string;
  definitionKey: string;
  businessStatus: string;
  workflowStatus: string;
  currentTaskId?: string;
  currentTaskName?: string;
  currentTaskAssignee?: string;
  version: string;
  owner?: string;
  pendingCounterSign: boolean;
  counterSigner?: string;
}

export interface CaseHistoryEntry {
  caseId: string;
  kind: 'TaskCompleted' | 'ProcessCompleted' | 'ProcessRejected' | 'ProcessCancelled';
  taskId?: string;
  taskName?: string;
  actor?: string;
  decision?: string;
  occurredAt: string;
}

export interface ProcessStateView {
  businessKey: string;
  definitionKey: string;
  status: string;
  activeTasks: { taskId: string; name: string }[];
}

export interface CreateDefinitionRequest {
  name: string;
  steps: string[];
  endsWithDecision: boolean;
  assignees?: (string | null)[];
}

export interface CreateCaseRequest {
  title: string;
  definitionKey?: string;
}

export interface CompleteTaskRequest {
  taskId: string;
  decision?: string;
}
