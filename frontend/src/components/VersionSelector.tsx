// ---------------------------------------------------------------------------
// frontend/src/components/VersionSelector.tsx
// ---------------------------------------------------------------------------
import React from 'react';
import { MinutesVersion } from '../lib/useMinutesVersions';

interface Props {
  versions: MinutesVersion[];
  value: number | null;
  onChange: (id: number) => void;
}

/**
 * ドロップダウン 1 つだけでシンプルにバージョンを切り替える UI
 */
const VersionSelector: React.FC<Props> = ({ versions, value, onChange }) => {
  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(Number(e.target.value))}
      className="border rounded px-2 py-1 text-sm"
    >
      {versions.map((v) => (
        <option key={v.id} value={v.id}>
          {`v${v.id}  –  ${new Date(v.created_at).toLocaleString()}`}
        </option>
      ))}
    </select>
  );
};

export default VersionSelector;
