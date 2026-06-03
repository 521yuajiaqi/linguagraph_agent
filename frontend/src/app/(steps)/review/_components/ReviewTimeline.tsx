import { Calendar, ArrowRight } from "lucide-react";
import type { ReviewTask } from "@/lib/utils/types";

export function ReviewTimeline({ plan }: { plan: ReviewTask[] }) {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-3 text-sm font-semibold">复习时间线</h3>
      <div className="space-y-2">
        {plan.map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg border border-[var(--line)] bg-[var(--panel-soft)] p-3"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--teal)] text-white">
              <Calendar size={14} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{item.mode}</span>
                <span className="text-xs text-[var(--muted)]">{item.due}</span>
              </div>
              <p className="text-sm text-[var(--muted)]">
                {item.focus}：{item.task}
              </p>
            </div>
            <ArrowRight size={16} className="shrink-0 text-[var(--muted)]" />
          </div>
        ))}
      </div>
    </div>
  );
}
