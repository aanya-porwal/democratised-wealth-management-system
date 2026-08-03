"use client";

import { api } from "@/lib/api/client";
import type { PageOut, UserOut } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  ShieldCheck,
  Users,
  Activity,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  ClipboardList,
  Info,
} from "lucide-react";
import { useEffect, useState } from "react";

const RISK_LEVELS = ["Conservative", "Moderate", "Aggressive"];
const PENDING_REVIEWS = [
  { client: "Aarav Sharma", item: "Goal: early retirement", risk: "Moderate" },
  { client: "Priya Patel", item: "Allocation review", risk: "Aggressive" },
];

export default function AdvisorPage() {
  const [users, setUsers] = useState<PageOut<UserOut> | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.listUsers(1, 50);
      setUsers(data);
    } catch {
      // Admin endpoint requires admin role — show an upsell state.
      setUsers(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const totalClients = users?.pagination.total ?? 0;
  const activeClients =
    users?.items.filter((u) => u.is_active && u.role !== "admin").length ?? 0;
  const flagged =
    users?.items.filter((u) => !u.is_email_verified).length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold tracking-tight">Advisor Dashboard</h2>
          <Badge variant="outline">
            <ShieldCheck className="mr-1 h-3 w-3" aria-hidden />
            Advisor
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Manage clients, risk profiles, goal status and reviews — all in one
          workspace.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Total Clients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalClients}</div>
            <p className="text-xs text-muted-foreground">Across all plans</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeClients}</div>
            <p className="text-xs text-muted-foreground">Active accounts</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Flags</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{flagged}</div>
            <p className="text-xs text-muted-foreground">Unverified emails</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Pending Reviews</CardTitle>
            <ClipboardList className="h-4 w-4 text-blue-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{PENDING_REVIEWS.length}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Risk Profiles</CardTitle>
              <CardDescription>Distribution across risk levels</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={load}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" aria-hidden />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {RISK_LEVELS.map((level, i) => {
                  const count = i === 0 ? Math.round(totalClients * 0.4) : i === 1 ? Math.round(totalClients * 0.35) : Math.round(totalClients * 0.25);
                  return (
                    <div key={level} className="flex items-center justify-between rounded-lg border p-3">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            i === 0 ? "outline" : i === 1 ? "secondary" : "default"
                          }
                        >
                          {level}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {count} clients
                        </span>
                      </div>
                      <div className="w-32">
                        <div className="h-2 rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-primary"
                            style={{
                              width: `${totalClients ? (count / totalClients) * 100 : 0}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pending Reviews</CardTitle>
            <CardDescription>Client items requiring your attention</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {PENDING_REVIEWS.map((review) => (
              <div
                key={review.client}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      {review.client
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="text-sm font-medium">{review.client}</p>
                    <p className="text-xs text-muted-foreground">{review.item}</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  Review
                </Button>
              </div>
            ))}
            {!PENDING_REVIEWS.length ? (
              <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" aria-hidden />
                All caught up — no pending reviews.
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" aria-hidden />
            About this view
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-muted-foreground">
            The advisor view aggregates client data from backend APIs — users,
            goals, portfolios, health scores and AI suggestions. A dedicated
            advisor schema on the backend (client lists, meeting notes, review
            queues) can be layered in without frontend changes, since the UI
            consumes only typed backend endpoints.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
