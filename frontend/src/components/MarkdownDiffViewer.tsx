import React from "react";
import {
  diff_match_patch,
  DIFF_DELETE,
  DIFF_EQUAL,
  DIFF_INSERT,
} from "diff-match-patch";
import { ResizableTwoPane } from "./ResizableTwoPane"; // 既存コンポーネント

interface Props {
  left: string;
  right: string;
}

const dmp = new diff_match_patch();

function renderSide(
  diffs: ReturnType<typeof dmp.diff_main>,
  side: "left" | "right",
) {
  return diffs.map(([op, text], idx) => {
    if (op === DIFF_EQUAL) return <span key={idx}>{text}</span>;
    if (op === DIFF_DELETE && side === "left")
      return (
        <span key={idx} className="bg-red-100 line-through whitespace-pre-wrap">
          {text}
        </span>
      );
    if (op === DIFF_INSERT && side === "right")
      return (
        <span key={idx} className="bg-emerald-100 whitespace-pre-wrap">
          {text}
        </span>
      );
    return null;
  });
}

export const MarkdownDiffViewer: React.FC<Props> = ({ left, right }) => {
  const diffs = React.useMemo(() => {
    const d = dmp.diff_main(left, right);
    dmp.diff_cleanupSemantic(d);
    return d;
  }, [left, right]);

  return (
    <ResizableTwoPane
      left={<pre className="p-4 text-sm">{renderSide(diffs, "left")}</pre>}
      right={<pre className="p-4 text-sm">{renderSide(diffs, "right")}</pre>}
    />
  );
};
