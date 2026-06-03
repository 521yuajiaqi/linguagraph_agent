"use client";

import { Star, TrendingUp, TrendingDown, Minus, ArrowUp } from "lucide-react";
import { DIMENSION_ORDER } from "@/lib/utils/constants";
import type { AbilityStats } from "@/lib/utils/types";

const LEVEL_COLORS: Record<number, string> = {
  0: "var(--muted)",
  1: "var(--amber)",
  2: "var(--accent)",
  3: "var(--purple)",
  4: "var(--green)",
};

const BAR_COLORS: string[] = [
  "var(--accent)",
  "var(--green)",
  "var(--amber)",
  "var(--purple)",
  "var(--teal)",
];

function XpBar({
  dimKey,
  currentLevelXp,
  total,
  cap,
  label,
  color,
}: {
  dimKey: string;
  currentLevelXp: number;
  total: number;
  cap: number;
  label: string;
  color: string;
}) {
  const pct = Math.min(100, Math.max(0, (currentLevelXp / cap) * 100));
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 text-xs font-medium text-slate-600">{label}</span>
      <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="w-20 text-right text-xs tabular-nums text-slate-500">
        {currentLevelXp}/{cap}
      </span>
    </div>
  );
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "improving") return <TrendingUp size={14} className="text-[var(--green)]" />;
  if (trend === "declining") return <TrendingDown size={14} className="text-[var(--amber)]" />;
  return <Minus size={14} className="text-[var(--muted)]" />;
}

function TrendLabel({ trend }: { trend: string }) {
  if (trend === "improving") return "上升中";
  if (trend === "declining") return "需关注";
  if (trend === "new") return "新学员";
  return "平稳";
}

export function AbilityCard({ stats }: { stats: AbilityStats }) {
  const {
    current_level,
    current_title,
    level_index,
    level_description,
    per_dim_progress,
    bottleneck_dim,
    bottleneck_label,
    xp_needed_for_next_level,
    can_advance_level,
    progress_to_next,
    next_title,
    total_exercises,
    recent_trend,
  } = stats;

  const levelColor = LEVEL_COLORS[level_index] ?? "var(--muted)";

  return (
    <div className="rounded-[1.75rem] border border-white/70 bg-white/85 p-5 shadow-[0_14px_40px_rgba(15,23,42,0.05)] backdrop-blur-xl">
      <div className="mb-4 flex items-center gap-4">
        <div
          className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-lg font-extrabold text-white shadow-inner"
          style={{ backgroundColor: levelColor }}
        >
          {current_level}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold">{current_title}</span>
            <span className="text-xs text-[var(--muted)]">
              Lv.{level_index * 5 + (stats.current_rank || 1)}
            </span>
          </div>
          <p className="text-xs text-[var(--muted)]">{level_description}</p>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xs text-slate-500">下一称号</div>
          <div className="flex items-center gap-1 text-sm font-semibold text-slate-900">
            <Star size={13} />
            {next_title}
          </div>
          <div className="text-xs text-slate-500">
            还需 {progress_to_next} 分
          </div>
        </div>
      </div>

      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          五维成长
        </span>
        <span className="text-xs text-slate-500">当前 / 上限</span>
      </div>

      <div className="mb-4 space-y-2.5 rounded-2xl bg-slate-50 p-4">
        {DIMENSION_ORDER.map((dimKey, i) => {
          const dp = per_dim_progress[dimKey];
          if (!dp) return null;
          return (
            <XpBar
              key={dimKey}
              dimKey={dimKey}
              currentLevelXp={dp.current_level_xp}
              total={dp.total}
              cap={dp.cap}
              label={dp.label}
              color={BAR_COLORS[i % BAR_COLORS.length]}
            />
          );
        })}
      </div>

      <div className="mb-3">
        {can_advance_level ? (
          <div className="flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2.5">
            <ArrowUp size={16} className="text-[var(--green)]" />
            <span className="text-sm font-semibold text-emerald-700">
              全部维度已达标，可以进阶！
            </span>
          </div>
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5">
            <p className="text-xs text-slate-600">
              <span className="font-semibold text-amber-600">{bottleneck_label}</span>
              {" 还需 "}
              <span className="font-semibold text-slate-900">{xp_needed_for_next_level}</span>
              {" 分解锁下一等级"}
            </p>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <TrendIcon trend={recent_trend} />
          趋势：<span className="font-medium"><TrendLabel trend={recent_trend} /></span>
        </div>
        <div>
          累计练习：<span className="font-semibold">{total_exercises}</span> 次
        </div>
      </div>
    </div>
  );
}
