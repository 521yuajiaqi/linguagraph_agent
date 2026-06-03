"use client";

import { useStepStore } from "@/lib/stores/step-store";
import { STEPS, STEP_COLORS } from "@/lib/utils/constants";
import type { StepId } from "@/lib/utils/types";
import { Check } from "lucide-react";

export function StepIndicator() {
  const currentStep = useStepStore((s) => s.currentStep);
  const isCompleted = useStepStore((s) => s.isCompleted);

  return (
    <nav className="flex items-center gap-0 px-6 py-4">
      {STEPS.map((step, i) => {
        const active = currentStep === step.id;
        const completed = isCompleted(step.id);
        const color = STEP_COLORS[step.id];

        return (
          <div key={step.id} className="flex items-center">
            {i > 0 && (
              <div
                className="mx-2 h-0.5 w-8 rounded-full transition-colors"
                style={{
                  backgroundColor: completed ? color : "var(--line)",
                }}
              />
            )}
            <button
              onClick={() => {
                const store = useStepStore.getState();
                if (store.canAccess(step.id)) {
                  store.setCurrentStep(step.id);
                  window.location.href = `/${step.id}`;
                }
              }}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
              style={{
                color: active || completed ? color : "var(--muted)",
              }}
            >
              <span
                className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold transition-colors"
                style={{
                  backgroundColor:
                    active || completed ? color : "var(--line)",
                  color: active || completed ? "#fff" : "var(--muted)",
                }}
              >
                {completed ? <Check size={12} /> : step.number}
              </span>
              <span className="hidden sm:inline">{step.label}</span>
            </button>
          </div>
        );
      })}
    </nav>
  );
}
