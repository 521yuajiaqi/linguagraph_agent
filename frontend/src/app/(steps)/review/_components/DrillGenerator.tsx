"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { usePracticeStore } from "@/lib/stores/practice-store";
import { useStepStore } from "@/lib/stores/step-store";
import * as api from "@/lib/api/review";
import { Tag } from "@/components/shared/Tag";
import { Target, Loader2 } from "lucide-react";
import type { ReviewDrillResponse } from "@/lib/utils/types";

export function DrillGenerator({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const setCurrentStep = useStepStore((s) => s.setCurrentStep);
  const setExercise = usePracticeStore((s) => s.setExercise);

  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [drills, setDrills] = useState<ReviewDrillResponse["drills"] | null>(null);

  const commonTags = ["格错误", "动词体错误", "前置词搭配错误", "中文直译痕迹", "漏译", "语义偏离"];

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await api.generateDrill({
        session_id: sessionId,
        error_types: selectedTags,
        count: 3,
      });
      setDrills(res.drills);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const startDrill = (drill: ReviewDrillResponse["drills"][0]) => {
    setExercise(
      drill.id,
      drill.source_text,
      drill.reference_translation,
      drill.hints,
      [],
      {} as never,
      {} as never
    );
    setCurrentStep("practice");
    router.push("/practice");
  };

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-3 text-sm font-semibold">专项训练生成器</h3>
      <p className="mb-3 text-sm text-[var(--muted)]">
        选择要针对性训练的错误类型，系统会生成专项练习
      </p>

      <div className="mb-3 flex flex-wrap gap-1.5">
        {commonTags.map((tag) => (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            className={selectedTags.includes(tag) ? "ring-2 ring-[var(--accent)] rounded-full" : ""}
          >
            <Tag
              label={tag}
              variant={selectedTags.includes(tag) ? "warn" : "default"}
            />
          </button>
        ))}
      </div>

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-xl bg-[var(--teal)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        {loading ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Target size={16} />
        )}
        {loading ? "生成中..." : "生成专项训练"}
      </button>

      {drills && drills.length > 0 && (
        <div className="mt-4 space-y-2">
          {drills.map((drill) => (
            <div
              key={drill.id}
              className="flex items-center justify-between rounded-lg border border-[var(--line)] bg-[var(--panel-soft)] p-3"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{drill.source_text}</p>
                <span className="text-xs text-[var(--muted)]">{drill.focus}</span>
              </div>
              <button
                onClick={() => startDrill(drill)}
                className="ml-3 shrink-0 rounded-lg bg-[var(--accent)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
              >
                开始练习
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
