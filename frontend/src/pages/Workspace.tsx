// frontend/src/pages/Workspace.tsx

import React, {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
  RefObject,
} from 'react';
import { useParams } from 'react-router-dom';
import { Loader2, Send, Save, Sparkles, ListTodo } from 'lucide-react';
import { json } from '../lib/api';
import { ResizableTwoPane } from '../components/ResizableTwoPane';

import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import '@uiw/react-markdown-preview/markdown.css';
import remarkGfm from 'remark-gfm';

/* ---------- Chat (左カラム) ---------- */
export interface ChatBotHandle {
  sendPrompt: (body: string) => Promise<void>;
}

const ChatBotPanel = forwardRef<ChatBotHandle>((_, ref) => {
  const [messages, setMessages] = useState<{ role: string; body: string }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const post = async (body: string) => {
    setMessages(m => [...m, { role: 'user', body }]);
    setLoading(true);
    try {
      const res = await fetch('/minutes/api/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body }),
      });
      const data = await res.json();
      setMessages(m => [
        ...m,
        { role: 'assistant', body: data.body ?? data.assistant?.body },
      ]);
    } catch (e: any) {
      setMessages(m => [
        ...m,
        { role: 'assistant', body: 'Error: ' + (e.message || e) },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const send = () => {
    if (!input.trim()) return;
    post(input.trim());
    setInput('');
  };

  useImperativeHandle(ref, () => ({ sendPrompt: post }), []);

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === 'user'
                ? 'self-end bg-blue-600 text-white rounded-lg px-3 py-2 max-w-xs'
                : 'self-start bg-gray-100 text-gray-900 rounded-lg px-3 py-2 max-w-xs'
            }
          >
            {m.body}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="border-t p-2 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          className="flex-1 border rounded px-3 py-2"
          placeholder="Ask anything…"
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-3 rounded disabled:opacity-60"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
});
ChatBotPanel.displayName = 'ChatBotPanel';

/* ---------- Editor (右カラム) ---------- */
interface EditorProps {
  transcriptId: number;
  chatBotRef: RefObject<ChatBotHandle>;
}
function EditorPanel({ transcriptId, chatBotRef }: EditorProps) {
  const [content, setContent] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  /* 初期ドラフト取得 */
  useEffect(() => {
    json<any[]>(
      `/minutes/api/minutes_versions?transcript_id=${transcriptId}`
    ).then(v => setContent(v.length ? v[0].markdown : '# (no draft)'));
  }, [transcriptId]);

  const save = async () => {
    if (content === null) return;
    setSaving(true);
    await fetch(`/minutes/api/minutes_versions?transcript_id=${transcriptId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: content }),
    });
    setSaving(false);
    alert('Saved!');
  };

  const askAI = async (mode: 'simplify' | 'todo') => {
    if (!content) return;
    const prompt =
      mode === 'simplify'
        ? `以下の議事録をより簡潔に要約してください。\n\n${content}`
        : `以下の議事録から今後のアクションアイテム (TODO) を箇条書きで抽出してください。\n\n${content}`;
    await chatBotRef.current?.sendPrompt(prompt);
  };

  if (content === null) {
    return <Loader2 className="m-auto animate-spin" />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* header */}
      <div className="border-b p-2 flex justify-between items-center bg-white sticky top-0 z-10">
        <h2 className="font-semibold text-gray-800">Minutes Editor</h2>
        <div className="flex gap-1">
          <button
            onClick={() => askAI('simplify')}
            className="flex items-center gap-1 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded px-2 py-1"
          >
            <Sparkles size={14} /> 簡潔に
          </button>
          <button
            onClick={() => askAI('todo')}
            className="flex items-center gap-1 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded px-2 py-1"
          >
            <ListTodo size={14} />
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="text-sm bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1 disabled:opacity-60"
          >
            {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
          </button>
        </div>
      </div>

      {/* editor */}
      <div className="relative flex-1 overflow-hidden h-full">
        <MDEditor
          height="100%"
          className="h-full w-md-editor"
          value={content}
          onChange={v => setContent(v ?? '')}
          preview="live"
          previewOptions={{
            remarkPlugins: [remarkGfm],
            className: 'h-full overflow-auto w-md-editor-preview',
            style: { height: '100%' },
          }}
          textareaProps={{
            className: 'text-gray-900 bg-white h-full w-md-editor-text',
            style: { height: '100%' },
          }}
        />
      </div>
    </div>
  );
}

/* ---------- Workspace ---------- */
export default function Workspace() {
  const { tid } = useParams<{ tid: string }>();
  const chatBotRef = useRef<ChatBotHandle>(null);

  if (!tid) return <p className="p-4 text-red-500">no transcriptId</p>;

  return (
    <div className="h-screen flex">
      <ResizableTwoPane
        left={<ChatBotPanel ref={chatBotRef} />}
        right={
          <EditorPanel
            transcriptId={parseInt(tid, 10)}
            chatBotRef={chatBotRef}
          />
        }
      />
    </div>
  );
}
