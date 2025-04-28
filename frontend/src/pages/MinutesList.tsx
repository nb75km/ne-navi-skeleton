import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Loader2 } from "lucide-react";
import { json } from "../lib/api";

/* ---------- UploadDialog ---------- */
function UploadDialog({ onDone }: { onDone: (fid: string) => void }) {
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setUploading(true);

    const fd = new FormData();
    fd.append("file", file);
    const rsp = await fetch("/minutes/api/files", { method: "POST", body: fd });
    const { file_id } = await rsp.json();
    setUploading(false);
    setOpen(false);
    onDone(file_id);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white rounded px-3 py-1 text-sm"
      >
        <Plus size={16} /> Upload
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow space-y-4">
            <h2 className="font-semibold">Upload audio</h2>
            <input type="file" accept="audio/*" onChange={handleFile} />
            {uploading && <Loader2 className="animate-spin mx-auto" />}
            <button
              onClick={() => setOpen(false)}
              className="text-sm text-gray-500 hover:underline"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}

/* ---------- MinutesList Page ---------- */
interface Transcript {
  id: number;
  file_id: string;
  filename: string;
  created_at: string;
}

export default function MinutesList() {
  const [items, setItems] = useState<Transcript[] | null>(null);
  const navigate = useNavigate();

  /* 一覧ロード */
  useEffect(() => {
    json<any>("/minutes/api/transcripts").then((resp) =>
      setItems((resp.items ?? resp) as Transcript[]),
    );
  }, []);

  /* 新規アップロード後の Draft 生成 → Workspace 遷移 */
  const handleUploadSuccess = (fileId: string) => {
    const poll = setInterval(async () => {
      const t = await json<Transcript[]>(
        `/minutes/api/transcripts?file_id=${fileId}`,
      );
      if (t.length) {
        clearInterval(poll);
        const transcript = t[0];

        /* 初回 Draft を GPT で生成 */
        await fetch(`/minutes/api/${transcript.id}/draft`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model: "gpt-4o-mini" }),
        });

        navigate(`/workspace/${transcript.id}`);
      }
    }, 3000);
  };

  if (!items) return <Loader2 className="animate-spin m-4" />;

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">Transcripts</h1>
        <UploadDialog onDone={handleUploadSuccess} />
      </div>

      <ul className="space-y-2">
        {items.map((t) => (
          <li
            key={t.id}
            className="border rounded p-3 hover:bg-gray-50 flex justify-between"
          >
            {/* ★ ここを TranscriptDetail ではなく Workspace へ */}
            <Link
              to={`/workspace/${t.id}`}
              className="font-medium truncate max-w-xs"
            >
              {t.filename}
            </Link>
            <span className="text-xs text-gray-500">
              {new Date(t.created_at).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
