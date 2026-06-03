import { get, post } from "./client";
import type {
  ReviewDashboardResponse,
  ReviewMistakesResponse,
  ReviewDrillRequest,
  ReviewDrillResponse,
} from "@/lib/utils/types";

export async function getDashboard(
  sessionId: string
): Promise<ReviewDashboardResponse> {
  return get<ReviewDashboardResponse>(
    `/api/review/dashboard?session_id=${encodeURIComponent(sessionId)}`
  );
}

export async function getMistakes(
  sessionId: string,
  errorType?: string,
  status?: string
): Promise<ReviewMistakesResponse> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (errorType) params.set("error_type", errorType);
  if (status) params.set("status", status);
  return get<ReviewMistakesResponse>(`/api/review/mistakes?${params}`);
}

export async function generateDrill(
  data: ReviewDrillRequest
): Promise<ReviewDrillResponse> {
  return post<ReviewDrillResponse>("/api/review/drill", data);
}

export async function rateVocabulary(
  sessionId: string,
  term: string,
  rating: "again" | "hard" | "good" | "easy"
): Promise<{ next_review_at: string }> {
  return post("/api/review/vocabulary/rate", {
    session_id: sessionId,
    term,
    rating,
  });
}
