import React from "react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ChevronDown } from "lucide-react";

interface Version {
  id: number;
  label: string; // "v12" など
}

interface Props {
  versions: Version[];
  current: number | null;
  onChange: (id: number) => void;
}

/**
 * バージョン選択ドロップダウン (Radix UI)。
 * shadcn/ui ラッパーを使わず直接 Radix を呼び出しているので、
 * Vite のビルド時にモジュール解決エラーが起きません。
 */
export default function VersionSelector({ versions, current, onChange }: Props) {
  const selected =
    versions.find((v) => v.id === current) ?? versions[0] ?? null;

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className="border rounded-lg px-3 py-1 flex items-center gap-1 text-gray-800 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          {selected ? selected.label : "Ver"}
          <ChevronDown className="w-4 h-4 opacity-70" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={4}
          className="min-w-[4.5rem] rounded-lg border bg-white shadow-md p-1"
        >
          {versions.length === 0 && (
            <div className="px-2 py-1 text-sm text-gray-500 select-none">(none)</div>
          )}
          {versions.map((v) => (
            <DropdownMenu.Item
              key={v.id}
              onSelect={() => onChange(v.id)}
              className={`px-2 py-1 text-sm rounded-md cursor-pointer select-none focus:bg-emerald-600 focus:text-white outline-none ${
                v.id === selected?.id ? "bg-emerald-50 text-emerald-600" : "hover:bg-gray-100"
              }`}
            >
              {v.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
