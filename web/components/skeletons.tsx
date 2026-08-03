import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export interface StatSkeletonProps {
  className?: string;
  lines?: number;
}

export function StatSkeleton({ className, lines = 3 }: StatSkeletonProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-40" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-3 w-full" />
      ))}
    </div>
  );
}

export function CardGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <StatSkeleton key={i} />
      ))}
    </div>
  );
}
