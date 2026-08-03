"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Wallet,
  HeartPulse,
  Target,
  PieChart,
  LineChart,
  FileSearch,
  GitCompareArrows,
  FlaskConical,
  Dices,
  Sparkles,
  Bot,
  Settings,
  User,
  Bell,
  Command,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const primaryNav: NavItem[] = [
  { title: "Command Center", href: "/app", icon: Command },
  { title: "Dashboard", href: "/app/dashboard", icon: LayoutDashboard },
  { title: "Net Worth", href: "/app/net-worth", icon: Wallet },
  { title: "Financial Health", href: "/app/health", icon: HeartPulse },
  { title: "Goals", href: "/app/goals", icon: Target },
  { title: "Portfolio", href: "/app/portfolio", icon: PieChart },
  { title: "Asset Allocation", href: "/app/allocation", icon: PieChart },
];

const analysisNav: NavItem[] = [
  { title: "Research Reports", href: "/app/research", icon: FileSearch },
  { title: "Security Comparison", href: "/app/compare", icon: GitCompareArrows },
  { title: "Scenario Analysis", href: "/app/scenarios", icon: FlaskConical },
  { title: "Monte Carlo", href: "/app/monte-carlo", icon: Dices },
  { title: "Recommendations", href: "/app/recommendations", icon: Sparkles },
  { title: "AI Coach", href: "/app/coach", icon: Bot },
];

const accountNav: NavItem[] = [
  { title: "Notifications", href: "/app/notifications", icon: Bell },
  { title: "Profile", href: "/app/profile", icon: User },
  { title: "Settings", href: "/app/settings", icon: Settings },
];

export function Sidebar({ role }: { role?: string }) {
  const pathname = usePathname();

  const renderItem = (item: NavItem) => {
    const active =
      pathname === item.href || pathname.startsWith(`${item.href}/`);
    return (
      <Link
        key={item.href}
        href={item.href}
        className={cn(
          "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          active
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-accent hover:text-foreground"
        )}
        aria-current={active ? "page" : undefined}
      >
        <item.icon className="h-4 w-4 shrink-0" aria-hidden />
        <span className="truncate">{item.title}</span>
        {item.badge ? (
          <span className="ml-auto rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
            {item.badge}
          </span>
        ) : null}
      </Link>
    );
  };

  return (
    <nav
      className="flex h-full flex-col gap-1 overflow-y-auto p-3 scrollbar-thin"
      aria-label="Primary navigation"
    >
      <div className="px-3 pb-2 pt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        Overview
      </div>
      {primaryNav.map(renderItem)}

      <div className="px-3 pb-2 pt-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        Analysis
      </div>
      {analysisNav.map(renderItem)}

      {role === "advisor" || role === "admin" ? (
        <>
          <div className="px-3 pb-2 pt-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
            Advisor
          </div>
          <Link
            href="/app/advisor"
            className={cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname.startsWith("/app/advisor")
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <ShieldCheck className="h-4 w-4 shrink-0" aria-hidden />
            <span className="truncate">Advisor Dashboard</span>
          </Link>
        </>
      ) : null}

      <div className="px-3 pb-2 pt-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        Account
      </div>
      {accountNav.map(renderItem)}
    </nav>
  );
}
