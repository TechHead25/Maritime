export type CaseStatus =
  | 'CREATED'
  | 'SAR_PROCESSED'
  | 'DRIFT_SIMULATED'
  | 'AIS_INTERCEPTED'
  | 'ATTRIBUTION_COMPLETED'
  | 'CLOSED';

export type VesselType = 'TANKER' | 'CARGO' | 'BUNKER' | 'FISHING' | 'PASSENGER' | 'OTHER';

export type RiskLevel = 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NEGLIGIBLE';

export type EvidenceCategory =
  | 'SUPPORTING_EVIDENCE'
  | 'CONTRADICTING_EVIDENCE'
  | 'EXCULPATORY_EVIDENCE'
  | 'DATA_QUALITY'
  | 'UNCERTAINTY';

export type FactorCategory =
  | 'PROXIMITY'
  | 'ALIGNMENT'
  | 'VESSEL_TYPE'
  | 'BEHAVIOR'
  | 'AIS_INTEGRITY'
  | 'DATA_QUALITY'
  | 'UNCERTAINTY';

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface GeoPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // [[[lon, lat], ...]]
}

export interface InvestigationCase {
  id: string;
  title: string;
  status: CaseStatus;
  region_of_interest?: GeoPolygon;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface SARScene {
  id: string;
  case_id: string;
  satellite_platform: string;
  sensor_mode: string;
  polarization: string;
  acquisition_timestamp: string;
  footprint_polygon?: GeoPolygon;
  pixel_resolution_meters: number;
}

export interface SlickDetection {
  id: string;
  sar_scene_id: string;
  slick_polygon: GeoPolygon;
  centroid: GeoPoint;
  area_sq_km: number;
  perimeter_km: number;
  major_axis_orientation_deg: number;
  confidence_score: number;
  lookalike_probability?: number;
}

export interface ProbabilityCloud {
  id: string;
  drift_simulation_id: string;
  timestamp: string;
  hours_before_sar: number;
  hours_backward?: number;
  center_point: GeoPoint;
  dispersion_radius_km: number;
  envelope_polygon?: GeoPolygon;
  convex_hull_polygon?: GeoPolygon;
  particle_sample_points?: number[][];
}

export interface ReleaseWindow {
  id: string;
  drift_simulation_id: string;
  estimated_start_time: string;
  estimated_end_time: string;
  peak_probability_time: string;
  confidence_interval: number;
}

export interface VesselPosition {
  timestamp: string;
  longitude: number;
  latitude: number;
  speed_over_ground_knots?: number;
  course_over_ground_deg?: number;
  navigational_status?: string;
}

export interface VesselTrack {
  id: string;
  mmsi: string;
  vessel_name: string;
  vessel_type: VesselType;
  flag_country: string;
  waypoints: VesselPosition[];
  has_ais_gaps: boolean;
  gap_intervals: [string, string][];
}

export interface CandidateVessel {
  id: string;
  case_id: string;
  vessel_track_id: string;
  mmsi: string;
  vessel_name: string;
  vessel_type: VesselType;
  flag_country: string;
  closest_point_of_approach_km: number;
  time_of_closest_approach: string;
  interpolated_position_at_cpa?: GeoPoint;
  is_in_release_envelope: boolean;
  has_ais_gaps: boolean;
  gap_intervals?: [string, string][];
}

export interface EvidenceItem {
  id: string;
  attribution_score_id: string;
  candidate_vessel?: string;
  category?: EvidenceCategory;
  factor_category: FactorCategory;
  title: string;
  description: string;
  severity?: string; // 'HIGH' | 'MEDIUM' | 'LOW' | 'INFORMATIONAL'
  source?: string;
  source_timestamp_start?: string;
  source_timestamp_end?: string;
  calculated_value?: string;
  threshold_used?: string;
  calculation_reference?: string;
  confidence?: number;
  uncertainty?: string;
  score_impact: number;
  verifiable_data?: Record<string, any>;
}

export interface AttributionScoreSubScores {
  proximity_score: number;
  trajectory_alignment_score: number;
  vessel_type_risk_score: number;
  navigational_anomaly_score: number;
  ais_integrity_penalty: number;
}

export interface AttributionScore {
  id: string;
  candidate_vessel_id: string;
  candidate_name: string;
  mmsi: string;
  vessel_type: VesselType;
  rank: number;
  total_score: number;
  risk_level: RiskLevel;
  sub_scores: AttributionScoreSubScores;
  supporting_evidence?: EvidenceItem[];
  contradicting_evidence?: EvidenceItem[];
  exculpatory_evidence?: EvidenceItem[];
  data_quality_items?: EvidenceItem[];
  uncertainty_items?: EvidenceItem[];
  evidence_items: EvidenceItem[];
}

export interface DriftSimulation {
  id: string;
  slick_detection_id: string;
  simulation_mode: string;
  simulation_start_time: string;
  simulation_end_time: string;
  time_step_minutes: number;
  particle_count: number;
  wind_leeway_factor: number;
  current_advection_factor: number;
  created_at: string;
}

export interface FullInvestigationResponse {
  case: InvestigationCase;
  sar_scenes: SARScene[];
  slicks: SlickDetection[];
  drift_simulations: DriftSimulation[];
  probability_clouds: ProbabilityCloud[];
  release_windows: ReleaseWindow[];
  origin_centroid: GeoPoint;
  origin_uncertainty_radius_km: number;
  candidate_vessels: CandidateVessel[];
  attribution_scores: AttributionScore[];
  summary_verdict: string;
  data_sources: Record<string, any>;
  generated_at: string;
}

export interface CaseDetails {
  case: InvestigationCase;
  sar_scenes: SARScene[];
  slicks: SlickDetection[];
  vessel_tracks: VesselTrack[];
  environment: Record<string, any>;
  drift_simulations: DriftSimulation[];
  probability_clouds: ProbabilityCloud[];
  release_windows: ReleaseWindow[];
  candidates: CandidateVessel[];
  attribution_scores: AttributionScore[];
}

export interface HealthStatus {
  status: string;
  service: string;
  problem_statement: string;
  version: string;
  timestamp_utc: string;
  loaded_cases_count?: number;
}
