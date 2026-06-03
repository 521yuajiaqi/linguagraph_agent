"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSessionStore } from "@/lib/stores/session-store";
import { useDiagnosisStore } from "@/lib/stores/diagnosis-store";
import { useStepStore } from "@/lib/stores/step-store";
import * as api from "@/lib/api/diagnosis";
import * as sessionApi from "@/lib/api/session";
import { WelcomePanel } from "./_components/WelcomePanel";
import { QuestionCard } from "./_components/QuestionCard";
import { ProgressDots } from "./_components/ProgressDots";
import { DiagnosisReport } from "./_components/DiagnosisReport";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

export default function DiagnosisPage() {
  const router = useRouter();
  const sessionId = useSessionStore((s) => s.sessionId);
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const languagePair = useSessionStore((s) => s.languagePair);
  const setUserLevel = useSessionStore((s) => s.setUserLevel);
  const setInitialized = useSessionStore((s) => s.setInitialized);
  const setLearnerProfile = useSessionStore((s) => s.setLearnerProfile);

  const questions = useDiagnosisStore((s) => s.questions);
  const currentIndex = useDiagnosisStore((s) => s.currentIndex);
  const results = useDiagnosisStore((s) => s.results);
  const setQuestions = useDiagnosisStore((s) => s.setQuestions);
  const setResults = useDiagnosisStore((s) => s.setResults);
  const setCurrentIndex = useDiagnosisStore((s) => s.setCurrentIndex);

  const markCompleted = useStepStore((s) => s.markCompleted);
  const setCurrentStep = useStepStore((s) => s.setCurrentStep);

  const [phase, setPhase] = useState<"welcome" | "questions" | "submitting" | "report">(
    questions.length > 0 && results ? "report" : questions.length > 0 ? "questions" : "welcome"
  );
  const [error, setError] = useState<string | null>(null);

  const startDiagnosis = async () => {
    setError(null);
    try {
      let sid = sessionId;
      if (!sid) {
        const init = await sessionApi.initSession({
          language_pair: languagePair,
          domain: "general",
          mode: "student",
        });
        sid = init.session_id;
        setSessionId(sid);
      }
      const res = await api.startDiagnosis({ session_id: sid! });
      setQuestions(res.questions);
      setCurrentIndex(0);
      setPhase("questions");
    } catch (e) {
      setError(e instanceof Error ? e.message : "无法加载诊断题目");
    }
  };

  const submitDiagnosis = async () => {
    setPhase("submitting");
    setError(null);
    try {
      const answers = useDiagnosisStore.getState().getAnswers();
      const res = await api.submitDiagnosis({
        session_id: sessionId!,
        answers,
      });
      setResults(res);
      setUserLevel(res.estimated_level);
      setLearnerProfile(res.learner_profile);
      setInitialized(true);
      markCompleted("diagnosis");
      setPhase("report");
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交诊断失败");
      setPhase("questions");
    }
  };

  const goToPractice = () => {
    setCurrentStep("practice");
    router.push("/practice");
  };

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-2xl">
        {phase === "welcome" && (
          <WelcomePanel onStart={startDiagnosis} error={error} />
        )}

        {phase === "questions" && questions.length > 0 && (
          <>
            <ProgressDots
              total={questions.length}
              current={currentIndex}
              onDotClick={setCurrentIndex}
            />
            <QuestionCard
              question={questions[currentIndex]}
              onSubmit={submitDiagnosis}
              isLast={currentIndex === questions.length - 1}
            />
          </>
        )}

        {phase === "submitting" && (
          <LoadingSpinner text="正在分析您的翻译能力..." />
        )}

        {phase === "report" && results && (
          <DiagnosisReport results={results} onContinue={goToPractice} />
        )}

        {error && phase === "welcome" && (
          <p className="mt-4 text-center text-sm text-[var(--danger)]">{error}</p>
        )}
      </div>
    </ErrorBoundary>
  );
}
