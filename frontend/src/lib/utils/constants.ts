import type { StepInfo } from "./types";

export const API_BASE = "http://127.0.0.1:8000";

export const STEPS: StepInfo[] = [
  { id: "diagnosis", label: "诊断", number: 1 },
  { id: "practice", label: "练习", number: 2 },
  { id: "feedback", label: "反馈", number: 3 },
  { id: "review", label: "复习", number: 4 },
];

export const STEP_COLORS: Record<string, string> = {
  diagnosis: "var(--purple)",
  practice: "var(--accent)",
  feedback: "var(--green)",
  review: "var(--teal)",
};

export const LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;

export const DOMAINS = ["general", "education", "business", "literature"] as const;

export const LANGUAGE_PAIRS = {
  zh_ru: { label: "中译俄", source: "zh", target: "ru" },
  ru_zh: { label: "俄译中", source: "ru", target: "zh" },
} as const;

export const DIMENSION_LABELS: Record<string, string> = {
  accuracy: "语义传达",
  fluency: "表达自然",
  terminology: "术语精准",
  grammar: "结构正确",
  strategy: "策略运用",
};

export const DIMENSION_ORDER = [
  "accuracy",
  "fluency",
  "terminology",
  "grammar",
  "strategy",
];

export const HINT_LEVELS = [
  { key: "vocabulary", label: "词汇提示", shortcut: "Ctrl+1" },
  { key: "structure", label: "结构提示", shortcut: "Ctrl+2" },
  { key: "grammar", label: "语法提示", shortcut: "Ctrl+3" },
  { key: "half_sentence", label: "半句提示", shortcut: "Ctrl+4" },
] as const;

export const SCORE_COLORS = {
  excellent: { min: 85, color: "var(--green)", label: "优秀" },
  good: { min: 70, color: "var(--accent)", label: "良好" },
  fair: { min: 50, color: "var(--amber)", label: "一般" },
  needs_work: { min: 0, color: "var(--danger)", label: "需加强" },
};

export const LOCAL_STORAGE_KEYS = {
  session: "linguagraph.session.v2",
  progress: "linguagraph.progress.v2",
  vocab: "linguagraph.vocab.v2",
  diagnosis: "linguagraph.diagnosis.v2",
} as const;
