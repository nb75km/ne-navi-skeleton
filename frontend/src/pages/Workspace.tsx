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
import { ExportButton } from '../components/ExportButton';
import TranscriptToggle from '../components/TranscriptToggle';

import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import '@uiw/react-markdown-preview/markdown.css';
import remarkGfm from 'remark-gfm';

export interface ChatBotHandle {
  sendPrompt: (
    instruction: string
  ) => Promise<{ chatResponse: string; editedMinutes: string; versionNo: number }>;
  appendMessage: (role: 'assistant' | 'user', body: string) => void;
}

interface ChatBotPanelProps {
  content: string;
}

const ChatBotPanel = forwardRef<ChatBotHandle, ChatBotPanelProps>(
  ({ content }, ref) => {
    const [messages, setMessages] = useState<{ role: string; body: string }[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef<HTMLDivElement>(null);

    // 会話履歴を localStorage から復元
    useEffect(() => {
      const saved = localStorage.getItem('minutesMessages');
      if (saved) setMessages(JSON.parse(saved));
    }, []);

    // ローカル保存 & スクロール
    useEffect(() => {
      localStorage.setItem('minutesMessages', JSON.stringify(messages));
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const post = async (
      instruction: string
    ): Promise<{ chatResponse: string; editedMinutes: string; versionNo: number }> => {
      setMessages((m) => [...m, { role: 'user', body: instruction }]);
      setLoading(true);

      // 全文＋命令を組み合わせ
      const fullBody = [
        '以下は現在の議事録全文です。',
        'CONTENT_START',
        content,
        'CONTENT_END',
        '指示:',
        instruction,
      ].join('\n');

      try {
        const res = await fetch('/minutes/api/agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ body: fullBody }),
        });
        const data = await res.json();
        const { chatResponse, editedMinutes, versionNo } = data;
        setMessages((m) => [...m, { role: 'assistant', body: chatResponse }]);
        return { chatResponse, editedMinutes, versionNo };
      } catch (e: any) {
        const err = 'Error: ' + (e.message || e);
        setMessages((m) => [...m, { role: 'assistant', body: err }]);
        return { chatResponse: err, editedMinutes: '', versionNo: -1 };
      } finally {
        setLoading(false);
      }
    };

    const appendMessage = (role: 'assistant' | 'user', body: string) => {
      setMessages((m) => [...m, { role, body }]);
    };

    useImperativeHandle(
      ref,
      () => ({ sendPrompt: post, appendMessage }),
      []
    );

    const send = () => {
      if (!input.trim()) return;
      post(input.trim());
      setInput('');
    };

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
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
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
  }
);
ChatBotPanel.displayName = 'ChatBotPanel';

interface EditorProps {
  transcriptId: number;
  content: string | null;
  setContent: (c: string) => void;
  chatBotRef: RefObject<ChatBotHandle>;
}

function EditorPanel({
  transcriptId,
  content,
  setContent,
  chatBotRef,
}: EditorProps) {
  const [saving, setSaving] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [versionNo, setVersionNo] = useState<number | null>(null);

  useEffect(() => {
    json<any[]>(`/minutes/api/minutes_versions?transcript_id=${transcriptId}`).then(
      (v) => {
        if (v.length) {
          setVersionNo(v[0].version_no);
          setContent(v[0].markdown);
        } else {
          setVersionNo(null);
          setContent('# (no draft)');
        }
      }
    );
  }, [transcriptId, setContent]);

  const save = async () => {
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
    const instruction =
      mode === 'simplify'
        ? '以下の議事録をより簡潔に要約してください。'
        : '以下の議事録からTODOを抽出してください。';

    setAiLoading(true);
    try {
      const { chatResponse, editedMinutes, versionNo: newVer } =
        await chatBotRef.current!.sendPrompt(instruction);
      chatBotRef.current!.appendMessage('assistant', chatResponse);
      setContent(editedMinutes);
      if (newVer > 0) setVersionNo(newVer);
    } finally {
      setAiLoading(false);
    }
  };

  if (content === null) {
    return <Loader2 className="m-auto animate-spin" />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="border-b p-2 flex justify-between items-center bg-white sticky top-0 z-10">
        <h2 className="font-semibold text-gray-800">Minutes Editor</h2>
        <div className="flex gap-1">
          <div className="flex items-center space-x-4">
            <span className="text-xl font-bold">
              {versionNo !== null ? `Version ${versionNo}` : 'No Draft'}
            </span>
            <ExportButton versionId={versionNo ?? 0} />
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => askAI('simplify')}
              disabled={saving || aiLoading}
              className="flex items-center gap-1 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded px-2 py-1 disabled:opacity-60"
            >
              <Sparkles size={14} /> 簡潔に
            </button>
            <button
              onClick={() => askAI('todo')}
              disabled={saving || aiLoading}
              className="flex items-center gap-1 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded px-2 py-1 disabled:opacity-60"
            >
              <ListTodo size={14} /> TODO抽出
            </button>
            <button
              onClick={save}
              disabled={saving || aiLoading}
              className="text-sm bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1 disabled:opacity-60"
            >
              {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
            </button>
          </div>
        </div>
      </div>
      <div className="relative flex-1 overflow-hidden h-full">
        <MDEditor
          value={content}
          onChange={(v) => setContent(v ?? '')}
          preview="live"
          previewOptions={{
            remarkPlugins: [remarkGfm],
            className: 'h-full overflow-auto w-md-editor-preview',
            style: { height: '100%' },
          }}
          textareaProps={{
            readOnly: aiLoading,
            className: 'text-gray-900 bg-white h-full w-md-editor-text',
            style: { height: '100%' },
          }}
        />
        {aiLoading && (
          <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10">
            <Loader2 className="animate-spin" size={24} />
            <span className="ml-2 text-lg text-gray-700">AI応答待ち…</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Workspace() {
  const { tid } = useParams<{ tid: string }>();
  const [content, setContent] = useState<string | null>(null);
  const chatBotRef = useRef<ChatBotHandle>(null);

  if (!tid) return <p className="p-4 text-red-500">no transcriptId</p>;

  return (
    <div className="h-screen flex">
      <ResizableTwoPane
        left={<ChatBotPanel content={content ?? ''} ref={chatBotRef} />}
        right={
          <EditorPanel
            transcriptId={parseInt(tid, 10)}
            content={content}
            setContent={setContent}
            chatBotRef={chatBotRef}
          />
        }
      />
      <TranscriptToggle transcriptId={parseInt(tid, 10)} />
    </div>
  );
}
