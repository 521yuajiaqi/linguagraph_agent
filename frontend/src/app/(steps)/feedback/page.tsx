"use client";

import { useRouter } from "next/navigation";
import { useFeedbackStore } from "@/lib/stores/feedback-store";
import { usePracticeStore } from "@/lib/stores/practice-store";
import { useStepStore } from "@/lib/stores/step-store";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { EmptyState } from "@/components/shared/EmptyState";
import { ScoreHero } from "./_components/ScoreHero";
import { DimensionRadar } from "./_components/DimensionRadar";
import { DimensionBarList } from "./_components/DimensionBarList";
import { ErrorTagCloud } from "./_components/ErrorTagCloud";
import { IssueAccordion } from "./_components/IssueAccordion";
import { RevisionAdviceCard } from "./_components/RevisionAdviceCard";
import { AlternativesPanel } from "./_components/AlternativesPanel";

import { NextActionsBar } from "./_components/NextActionsBar";
import { FileSearch } from "lucide-react";

export default function FeedbackPage() {
  const router = useRouter();
  const evaluation = useFeedbackStore((s) => s.evaluation);
  const nextExercises = useFeedbackStore((s) => s.nextExercises);
  const focusAreas = useFeedbackStore((s) => s.focusAreas);
  const sessionSummary = useFeedbackStore((s) => s.sessionSummary);
  const setCurrentStep = useStepStore((s) => s.setCurrentStep);
  const markCompleted = useStepStore((s) => s.markCompleted);

  if (!evaluation) {
    return (
      <EmptyState
        icon={<FileSearch size={40} />}
        title="暂无批改结果"
        description="请先完成翻译练习并提交"
        action={
          <button
            onClick={() => {
              setCurrentStep("practice");
              router.push("/practice");
            }}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
          >
            前往练习
          </button>
        }
      />
    );
  }

  const handleRetry = () => {
    setCurrentStep("practice");
    router.push("/practice");
  };

  const handleNext = () => {
    usePracticeStore.getState().reset();
    setCurrentStep("practice");
    router.push("/practice");
  };

  const handleReview = () => {
    markCompleted("feedback");
    setCurrentStep("review");
    router.push("/review");
  };

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-3xl space-y-6">
        <ScoreHero
          score={evaluation.score}
          review={evaluation.review}
        />

        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <DimensionRadar
              scores={evaluation.dimension_scores}
              labels={evaluation.dimension_labels}
            />
          </div>
          <div className="lg:col-span-2 space-y-4">
            <DimensionBarList
              scores={evaluation.dimension_scores}
              labels={evaluation.dimension_labels}
            />
          </div>
        </div>

        <ErrorTagCloud
          tags={evaluation.error_tags}
          focusAreas={focusAreas}
        />

        <IssueAccordion issues={evaluation.major_issues} />

        <RevisionAdviceCard advice={evaluation.revision_advice} />

        <AlternativesPanel
          reference={evaluation.recommended_translation}
          alternatives={evaluation.acceptable_alternatives}
        />

        {sessionSummary && (
          <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
            <p className="text-sm leading-relaxed text-[var(--muted)]">
              {sessionSummary}
            </p>
          </div>
        )}

        <NextActionsBar
          onRetry={handleRetry}
          onNext={handleNext}
          onReview={handleReview}
        />
      </div>
    </ErrorBoundary>
  );
}
