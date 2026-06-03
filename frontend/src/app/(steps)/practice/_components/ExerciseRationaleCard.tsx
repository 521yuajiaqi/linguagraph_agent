"use client";

import type { ExerciseBlueprint, SelectedExercise } from "@/lib/utils/types";
import { Tag } from "@/components/shared/Tag";

export function ExerciseRationaleCard({
  blueprint,
  selectedExercise,
}: {
  blueprint: ExerciseBlueprint | null;
  selectedExercise: SelectedExercise | null;
}) {
  if (!blueprint) return null;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">出题说明</h3>
        <Tag label={`主维度：${blueprint.primary_focus}`} variant="accent" />
      </div>
      <div className="grid gap-2 text-sm text-[var(--muted)]">
        <p>选择原因：{blueprint.selection_reason}</p>
        <p>
          难度窗口：{blueprint.difficulty_band.floor} - {blueprint.difficulty_band.ceiling}
        </p>
        <p>句法负荷：{blueprint.syntax_load}，术语负荷：{blueprint.terminology_load}</p>
        <p>教学意图：{blueprint.teaching_intent}</p>
        {selectedExercise?.focus_tags?.length ? (
          <p>候选标签：{selectedExercise.focus_tags.join("、")}</p>
        ) : null}
        {selectedExercise?.domain ? <p>候选领域：{selectedExercise.domain}</p> : null}
      </div>
    </div>
  );
}
