import React from "react";

interface Props {
  versions: { id: number; label: string }[];
  current: number | null;
  onChange: (id: number) => void;
}

const VersionSelector: React.FC<Props> = ({
  versions,
  current,
  onChange,
}) => (
  <select
    className="border rounded px-2 py-1 bg-white"
    value={current ?? ""}
    onChange={(e) => onChange(Number(e.target.value))}
  >
    <option value="" disabled>
      Select…
    </option>
    {versions.map((v) => (
      <option key={v.id} value={v.id}>
        {v.label}
      </option>
    ))}
  </select>
);

export default VersionSelector;
