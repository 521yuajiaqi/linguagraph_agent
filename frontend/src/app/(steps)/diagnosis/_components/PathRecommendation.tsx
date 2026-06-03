"use client";

import { Check } from "lucide-react";

export function PathRecommendation({
  level,
  path,
}: {
  level: string;
  path: string[];
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">
        推荐学习路径 · {level} 阶段
      </h3>
      <div className="space-y-2">
        {path.map((step, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-lg border border-[var(--line)] bg-[var(--panel-soft)] p-3"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs text-white">
              {i + 1}
            </span>
            <span className="text-sm">{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
