const BASE = '';

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  const user = (document.getElementById('actor-name') as HTMLInputElement)?.value?.trim();
  if (user) h['X-User'] = user;
  return h;
}

export async function apiGet<T>(url: string): Promise<T> {
  const r = await fetch(BASE + url, { headers: headers() });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(BASE + url, {
    method: 'POST',
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export async function apiPostRaw(url: string, body?: unknown): Promise<Response> {
  const r = await fetch(BASE + url, {
    method: 'POST',
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  return r;
}
