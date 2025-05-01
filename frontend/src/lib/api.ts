/**
 * src/lib/api.ts  —  Cookie Transport 用共通 API ライブラリ
 * --------------------------------------------------------
 * FastAPI-Users の Cookie JWT に合わせて
 *   · fetch には常に `credentials:"include"`
 *   · JSON か x-www-form-urlencoded を自動判別
 *   · 204 → null, error → Error(message)
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

/* ------------------------------------------------------------------ */
/* 汎用リクエスト                                                      */
/* ------------------------------------------------------------------ */
async function request<T = unknown>(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
  extra: RequestInit = {},
): Promise<T> {
  const init: RequestInit = {
    method,
    credentials: "include", // ← Cookie を必ず送る
    headers: { ...(extra.headers ?? {}) },
    ...extra,
  };

  /* 送信形式の自動判定 */
  if (body !== undefined) {
    if (body instanceof URLSearchParams || body instanceof FormData) {
      // フォーム系 → fetch が Content-Type を自動付与
      init.body = body;
    } else {
      // JSON
      init.headers = { "Content-Type": "application/json", ...init.headers };
      init.body = JSON.stringify(body);
    }
  }

  const res = await fetch(`${API_BASE}${path}`, init);

  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null as unknown as T;

  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  } else {
    return (await res.text()) as unknown as T;
  }
}

/* ------------------------------------------------------------------ */
/* メソッド別ショートハンド                                            */
/* ------------------------------------------------------------------ */
export const api = {
  get:    <T = unknown>(p: string, i?: RequestInit) => request<T>("GET",    p, undefined, i),
  post:   <T = unknown>(p: string, b?: unknown)     => request<T>("POST",   p, b),
  put:    <T = unknown>(p: string, b?: unknown)     => request<T>("PUT",    p, b),
  patch:  <T = unknown>(p: string, b?: unknown)     => request<T>("PATCH",  p, b),
  delete: <T = unknown>(p: string)                 => request<T>("DELETE", p),
};

/* 旧 `{ json }` 互換 */
export const json = api.get;

/* ------------------------------------------------------------------ */
/* アプリ固有エンドポイント                                            */
/* ------------------------------------------------------------------ */

/* === Chat === */
export const postChat = (params: {
  title: string;
  messages: { role: "user" | "system" | "assistant"; content: string }[];
}) => api.post<{ reply: string }>("/chat", params);

/* === Minutes === */
export const fetchMinutes = () =>
  api.get<{ id: number; title: string; created_at: string }[]>("/minutes");

export const createMinutes = (payload: { title: string; body: string }) =>
  api.post<{ id: number }>("/minutes", payload);

export const getMinutes = (id: number) =>
  api.get<{ id: number; title: string; body: string; created_at: string }>(
    `/minutes/${id}`,
  );

export const updateMinutes = (
  id: number,
  payload: { title: string; body: string },
) => api.put<null>(`/minutes/${id}`, payload);

export const deleteMinutes = (id: number) => api.delete<null>(`/minutes/${id}`);

/* === 公開エンドポイント === */
export const ping = () => api.get<string>("/ping");
export const getMe = () => api.get<{ id: string; email: string }>("/minutes/users/me");