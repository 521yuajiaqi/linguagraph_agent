"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { LOCAL_STORAGE_KEYS } from "@/lib/utils/constants";
import type {
  ReviewTask,
  ProgressRecord,
  VocabRating,
  VocabRatingEntry,
} from "@/lib/utils/types";

interface ReviewStore {
  reviewPlan: ReviewTask[];
  progressHistory: ProgressRecord[];
  vocabRatings: Record<string, VocabRatingEntry>;

  setReviewPlan: (plan: ReviewTask[]) => void;
  addProgressRecord: (record: ProgressRecord) => void;
  setVocabRating: (term: string, rating: VocabRating) => void;
  getVocabRating: (term: string) => VocabRatingEntry | undefined;
  reset: () => void;
}

const initialState = {
  reviewPlan: [],
  progressHistory: [],
  vocabRatings: {},
};

export const useReviewStore = create<ReviewStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      setReviewPlan: (plan) => set({ reviewPlan: plan }),

      addProgressRecord: (record) =>
        set((state) => ({
          progressHistory: [...state.progressHistory, record].slice(-60),
        })),

      setVocabRating: (term, rating) =>
        set((state) => ({
          vocabRatings: {
            ...state.vocabRatings,
            [term]: {
              rating,
              at: new Date().toISOString(),
              nextReview: nextReviewFor(rating),
            },
          },
        })),

      getVocabRating: (term) => get().vocabRatings[term],

      reset: () => set(initialState),
    }),
    {
      name: LOCAL_STORAGE_KEYS.progress,
      partialize: (state) => ({
        progressHistory: state.progressHistory.slice(-60),
        vocabRatings: state.vocabRatings,
      }),
    }
  )
);

function nextReviewFor(rating: VocabRating): string {
  const now = new Date();
  const minutes = {
    again: 10,
    hard: 60,
    good: 24 * 60,
    easy: 3 * 24 * 60,
  }[rating];
  now.setMinutes(now.getMinutes() + minutes);
  return now.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
