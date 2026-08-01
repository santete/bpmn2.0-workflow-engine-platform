import { useState, useEffect, useCallback } from 'react';
import { apiGet, apiPost } from '../api/client';
import type { CaseView, CreateCaseRequest, CompleteTaskRequest } from '../types/models';

export function useCases() {
  const [cases, setCases] = useState<CaseView[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setCases(await apiGet<CaseView[]>('/cases')); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async (req: CreateCaseRequest) => {
    await apiPost('/cases', req);
    await load();
  };

  const complete = async (id: string, taskId: string, decision?: string) => {
    const c = cases.find(x => x.id === id);
    const opts: RequestInit = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
    const user = (document.getElementById('actor-name') as HTMLInputElement)?.value?.trim();
    if (user) (opts.headers as Record<string, string>)['X-User'] = user;
    if (c?.version) (opts.headers as Record<string, string>)['If-Match'] = `"${c.version}"`;
    const body: CompleteTaskRequest & { decision?: string } = { taskId };
    if (decision) body.decision = decision;
    const r = await fetch(`/cases/${id}/complete-task`, { ...opts, body: JSON.stringify(body) });
    if (r.status === 403) return alert('Bạn không phải người được phân công cho bước này.');
    if (r.status === 412) return alert('Hồ sơ đã bị thay đổi bởi người khác. Vui lòng tải lại.');
    await load();
  };

  const cancel = async (id: string) => {
    if (!confirm('Hủy hồ sơ này?')) return;
    await apiPostRaw(`/cases/${id}/cancel`);
    await load();
  };

  return { cases, loading, load, create, complete, cancel };
}
