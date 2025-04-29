import { FileText } from "lucide-react";

/**
 * ViewTranscriptButton – fetches transcript JSON and opens its raw text in a new tab.
 */
export default function ViewTranscriptButton({ transcriptId }: { transcriptId: string }) {
  const handleClick = async () => {
    if (!transcriptId) return;
    const apiPrefix = import.meta.env.VITE_API_BASE_URL || "/minutes/api";
    try {
      const res = await fetch(`${apiPrefix}/transcripts/${transcriptId}`);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const { content } = await res.json();
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(url), 1000 * 60); // cleanup after 1min
    } catch (err) {
      alert(`Failed to load transcript: ${err}`);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 text-sm bg-gray-200 hover:bg-gray-300 rounded px-3 py-1"
    >
      <FileText size={16} /> スクリプト
    </button>
  );
}
