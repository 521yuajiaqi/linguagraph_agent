"use client";

import { useEffect, useState } from "react";
import { useSessionStore } from "@/lib/stores/session-store";
import { useReviewStore } from "@/lib/stores/review-store";
import { useStepStore } from "@/lib/stores/step-store";
import * as api from "@/lib/api/review";
import type { ReviewDashboardResponse, ReviewMistakesResponse } from "@/lib/utils/types";
import { DashboardGrid } from "./_components/DashboardGrid";
import { AccuracyTrendChart } from "./_components/AccuracyTrendChart";
import { ErrorBreakdownChart } from "./_components/ErrorBreakdownChart";
import { MistakeNotebook } from "./_components/MistakeNotebook";
import { ReviewTimeline } from "./_components/ReviewTimeline";
import { DrillGenerator } from "./_components/DrillGenerator";
import { AbilityCard } from "./_components/AbilityCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { EmptyState } from "@/components/shared/EmptyState";
import { AlertTriangle } from "lucide-react";

export default function ReviewPage() {
  const sessionId = useSessionStore((s) => s.sessionId);
  const progressHistory = useReviewStore((s) => s.progressHistory);
  const reviewPlan = useReviewStore((s) => s.reviewPlan);

  const [dashboard, setDashboard] = useState<ReviewDashboardResponse | null>(null);
  const [mistakes, setMistakes] = useState<ReviewMistakesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      api.getDashboard(sessionId),
      api.getMistakes(sessionId),
    ])
      .then(([d, m]) => {
        setDashboard(d);
        setMistakes(m);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "加载复习数据失败"))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (!sessionId) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="请先完成能力诊断"
        description="完成诊断和至少一次练习后可查看复习面板"
      />
    );
  }

  if (loading) return <LoadingSpinner text="加载学习数据..." />;

  if (error) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="数据加载失败"
        description={error}
        action={
          <button
            onClick={() => window.location.reload()}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
          >
            重试
          </button>
        }
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-4xl space-y-6">
        {dashboard && (
          <DashboardGrid
            level={dashboard.current_level}
            trend={dashboard.accuracy_trend}
            reviewDue={dashboard.review_due_count}
            recommendedAction={dashboard.recommended_action}
          />
        )}

        {dashboard?.ability_stats && (
          <AbilityCard stats={dashboard.ability_stats} />
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          {dashboard?.accuracy_trend && dashboard.accuracy_trend.length > 0 && (
            <AccuracyTrendChart data={dashboard.accuracy_trend} />
          )}
          {dashboard?.error_breakdown && dashboard.error_breakdown.length > 0 && (
            <ErrorBreakdownChart data={dashboard.error_breakdown} />
          )}
        </div>

        {mistakes?.mistakes && mistakes.mistakes.length > 0 && (
          <MistakeNotebook mistakes={mistakes.mistakes} />
        )}

        {reviewPlan.length > 0 && <ReviewTimeline plan={reviewPlan} />}

        <DrillGenerator sessionId={sessionId} />
      </div>
    </ErrorBoundary>
  );
}
