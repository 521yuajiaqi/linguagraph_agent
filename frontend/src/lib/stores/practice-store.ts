"use client";

import { create } from "zustand";
import type {
  Hints,
  VocabularyCard,
  GrammarAnalysis,
  DifficultyEstimate,
  ExerciseBlueprint,
  SelectedExercise,
} from "@/lib/utils/types";

interface PracticeStore {
  exerciseId: string | null;
  sourceText: string;
  referenceTranslation: string;
  userTranslation: string;
  hints: Hints | null;
  vocabularyCards: VocabularyCard[];
  grammarAnalysis: GrammarAnalysis | null;
  difficulty: DifficultyEstimate | null;
  exerciseBlueprint: ExerciseBlueprint | null;
  selectedExercise: SelectedExercise | null;
  revealedHints: Set<string>;
  isGenerating: boolean;
  isSubmitting: boolean;

  setExercise: (
    id: string,
    source: string,
    reference: string,
    hints: Hints,
    vocab: VocabularyCard[],
    grammar: GrammarAnalysis,
    difficulty: DifficultyEstimate,
    exerciseBlueprint?: ExerciseBlueprint | null,
    selectedExercise?: SelectedExercise | null
  ) => void;
  setUserTranslation: (text: string) => void;
  revealHint: (level: string) => void;
  isHintRevealed: (level: string) => boolean;
  setIsGenerating: (value: boolean) => void;
  setIsSubmitting: (value: boolean) => void;
  reset: () => void;
}

const initialState = {
  exerciseId: null,
  sourceText: "",
  referenceTranslation: "",
  userTranslation: "",
  hints: null,
  vocabularyCards: [],
  grammarAnalysis: null,
  difficulty: null,
  exerciseBlueprint: null,
  selectedExercise: null,
  revealedHints: new Set<string>(),
  isGenerating: false,
  isSubmitting: false,
};

export const usePracticeStore = create<PracticeStore>()((set, get) => ({
  ...initialState,

  setExercise: (
    id,
    source,
    reference,
    hints,
    vocab,
    grammar,
    difficulty,
    exerciseBlueprint = null,
    selectedExercise = null
  ) =>
    set({
      exerciseId: id,
      sourceText: source,
      referenceTranslation: reference,
      hints,
      vocabularyCards: vocab,
      grammarAnalysis: grammar,
      difficulty,
      exerciseBlueprint,
      selectedExercise,
      userTranslation: "",
      revealedHints: new Set(),
      isGenerating: false,
    }),

  setUserTranslation: (text) => set({ userTranslation: text }),

  revealHint: (level) =>
    set((state) => {
      const next = new Set(state.revealedHints);
      next.add(level);
      return { revealedHints: next };
    }),

  isHintRevealed: (level) => get().revealedHints.has(level),

  setIsGenerating: (value) => set({ isGenerating: value }),
  setIsSubmitting: (value) => set({ isSubmitting: value }),

  reset: () => set(initialState),
}));
