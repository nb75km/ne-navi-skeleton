// ---------------------------------------------------------------------------
// frontend/src/pages/Workspace.tsx  – バージョン切替 & AI 編集 対応版
// ---------------------------------------------------------------------------
import React, {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
  RefObject,
} from 'react';
import { useParams } from 'react-router-dom';
import {
  Loader2,
  Send,
  Save,
  Sparkles,
  ListTodo,
  Wand2,
} from 'lucide-react';
import { json } from '../lib/api';
import { ResizableTwoPane } from '../components/ResizableTwoPane';
import { ExportButton } from '../components/ExportButton';
import VersionSelector from '../components/VersionSelector';
import {
  useMinutesVersions,
  MinutesVersion,
} from '../lib/useMinutesVersions';

import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import '@uiw/react-markdown-preview/markdown.css';
import remarkGfm from 'remark-gfm';

/* -------------------------------------------------------------------------
 * ChatBotPanel – 既存実装を保持
 * ----------------------------------------------------------------------*/
export interface ChatBotHandle {
  sendPrompt: (body: string) => Promise<void>;
}

const ChatBotPanel = forwardRef<ChatBotHandle, { content: () => string }>(
  ({ content }, ref) => {
    const [messages, setMessages] = useState<{ role: string; body: string }[]>(
      []
    );
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const post = async (body: string) => {
      setMessages((m) => [...m, { role: 'user', body }]);
      setLoading(true);

      // Minutes全文をプロンプトに含めて送信
      const full = [
        'CONTENT_START',
        content(),
        'CONTENT_END',
        'INSTRUCTION:',
        body,
      ].join('\n');

      try {
        const res = await fetch('/minutes/api/agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ body: full }),
        });
        const data = await res.json();
        setMessages((m) => [
          ...m,
          { role: 'assistant', body: data.body ?? data.chatResponse ?? '(no resp)' },
        ]);
      } catch (e: any) {
        setMessages((m) => [
          ...m,
          { role: 'assistant', body: 'Error: ' + (e.message || e) },
        ]);
      } finally {
        setLoading(false);
      }
    };

    useImperativeHandle(ref, () => ({ sendPrompt: post }), []);

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
            {loading ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
      </div>
    );
  }
);
ChatBotPanel.displayName = 'ChatBotPanel';

/* -------------------------------------------------------------------------
 * EditorPanel – ここにバージョン切替 & AI 編集を追加
 * ----------------------------------------------------------------------*/
interface EditorProps {
  transcriptId: number;
  chatBotRef: RefObject<ChatBotHandle>;
}

function EditorPanel({ transcriptId, chatBotRef }: EditorProps) {
  const { versions, loading: versionsLoading, reload } =
    useMinutesVersions(transcriptId);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [content, setContent] = useState<string>('');
  const [saving, setSaving] = useState(false);

  /* 初期ロード & バージョン変更 */
  useEffect(() => {
    if (!versionsLoading && versions.length && selectedId === null) {
      setSelectedId(versions[0].id);
    }
  }, [versionsLoading, versions, selectedId]);

  useEffect(() => {
    if (selectedId !== null) {
      const v = versions.find((v) => v.id === selectedId);
      if (v) setContent(v.markdown);
    }
  }, [selectedId, versions]);

  /* 保存 (新規バージョン) */
  const saveAsNew = async () => {
    if (!content.trim()) return;
    setSaving(true);
    await fetch(`/minutes/api/minutes_versions?transcript_id=${transcriptId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: content }),
    });
    setSaving(false);
    reload();
  };

  /* AI 編集 → backend /ai_edit */
  const aiEdit = async () => {
    if (selectedId === null) return alert('バージョンが選択されていません');
    const instruction = window.prompt('AI への編集指示を入力してください');
    if (!instruction) return;
    setSaving(true);
    const rsp = await fetch(`/minutes/api/minutes_versions/${selectedId}/ai_edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction }),
    });
    setSaving(false);
    if (!rsp.ok) {
      return alert('AI 編集に失敗しました:\n' + (await rsp.text()));
    }
    reload();
  };

  if (versionsLoading && versions.length === 0) {
    return <Loader2 className="m-auto animate-spin" />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* header */}
      <div className="border-b p-2 flex flex-wrap items-center gap-2 bg-white sticky top-0 z-10">
        <VersionSelector
          versions={versions}
          value={selectedId}
          onChange={(id) => setSelectedId(id)}
        />
        <ExportButton versionId={selectedId ?? 0} />
        <button
          onClick={aiEdit}
          className="flex items-center gap-1 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded px-2 py-1"
        >
          <Wand2 size={14} /> AI Edit
        </button>
        <button
          onClick={saveAsNew}
          disabled={saving}
          className="text-sm bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1 disabled:opacity-60"
        >
          {saving ? (
            <Loader2 className="animate-spin" size={16} />
          ) : (
            <Save size={16} />
          )}
          Save as New
        </button>
      </div>

      {/* editor */}
      <div className="relative flex-1 overflow-hidden h-full">
        <MDEditor
          height="100%"
          className="h-full w-md-editor"
          value={content}
          onChange={(v) => setContent(v ?? '')}
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

/* -------------------------------------------------------------------------
 * Workspace – Two‑pane レイアウト
 * ----------------------------------------------------------------------*/
export default function Workspace() {
  const { tid } = useParams<{ tid: string }>();
  const minutesRef = useRef<string>('');
  const chatBotRef = useRef<ChatBotHandle>(null);

  // Memoize current minutes for ChatBotPanel prompt
  const setMinutes = (m: string) => {
    minutesRef.current = m;
  };

  if (!tid) return <p className="p-4 text-red-500">no transcriptId</p>;

  return (
    <div className="h-screen flex">
      <ResizableTwoPane
        left={<ChatBotPanel ref={chatBotRef} content={() => minutesRef.current} />}
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
