"use client";

import { Send, RefreshCw, Loader2 } from "lucide-react";

interface Props {
  onSubmit: () => void;
  onNewExercise: () => void;
  canSubmit: boolean;
  isSubmitting: boolean;
}

export function ActionToolbar({
  onSubmit,
  onNewExercise,
  canSubmit,
  isSubmitting,
}: Props) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onSubmit}
        disabled={!canSubmit || isSubmitting}
        className="inline-flex items-center gap-2 rounded-xl bg-[var(--accent)] px-6 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        {isSubmitting ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Send size={16} />
        )}
        {isSubmitting ? "批改中..." : "提交批改"}
      </button>

      <button
        onClick={onNewExercise}
        disabled={isSubmitting}
        className="inline-flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--panel)] px-4 py-2.5 text-sm text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--panel-soft)] disabled:opacity-40 transition-colors"
      >
        <RefreshCw size={16} />
        换题
      </button>
    </div>
  );
}
