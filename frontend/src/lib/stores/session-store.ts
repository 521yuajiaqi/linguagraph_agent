"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { LOCAL_STORAGE_KEYS } from "@/lib/utils/constants";
import type { SessionState, LearnerProfile } from "@/lib/utils/types";

interface SessionStore extends SessionState {
  learnerProfile: LearnerProfile | null;

  setSessionId: (id: string) => void;
  setLanguagePair: (pair: string) => void;
  setUserLevel: (level: string) => void;
  setDomain: (domain: string) => void;
  setMode: (mode: "student" | "teacher") => void;
  setInitialized: (value: boolean) => void;
  setLearnerProfile: (profile: LearnerProfile | null) => void;
  reset: () => void;
}

const initialState: SessionState & { learnerProfile: LearnerProfile | null } = {
  sessionId: null,
  languagePair: "zh_ru",
  userLevel: "",
  domain: "general",
  mode: "student",
  initialized: false,
  learnerProfile: null,
};

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      ...initialState,

      setSessionId: (id) => set({ sessionId: id }),
      setLanguagePair: (pair) => set({ languagePair: pair }),
      setUserLevel: (level) => set({ userLevel: level }),
      setDomain: (domain) => set({ domain }),
      setMode: (mode) => set({ mode }),
      setInitialized: (value) => set({ initialized: value }),
      setLearnerProfile: (profile) => set({ learnerProfile: profile }),
      reset: () => set(initialState),
    }),
    {
      name: LOCAL_STORAGE_KEYS.session,
    }
  )
);
