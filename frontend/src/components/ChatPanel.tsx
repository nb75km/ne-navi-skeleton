import React, { useState } from "react";
import { ChatMessage, postChat } from "../lib/api";

interface Props {
  transcriptId: number;
  onMinutesUpdate: (markdown: string, versionId: number) => void;
}

const ChatPanel: React.FC<Props> = ({
  transcriptId,
  onMinutesUpdate,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    setInput("");

    const next = [...messages, { role: "user", content: text }];
    setMessages(next);

    try {
      const res = await postChat(transcriptId, {
        messages: next.filter((m) => m.role === "user"),
        user_input: text,
      });
      setMessages([
        ...next,
        { role: "assistant", content: res.assistant_message },
      ]);
      onMinutesUpdate(res.markdown, res.version_id);
    } catch (e) {
      console.error(e);
      setMessages([
        ...next,
        { role: "assistant", content: "⚠️ エラーが発生しました。" },
      ]);
    }
  };

  return (
    <div className="flex flex-col h-full border-l border-gray-200">
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : ""}`}>
            <div
              className={`px-3 py-2 rounded-2xl text-sm shadow-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-emerald-500 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
      </div>
      <div className="flex border-t border-gray-200">
        <input
          className="flex-1 px-3 py-2 text-sm outline-none"
          placeholder="AI に指示を入力..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          className="px-4 text-white bg-emerald-600 disabled:opacity-40"
          onClick={send}
          disabled={!input.trim()}
        >
          送信
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
