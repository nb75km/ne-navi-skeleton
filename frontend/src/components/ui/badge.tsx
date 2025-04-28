import React from "react";
import { cn } from "../../lib/utils";

export function Badge({ variant = "primary", className = "", children }: React.PropsWithChildren<{ variant?: "primary" | "secondary"; className?: string }>) {
  const colorClasses = variant === "secondary" ? "bg-gray-100 text-gray-800" : "bg-blue-600 text-white";
  return <span className={cn("inline-block text-xs font-medium rounded px-2 py-0.5", colorClasses, className)}>{children}</span>;
}
