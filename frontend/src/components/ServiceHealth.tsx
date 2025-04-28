import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "./ui/card";
import { HeartPulse } from "lucide-react";
import { json } from "../lib/api";

interface Props {
  label: string;         // カードに表示するラベル
  path: string;          // バックエンド /health パス
  to?: string;           // クリック遷移先 (省略可)
}

export default function ServiceHealth({ label, path, to }: Props) {
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = () =>
      json<{ status: string }>(path)
        .then((d) => setStatus(d.status))
        .catch(() => setStatus("down"));

    fetchStatus();                           // 初回
    const id = setInterval(fetchStatus, 30_000); // 30 秒ごと
    return () => clearInterval(id);
  }, [path]);

  const color =
    status === "ok" ? "bg-green-500"
    : status ? "bg-red-500"
    : "bg-gray-400";

  const card = (
    <Card className="flex items-center gap-3 p-4 w-full max-w-xs hover:shadow transition">
      <HeartPulse className="shrink-0" />
      <span className="flex-1 font-semibold">{label}</span>
      <span className={`w-3 h-3 rounded-full ${color}`}></span>
    </Card>
  );

  return to ? <Link to={to}>{card}</Link> : card;
}
