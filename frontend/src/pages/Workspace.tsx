// ---------------------------------------------------------------------------
// frontend/src/pages/Workspace.tsx – バージョン切替 & モデル選択
// ---------------------------------------------------------------------------
import React, {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";
import { useParams, Link } from "react-router-dom";
import { Loader2, Send, Save, Wand2, GitCompare } from "lucide-react";

import { ResizableTwoPane } from "../components/ResizableTwoPane";
import { ExportButton } from "../components/ExportButton";
import VersionSelector from "../components/VersionSelector";
import ModelSelector from "../components/ModelSelector";
import ViewTranscriptButton from "../components/ViewTranscriptButton";
import { useMinutesVersions } from "../lib/useMinutesVersions";
import { ChatMessage, postChat } from "../lib/api";

import MDEditor from "@uiw/react-md-editor";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";
import remarkGfm from "remark-gfm";

/* -------------------------------------------------------------------------
 * ChatBotPanel
 * ----------------------------------------------------------------------*/
export interface ChatBotHandle {
  sendPrompt: (body: string) => Promise<void>;
}

const ChatBotPanel = forwardRef<
  ChatBotHandle,
  { content: () => string; model: string }
>(({ content, model }, ref) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const post = async (body: string) => {
    const next = [...messages, { role: "user", content: body }];
    setMessages(next);
    setLoading(true);

    try {
      const res = await postChat((window as any).__CURRENT_TID__, {
        messages: next.filter((m) => m.role === "user"),
        user_input: body,
        model,
      });

      setMessages([
        ...next,
        { role: "assistant", content: res.assistant_message },
      ]);

      if (res.markdown) {
        (window as any).__ON_MARKDOWN_UPDATE__(res.markdown, res.version_id);
      }
    } catch (e: any) {
      setMessages([
        ...next,
        { role: "assistant", content: `Error: ${e?.message || e}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useImperativeHandle(ref, () => ({ sendPrompt: post }), [messages]);

  const send = () => {
    if (!input.trim()) return;
    post(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* chat log */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "self-end bg-blue-600 text-white rounded-lg px-3 py-2 max-w-xs"
                : "self-start bg-gray-100 text-gray-900 rounded-lg px-3 py-2 max-w-xs"
            }
          >
            {m.content}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* input */}
      <div className="border-t p-2 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          onInput={(e) => {
            const el = e.currentTarget;
            el.style.height = "auto";
            el.style.height = `${el.scrollHeight}px`;
          }}
          rows={1}
          className="flex-1 border rounded px-3 py-2 resize-none leading-6"
          style={{ maxHeight: "160px", overflowY: "auto" }}
          placeholder="Enter で改行 / Shift+Enter で送信"
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-3 rounded disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="animate-spin" size={16} />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>
    </div>
  );
});
ChatBotPanel.displayName = "ChatBotPanel";

/* -------------------------------------------------------------------------
 * EditorPanel
 * ----------------------------------------------------------------------*/
interface EditorProps {
  transcriptId: number;
  model: string;
  setModel: (m: string) => void;
  onMinutesChange: (md: string, vid: number) => void;
}

function EditorPanel({
  transcriptId,
  model,
  setModel,
  onMinutesChange,
}: EditorProps) {
  const { versions, loading, reload } = useMinutesVersions(transcriptId);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [content, setContent] = useState("");

  useEffect(() => {
    if (!loading && versions.length && selectedId === null) {
      setSelectedId(versions[0].id);
    }
  }, [loading, versions, selectedId]);

  useEffect(() => {
    const v = versions.find((v) => v.id === selectedId);
    if (v) setContent(v.markdown);
  }, [selectedId, versions]);

  useEffect(() => {
    if (selectedId !== null) onMinutesChange(content, selectedId);
  }, [content, onMinutesChange, selectedId]);

  const saveAsNew = async () => {
    await fetch(`/minutes/api/minutes_versions?transcript_id=${transcriptId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown: content }),
    });
    await reload();
  };

  const aiEdit = async () => {
    if (!selectedId) return;
    const instruction = window.prompt("AI への編集指示を入力");
    if (!instruction) return;
    await fetch(`/minutes/api/minutes_versions/${selectedId}/ai_edit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction, model }),
    });
    await reload();
  };

  if (loading && !versions.length) {
    return <Loader2 className="m-auto animate-spin" />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="border-b p-2 flex flex-wrap items-center gap-2 bg-white">
        <VersionSelector
          versions={versions.map((v) => ({
            id: v.id,
            label: `ver${v.version_no}`,
          }))}
          current={selectedId}
          onChange={setSelectedId}
        />
        <ModelSelector value={model} onChange={setModel} /> {/* ←唯一のセレクター */}
        <ViewTranscriptButton transcriptId={String(transcriptId)} />
        <ExportButton versionId={selectedId ?? 0} />
        <Link
          to={`/minutes/${transcriptId}/diff`}
          className="flex items-center gap-1 text-sm bg-gray-200 hover:bg-gray-300 rounded px-3 py-1"
        >
          <GitCompare size={16} /> Diff
        </Link>
        <button
          onClick={aiEdit}
          className="flex items-center gap-1 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded px-2 py-1"
        >
          <Wand2 size={14} /> AI Edit
        </button>
        <button
          onClick={saveAsNew}
          className="flex items-center gap-1 text-sm bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1"
        >
          <Save size={16} /> Save as New
        </button>
      </div>

      <MDEditor
        height="100%"
        value={content}
        onChange={(v) => setContent(v ?? "")}
        preview="live"
        previewOptions={{ remarkPlugins: [remarkGfm] }}
      />
    </div>
  );
}

/* -------------------------------------------------------------------------
 * Workspace (Two-pane)
 * ----------------------------------------------------------------------*/
export default function Workspace() {
  const { tid } = useParams<{ tid: string }>();
  if (!tid) return <p className="p-4 text-red-500">no transcriptId</p>;

  (window as any).__CURRENT_TID__ = Number(tid);

  const [model, setModel] = useState("gpt-4o-mini");

  const handleMinutesChange = (md: string, vid: number) => {
    (window as any).__ON_MARKDOWN_UPDATE__?.(md, vid);
  };

  return (
    <div className="h-screen flex">
      <ResizableTwoPane
        left={
          <ChatBotPanel
            content={() => (window as any).__CURRENT_CONTENT__ || ""}
            model={model}
            ref={(ref) => {
              (window as any).__ON_MARKDOWN_UPDATE__ = (
                md: string,
                vid: number
              ) => {
                (window as any).__CURRENT_CONTENT__ = md;
              };
            }}
          />
        }
        right={
          <EditorPanel
            transcriptId={Number(tid)}
            model={model}
            setModel={setModel}
            onMinutesChange={(md, vid) => {
              (window as any).__CURRENT_CONTENT__ = md;
              handleMinutesChange(md, vid);
            }}
          />
        }
      />
    </div>
  );
}
