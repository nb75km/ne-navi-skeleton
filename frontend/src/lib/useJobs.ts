import { useQuery } from "@tanstack/react-query";
import { json } from "./api";

export interface Job {
  id: string;
  task_id: string;
  transcript_id: number | null;
  status: "pending" | "processing" | "draft_ready" | "failed";
  filename?: string; // ← server に追加してもOK
}

export function useJobs() {
  return useQuery<Job[]>({
    queryKey: ["jobs"],
    queryFn: () => json<Job[]>("/minutes/api/jobs"),
    refetchInterval: 3000,
    keepPreviousData: true,
  });
}