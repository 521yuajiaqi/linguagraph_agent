import { post, get } from "./client";
import type {
  SessionInitRequest,
  SessionInitResponse,
  LearnerProfile,
} from "@/lib/utils/types";

export async function initSession(
  data: SessionInitRequest
): Promise<SessionInitResponse> {
  return post<SessionInitResponse>("/api/session/init", data);
}

export async function getSession(
  sessionId: string
): Promise<{
  session_id: string;
  learner_profile?: LearnerProfile;
  state?: Record<string, unknown>;
}> {
  return get(`/api/session/${sessionId}`);
}
