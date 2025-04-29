// ---------------------------------------------------------------------------
// frontend/src/lib/useMinutesVersions.ts
// ---------------------------------------------------------------------------
import { useEffect, useState } from 'react';
import { json } from './api';

/**
 * バックエンド `/api/minutes_versions` のレスポンス型
 */
export interface MinutesVersion {
  id: number;
  markdown: string;
  created_at: string;
}

/**
 * トランスクリプト単位でバージョン一覧を取得し、再取得(reload)ハンドラも返すカスタム Hook。
 */
export function useMinutesVersions(transcriptId: number) {
  const [versions, setVersions] = useState<MinutesVersion[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    json<MinutesVersion[]>(
      `/minutes/api/minutes_versions?transcript_id=${transcriptId}`,
    )
      .then(setVersions)
      .finally(() => setLoading(false));
  };

  // 初回 & transcriptId 変更時
  useEffect(load, [transcriptId]);

  return { versions, loading, reload: load } as const;
}
