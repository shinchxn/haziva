import type {
  HabitationDetail,
  HabitationSummary,
  RelocationProfile,
  RiskProfile,
  SystemStatus,
  TrajectoryResponse,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let errorDetail = `API error (${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        errorDetail =
          typeof errorJson.detail === "string"
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  async getHabitations(): Promise<HabitationSummary[]> {
    return fetchJson<HabitationSummary[]>("/habitations");
  },

  async getHabitation(id: string): Promise<HabitationDetail> {
    return fetchJson<HabitationDetail>(`/habitations/${id}`);
  },

  async getHabitationRisk(id: string): Promise<RiskProfile> {
    return fetchJson<RiskProfile>(`/habitations/${id}/risk`);
  },

  async getRisk(id: string): Promise<RiskProfile> {
    return this.getHabitationRisk(id);
  },

  async getHabitationTrajectory(id: string): Promise<TrajectoryResponse> {
    return fetchJson<TrajectoryResponse>(`/habitations/${id}/trajectory`);
  },

  async getHabitationRelocation(id: string): Promise<RelocationProfile> {
    return fetchJson<RelocationProfile>(`/habitations/${id}/relocation`);
  },

  async getSystemStatus(): Promise<SystemStatus> {
    return fetchJson<SystemStatus>("/system/status");
  },
};
