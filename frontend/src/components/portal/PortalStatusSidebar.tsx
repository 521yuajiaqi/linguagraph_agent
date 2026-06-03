"use client";

import {
  Trophy,
  ShieldAlert,
  Sparkles,
  CalendarDays,
  Orbit,
  TrendingUp,
  Target,
} from "lucide-react";
import type { LearnerProfile, ReviewTask, AbilityStats } from "@/lib/utils/types";
import { AbilityCard } from "@/app/(steps)/review/_components/AbilityCard";

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[1.5rem] border border-white/70 bg-white/82 p-4 shadow-[0_14px_40px_rgba(15,23,42,0.05)] backdrop-blur-xl">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-[var(--accent)]">
          {icon}
        </span>
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function TagList({
  items,
  tone,
  emptyLabel,
}: {
  items: string[];
  tone: "good" | "warn";
  emptyLabel: string;
}) {
  if (!items.length) {
    return <p className="text-sm text-[var(--muted)]">{emptyLabel}</p>;
  }

  const toneClass =
    tone === "good"
      ? "border-[#9bd2b6] bg-[#f2fbf6] text-[var(--green)]"
      : "border-[#f2c36b] bg-[#fff7e6] text-[#754200]";

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className={`rounded-full border px-2.5 py-1 text-xs ${toneClass}`}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function MiniCalendar({ plan }: { plan: ReviewTask[] }) {
  const days = Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() + index);
    const label = `${date.getMonth() + 1}/${date.getDate()}`;
    const dueItems = plan.filter((item) => item.due.includes(label));
    return {
      label,
      weekday: date.toLocaleDateString("zh-CN", { weekday: "short" }),
      count: dueItems.length,
      focus: dueItems[0]?.focus ?? "",
    };
  });

  return (
    <div className="grid grid-cols-7 gap-2">
      {days.map((day) => (
        <div
          key={day.label}
          className={`rounded-xl border p-2 text-center transition-colors ${
            day.count > 0
              ? "border-[var(--teal)] bg-[#effaf8]"
              : "border-[var(--line)] bg-[var(--panel-soft)]"
          }`}
        >
          <div className="text-[10px] text-[var(--muted)]">{day.weekday}</div>
          <div className="mt-1 text-sm font-semibold">{day.label}</div>
          <div className="mt-1 text-[10px] text-[var(--muted)]">
            {day.count > 0 ? `${day.count} 项` : "空闲"}
          </div>
          {day.focus && (
            <div className="mt-1 line-clamp-2 text-[10px] text-[var(--teal)]">
              {day.focus}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function PortalStatusSidebar({
  abilityStats,
  learnerProfile,
  reviewPlan,
}: {
  abilityStats: AbilityStats | null;
  learnerProfile: LearnerProfile | null;
  reviewPlan: ReviewTask[];
}) {
  const strengths = learnerProfile?.performance_strengths ?? [];
  const risks = learnerProfile?.performance_risks ?? [];
  const titleLabel = abilityStats
    ? `${abilityStats.current_level} · ${abilityStats.current_title}`
    : "等待诊断";
  const nextGoal = abilityStats?.next_title ?? "初级译者";
  const trend = abilityStats?.recent_trend ?? "new";
  const trendLabel =
    trend === "improving" ? "稳步上升" : trend === "declining" ? "需要关注" : "新开始";

  return (
    <aside className="space-y-4 xl:sticky xl:top-6 self-start">
      <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(233,244,255,0.92))] p-5 shadow-[0_18px_60px_rgba(15,23,42,0.08)]">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-white/80 px-3 py-1 text-xs font-semibold text-[var(--accent)]">
              <Orbit size={12} />
              学习状态区
            </div>
            <h2 className="mt-3 text-2xl font-black tracking-tight text-slate-900">
              成长仪表盘
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              用五维能力、优势短板和未来规划，统一管理你的学习节奏。
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-white/80 bg-white/80 p-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Trophy size={12} />
              当前称号
            </div>
            <div className="mt-1 text-lg font-bold text-slate-900">{titleLabel}</div>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white/80 p-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <TrendingUp size={12} />
              学习趋势
            </div>
            <div className="mt-1 text-lg font-bold text-slate-900">{trendLabel}</div>
          </div>
        </div>

        <div className="mt-3 rounded-2xl border border-white/80 bg-white/80 p-3">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Target size={12} />
            下一目标
          </div>
          <div className="mt-1 text-sm font-semibold text-slate-900">{nextGoal}</div>
        </div>
      </section>

      {abilityStats ? (
        <AbilityCard stats={abilityStats} />
      ) : (
        <Section title="学习称号" icon={<Trophy size={16} />}>
          <p className="text-sm text-[var(--muted)]">
            完成诊断和至少一次练习后，这里会展示五维成长、称号和升级路径。
          </p>
        </Section>
      )}

      <Section title="当前优势" icon={<Sparkles size={16} />}>
        <TagList items={strengths} tone="good" emptyLabel="尚未形成稳定优势。" />
      </Section>

      <Section title="当前薄弱项" icon={<ShieldAlert size={16} />}>
        <TagList items={risks} tone="warn" emptyLabel="尚未识别出明确薄弱项。" />
      </Section>

      <Section title="未来规划" icon={<CalendarDays size={16} />}>
        <MiniCalendar plan={reviewPlan} />
      </Section>
    </aside>
  );
}
