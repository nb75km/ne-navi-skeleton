import React from "react";

interface Props {
  transcriptId: number;
}

export default function ExportControls({ transcriptId }: Props) {
  const formats = ["markdown", "docx", "pdf", "html"] as const;

  const download = async (fmt: typeof formats[number]) => {
    const res = await fetch(
      `/minutes/api/transcripts/${transcriptId}/export?format=${fmt}`
    );
    if (!res.ok) {
      alert(`${fmt.toUpperCase()} のエクスポートに失敗しました`);
      return;
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript_${transcriptId}.${
      fmt === "markdown" ? "md" : fmt
    }`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-2">
      {formats.map((fmt) => (
        <button
          key={fmt}
          onClick={() => download(fmt)}
          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded"
        >
          {fmt.toUpperCase()} ダウンロード
        </button>
      ))}
    </div>
  );
}
