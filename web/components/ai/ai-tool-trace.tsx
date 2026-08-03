"use client";

// AI tool-trace visualization — shows the orchestration trail of tools the
// AI advisors ran (e.g. "✓ Portfolio retrieved · 120ms").

import { CheckCircle2, XCircle, Loader2, Wrench } from "lucide-react";
import type { AiToolCall } from "@/types/api";
import { cn } from "@/lib/utils";

export function AiToolTrace({
  toolCalls,
  className,
}: {
  toolCalls: AiToolCall[];
  className?: string;
}) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div
      className={cn(
        "space-y-1 rounded-lg border bg-muted/40 p-2.5 text-xs",
        className
      )}
      role="status"
      aria-label="AI tool execution trace"
    >
      {toolCalls.map((tc) => {
        const isRunning = tc.status === "running" || tc.status === "pending";
        const isError = tc.status === "error";
        return (
          <div key={tc.id} className="flex items-center gap-2">
            {isRunning ? (
              <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-primary" aria-hidden />
            ) : isError ? (
              <XCircle className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-500" aria-hidden />
            )}
            <Wrench className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden />
            <span className="font-medium">{tc.friendlyName ?? tc.name}</span>
            {tc.latencyMs !== undefined && tc.status === "done" ? (
              <span className="ml-auto tabular-nums text-muted-foreground">
                {tc.latencyMs}ms
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
