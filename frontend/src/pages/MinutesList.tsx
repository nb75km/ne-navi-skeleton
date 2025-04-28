import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, UploadCloud, Trash2 } from "lucide-react";
import { json } from "../lib/api";
import { StatusLamp } from "../components/StatusLamp";

/* -------------------- 型 -------------------- */
export interface Transcript {
  id: number;
  file_id: string;
  filename: string;
  created_at: string;
}

type Phase = "stt" | "draft" | "ready" | "error";

type ItemEx = Transcript & {
  phase: Phase;
  sttJobId?: string;
  draftJobId?: string;
};

/* -------------------- ページ -------------------- */
export default function MinutesList() {
  const [items, setItems] = useState<ItemEx[]>([]);
  const [loading, setLoading] = useState(true);

  /* setInterval の id を保持してアンマウント時に全て停止 */
  const timers = useRef<number[]>([]);
  useEffect(() => () => timers.current.forEach(clearInterval), []);

  /* ---------- 初回ロード ---------- */
  useEffect(() => {
    json<{ items: Transcript[] }>(
      "/minutes/api/transcripts?limit=100&order=desc"
    ).then(({ items: list }) => {
      setItems(list.map((x) => ({ ...x, phase: "ready" as const })));
      setLoading(false);
    });
  }, []);

  /* ---------- 削除 ---------- */
  const deleteTranscript = async (id: number, fileId: string) => {
    if (!confirm("選択したトランスクリプトを完全に削除します。よろしいですか？")) return;
    try {
      const rsp = await fetch(`/minutes/api/transcripts/${id}`, {
        method: "DELETE",
      });
      if (!rsp.ok) throw new Error(await rsp.text());

      // 楽観的に一覧から除外
      setItems((prev) => prev.filter((it) => it.file_id !== fileId));
    } catch (e: any) {
      alert(e.message || e);
    }
  };

  /* ---------- アップロード後コールバック ---------- */
  const handleUploadSuccess = (info: {
    fileId: string;
    taskId: string;
    filename: string;
  }) => {
    /* ❶ プレースホルダ行を即表示 */
    setItems((prev) => [
      {
        id: -1,
        file_id: info.fileId,
        filename: info.filename,
        created_at: new Date().toISOString(),
        phase: "stt",
        sttJobId: info.taskId,
      },
      ...prev,
    ]);

    /* ❷ Whisper ジョブをポーリング */
    const pollStt = window.setInterval(async () => {
      try {
        const res = await fetch(`/minutes/api/jobs/${info.taskId}`);
        if (!res.ok) return; // まだ完了していない

        clearInterval(pollStt);

        /* transcript 一覧を再取得して該当 file_id を探す */
        const { items: list } = await json<{ items: Transcript[] }>(
          "/minutes/api/transcripts?limit=100&order=desc"
        );
        const tr = list.find((row) => row.file_id === info.fileId);
        if (!tr) {
          setItems((prev) =>
            prev.map((it) =>
              it.file_id === info.fileId ? { ...it, phase: "error" } : it
            )
          );
          return;
        }

        /* プレースホルダ置換 → phase=draft */
        setItems((prev) =>
          prev.map((it) =>
            it.file_id === info.fileId ? { ...tr, phase: "draft" } : it
          )
        );

        /* GPT ドラフト生成を開始 */
        const resp = await fetch(`/minutes/api/${tr.id}/draft`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!resp.ok) throw new Error(await resp.text());
        const { task_id: draftId } = await resp.json();

        /* draft ジョブをポーリング */
        const pollDraft = window.setInterval(async () => {
          const r = await fetch(`/minutes/api/jobs/${draftId}`);
          if (!r.ok) return;

          clearInterval(pollDraft);
          setItems((prev) =>
            prev.map((it) =>
              it.file_id === info.fileId ? { ...it, phase: "ready" } : it
            )
          );
        }, 3000);
        timers.current.push(pollDraft);
      } catch {
        clearInterval(pollStt);
        setItems((prev) =>
          prev.map((it) =>
            it.file_id === info.fileId ? { ...it, phase: "error" } : it
          )
        );
      }
    }, 3000);
    timers.current.push(pollStt);
  };

  /* -------------------- レンダリング -------------------- */
  if (loading) {
    return <Loader2 className="m-auto animate-spin" size={32} />;
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-xl font-semibold flex items-center gap-2">
        Minutes
        <UploadDialog onDone={handleUploadSuccess} />
      </h1>

      <ul className="space-y-2">
        {items.map((t) => (
          <li
            key={`${t.file_id}-${t.phase}`}
            className="border rounded p-3 hover:bg-gray-50"
          >
            {t.phase === "ready" ? (
              <div className="flex items-center gap-2">
                <Link
                  to={`/workspace/${t.id}`}
                  className="flex-1 truncate hover:underline"
                >
                  {t.filename}
                </Link>
                <StatusLamp state="ready" />
                <button
                  onClick={() => deleteTranscript(t.id, t.file_id)}
                  title="Delete"
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="flex-1 truncate text-gray-500">
                  {t.filename}
                </span>
                <StatusLamp state={t.phase} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* -------------------- UploadDialog -------------------- */
function UploadDialog({
  onDone,
}: {
  onDone: (info: {
    fileId: string;
    taskId: string;
    filename: string;
  }) => void;
}) {
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setUploading(true);

    try {
      const fd = new FormData();
      fd.append("file", file);
      const rsp = await fetch("/minutes/api/files", {
        method: "POST",
        body: fd,
      });
      if (!rsp.ok) throw new Error(await rsp.text());
      const { file_id, task_id } = await rsp.json();

      onDone({ fileId: file_id, taskId: task_id, filename: file.name });
      setOpen(false);
    } catch (err) {
      alert("Upload failed: " + err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="ml-auto flex items-center gap-1 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded px-3 py-1"
      >
        <UploadCloud size={16} /> Upload
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded shadow-lg p-6 w-80 space-y-4">
            <h2 className="text-lg font-semibold">Upload Audio</h2>
            <input type="file" accept="audio/*" onChange={handleFile} />

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setOpen(false)}
                className="px-3 py-1 rounded border"
              >
                Cancel
              </button>
              <button
                disabled={uploading}
                className="px-3 py-1 rounded bg-indigo-600 text-white disabled:opacity-60"
              >
                {uploading ? (
                  <Loader2 className="animate-spin" size={16} />
                ) : (
                  "Upload"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
