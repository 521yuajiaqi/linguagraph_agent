import { RotateCcw, ArrowRight, BarChart3 } from "lucide-react";

export function NextActionsBar({
  onRetry,
  onNext,
  onReview,
}: {
  onRetry: () => void;
  onNext: () => void;
  onReview: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 border-t border-[var(--line)] pt-6">
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--panel)] px-5 py-2.5 text-sm font-medium text-[var(--text)] hover:bg-[var(--panel-soft)] transition-colors"
      >
        <RotateCcw size={16} />
        重译一次
      </button>

      <button
        onClick={onNext}
        className="inline-flex items-center gap-2 rounded-xl bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
      >
        <ArrowRight size={16} />
        下一题
      </button>

      <button
        onClick={onReview}
        className="inline-flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--panel)] px-5 py-2.5 text-sm font-medium text-[var(--teal)] hover:bg-[var(--panel-soft)] transition-colors"
      >
        <BarChart3 size={16} />
        查看复习计划
      </button>
    </div>
  );
}
