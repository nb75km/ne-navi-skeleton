import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { MarkdownDiffViewer } from "../components/MarkdownDiffViewer";
import VersionSelector from "../components/VersionSelector"; // 既存

interface Version {
  id: number;
  version_no: number;
  markdown: string;
}

export default function TranscriptDiff() {
  const { id } = useParams();            // transcript_id
  const [versions, setVersions] = useState<Version[]>([]);
  const [fromId, setFromId] = useState<number | null>(null);
  const [toId, setToId] = useState<number | null>(null);

  useEffect(() => {
    axios
      .get<Version[]>("/minutes/api/minutes_versions", {
        params: { transcript_id: Number(id) },
      })
      .then((r) => {
        setVersions(r.data);
        if (r.data.length >= 2) {
          setFromId(r.data[1].id);
          setToId(r.data[0].id);
        }
      });
  }, [id]);

  const fromMd = versions.find((v) => v.id === fromId)?.markdown ?? "";
  const toMd = versions.find((v) => v.id === toId)?.markdown ?? "";

  return (
    <div className="h-full flex flex-col gap-2 p-3">
      <div className="flex gap-2 items-center">
        <span className="text-sm font-medium">Compare:</span>
        <VersionSelector
          versions={versions.map((v) => ({
            id: v.id,
            label: `v${v.version_no}`,
          }))}
          current={fromId}
          onChange={setFromId}
        />
        <span className="text-gray-500">→</span>
        <VersionSelector
          versions={versions.map((v) => ({
            id: v.id,
            label: `v${v.version_no}`,
          }))}
          current={toId}
          onChange={setToId}
        />
      </div>

      <div className="flex-1 border rounded-lg overflow-hidden">
        <MarkdownDiffViewer left={fromMd} right={toMd} />
      </div>
    </div>
  );
}
