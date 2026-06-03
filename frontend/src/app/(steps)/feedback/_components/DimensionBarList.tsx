import { ScoreBar } from "@/components/shared/ScoreBar";
import { DIMENSION_ORDER, DIMENSION_LABELS } from "@/lib/utils/constants";
import type { DimensionScores } from "@/lib/utils/types";

export function DimensionBarList({
  scores,
  labels,
}: {
  scores: DimensionScores;
  labels: Record<string, string>;
}) {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-3 text-sm font-semibold">各维度详情</h3>
      <div className="space-y-2.5">
        {DIMENSION_ORDER.map((dim) => {
          const score = scores[dim as keyof DimensionScores];
          if (score === undefined) return null;
          return (
            <ScoreBar
              key={dim}
              label={labels[dim] || DIMENSION_LABELS[dim] || dim}
              score={score}
              max={5}
            />
          );
        })}
      </div>
    </div>
  );
}
