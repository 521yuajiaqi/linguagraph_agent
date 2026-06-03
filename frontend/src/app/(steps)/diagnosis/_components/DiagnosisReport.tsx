"use client";

import type { DiagnosisSubmitResponse } from "@/lib/utils/types";
import { DIMENSION_LABELS } from "@/lib/utils/constants";
import { LevelBadge } from "./LevelBadge";
import { WeaknessChart } from "./WeaknessChart";
import { PathRecommendation } from "./PathRecommendation";
import { ArrowRight } from "lucide-react";

export function DiagnosisReport({
  results,
  onContinue,
}: {
  results: DiagnosisSubmitResponse;
  onContinue: () => void;
}) {
  return (
    <div className="space-y-6 py-4">
      <div className="text-center">
        <LevelBadge level={results.estimated_level} />
        <p className="mt-3 text-[var(--muted)]">
          诊断完成！以下是您的学习画像
        </p>
      </div>

      <WeaknessChart
        dimensionScores={results.dimension_scores}
        strengths={results.strengths}
        weaknesses={results.weaknesses}
      />

      <PathRecommendation
        level={results.estimated_level}
        path={results.recommended_path}
      />

      <div className="text-center">
        <button
          onClick={onContinue}
          className="inline-flex items-center gap-2 rounded-xl bg-[var(--accent)] px-8 py-3 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
        >
          开始学习
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
