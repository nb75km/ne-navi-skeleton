import React, { useState } from "react";
import Modal from "./ui/Modal";

interface Props {
  transcriptId: number;
}

export default function TranscriptControls({ transcriptId }: Props) {
  const [open, setOpen] = useState(false);
  const [script, setScript] = useState<string>("");

  const fetchScript = async () => {
    const res = await fetch(`/minutes/api/transcripts/${transcriptId}`);
    if (!res.ok) {
      alert("スクリプトの取得に失敗しました");
      return;
    }
    const data = await res.json();
    setScript(data.content);
    setOpen(true);
  };

  return (
    <>
      <button
        onClick={fetchScript}
        className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
      >
        音声スクリプト確認
      </button>

      {open && (
        <Modal title="全文字起こしスクリプト" onClose={() => setOpen(false)}>
          <pre className="whitespace-pre-wrap max-h-[60vh] overflow-auto p-4">
            {script}
          </pre>
        </Modal>
      )}
    </>
  );
}
