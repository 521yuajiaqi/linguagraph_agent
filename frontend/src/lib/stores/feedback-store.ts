"use client";

import { create } from "zustand";
import type {
  EvaluationResult,
  NextExercise,
  MistakeRecord,
  VocabularyCard,
  GrammarAnalysis,
  Diagnostics,
} from "@/lib/utils/types";

interface FeedbackStore {
  evaluation: EvaluationResult | null;
  nextExercises: NextExercise[];
  focusAreas: string[];
  sessionSummary: string;
  mistakeRecord: MistakeRecord | null;
  vocabularyCards: VocabularyCard[];
  grammarAnalysis: GrammarAnalysis | null;
  diagnostics: Diagnostics | null;

  setFeedback: (
    evaluation: EvaluationResult,
    nextExercises: NextExercise[],
    focusAreas: string[],
    sessionSummary: string,
    mistakeRecord: MistakeRecord | null,
    vocabularyCards: VocabularyCard[],
    grammarAnalysis: GrammarAnalysis | null,
    diagnostics: Diagnostics | null
  ) => void;
  reset: () => void;
}

const initialState = {
  evaluation: null,
  nextExercises: [],
  focusAreas: [],
  sessionSummary: "",
  mistakeRecord: null,
  vocabularyCards: [],
  grammarAnalysis: null,
  diagnostics: null,
};

export const useFeedbackStore = create<FeedbackStore>()((set) => ({
  ...initialState,

  setFeedback: (
    evaluation,
    nextExercises,
    focusAreas,
    sessionSummary,
    mistakeRecord,
    vocabularyCards,
    grammarAnalysis,
    diagnostics
  ) =>
    set({
      evaluation,
      nextExercises,
      focusAreas,
      sessionSummary,
      mistakeRecord,
      vocabularyCards,
      grammarAnalysis,
      diagnostics,
    }),

  reset: () => set(initialState),
}));
