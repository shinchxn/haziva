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
  confidence_reason?: string | null;
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
  name?: string | null;
  facility_category?: string | null;
  status: string;
  safety: string;
  capacity?: number | null;
  capacity_status?: string | null;
  accessibility?: string | null;
  infrastructure?: Record<string, unknown> | null;
  location?: Record<string, unknown> | null;
  rejection_reason?: string | null;
  transparent_priority_score?: number | null;
  ranking_explanation?: string | null;
}

export interface RelocationProfile {
  habitation_id: string;
  sites: RelocationSite[];
}

export interface SimulationResult {
  is_simulation: boolean;
  simulation_disclaimer: string;
  habitation_id: string;
  habitation_name: string;
  simulated_rainfall_mm: number;
  horizon: string;
  baseline: {
    current_risk: number;
    risk_24h: number;
    risk_72h: number;
    trajectory: string;
    priority: string;
  };
  simulation_result: {
    current_risk: number;
    risk_24h: number;
    risk_72h: number;
    trajectory: string;
    priority: string;
    confidence: number;
    confidence_reason: string;
    drivers: string[];
  };
  relocation_sites: RelocationSite[];
}

export interface SystemStatus {
  model_status: string;
  model_name?: string | null;
  forecast_horizon: string;
  data_status: string;
  weather_status?: string | null;
  weather_provider?: string | null;
  weather_location?: string | null;
  observed_24h_mm?: number | null;
  forecast_24h_mm?: number | null;
  forecast_72h_mm?: number | null;
  last_update: string;
}

export type HabitationRisk = RiskProfile;
export type HabitationTrajectory = TrajectoryResponse;
export type HabitationRelocation = RelocationProfile;
