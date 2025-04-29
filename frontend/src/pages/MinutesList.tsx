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

/* -------------------- LocalStorage Helpers -------------------- */
const LS_KEY = "minutes_items";
const loadLS = (): ItemEx[] => {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || "[]");
  } catch {
    return [];
  }
};
const saveLS = (items: ItemEx[]) =>
  localStorage.setItem(LS_KEY, JSON.stringify(items));

/* -------------------- ページ -------------------- */
export default function MinutesList() {
  const [items, setItems] = useState<ItemEx[]>(loadLS);
  const [loading, setLoading] = useState(items.length === 0);

  /* setInterval の id を保持してアンマウント時に停止 */
  const timers = useRef<number[]>([]);
  useEffect(() => () => timers.current.forEach(clearInterval), []);

  /* ------ 状態が変わるたび localStorage へ反映 ------ */
  useEffect(() => saveLS(items), [items]);

  /* ---------- 初回ロード (Transcripts + Jobs) ---------- */
  useEffect(() => {
    (async () => {
      // ❶ 既存 transcript を取得
      const { items: list } = await json<{ items: Transcript[] }>(
        "/minutes/api/transcripts?limit=100&order=desc"
      );

      // ❷ 進行中 Job を取得
      const jobs = await json<
        {
          id: string;
          transcript_id: number | null;
          status: "PENDING" | "PROCESSING" | "DRAFT_READY" | "FAILED";
          created_at: string;
          task_id: string;
        }[]
      >("/minutes/api/jobs");

      /* Transcript に紐づくジョブ進捗を phase に変換 */
      const jobMap = new Map<string, ItemEx>();
      jobs.forEach((j) => {
        const phase: Phase =
          j.status === "DRAFT_READY"
            ? "ready"
            : j.status === "FAILED"
            ? "error"
            : j.status === "PROCESSING"
            ? "draft"
            : "stt";
        jobMap.set(j.task_id, {
          id: j.transcript_id ?? -1,
          file_id: j.id,
          filename: "(processing)",
          created_at: j.created_at,
          phase,
          sttJobId: j.task_id,
        });
      });

      // list を ItemEx に変換
      const merged = list.map<ItemEx>((t) => ({
        ...t,
        phase: "ready",
      }));

      /* jobs 側でまだ transcript が無いものをプレースホルダとして追加 */
      for (const job of jobMap.values()) {
        const exists = merged.find((m) => m.sttJobId === job.sttJobId);
        if (!exists) merged.unshift(job);
      }

      setItems(merged);
      setLoading(false);

      /* ❸ 未完了ジョブのポーリングを再開 */
      merged
        .filter((it) => it.phase !== "ready" && it.phase !== "error")
        .forEach((it) =>
          startPolling(it.sttJobId!, it.file_id, it.phase === "draft")
        );
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------- ジョブポーリング ---------- */
  const startPolling = (jobId: string, fileId: string, draftAlready = false) => {
    /* Whisper or Draft どちらのジョブかは draftAlready で分岐 */
    const poll = window.setInterval(async () => {
      const res = await fetch(`/minutes/api/jobs/${jobId}`);
      if (!res.ok) return; // まだ
      clearInterval(poll);

      if (!draftAlready) {
        /* Whisper 完了 → transcript 再取得してプレースホルダ置換 */
        const { items: list } = await json<{ items: Transcript[] }>(
          "/minutes/api/transcripts?limit=100&order=desc"
        );
        const tr = list.find((row) => row.file_id === fileId);
        if (!tr) {
          setItems((prev) =>
            prev.map((it) =>
              it.file_id === fileId ? { ...it, phase: "error" } : it
            )
          );
          return;
        }
        /* phase = draft */
        setItems((prev) =>
          prev.map((it) =>
            it.file_id === fileId
              ? { ...tr, phase: "draft", sttJobId: jobId }
              : it
          )
        );

        /* Draft 生成開始 */
        const resp = await fetch(`/minutes/api/${tr.id}/draft`, {
          method: "POST",
        });
        if (!resp.ok) {
          setItems((prev) =>
            prev.map((it) =>
              it.file_id === fileId ? { ...it, phase: "error" } : it
            )
          );
          return;
        }
        const { task_id: draftId } = await resp.json();
        startPolling(draftId, fileId, true);
      } else {
        /* Draft 完了 */
        setItems((prev) =>
          prev.map((it) =>
            it.file_id === fileId ? { ...it, phase: "ready" } : it
          )
        );
      }
    }, 3000);
    timers.current.push(poll);
  };

  /* ---------- 削除 ---------- */
  const deleteTranscript = async (id: number, fileId: string) => {
    if (!confirm("選択したトランスクリプトを完全に削除します。よろしいですか？"))
      return;
    try {
      const rsp = await fetch(`/minutes/api/transcripts/${id}`, {
        method: "DELETE",
      });
      if (!rsp.ok) throw new Error(await rsp.text());

      setItems((prev) => prev.filter((it) => it.file_id !== fileId));
    } catch (e: any) {
      alert(e.message || e);
    }
  };

  /* ---------- アップロード成功時 ---------- */
  const handleUploadSuccess = ({
    fileId,
    taskId,
    filename,
  }: {
    fileId: string;
    taskId: string;
    filename: string;
  }) => {
    setItems((prev) => [
      {
        id: -1,
        file_id: fileId,
        filename,
        created_at: new Date().toISOString(),
        phase: "stt",
        sttJobId: taskId,
      },
      ...prev,
    ]);
    startPolling(taskId, fileId);
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

/* -------------------- UploadDialog (既存) -------------------- */
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
