"use client";

import { ScoreBar } from "@/components/shared/ScoreBar";
import { DIMENSION_ORDER, DIMENSION_LABELS } from "@/lib/utils/constants";
import type { DimensionScores } from "@/lib/utils/types";
import { TrendingUp, AlertTriangle } from "lucide-react";

export function WeaknessChart({
  dimensionScores,
  strengths,
  weaknesses,
}: {
  dimensionScores: DimensionScores;
  strengths: string[];
  weaknesses: string[];
}) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold">能力维度分析</h3>

      <div className="space-y-2">
        {DIMENSION_ORDER.map((dim) => {
          const score = dimensionScores[dim as keyof DimensionScores] || 3;
          return (
            <ScoreBar
              key={dim}
              label={DIMENSION_LABELS[dim] || dim}
              score={score}
              max={5}
            />
          );
        })}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-[#9bd2b6] bg-[#f2fbf6] p-3">
          <div className="mb-1 flex items-center gap-1.5 text-[var(--green)]">
            <TrendingUp size={14} />
            <span className="text-xs font-semibold">强项</span>
          </div>
          <p className="text-sm">{strengths.join("、") || "暂无"}</p>
        </div>
        <div className="rounded-lg border border-[#f2c36b] bg-[#fff7e6] p-3">
          <div className="mb-1 flex items-center gap-1.5 text-[#754200]">
            <AlertTriangle size={14} />
            <span className="text-xs font-semibold">待提升</span>
          </div>
          <p className="text-sm">{weaknesses.join("、") || "暂无"}</p>
        </div>
      </div>
    </div>
  );
}
