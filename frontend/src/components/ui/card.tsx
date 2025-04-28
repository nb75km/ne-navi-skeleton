import React from "react";
import { cn } from "../../lib/utils";

export function Card({ className = "", children }: React.PropsWithChildren<{ className?: string }>) {
  return <div className={cn("rounded-2xl border bg-white", className)}>{children}</div>;
}

export function CardContent({ children }: React.PropsWithChildren<{}>) {
  return <div className="p-4">{children}</div>;
}
