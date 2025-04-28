import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Card } from "../components/ui/card";
import { Loader2 } from "lucide-react";
import { json } from "../lib/api";
import DraftControls from "../components/DraftControls";
import MinutesEditor from "../components/MinutesEditor";
import GenerateDraftButton from "../components/GenerateDraftButton";

interface Transcript {
  id: number;
  filename: string;
  language: string | null;
  created_at: string;
  content: string;
}

export default function TranscriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<Transcript | null>(null);
  const [latestMd, setLatestMd] = useState<string | null>(null);
  const [hasDraft, setHasDraft] = useState<boolean | null>(null); // null = loading
  const [editing, setEditing] = useState(false);

  /* fetch transcript + versions */
  useEffect(() => {
    if (!id) return;
    const load = async () => {
      const d = await json<Transcript>(`/minutes/api/transcripts/${id}`);
      setData(d);
      const versions = await json<any[]>(
        `/minutes/api/minutes_versions?transcript_id=${d.id}`
      );
      if (versions.length) {
        setHasDraft(true);
        setLatestMd(versions[0].markdown);
      } else {
        setHasDraft(false);
      }
    };
    load();
  }, [id]);

  if (!data || hasDraft === null) return <Loader2 className="animate-spin m-4" />;

  /* Draft 生成後に即 Workspace に行きたい場合 */
  if (hasDraft && !latestMd) {
    navigate(`/workspace/${data.id}`);
    return null;
  }

  return (
    <div className="p-4 space-y-4">
      {/* header */}
      <div className="flex items-center gap-2">
        <Link to="/minutes" className="text-blue-600 hover:underline">
          ← Back
        </Link>
        <h1 className="text-xl font-bold truncate">{data.filename}</h1>

        {hasDraft ? (
          /* 既にドラフトがあればモデル選択＋再生成 UI */
          <DraftControls transcriptId={data.id} />
        ) : (
          /* ドラフトが無い場合だけ表示 */
          <GenerateDraftButton transcriptId={data.id} />
        )}
      </div>

      {/* Draft が存在する場合のみ表示 & 編集 */}
      {hasDraft && (
        <>
          {!editing && (
            <div className="flex justify-end">
              <button
                onClick={() => setEditing(true)}
                className="text-sm text-blue-600 hover:underline"
              >
                Edit Latest
              </button>
            </div>
          )}

          <Card className="p-4 space-y-2">
            <p className="text-sm text-gray-600">
              {new Date(data.created_at).toLocaleString()}{" "}
              {data.language && `| ${data.language}`}
            </p>
            <pre className="whitespace-pre-wrap leading-relaxed">
              {latestMd ?? "(generating…)"}
            </pre>
          </Card>

          {editing && latestMd && (
            <MinutesEditor
              transcriptId={data.id}
              currentMarkdown={latestMd}
              onSaved={() => {
                setEditing(false);
                window.location.reload();
              }}
              onCancel={() => setEditing(false)}
            />
          )}
        </>
      )}

      {/* ドラフトが無い場合のガイド表示 */}
      {!hasDraft && (
        <Card className="p-4 text-gray-600">
          このトランスクリプトにはまだ議事録ドラフトがありません。<br />
          右上の<strong>「Draft を生成」</strong>ボタンで GPT に要約を作成させましょう。
        </Card>
      )}
    </div>
  );
}
