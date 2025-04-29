import React from "react";
const MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
  { value: "o3", label: "o3 (高精度)" },
  { value: "o1", label: "o1 (高速)" },
];

export default function ModelSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (m: string) => void;
}) {
  return (
    <select
      className="border rounded px-2 py-1 text-sm"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {MODELS.map((m) => (
        <option key={m.value} value={m.value}>
          {m.label}
        </option>
      ))}
    </select>
  );
}
