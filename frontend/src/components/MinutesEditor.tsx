import { useState } from "react";
import { Loader2, Save, X } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  transcriptId: number;
  currentMarkdown: string;
  onSaved: () => void;
  onCancel: () => void;
}

export default function MinutesEditor({
  transcriptId,
  currentMarkdown,
  onSaved,
  onCancel,
}: Props) {
  const [md, setMd] = useState(currentMarkdown);
  const [saving, setSaving] = useState(false);

  /* 保存 */
  const submit = async () => {
    if (md.trim().length < 10) {
      alert("内容が短すぎます");
      return;
    }
    setSaving(true);
    try {
      const rsp = await fetch(
        `/minutes/api/minutes_versions?transcript_id=${transcriptId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ markdown: md }),
        }
      );
      if (!rsp.ok) throw new Error(await rsp.text());
      onSaved();
    } catch (e: any) {
      alert(e.message || e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-5xl rounded-lg shadow-xl p-4 flex flex-col gap-3">
        {/* 編集エリア + プレビュー */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-[60vh]">
          <textarea
            value={md}
            onChange={(e) => setMd(e.target.value)}
            className="w-full h-full font-mono text-sm bg-white border rounded p-3 resize-none outline-none"
          />
          <div className="prose prose-sm max-w-none overflow-auto border rounded p-3 bg-white">
            <ReactMarkdown>{md}</ReactMarkdown>
          </div>
        </div>

        {/* 操作ボタン */}
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-3 py-1 bg-gray-200 rounded flex items-center gap-1"
          >
            <X size={16} /> Cancel
          </button>
          <button
            onClick={submit}
            disabled={saving}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-1 disabled:opacity-60"
          >
            {saving ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Save size={16} />
            )}
            Save as New Version
          </button>
        </div>
      </div>
    </div>
  );
}
