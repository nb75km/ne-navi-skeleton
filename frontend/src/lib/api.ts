const API_BASE = import.meta.env.VITE_BACKEND_BASE || "";

// 既存 import 群...
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  assistant_message: string;
  version_id: number;
  markdown: string;
}


export async function json<T>(path: string): Promise<T> {
  const rsp = await fetch(`${API_BASE}${path}`);
  if (!rsp.ok) throw new Error(await rsp.text());
  return await rsp.json();
}

export async function postChat(
  transcriptId: number,
  body: { messages: ChatMessage[]; user_input: string }
) {
  const res = await fetch(`/api/minutes_chat/${transcriptId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = (await res.json()) as ChatResponse;
  return data;
}
