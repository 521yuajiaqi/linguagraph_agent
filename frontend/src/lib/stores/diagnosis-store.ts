"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { LOCAL_STORAGE_KEYS } from "@/lib/utils/constants";
import type {
  DiagnosisQuestion,
  DiagnosisAnswer,
  DiagnosisSubmitResponse,
} from "@/lib/utils/types";

interface DiagnosisStore {
  questions: DiagnosisQuestion[];
  answers: Record<string, string>;
  currentIndex: number;
  results: DiagnosisSubmitResponse | null;

  setQuestions: (questions: DiagnosisQuestion[]) => void;
  setAnswer: (questionId: string, answer: string) => void;
  setCurrentIndex: (index: number) => void;
  next: () => void;
  prev: () => void;
  setResults: (results: DiagnosisSubmitResponse) => void;
  allAnswered: () => boolean;
  getAnswers: () => DiagnosisAnswer[];
  reset: () => void;
}

const initialState = {
  questions: [],
  answers: {},
  currentIndex: 0,
  results: null,
};

export const useDiagnosisStore = create<DiagnosisStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      setQuestions: (questions) => set({ questions, currentIndex: 0, answers: {} }),
      setAnswer: (questionId, answer) =>
        set((state) => ({
          answers: { ...state.answers, [questionId]: answer },
        })),
      setCurrentIndex: (index) => set({ currentIndex: index }),
      next: () =>
        set((state) => ({
          currentIndex: Math.min(state.currentIndex + 1, state.questions.length - 1),
        })),
      prev: () =>
        set((state) => ({
          currentIndex: Math.max(state.currentIndex - 1, 0),
        })),
      setResults: (results) => set({ results }),
      allAnswered: () => {
        const { questions, answers } = get();
        return questions.length > 0 && questions.every((q) => answers[q.id]?.trim());
      },
      getAnswers: () => {
        const { questions, answers } = get();
        return questions.map((q) => ({
          question_id: q.id,
          answer: answers[q.id] || "",
        }));
      },
      reset: () => set(initialState),
    }),
    {
      name: LOCAL_STORAGE_KEYS.diagnosis,
    }
  )
);
