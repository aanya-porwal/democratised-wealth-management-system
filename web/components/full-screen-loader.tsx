import { Landmark } from "lucide-react";

export function FullScreenLoader() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background">
      <Landmark className="h-10 w-10 animate-pulse text-primary" aria-hidden />
      <p className="text-sm text-muted-foreground">Loading your workspace…</p>
    </div>
  );
}
