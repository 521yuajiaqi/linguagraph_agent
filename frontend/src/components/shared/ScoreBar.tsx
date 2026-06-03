import { getScoreColor } from "@/lib/utils/formatters";

export function ScoreBar({
  label,
  score,
  max = 5,
}: {
  label: string;
  score: number;
  max?: number;
}) {
  const pct = Math.max(0, Math.min(100, (score / max) * 100));
  const color = getScoreColor((score / max) * 100);

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-20 shrink-0 text-[var(--muted)]">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--line)]">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="w-8 text-right font-semibold tabular-nums">
        {score}/{max}
      </span>
    </div>
  );
}
