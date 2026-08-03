"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { FullProfile } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { User, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

export default function ProfilePage() {
  const [profile, setProfile] = useState<FullProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getFullProfile();
      setProfile(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Profile</h2>
          <p className="text-sm text-muted-foreground">
            Your demographic, financial and behavioral profile.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="mr-2 h-4 w-4" aria-hidden />
          Refresh
        </Button>
      </div>

      {loading || !profile ? (
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl border bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-4 w-4 text-primary" aria-hidden />
                  Demographics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {profile.profile ? (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Name</span>
                      <span className="font-medium">{profile.profile.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Age</span>
                      <span className="font-medium">{profile.profile.age}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Dependents</span>
                      <span className="font-medium">{profile.profile.dependents}</span>
                    </div>
                  </>
                ) : (
                  <p className="text-muted-foreground">
                    Demographic profile not set up yet.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Financial Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {profile.financial_profile ? (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly income</span>
                      <span className="font-medium">
                        {formatCurrency(profile.financial_profile.monthly_income, { compact: true })}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fixed expenses</span>
                      <span className="font-medium">
                        {formatCurrency(profile.financial_profile.monthly_fixed_expenses, { compact: true })}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total debt</span>
                      <span className="font-medium">
                        {formatCurrency(profile.financial_profile.total_debt, { compact: true })}
                      </span>
                    </div>
                  </>
                ) : (
                  <p className="text-muted-foreground">
                    Financial profile not set up yet.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Score</span>
                  <span className="font-medium">
                    {profile.risk?.score ?? profile.risk?.risk_score ?? "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Category</span>
                  <Badge variant="secondary">{profile.risk?.risk_category ?? "—"}</Badge>
                </div>
                {profile.risk?.explanation ? (
                  <p className="pt-2 text-xs leading-relaxed text-muted-foreground">
                    {profile.risk.explanation}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
