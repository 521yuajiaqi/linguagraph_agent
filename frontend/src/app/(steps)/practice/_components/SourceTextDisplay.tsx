"use client";

import { useSessionStore } from "@/lib/stores/session-store";
import { LANGUAGE_PAIRS } from "@/lib/utils/constants";
import { Globe } from "lucide-react";

export function SourceTextDisplay({ text }: { text: string }) {
  const languagePair = useSessionStore((s) => s.languagePair);
  const pairLabel =
    LANGUAGE_PAIRS[languagePair as keyof typeof LANGUAGE_PAIRS]?.label ||
    "翻译";

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-[#eef6ff] px-2.5 py-0.5 text-xs font-medium text-[var(--accent)]">
          <Globe size={12} />
          {pairLabel}
        </span>
        <span className="text-xs text-[var(--muted)]">原文</span>
      </div>
      <p className="whitespace-pre-wrap break-words text-lg leading-relaxed">
        {text}
      </p>
    </div>
  );
}
