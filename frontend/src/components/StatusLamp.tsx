import React from "react";

/** ジョブ進行状況を示すランプ
 *  - stt   : 音声→文字起こし中（黄）
 *  - draft : 初期ドラフト生成中（青）
 *  - ready : 完了（緑、点灯のみ）
 *  - error : 失敗（赤） */
export function StatusLamp(
  { state }: { state: "stt" | "draft" | "ready" | "error" }
) {
  const color =
    state === "ready" ? "bg-emerald-500" :
    state === "draft" ? "bg-sky-400" :
    state === "stt"   ? "bg-amber-400" :
                        "bg-red-500";

  const pulse = state === "ready" ? "" : "animate-pulse";
  return <span className={`inline-block w-3 h-3 rounded-full ${color} ${pulse}`} />;
}
