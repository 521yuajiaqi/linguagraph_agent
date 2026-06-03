// ===== API Response Types (mirrors backend TranslationAgentState) =====

export interface DimensionScores {
  accuracy: number;
  fluency: number;
  terminology: number;
  grammar: number;
  strategy: number;
}

export interface EvaluationResult {
  score: number | null;
  dimension_scores: DimensionScores;
  dimension_labels: Record<string, string>;
  dimension_descriptions: Record<string, string>;
  error_tags: string[];
  major_issues: string[];
  revision_advice: string;
  review: string;

  hints?: Hints;
  recommended_translation?: string;
  acceptable_alternatives?: string[];
  needs_retry?: boolean;
  difficulty?: DifficultyEstimate;
}

export interface Hints {
  vocabulary: string;
  structure: string;
  grammar: string;
  half_sentence: string;
}

export interface DifficultyEstimate {
  estimated_level: string;
  token_count: number;
  average_sentence_length: number;
  grammar_load: string;
  target_level: string;
  advice: string;
}

export interface Diagnostics {
  estimated_level: string;
  strengths: string[];
  weaknesses: string[];
  recommended_path: string[];
  difficulty?: DifficultyEstimate;
}

export interface ExerciseBlueprint {
  primary_focus: string;
  target_level: string;
  difficulty_band: {
    floor: string;
    target: string;
    ceiling: string;
  };
  syntax_load: "low" | "medium" | "high";
  terminology_load: "low" | "medium" | "high";
  teaching_intent: string;
  selection_reason: string;
  avoid_overload_dimensions: string[];
  preferred_domain: string;
  recent_error_tags: string[];
}

export interface SelectedExercise {
  source_text: string;
  reference_translation: string;
  language_pair?: string;
  level?: string;
  focus_tags?: string[];
  syntax_load?: "low" | "medium" | "high";
  terminology_load?: "low" | "medium" | "high";
  teaching_points?: string[];
  domain?: string;
}

export interface GrammarAnalysis {
  spine: string;
  tokens: Array<{ text: string; role: string }>;
  key_grammar: string[];
  translation_difficulty: string[];
  common_misreadings: string[];
}

export interface VocabularyCard {
  term: string;
  translation: string;
  meaning: string;
  collocations: string[];
  risk: string;
  retrieval_prompt: string;
  cloze: string;
  production_task: string;
  memory_cue: string;
  review_interval: string;
}

export interface TerminologyHit {
  source_term: string;
  target_term: string;
  note?: string;
  example?: string;
}

export interface MistakeRecord {
  source_text: string;
  student_answer: string;
  recommended_answer: string;
  error_types: string[];
  reason: string;
  review_count?: number;
  last_result?: string;
}

export interface LearnerProfile {
  level: string;
  goal?: string;
  common_errors: Array<{ tag: string; count: number }>;
  performance_strengths: string[];
  performance_risks: string[];
  weak_grammar?: string[];
  familiar_terms?: string[];
}

export interface ReviewTask {
  due: string;
  mode: string;
  focus: string;
  task: string;
}

export interface NextExercise {
  type: string;
  focus: string;
  description: string;
  action: string;
}

export interface ToolTrace {
  tool: string;
  result: string;
}

export interface DashboardData {
  current_score: number | null;
  accuracy_trend: string;
  review_due_count: number;
  next_task: string;
  today_work?: string;
  error_top?: Array<{ tag: string; count: number }>;
  mastered_points?: string[];
  progress_strengths?: string[];
  progress_risks?: string[];
}

// ===== API Request Types =====

export interface AgentRequest {
  language_pair: string;
  task_type: "generate_exercise" | "evaluate_translation";
  user_level: string;
  domain: string;
  mode: "student" | "teacher";
  source_text: string;
  user_translation: string;
  reference_translation: string;
  focus_areas: string[];
}

// ===== Step-Specific API Types =====

export interface SessionInitRequest {
  language_pair: string;
  user_level?: string;
  domain?: string;
  mode?: "student" | "teacher";
}

export interface SessionInitResponse {
  session_id: string;
  learner_profile?: LearnerProfile;
}

export interface DiagnosisQuestion {
  id: string;
  type: "choice" | "fill_blank" | "short_translate" | "error_correction";
  source_text: string;
  reference_translation?: string;
  error_sentence?: string;
  options?: string[];
  hint?: string;
  difficulty: string;
}

export interface DiagnosisStartRequest {
  session_id: string;
  question_count?: number;
}

export interface DiagnosisStartResponse {
  questions: DiagnosisQuestion[];
}

export interface DiagnosisAnswer {
  question_id: string;
  answer: string;
}

export interface DiagnosisSubmitRequest {
  session_id: string;
  answers: DiagnosisAnswer[];
}

export interface DiagnosisSubmitResponse {
  estimated_level: string;
  dimension_scores: DimensionScores;
  strengths: string[];
  weaknesses: string[];
  recommended_path: string[];
  learner_profile: LearnerProfile;
}

export interface PracticeGenerateRequest {
  session_id: string;
  focus_areas?: string[];
  domain?: string;
}

export interface PracticeGenerateResponse {
  exercise_id: string;
  source_text: string;
  reference_translation: string;
  hints: Hints;
  vocabulary_cards: VocabularyCard[];
  grammar_analysis: GrammarAnalysis;
  difficulty: DifficultyEstimate;
  diagnostics: Diagnostics;
  exercise_blueprint?: ExerciseBlueprint;
  selected_exercise?: SelectedExercise;
}

export interface PracticeEvaluateRequest {
  session_id: string;
  exercise_id: string;
  user_translation: string;
}

export interface PracticeEvaluateResponse {
  evaluation: EvaluationResult;
  next_exercises: NextExercise[];
  focus_areas: string[];
  session_summary: string;
  mistake_record: MistakeRecord;
  vocabulary_cards: VocabularyCard[];
  grammar_analysis: GrammarAnalysis;
  diagnostics: Diagnostics;
}

export interface DimProgress {
  total: number;
  current_level_xp: number;
  cap: number;
  label: string;
}

export interface AbilityStats {
  ability_xp: Record<string, number>;
  current_level: string;
  level_index: number;
  current_rank: number;
  current_title: string;
  next_title: string;
  progress_to_next: number;
  can_advance_level: boolean;
  xp_needed_for_next_level: number;
  bottleneck_dim: string;
  bottleneck_label: string;
  per_dim_progress: Record<string, DimProgress>;
  level_description: string;
  total_exercises: number;
  recent_trend: string;
}

export interface ReviewDashboardResponse {
  current_level: string;
  accuracy_trend: Array<{ date: string; score: number }>;
  error_breakdown: Array<{ tag: string; count: number }>;
  vocabulary_status: { mastered: number; learning: number; new: number };
  review_due_count: number;
  recommended_action: string;
  dashboard: DashboardData;
  learner_profile: LearnerProfile;
  ability_stats: AbilityStats;
}

export interface ReviewMistakesResponse {
  mistakes: Array<MistakeRecord & { id: string; created_at: string }>;
}

export interface ReviewDrillRequest {
  session_id: string;
  error_types?: string[];
  count?: number;
}

export interface ReviewDrillResponse {
  drills: Array<{
    id: string;
    source_text: string;
    reference_translation: string;
    focus: string;
    hints: Hints;
  }>;
}

// ===== Frontend State Types =====

export type StepId = "diagnosis" | "practice" | "feedback" | "review";

export type StepStatus = "pending" | "active" | "completed";

export interface StepInfo {
  id: StepId;
  label: string;
  number: number;
}

export interface SessionState {
  sessionId: string | null;
  languagePair: string;
  userLevel: string;
  domain: string;
  mode: "student" | "teacher";
  initialized: boolean;
}

export type VocabRating = "again" | "hard" | "good" | "easy";

export interface VocabRatingEntry {
  rating: VocabRating;
  at: string;
  nextReview: string;
}

export interface ProgressRecord {
  key: string;
  at: string;
  score: number;
  dimensions: Record<string, number>;
  dimensionLabels: Record<string, string>;
  tags: string[];
  source: string;
}
