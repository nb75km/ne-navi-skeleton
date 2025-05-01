/* =========================================================
 *  MinutesList.tsx  –  localStorage を一切使わずに描画
 * ======================================================= */
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, UploadCloud, Trash2 } from "lucide-react";
import { json } from "../lib/api";
import { StatusLamp } from "../components/StatusLamp";

/* ---------- 型 ---------- */
type Phase = "stt" | "draft" | "ready" | "error";

interface Transcript {
  id: number;
  file_id: string;
  filename: string;
  created_at: string;
}

type ItemEx = Transcript & {
  phase: Phase;
  sttJobId?: string; // Whisper ジョブ UUID
};

/* ---------- ページ ---------- */
export default function MinutesList() {
  const [items, setItems]   = useState<ItemEx[]>([]);
  const [loading, setLoad]  = useState(true);
  const timers = useRef<number[]>([]);

  /* unmount 時にポーリング停止 */
  useEffect(() => () => timers.current.forEach(clearInterval), []);

  /* --------- 初回ロード (毎回サーバから取得) --------- */
  useEffect(() => {
    refreshFromServer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* --------- サーバから一覧を取得 --------- */
  const refreshFromServer = async () => {
    /* 1. transcripts */
    const { items: trs } = await json<{ items: Transcript[] }>(
      "/minutes/api/transcripts?limit=100&order=desc"
    );

    /* 2. jobs */
    const jobs = await json<
      {
        task_id: string;
        status: "PENDING" | "PROCESSING" | "DRAFT_READY" | "FAILED";
      }[]
    >("/minutes/api/jobs");
    const phaseByJob = new Map<string, Phase>();
    jobs.forEach((j) =>
      phaseByJob.set(
        j.task_id,
        j.status === "DRAFT_READY"
          ? "ready"
          : j.status === "FAILED"
          ? "error"
          : j.status === "PROCESSING"
          ? "draft"
          : "stt"
      )
    );

    /* 3. transcripts をベースに items を構築 */
    const list: ItemEx[] = trs.map((t) => ({
      ...t,
      phase: "ready",
    }));

    /* 4. state に既にある “処理中プレースホルダー” を維持しつつ phase 更新 */
    items
      .filter((it) => it.phase !== "ready" && it.phase !== "error")
      .forEach((ph) => {
        const p = phaseByJob.get(ph.sttJobId!);
        list.unshift({
          ...ph,
          phase: p ?? ph.phase,
        });
      });

    /* 5. ソート */
    list.sort(
      (a, b) => +new Date(b.created_at) - +new Date(a.created_at)
    );

    setItems(list);
    setLoad(false);

    /* 6. ポーリング再開 */
    list
      .filter((it) => it.phase !== "ready" && it.phase !== "error")
      .forEach((it) =>
        startPolling(it.sttJobId!, it.file_id, it.phase === "draft")
      );
  };

  /* --------- ポーリング --------- */
  const startPolling = (
    jobId: string,
    fileId: string,
    draftAlready = false
  ) => {
    const poll = window.setInterval(async () => {
      const r = await fetch(`/minutes/api/jobs/${jobId}`);
      if (!r.ok) return;
      clearInterval(poll);

      if (!draftAlready) {
        /* Whisper 完了 → transcript 取得 */
        const { items: list } = await json<{ items: Transcript[] }>(
          "/minutes/api/transcripts?limit=100&order=desc"
        );
        const tr = list.find((t) => t.file_id === fileId);
        if (!tr) {
          setItems((p) =>
            p.map((it) =>
              it.sttJobId === jobId ? { ...it, phase: "error" } : it
            )
          );
          return;
        }
        /* draft フェーズへ */
        setItems((p) =>
          p.map((it) =>
            it.sttJobId === jobId
              ? { ...tr, phase: "draft", sttJobId: jobId }
              : it
          )
        );
        /* Draft 生成要求 */
        const resp = await fetch(`/minutes/api/${tr.id}/draft`, {
          method: "POST",
        });
        if (!resp.ok) return;
        const { task_id } = await resp.json();
        startPolling(task_id, fileId, true);
      } else {
        /* Draft 完了 */
        setItems((p) =>
          p.map((it) =>
            it.sttJobId === jobId ? { ...it, phase: "ready" } : it
          )
        );
      }
    }, 3000);
    timers.current.push(poll);
  };

  /* --------- アップロード成功 --------- */
  const handleUploadSuccess = ({
    fileId,
    taskId,
    filename,
  }: {
    fileId: string;
    taskId: string;
    filename: string;
  }) => {
    setItems((p) => [
      {
        id: -1,
        file_id: fileId,
        filename,
        created_at: new Date().toISOString(),
        phase: "stt",
        sttJobId: taskId,
      },
      ...p,
    ]);
    startPolling(taskId, fileId);
  };

  /* --------- 削除 --------- */
  const deleteTranscript = async (id: number, sttJobId: string) => {
    if (!confirm("Delete this transcript?")) return;
    await fetch(`/minutes/api/transcripts/${id}`, { method: "DELETE" });
    setItems((p) => p.filter((it) => it.sttJobId !== sttJobId));
  };

  /* --------- UI --------- */
  if (loading) return <Loader2 className="m-auto animate-spin" size={32} />;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-xl font-semibold flex items-center gap-2">
        Minutes
        <UploadDialog onDone={handleUploadSuccess} />
      </h1>

      <ul className="space-y-2">
        {items.map((t) => (
          <li key={t.sttJobId + t.phase} className="border rounded p-3">
            {t.phase === "ready" ? (
              <ReadyRow item={t} onDelete={deleteTranscript} />
            ) : (
              <ProcessingRow item={t} />
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- サブコンポーネント ---------- */
const ReadyRow = ({
  item,
  onDelete,
}: {
  item: ItemEx;
  onDelete: (id: number, sttJobId: string) => void;
}) => (
  <div className="flex items-center gap-2">
    <Link
      to={`/workspace/${item.id}`}
      className="flex-1 truncate hover:underline"
    >
      {item.filename}
    </Link>
    <StatusLamp state="ready" />
    <button
      onClick={() => onDelete(item.id, item.sttJobId)}
      className="text-gray-400 hover:text-red-600"
      title="Delete"
    >
      <Trash2 size={18} />
    </button>
  </div>
);

const ProcessingRow = ({ item }: { item: ItemEx }) => (
  <div className="flex items-center gap-2">
    {item.filename}
    <span className="text-gray-500 ml-1">(Processing)</span>
    <StatusLamp state={item.phase} />
  </div>
);

/* ---------- UploadDialog (既存) ---------- */
function UploadDialog({
  onDone,
}: {
  onDone: (info: { fileId: string; taskId: string; filename: string }) => void;
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
      const { file_id, task_id } = await rsp.json();
      onDone({ fileId: file_id, taskId: task_id, filename: file.name });
      setOpen(false);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="ml-auto flex items-center gap-1 text-sm bg-indigo-600 text-white rounded px-3 py-1"
      >
        <UploadCloud size={16} /> Upload
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded shadow-lg p-6 w-80 space-y-4">
            <h2 className="text-lg font-semibold">Upload Audio</h2>
            <input type="file" accept="audio/*" onChange={handleFile} />
            <div className="flex justify-end gap-2">
              <button onClick={() => setOpen(false)} className="px-3 py-1 rounded border">
                Cancel
              </button>
              <button
                disabled={uploading}
                className="px-3 py-1 rounded bg-indigo-600 text-white disabled:opacity-60"
              >
                {uploading ? <Loader2 className="animate-spin" size={16} /> : "Upload"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
