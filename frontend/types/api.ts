export interface HabitationSummary {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  priority: string;
  current_risk: number;
}

export interface HabitationDetail {
  id: string;
  name: string;
  location: Record<string, unknown>;
  latitude: number;
  longitude: number;
  population: number;
  households: number;

  exposure_info: {
    landslide_susceptibility: string;
    population_exposure: string;
    score: number;
  };

  vulnerability_info: {
    socioeconomic_vulnerability: string;
    health_access: string;
    score: number;
  };

  accessibility_info: {
    road_access: string;
    evacuation_route: string;
    score: number;
  };

  current_risk: number;

  risk_24h: number;
  risk_72h: number;
  priority: string;
}

export interface RiskProfile {
  current: number;
  risk_24h: number;
  risk_72h: number;
  confidence: number;
  drivers: string[];
  hazard_type: string;
  timestamp: string | null;
}

export interface TrajectoryResponse {
  habitation_id: string;
  trajectory: string;
  current: number;
  risk_24h: number;
  risk_72h: number;
  hazard_type: string;
  timestamp: string;
}

export interface RelocationSite {
  site_id: string;
  status: string;
  safety: string;
  capacity: number;
  accessibility?: string | null;
  infrastructure?: Record<string, unknown> | null;
  location?: Record<string, unknown> | null;
  rejection_reason?: string | null;
}

export interface RelocationProfile {
  habitation_id: string;
  sites: RelocationSite[];
}

export interface SystemStatus {
  model_status: string;
  forecast_horizon: string;
  data_status: string;
  last_update: string;
}

/*
 * Aliases used by the habitation intelligence API.
 */

export type HabitationRisk = RiskProfile;

export type HabitationTrajectory = TrajectoryResponse;

export type HabitationRelocation = RelocationProfile;
