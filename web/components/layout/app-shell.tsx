"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/providers/auth-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { AiAssistantPanel } from "@/components/ai/ai-assistant-panel";
import { Button } from "@/components/ui/button";
import { Menu, X, Landmark } from "lucide-react";
import { useState } from "react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-14 items-center gap-2 border-b px-4">
          <Landmark className="h-6 w-6 text-primary" aria-hidden />
          <span className="text-lg font-bold tracking-tight">Wealth</span>
        </div>
        <Sidebar role={user?.role} />
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileOpen(false)}
            aria-hidden
          />
          <aside className="absolute inset-y-0 left-0 w-72 bg-card shadow-xl">
            <div className="flex h-14 items-center justify-between border-b px-4">
              <div className="flex items-center gap-2">
                <Landmark className="h-6 w-6 text-primary" aria-hidden />
                <span className="text-lg font-bold tracking-tight">Wealth</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <Sidebar role={user?.role} />
          </aside>
        </div>
      ) : null}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col lg:pl-64">
        <div className="flex h-14 items-center gap-2 border-b px-4 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <Link href="/app" className="flex items-center gap-2">
            <Landmark className="h-5 w-5 text-primary" aria-hidden />
            <span className="font-bold">Wealth</span>
          </Link>
        </div>
        <Topbar />
        <main className="flex-1 space-y-6 p-4 sm:p-6 lg:p-8">
          <div key={pathname} className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>

      {/* Persistent AI Financial Coach */}
      <AiAssistantPanel />
    </div>
  );
}
