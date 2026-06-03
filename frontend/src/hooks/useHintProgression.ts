"use client";

import { useCallback } from "react";
import { usePracticeStore } from "@/lib/stores/practice-store";

export function useHintProgression() {
  const hints = usePracticeStore((s) => s.hints);
  const revealedHints = usePracticeStore((s) => s.revealedHints);
  const revealHint = usePracticeStore((s) => s.revealHint);
  const isHintRevealed = usePracticeStore((s) => s.isHintRevealed);

  const revealedCount = revealedHints.size;
  const totalHints = 4;
  const allRevealed = revealedCount >= totalHints;

  const revealNext = useCallback(() => {
    const order = ["vocabulary", "structure", "grammar", "half_sentence"];
    for (const key of order) {
      if (!isHintRevealed(key)) {
        revealHint(key);
        return key;
      }
    }
    return null;
  }, [revealHint, isHintRevealed]);

  return {
    hints,
    revealedHints,
    revealedCount,
    totalHints,
    allRevealed,
    revealHint,
    revealNext,
    isHintRevealed,
  };
}
