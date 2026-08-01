import { useState, useEffect, useCallback } from 'react';
import { apiGet, apiPost } from '../api/client';
import type { ProcessDefinitionSpec, CreateDefinitionRequest } from '../types/models';

export function useDefinitions() {
  const [defs, setDefs] = useState<ProcessDefinitionSpec[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setDefs(await apiGet<ProcessDefinitionSpec[]>('/definitions')); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async (req: CreateDefinitionRequest) => {
    await apiPost('/definitions', req);
    await load();
  };

  return { defs, loading, load, create };
}
