"use client";

import { create } from "zustand";
import type { StepId } from "@/lib/utils/types";

interface StepStore {
  currentStep: StepId;
  completedSteps: Set<StepId>;

  setCurrentStep: (step: StepId) => void;
  markCompleted: (step: StepId) => void;
  isCompleted: (step: StepId) => boolean;
  canAccess: (step: StepId) => boolean;
  reset: () => void;
}

const STEP_ORDER: StepId[] = ["diagnosis", "practice", "feedback", "review"];

export const useStepStore = create<StepStore>()((set, get) => ({
  currentStep: "diagnosis",
  completedSteps: new Set(),

  setCurrentStep: (step) => set({ currentStep: step }),

  markCompleted: (step) =>
    set((state) => {
      const next = new Set(state.completedSteps);
      next.add(step);
      return { completedSteps: next };
    }),

  isCompleted: (step) => get().completedSteps.has(step),

  canAccess: (step) => {
    const { completedSteps } = get();
    const idx = STEP_ORDER.indexOf(step);
    if (idx === 0) return true;
    const prevStep = STEP_ORDER[idx - 1];
    return completedSteps.has(prevStep);
  },

  reset: () =>
    set({
      currentStep: "diagnosis",
      completedSteps: new Set(),
    }),
}));
