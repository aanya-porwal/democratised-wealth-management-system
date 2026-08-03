"use client";

import type { ReactNode } from "react";

export interface MetricCardProps {
  label: string;
  value: ReactNode;
  sublabel?: ReactNode;
  icon?: ReactNode;
  trend?: number; // percentage change, positive = up
  accent?: "emerald" | "red" | "blue" | "amber" | "violet";
  className?: string;
}

const ACCENTS: Record<NonNullable<MetricCardProps["accent"]>, string> = {
  emerald: "from-emerald-500/15 via-emerald-500/5 to-transparent",
  red: "from-red-500/15 via-red-500/5 to-transparent",
  blue: "from-blue-500/15 via-blue-500/5 to-transparent",
  amber: "from-amber-500/15 via-amber-500/5 to-transparent",
  violet: "from-violet-500/15 via-violet-500/5 to-transparent",
};

export function MetricCard({
  label,
  value,
  sublabel,
  icon,
  trend,
  accent = "emerald",
  className,
}: MetricCardProps) {
  const trendPositive = trend !== undefined && trend >= 0;
  return (
    <div
      className={`relative overflow-hidden rounded-xl border bg-card p-4 shadow-sm ${className ?? ""}`}
    >
      <div
        className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${ACCENTS[accent]}`}
        aria-hidden
      />
      <div className="relative flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="mt-1.5 truncate text-2xl font-semibold tracking-tight">
            {value}
          </p>
          {sublabel ? (
            <p className="mt-1 truncate text-xs text-muted-foreground">
              {sublabel}
            </p>
          ) : null}
          {trend !== undefined ? (
            <p
              className={`mt-1.5 text-xs font-medium ${
                trendPositive ? "text-emerald-500" : "text-red-500"
              }`}
            >
              {trendPositive ? "▲" : "▼"} {Math.abs(trend).toFixed(1)}%
            </p>
          ) : null}
        </div>
        {icon ? (
          <div className="shrink-0 rounded-lg border bg-background/60 p-2 text-foreground/80">
            {icon}
          </div>
        ) : null}
      </div>
    </div>
  );
}
