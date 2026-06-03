"use client";

import { useSessionStore } from "@/lib/stores/session-store";
import { useReviewStore } from "@/lib/stores/review-store";
import { StepIndicator } from "./StepIndicator";
import { BookOpen, Target, TrendingUp, Calendar } from "lucide-react";

export function Sidebar() {
  const userLevel = useSessionStore((s) => s.userLevel);
  const languagePair = useSessionStore((s) => s.languagePair);
  const learnerProfile = useSessionStore((s) => s.learnerProfile);
  const progressHistory = useReviewStore((s) => s.progressHistory);

  const pairLabel = languagePair === "zh_ru" ? "中译俄" : "俄译中";
  const todayCount = progressHistory.filter((r) => {
    const d = new Date(r.at);
    const today = new Date();
    return (
      d.getDate() === today.getDate() &&
      d.getMonth() === today.getMonth() &&
      d.getFullYear() === today.getFullYear()
    );
  }).length;

  const recentAvg =
    progressHistory.length > 0
      ? Math.round(
          progressHistory.slice(-5).reduce((a, r) => a + r.score, 0) /
            Math.min(5, progressHistory.length)
        )
      : null;

  return (
    <aside className="flex w-[260px] flex-col gap-4 border-r border-[var(--line)] bg-[var(--panel)] p-5 overflow-y-auto h-full">
      <StepIndicator />

      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
          学习概览
        </h3>

        <div className="grid grid-cols-2 gap-2">
          <StatCard
            icon={<Target size={16} />}
            label="当前方向"
            value={pairLabel}
          />
          <StatCard
            icon={<BookOpen size={16} />}
            label="估计水平"
            value={userLevel || "未诊断"}
          />
          <StatCard
            icon={<TrendingUp size={16} />}
            label="近期均分"
            value={recentAvg != null ? `${recentAvg}` : "--"}
          />
          <StatCard
            icon={<Calendar size={16} />}
            label="今日练习"
            value={`${todayCount} 题`}
          />
        </div>

        {learnerProfile?.performance_strengths &&
          learnerProfile.performance_strengths.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-[var(--muted)]">强项</p>
              <div className="flex flex-wrap gap-1">
                {learnerProfile.performance_strengths.slice(0, 3).map((s) => (
                  <span
                    key={s}
                    className="rounded-full border border-[#9bd2b6] bg-[#f2fbf6] px-2 py-0.5 text-xs text-[var(--green)]"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

        {learnerProfile?.performance_risks &&
          learnerProfile.performance_risks.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-[var(--muted)]">待提升</p>
              <div className="flex flex-wrap gap-1">
                {learnerProfile.performance_risks.slice(0, 3).map((r) => (
                  <span
                    key={r}
                    className="rounded-full border border-[#f2c36b] bg-[#fff7e6] px-2 py-0.5 text-xs text-[#754200]"
                  >
                    {r}
                  </span>
                ))}
              </div>
            </div>
          )}
      </div>
    </aside>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--line)] bg-[var(--panel-soft)] p-3">
      <div className="mb-1 text-[var(--muted)]">{icon}</div>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-[var(--muted)]">{label}</div>
    </div>
  );
}
