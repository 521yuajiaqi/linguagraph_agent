"use client";

import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

export default function StepsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ErrorBoundary>
      <div className="rounded-[2.25rem] border border-white/60 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(241,245,249,0.92))] p-3 shadow-[0_20px_80px_rgba(15,23,42,0.06)]">
        <AppShell>{children}</AppShell>
      </div>
    </ErrorBoundary>
  );
}
