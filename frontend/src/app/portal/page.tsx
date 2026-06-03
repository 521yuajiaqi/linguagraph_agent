"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PortalStatusSidebar } from "@/components/portal/PortalStatusSidebar";
import { LearningWorkspace } from "@/components/portal/LearningWorkspace";
import { useSessionStore } from "@/lib/stores/session-store";
import { useReviewStore } from "@/lib/stores/review-store";
import { usePracticeStore } from "@/lib/stores/practice-store";
import { useFeedbackStore } from "@/lib/stores/feedback-store";
import * as reviewApi from "@/lib/api/review";
import type { ReviewDashboardResponse } from "@/lib/utils/types";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { AlertTriangle } from "lucide-react";

export default function PortalPage() {
  const router = useRouter();
  const sessionId = useSessionStore((s) => s.sessionId);
  const setReviewPlan = useReviewStore((s) => s.setReviewPlan);
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const learnerProfile = useSessionStore((s) => s.learnerProfile);
  const reviewPlan = useReviewStore((s) => s.reviewPlan);
  const resetPractice = usePracticeStore((s) => s.reset);
  const resetFeedback = useFeedbackStore((s) => s.reset);
  const resetReview = useReviewStore((s) => s.reset);
  const [dashboard, setDashboard] = useState<ReviewDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    reviewApi
      .getDashboard(sessionId)
      .then((data) => setDashboard(data))
      .catch((e) => setError(e instanceof Error ? e.message : "加载门户数据失败"))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (!sessionId) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="先完成会话初始化"
        description="门户需要会话数据。请先进入诊断流程。"
        action={
          <button
          onClick={() => {
            resetPractice();
            resetFeedback();
            resetReview();
            setSessionId("");
            router.push("/diagnosis");
          }}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
          >
            前往诊断
          </button>
        }
      />
    );
  }

  if (loading) return <LoadingSpinner text="加载门户数据..." />;

  if (error) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="门户加载失败"
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
    <div className="relative min-h-[calc(100vh-96px)] overflow-hidden rounded-[2.25rem] border border-white/60 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(241,245,249,0.92))] p-4 shadow-[0_20px_80px_rgba(15,23,42,0.06)] md:p-6">
      <div className="pointer-events-none absolute -right-20 top-0 h-64 w-64 rounded-full bg-[rgba(31,168,146,0.10)] blur-3xl" />
      <div className="pointer-events-none absolute -left-16 top-24 h-72 w-72 rounded-full bg-[rgba(47,109,184,0.10)] blur-3xl" />

      <div className="relative grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <PortalStatusSidebar
          abilityStats={dashboard?.ability_stats ?? null}
          learnerProfile={dashboard?.learner_profile ?? learnerProfile}
          reviewPlan={reviewPlan}
        />
        <LearningWorkspace />
      </div>
    </div>
  );
}
