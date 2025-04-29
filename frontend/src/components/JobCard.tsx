import React from "react";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Job } from "../lib/useJobs";

export default function JobCard({ job }: { job: Job }) {
  const disabled = job.status !== "draft_ready";
  const statusColor: Record<Job["status"], string> = {
    pending: "bg-amber-300",
    processing: "bg-blue-300",
    draft_ready: "bg-emerald-400",
    failed: "bg-red-400",
  };

  return (
    <div className="border rounded p-3 flex items-center gap-3">
      <span className="flex-1 truncate">{job.filename || job.task_id}</span>
      <span
        className={`w-3 h-3 rounded-full ${statusColor[job.status]}`}
      />
      {disabled ? (
        <button
          disabled
          className="px-2 py-1 text-sm border rounded opacity-60 flex items-center gap-1"
        >
          <Loader2 size={14} className="animate-spin" /> 処理中...
        </button>
      ) : (
        <Link
          to={`/workspace/${job.transcript_id}`}
          className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white"
        >
          編集する
        </Link>
      )}
    </div>
  );
}