import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/ui/card";
import { Loader2 } from "lucide-react";
import { json } from "../lib/api";

import DraftControls from "../components/DraftControls";
import GenerateDraftButton from "../components/GenerateDraftButton";
import MinutesEditor from "../components/MinutesEditor";
import TranscriptControls from "../components/TranscriptControls";
import ExportControls from "../components/ExportControls";
import VersionSelector from "../components/VersionSelector";

interface Transcript {
  id: number;
  filename: string;
  language: string | null;
  created_at: string;
}

interface Version {
  id: number;
  transcript_id: number;
  version_no: number;
  markdown: string;
  created_at: string;
}

export default function TranscriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  /* 初期ロード */
  useEffect(() => {
    if (!id) return;
    (async () => {
      setLoading(true);
      const t = await json<Transcript>(`/minutes/api/transcripts/${id}`);
      const vs = await json<Version[]>(
        `/minutes/api/minutes_versions?transcript_id=${t.id}`
      );
      setTranscript(t);
      setVersions(vs); // version_no DESC で返ってくる
      setSelectedVersionId(vs.length ? vs[0].id : null);
      setLoading(false);
    })();
  }, [id]);

  /* Draft が生成された直後は Workspace に自動遷移 */
  if (!loading && versions.length === 0) {
    navigate(`/workspace/${id}`);
    return null;
  }

  if (loading || !transcript) {
    return <Loader2 className="animate-spin m-4" />;
  }

  const selected = versions.find((v) => v.id === selectedVersionId) || null;
  const latestNo = versions[0]?.version_no ?? 0;

  return (
    <div className="p-4 space-y-4">
      {/* ヘッダ */}
      <div className="flex flex-wrap items-center gap-2">
        <Link to="/minutes" className="text-blue-600 hover:underline">
          ← Back
        </Link>
        <h1 className="text-xl font-bold truncate">{transcript.filename}</h1>

        {versions.length ? (
          <DraftControls transcriptId={transcript.id} />
        ) : (
          <GenerateDraftButton transcriptId={transcript.id} />
        )}
        <TranscriptControls transcriptId={transcript.id} />
        <ExportControls transcriptId={transcript.id} />
        {versions.length > 0 && (
          <VersionSelector
            versions={versions.map((v) => ({
              id: v.id,
              label: `v${v.version_no}`,
            }))}
            current={selectedVersionId}
            onChange={setSelectedVersionId}
          />
        )}
      </div>

      {/* 本文 */}
      {versions.length > 0 && selected && (
        <>
          {!editing && (
            <div className="flex justify-end">
              <button
                onClick={() => setEditing(true)}
                className="text-sm text-blue-600 hover:underline"
              >
                Edit (→ 新規 v{latestNo + 1})
              </button>
            </div>
          )}

          <Card className="p-4 space-y-2">
            <p className="text-sm text-gray-600">
              version v{selected.version_no} |{" "}
              {new Date(selected.created_at).toLocaleString()}
            </p>
            <pre className="whitespace-pre-wrap leading-relaxed">
              {selected.markdown}
            </pre>
          </Card>

          {editing && (
            <MinutesEditor
              transcriptId={transcript.id}
              currentMarkdown={selected.markdown}
              onSaved={() => window.location.reload()}
              onCancel={() => setEditing(false)}
            />
          )}
        </>
      )}

      {/* まだ Draft が無い場合のガイド */}
      {versions.length === 0 && (
        <Card className="p-4 text-gray-600">
          このトランスクリプトにはまだ議事録ドラフトがありません。<br />
          右上の<strong>「Draft を生成」</strong>ボタンで GPT に要約を作成させましょう。
        </Card>
      )}
    </div>
  );
}
