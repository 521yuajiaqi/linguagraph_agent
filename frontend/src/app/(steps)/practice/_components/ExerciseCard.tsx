"use client";

import { useState } from "react";
import { usePracticeStore } from "@/lib/stores/practice-store";
import { useHintProgression } from "@/hooks/useHintProgression";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { SourceTextDisplay } from "./SourceTextDisplay";
import { TranslationEditor } from "./TranslationEditor";
import { HintStack } from "./HintStack";
import { ReferenceReveal } from "./ReferenceReveal";
import { ActionToolbar } from "./ActionToolbar";

export function ExerciseCard({
  onSubmit,
  onNewExercise,
}: {
  onSubmit: (translation: string) => Promise<void>;
  onNewExercise: () => void;
}) {
  const sourceText = usePracticeStore((s) => s.sourceText);
  const referenceTranslation = usePracticeStore((s) => s.referenceTranslation);
  const userTranslation = usePracticeStore((s) => s.userTranslation);
  const setUserTranslation = usePracticeStore((s) => s.setUserTranslation);
  const isSubmitting = usePracticeStore((s) => s.isSubmitting);
  const { revealNext } = useHintProgression();

  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!userTranslation.trim() || isSubmitting) return;
    setSubmitted(true);
    await onSubmit(userTranslation);
  };

  useKeyboardShortcuts([
    { key: "Enter", ctrl: true, handler: handleSubmit },
    { key: "1", ctrl: true, handler: revealNext },
  ]);

  return (
    <div className="space-y-4">
      <SourceTextDisplay text={sourceText} />

      <HintStack />

      <TranslationEditor
        value={userTranslation}
        onChange={setUserTranslation}
        disabled={isSubmitting}
      />

      <ActionToolbar
        onSubmit={handleSubmit}
        onNewExercise={onNewExercise}
        canSubmit={userTranslation.trim().length > 0}
        isSubmitting={isSubmitting}
      />

      {submitted && (
        <ReferenceReveal reference={referenceTranslation} />
      )}
    </div>
  );
}
