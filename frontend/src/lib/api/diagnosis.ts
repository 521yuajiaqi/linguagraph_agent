import { post } from "./client";
import type {
  DiagnosisStartRequest,
  DiagnosisStartResponse,
  DiagnosisSubmitRequest,
  DiagnosisSubmitResponse,
} from "@/lib/utils/types";

export async function startDiagnosis(
  data: DiagnosisStartRequest
): Promise<DiagnosisStartResponse> {
  return post<DiagnosisStartResponse>("/api/diagnosis/start", data);
}

export async function submitDiagnosis(
  data: DiagnosisSubmitRequest
): Promise<DiagnosisSubmitResponse> {
  return post<DiagnosisSubmitResponse>("/api/diagnosis/submit", data);
}
