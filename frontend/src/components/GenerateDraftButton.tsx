import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function GenerateDraftButton({ transcriptId }: { transcriptId: number }) {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const generate = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/minutes/api/${transcriptId}/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "gpt-4o-mini" }),
      });
      if (!r.ok) throw new Error(await r.text());
      // Whisper + Draft が終わるまで 5 秒ほど待機して Workspace へ
      setTimeout(() => navigate(`/workspace/${transcriptId}`), 5000);
    } catch (e: any) {
      alert(e.message || e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={generate}
      disabled={loading}
      className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1 disabled:opacity-60"
    >
      {loading ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
      Draft を生成
    </button>
  );
}
