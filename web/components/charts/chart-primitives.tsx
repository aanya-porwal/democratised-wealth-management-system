"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ReactNode } from "react";

const CHART_COLORS = [
  "#34d399", // emerald-400
  "#60a5fa", // blue-400
  "#a78bfa", // violet-400
  "#f472b6", // pink-400
  "#fbbf24", // amber-400
  "#22d3ee", // cyan-400
  "#fb7185", // rose-400
  "#c084fc", // purple-400
  "#4ade80", // green-400
  "#facc15", // yellow-400
];

const DEFAULT_AXIS = { stroke: "hsl(var(--muted-foreground))", fontSize: 11 };
const DEFAULT_GRID = { stroke: "hsl(var(--border))", strokeDasharray: "4 4" };
const DEFAULT_TOOLTIP_STYLE = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.5rem",
  color: "hsl(var(--popover-foreground))",
  fontSize: "0.75rem",
  boxShadow: "0 8px 24px rgba(0,0,0,0.18)",
};

export function chartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}

export function ChartTooltipStyle(): Record<string, string> {
  return DEFAULT_TOOLTIP_STYLE;
}

export interface ChartContainerProps {
  children: ReactNode;
  height?: number;
  className?: string;
}

export function ChartContainer({
  children,
  height = 280,
  className,
}: ChartContainerProps) {
  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        {children as React.ReactElement}
      </ResponsiveContainer>
    </div>
  );
}

export {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CHART_COLORS,
  DEFAULT_AXIS,
  DEFAULT_GRID,
  DEFAULT_TOOLTIP_STYLE,
};
