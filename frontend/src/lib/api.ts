// ---------------------------------------------------------------------------
// frontend/src/lib/api.ts
// ---------------------------------------------------------------------------
const API_BASE = import.meta.env.VITE_BACKEND_BASE || "";

/* ---------- 共通ヘルパ ---------- */
export async function json<T = any>(path: string): Promise<T> {
  const rsp = await fetch(`${API_BASE}${path}`);
  if (!rsp.ok) throw new Error(await rsp.text());
  return await rsp.json();
}

/* ---------- Chat ---------- */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
export interface ChatResponse {
  assistant_message: string;
  version_id: number;
  markdown: string;
}

/** Minutes Chat API */
export async function postChat(
  transcriptId: number,
  body: { messages: ChatMessage[]; user_input: string }
): Promise<ChatResponse> {
  const res = await fetch(
    `/minutes/api/minutes_chat/${transcriptId}`, // ← /minutes プレフィックス付きに修正
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ChatResponse;
}
