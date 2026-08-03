"use client";

// AI explainability panel — shows which agents and tools the multi-agent
// advisor used, plus the data sources and the compliance disclaimer.

import { useState } from "react";
import { ChevronDown, Eye, ShieldAlert } from "lucide-react";
import type { AiExplainability } from "@/types/api";
import { cn } from "@/lib/utils";

export function AiExplainability({
  explainability,
  className,
}: {
  explainability: AiExplainability;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  if (!explainability) return null;

  return (
    <div className={cn("rounded-lg border bg-muted/30 text-xs", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left font-medium text-muted-foreground hover:text-foreground"
        aria-expanded={open}
      >
        <Eye className="h-3.5 w-3.5" aria-hidden />
        Why did AI do that?
        <ChevronDown
          className={cn("ml-auto h-3.5 w-3.5 transition-transform", open && "rotate-180")}
          aria-hidden
        />
      </button>
      {open ? (
        <div className="space-y-3 border-t px-3 py-3">
          <div className="space-y-1">
            <p className="font-semibold text-foreground/80">Agents used</p>
            <p className="text-muted-foreground">
              {explainability.agentsUsed?.length
                ? explainability.agentsUsed.join(", ")
                : "Planner → Coach routing"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="font-semibold text-foreground/80">Tools used</p>
            <p className="text-muted-foreground">
              {explainability.toolsUsed?.length
                ? explainability.toolsUsed.join(", ")
                : "None"}
            </p>
          </div>
          {explainability.dataSources?.length ? (
            <div className="space-y-1">
              <p className="font-semibold text-foreground/80">Data sources</p>
              <ul className="list-inside list-disc space-y-0.5 text-muted-foreground">
                {explainability.dataSources.map((ds) => (
                  <li key={`${ds.key}-${ds.value}`}>
                    {ds.label ?? ds.key}: {ds.value}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {explainability.calculations?.length ? (
            <div className="space-y-1">
              <p className="font-semibold text-foreground/80">Calculations</p>
              <ul className="list-inside list-disc space-y-0.5 text-muted-foreground">
                {explainability.calculations.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {explainability.disclaimer ? (
            <div className="flex items-start gap-2 rounded bg-amber-500/10 p-2 text-amber-700 dark:text-amber-400">
              <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              <p className="text-[11px] leading-relaxed">{explainability.disclaimer}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
