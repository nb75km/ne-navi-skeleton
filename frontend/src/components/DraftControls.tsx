import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

interface Props {
  transcriptId: number;
}

const MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"];

export default function DraftControls({ transcriptId }: Props) {
  const [model, setModel] = useState(MODELS[0]);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const triggerDraft = async () => {
    setLoading(true);
    try {
      const rsp = await fetch(`/minutes/api/${transcriptId}/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model }),
      });
      if (!rsp.ok) throw new Error(await rsp.text());
      const { task_id } = await rsp.json();
      setTaskId(task_id);
      alert("Draft generation queued! Task ID: " + task_id);
    } catch (err: any) {
      alert(err.message || err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <select
        value={model}
        onChange={(e) => setModel(e.target.value)}
        className="border rounded p-1 text-sm"
      >
        {MODELS.map((m) => (
          <option key={m}>{m}</option>
        ))}
      </select>

      <button
        onClick={triggerDraft}
        disabled={loading}
        className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1 text-sm shadow disabled:opacity-60"
      >
        {loading ? (
          <Loader2 className="animate-spin" size={16} />
        ) : (
          <Sparkles size={16} />
        )}
        Draft
      </button>

      {taskId && <span className="text-xs text-gray-500">{taskId}</span>}
    </div>
  );
}
