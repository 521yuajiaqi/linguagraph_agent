"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSessionStore } from "@/lib/stores/session-store";
import { usePracticeStore } from "@/lib/stores/practice-store";
import { useFeedbackStore } from "@/lib/stores/feedback-store";
import { useStepStore } from "@/lib/stores/step-store";
import { useReviewStore } from "@/lib/stores/review-store";
import * as api from "@/lib/api/practice";
import { ExerciseCard } from "./_components/ExerciseCard";
import { ExerciseRationaleCard } from "./_components/ExerciseRationaleCard";
import { LoadingSkeleton } from "./_components/LoadingSkeleton";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { EmptyState } from "@/components/shared/EmptyState";
import { AlertTriangle } from "lucide-react";

export default function PracticePage() {
  const router = useRouter();
  const sessionId = useSessionStore((s) => s.sessionId);
  const focusAreas = useFeedbackStore((s) => s.focusAreas);

  const isGenerating = usePracticeStore((s) => s.isGenerating);
  const setIsGenerating = usePracticeStore((s) => s.setIsGenerating);
  const sourceText = usePracticeStore((s) => s.sourceText);
  const exerciseBlueprint = usePracticeStore((s) => s.exerciseBlueprint);
  const selectedExercise = usePracticeStore((s) => s.selectedExercise);
  const setExercise = usePracticeStore((s) => s.setExercise);
  const resetPractice = usePracticeStore((s) => s.reset);

  const setFeedback = useFeedbackStore((s) => s.setFeedback);
  const setCurrentStep = useStepStore((s) => s.setCurrentStep);
  const markCompleted = useStepStore((s) => s.markCompleted);
  const addProgressRecord = useReviewStore((s) => s.addProgressRecord);

  const [error, setError] = useState<string | null>(null);

  const generateExercise = useCallback(async () => {
    if (!sessionId) return;
    setError(null);
    resetPractice();
    setIsGenerating(true);
    try {
      const res = await api.generateExercise({
        session_id: sessionId,
        focus_areas: focusAreas,
      });
      setExercise(
        res.exercise_id,
        res.source_text,
        res.reference_translation,
        res.hints,
        res.vocabulary_cards,
        res.grammar_analysis,
        res.difficulty,
        res.exercise_blueprint ?? null,
        res.selected_exercise ?? null
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "练习生成失败");
    } finally {
      setIsGenerating(false);
    }
  }, [sessionId, focusAreas, resetPractice, setExercise, setIsGenerating]);

  useEffect(() => {
    if (!sessionId || sourceText) return;
    const timer = window.setTimeout(() => {
      void generateExercise();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [sessionId, sourceText, generateExercise]);

  const handleSubmit = async (userTranslation: string) => {
    if (!sessionId) return;
    const state = usePracticeStore.getState();
    setError(null);
    const practiceState = usePracticeStore.getState();
    practiceState.setIsSubmitting(true);
    try {
      const res = await api.evaluateTranslation({
        session_id: sessionId,
        exercise_id: state.exerciseId || "",
        user_translation: userTranslation,
      });
      setFeedback(
        res.evaluation,
        res.next_exercises,
        res.focus_areas,
        res.session_summary,
        res.mistake_record,
        res.vocabulary_cards,
        res.grammar_analysis,
        res.diagnostics
      );
      if (res.evaluation.score != null) {
        addProgressRecord({
          key: `${useSessionStore.getState().languagePair}:${useSessionStore.getState().userLevel}:${useSessionStore.getState().domain}`,
          at: new Date().toISOString(),
          score: res.evaluation.score,
          dimensions: res.evaluation.dimension_scores as unknown as Record<string, number>,
          dimensionLabels: res.evaluation.dimension_labels as Record<string, string>,
          tags: res.evaluation.error_tags || [],
          source: state.sourceText,
        });
      }
      markCompleted("practice");
      setCurrentStep("feedback");
      router.push("/feedback");
    } catch (e) {
      setError(e instanceof Error ? e.message : "评估提交失败");
    } finally {
      practiceState.setIsSubmitting(false);
    }
  };

  if (!sessionId) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="请先完成能力诊断"
        description="诊断帮助系统了解您的水平，生成匹配的练习"
        action={
          <button
            onClick={() => router.push("/diagnosis")}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
          >
            前往诊断
          </button>
        }
      />
    );
  }

  if (isGenerating) return <LoadingSkeleton />;

  if (error && !sourceText) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="练习生成失败"
        description={error}
        action={
          <button
            onClick={generateExercise}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
          >
            重试
          </button>
        }
      />
    );
  }

  if (!sourceText) return <LoadingSkeleton />;

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-2xl space-y-4">
        <ExerciseRationaleCard
          blueprint={exerciseBlueprint}
          selectedExercise={selectedExercise}
        />
        <ExerciseCard onSubmit={handleSubmit} onNewExercise={generateExercise} />
        {error && (
          <p className="mt-3 text-center text-sm text-[var(--danger)]">{error}</p>
        )}
      </div>
    </ErrorBoundary>
  );
}
