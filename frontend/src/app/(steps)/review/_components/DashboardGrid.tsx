import { Target, TrendingUp, Calendar, Lightbulb } from "lucide-react";

interface Props {
  level: string;
  trend: Array<{ date: string; score: number }>;
  reviewDue: number;
  recommendedAction: string;
}

export function DashboardGrid({ level, trend, reviewDue, recommendedAction }: Props) {
  const recentAvg =
    trend.length > 0
      ? Math.round(trend.slice(-5).reduce((a, r) => a + r.score, 0) / Math.min(5, trend.length))
      : null;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard
        icon={<Target size={20} />}
        label="当前水平"
        value={level}
        color="var(--purple)"
      />
      <StatCard
        icon={<TrendingUp size={20} />}
        label="近期均分"
        value={recentAvg != null ? `${recentAvg}` : "--"}
        color="var(--accent)"
      />
      <StatCard
        icon={<Calendar size={20} />}
        label="待复习"
        value={`${reviewDue}`}
        color="var(--amber)"
      />
      <StatCard
        icon={<Lightbulb size={20} />}
        label="推荐"
        value={recommendedAction}
        color="var(--teal)"
        small
      />
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
  small,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  small?: boolean;
}) {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <div className="mb-2" style={{ color }}>
        {icon}
      </div>
      <div className={`font-bold ${small ? "text-sm" : "text-2xl"}`}>{value}</div>
      <div className="text-xs text-[var(--muted)]">{label}</div>
    </div>
  );
}
