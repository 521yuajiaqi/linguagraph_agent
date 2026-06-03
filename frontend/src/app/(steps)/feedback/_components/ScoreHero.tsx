"use client";

import { useEffect, useState } from "react";
import { getScoreColor } from "@/lib/utils/formatters";

export function ScoreHero({
  score,
  review,
}: {
  score: number | null;
  review?: string;
}) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    if (score == null) return;
    const duration = 800;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimated(Math.round(score * eased));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  const color = getScoreColor(score);
  const label =
    score == null
      ? "未评分"
      : score >= 85
        ? "优秀"
        : score >= 70
          ? "良好"
          : score >= 50
            ? "一般"
            : "需加强";

  return (
    <div className="text-center">
      <div
        className="inline-flex flex-col items-center rounded-2xl px-12 py-6"
        style={{ backgroundColor: `${color}10`, borderColor: `${color}30`, border: `1px solid ${color}30` }}
      >
        <span
          className="text-5xl font-extrabold tabular-nums"
          style={{ color }}
        >
          {score != null ? animated : "--"}
        </span>
        <span className="mt-1 text-sm font-medium" style={{ color }}>
          {label}
        </span>
        {review && (
          <p className="mt-3 max-w-md text-sm text-[var(--muted)]">
            {review}
          </p>
        )}
      </div>
    </div>
  );
}
