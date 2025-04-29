import { useState } from "react";
import { Menu } from "@headlessui/react"; // または shadcn/ui の Dropdown
import { Download } from "lucide-react";

interface Props { versionId: number; }
export function ExportButton({ versionId }: Props) {
  const [loading, setLoading] = useState(false);

  const download = async (format: string) => {
    setLoading(true);
    try {
      const res = await fetch(
        `/minutes/api/minutes/${versionId}/export?format=${format}`
      );
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `minutes_${versionId}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Menu as="div" className="relative inline-block text-left">
      <Menu.Button
        className="inline-flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
        disabled={loading}
      >
        <Download className="mr-1" size={16} /> Export
      </Menu.Button>
      <Menu.Items className="absolute right-0 mt-1 w-32 bg-white shadow rounded">
        {["md", "docx", "pdf"].map((fmt) => (
          <Menu.Item key={fmt}>
            {({ active }) => (
              <button
                onClick={() => download(fmt)}
                className={`w-full text-left px-3 py-1 ${active ? "bg-gray-100" : ""}`}
              >
                {fmt.toUpperCase()}
              </button>
            )}
          </Menu.Item>
        ))}
      </Menu.Items>
    </Menu>
  );
}
