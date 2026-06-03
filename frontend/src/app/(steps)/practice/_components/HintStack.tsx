"use client";

import { useHintProgression } from "@/hooks/useHintProgression";
import { HINT_LEVELS } from "@/lib/utils/constants";
import { ChevronDown } from "lucide-react";

export function HintStack() {
  const { hints, revealHint, isHintRevealed } = useHintProgression();

  if (!hints) return null;

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-[var(--muted)]">
        分层提示（建议按顺序打开）
      </p>
      <div className="space-y-1">
        {HINT_LEVELS.map(({ key, label, shortcut }) => {
          const revealed = isHintRevealed(key);
          const hintText = hints[key as keyof typeof hints];

          return (
            <div key={key} className="overflow-hidden rounded-lg border border-[var(--line)]">
              <button
                onClick={() => revealHint(key)}
                className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors ${
                  revealed
                    ? "bg-[#eef6ff] text-[var(--accent)]"
                    : "bg-[var(--panel)] text-[var(--muted)] hover:bg-[var(--panel-soft)]"
                }`}
              >
                <span>
                  {label}
                  {!revealed && (
                    <span className="ml-2 text-xs opacity-50">{shortcut}</span>
                  )}
                </span>
                <ChevronDown
                  size={14}
                  className={`transition-transform ${revealed ? "rotate-180" : ""}`}
                />
              </button>
              {revealed && (
                <div className="border-t border-[var(--line)] bg-[var(--panel-soft)] px-3 py-2 text-sm leading-relaxed">
                  {hintText || "暂无提示"}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
