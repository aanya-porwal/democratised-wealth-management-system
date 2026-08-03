"use client";

import type { LucideIcon } from "lucide-react";
import { Construction } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export interface PagePlaceholderProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionHref?: string;
  actionLabel?: string;
}

export function PagePlaceholder({
  title,
  description,
  icon: Icon = Construction,
  actionHref,
  actionLabel,
}: PagePlaceholderProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-4 py-20 text-center">
          <div className="rounded-full border bg-muted p-4">
            <Icon className="h-8 w-8 text-primary" aria-hidden />
          </div>
          <div className="max-w-md space-y-1">
            <h3 className="text-lg font-medium">This module is in progress</h3>
            <p className="text-sm text-muted-foreground">
              The {title.toLowerCase()} interface is being built. Backend APIs are
              ready — the frontend wires into them here.
            </p>
          </div>
          {actionHref ? (
            <Button asChild variant="outline">
              <a href={actionHref}>{actionLabel ?? "Go back"}</a>
            </Button>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
