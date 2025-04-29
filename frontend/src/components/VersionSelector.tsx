import React from "react";

interface Props {
  versions: { id: number; label: string }[];
  current: number | null;
  onChange: (id: number) => void;
}

/**
 * シンプルなネイティブ <select>。
 * WebKit/macOS のアクセントカラーで文字が見えなくなる現象を避けるため、
 * 明示的に text‑gray‑800 を指定し、最小幅を固定。
 */
const VersionSelector: React.FC<Props> = ({ versions, current, onChange }) => {
  return (
    <select
      value={current ?? versions[0]?.id ?? ""}
      onChange={(e) => onChange(Number(e.target.value))}
      className="border rounded px-2 pr-6 py-1 text-sm text-gray-800 min-w-[64px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
      style={{ WebkitAppearance: "menulist" }}
    >
      {versions.map((v) => (
        <option key={v.id} value={v.id} className="text-gray-900">
          {v.label}
        </option>
      ))}
    </select>
  );
};

export default VersionSelector;