import { post } from "./client";
import type {
  PracticeGenerateRequest,
  PracticeGenerateResponse,
  PracticeEvaluateRequest,
  PracticeEvaluateResponse,
} from "@/lib/utils/types";

export async function generateExercise(
  data: PracticeGenerateRequest
): Promise<PracticeGenerateResponse> {
  return post<PracticeGenerateResponse>("/api/practice/generate", data);
}

export async function evaluateTranslation(
  data: PracticeEvaluateRequest
): Promise<PracticeEvaluateResponse> {
  return post<PracticeEvaluateResponse>("/api/practice/evaluate", data);
}
