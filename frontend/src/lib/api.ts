const API_BASE = import.meta.env.VITE_BACKEND_BASE || "";

export async function json<T>(path: string): Promise<T> {
  const rsp = await fetch(`${API_BASE}${path}`);
  if (!rsp.ok) throw new Error(await rsp.text());
  return await rsp.json();
}
