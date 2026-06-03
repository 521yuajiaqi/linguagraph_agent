import { Skeleton } from "@/components/shared/LoadingSpinner";

export function LoadingSkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 pt-4">
      <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6">
        <Skeleton className="mb-3 h-4 w-20" />
        <Skeleton className="h-6 w-full" />
        <Skeleton className="mt-2 h-6 w-4/5" />
      </div>

      <div className="space-y-2">
        <Skeleton className="h-4 w-16" />
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>

      <Skeleton className="h-32 w-full rounded-xl" />

      <div className="flex gap-2">
        <Skeleton className="h-10 w-28 rounded-xl" />
        <Skeleton className="h-10 w-16 rounded-xl" />
      </div>

      <p className="text-center text-sm text-[var(--muted)]">
        正在生成适配您水平的练习...
      </p>
    </div>
  );
}
