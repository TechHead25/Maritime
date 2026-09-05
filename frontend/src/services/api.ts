import {
  CaseDetails,
  HealthStatus,
  InvestigationCase,
  FullInvestigationResponse,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCases(): Promise<InvestigationCase[]> {
  const res = await fetch(`${API_BASE}/cases`);
  if (!res.ok) {
    throw new Error(`Failed to fetch cases: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCaseDetails(caseId: string): Promise<CaseDetails> {
  const res = await fetch(`${API_BASE}/cases/${caseId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch case details for ${caseId}: ${res.status}`);
  }
  return res.json();
}

export async function fetchCaseSummary(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/summary`);
  if (!res.ok) {
    throw new Error(`Failed to fetch case summary for ${caseId}: ${res.status}`);
  }
  return res.json();
}

export async function runInvestigation(
  caseId: string,
  options: {
    time_step_minutes?: number;
    max_hours_backward?: number;
    particle_count?: number;
    random_seed?: number;
    estimated_release_hours_ago?: number;
  } = {}
): Promise<FullInvestigationResponse> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      time_step_minutes: options.time_step_minutes || 30,
      max_hours_backward: options.max_hours_backward || 24.0,
      particle_count: options.particle_count || 500,
      random_seed: options.random_seed || 42,
      ...(options.estimated_release_hours_ago !== undefined ? { estimated_release_hours_ago: options.estimated_release_hours_ago } : {}),
    }),
  });
  if (!res.ok) {
    throw new Error(`Investigation pipeline failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function getReportDownloadUrl(caseId: string): string {
  return `${API_BASE}/cases/${caseId}/report`;
}

export async function createInvestigation(formData: FormData): Promise<InvestigationCase> {
  const res = await fetch(`${API_BASE}/cases/create-investigation`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Case creation failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchDriftSimulation(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/drift`);
  if (!res.ok) {
    throw new Error(`Drift simulation not found for ${caseId}`);
  }
  return res.json();
}

export async function fetchDataSources(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/data-sources`);
  if (!res.ok) {
    throw new Error(`Failed to fetch data sources: ${res.status}`);
  }
  return res.json();
}

export async function fetchDataSourcesHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/data-sources/health`);
  if (!res.ok) {
    throw new Error(`Failed to fetch data sources health: ${res.status}`);
  }
  return res.json();
}

export async function fetchControlCenterStatus(): Promise<{
  status: string;
  timestamp_utc: string;
  providers: any[];
}> {
  const res = await fetch(`${API_BASE}/data-sources/control-center`);
  if (!res.ok) {
    throw new Error(`Failed to fetch control center telemetry: ${res.status}`);
  }
  return res.json();
}

export async function pingDataSource(providerId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/data-sources/${providerId}/ping`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Ping failed for ${providerId}: ${res.status}`);
  }
  return res.json();
}

export async function configureDataSource(providerId: string, payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/data-sources/${providerId}/configure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Configuration update failed for ${providerId}: ${res.status}`);
  }
  return res.json();
}


export async function searchCopernicusSAR(params: {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
  start_time_iso: string;
  end_time_iso: string;
  sensor_mode?: string;
  polarization?: string;
}): Promise<any> {
  const queryParams = new URLSearchParams({
    min_lon: params.min_lon.toString(),
    min_lat: params.min_lat.toString(),
    max_lon: params.max_lon.toString(),
    max_lat: params.max_lat.toString(),
    start_time_iso: params.start_time_iso,
    end_time_iso: params.end_time_iso,
    sensor_mode: params.sensor_mode || 'IW',
    polarization: params.polarization || 'VV',
  });
  const res = await fetch(`${API_BASE}/sar/search?${queryParams.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'SAR observation search failed');
  }
  return res.json();
}

export async function fetchLiveStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/status`);
  if (!res.ok) {
    throw new Error(`Failed to fetch live status: ${res.status}`);
  }
  return res.json();
}

export async function fetchLiveVessels(filters?: {
  min_lon?: number;
  min_lat?: number;
  max_lon?: number;
  max_lat?: number;
  vessel_type?: string;
  min_speed?: number;
}): Promise<any> {
  const params = new URLSearchParams();
  if (filters?.min_lon !== undefined) params.append('min_lon', filters.min_lon.toString());
  if (filters?.min_lat !== undefined) params.append('min_lat', filters.min_lat.toString());
  if (filters?.max_lon !== undefined) params.append('max_lon', filters.max_lon.toString());
  if (filters?.max_lat !== undefined) params.append('max_lat', filters.max_lat.toString());
  if (filters?.vessel_type && filters.vessel_type !== 'ALL') params.append('vessel_type', filters.vessel_type);
  if (filters?.min_speed !== undefined && filters.min_speed > 0) params.append('min_speed', filters.min_speed.toString());

  const qs = params.toString();
  const url = qs ? `${API_BASE}/live/vessels?${qs}` : `${API_BASE}/live/vessels`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch live vessels: ${res.status}`);
  }
  return res.json();
}

export async function fetchLiveVesselDetails(mmsi: string): Promise<any> {
  const res = await fetch(`${API_BASE}/live/vessels/${mmsi}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch live vessel details for ${mmsi}: ${res.status}`);
  }
  return res.json();
}

export async function updateLiveSubscription(payload: {
  region_name?: string;
  custom_bbox?: { min_lon: number; min_lat: number; max_lon: number; max_lat: number };
}): Promise<any> {
  const res = await fetch(`${API_BASE}/live/subscription`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Subscription update failed: ${res.status}`);
  }
  return res.json();
}

export function getLiveStreamUrl(): string {
  return `${API_BASE}/live/stream`;
}

export async function evaluateReadiness(payload: {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
  incident_time_utc: string;
  window_hours?: number;
  allow_partial_data?: boolean;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/readiness`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      min_lon: payload.min_lon,
      min_lat: payload.min_lat,
      max_lon: payload.max_lon,
      max_lat: payload.max_lat,
      incident_time_utc: payload.incident_time_utc,
      window_hours: payload.window_hours || 48.0,
      allow_partial_data: payload.allow_partial_data || false,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Readiness evaluation failed: ${res.status}`);
  }
  return res.json();
}

export async function executeInvestigationJob(caseId: string, options?: any): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ options: options || {} }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Investigation execution start failed: ${res.status}`);
  }
  return res.json();
}

export async function pollInvestigationProgress(caseId: string, jobId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/jobs/${jobId}/progress`);
  if (!res.ok) {
    throw new Error(`Progress query failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchCaseRuns(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/runs`);
  if (!res.ok) {
    throw new Error(`Failed to fetch runs for ${caseId}: ${res.status}`);
  }
  return res.json();
}

export async function fetchCaseRunDetails(caseId: string, runId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/runs/${runId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch run ${runId} for ${caseId}: ${res.status}`);
  }
  return res.json();
}

export async function compareCaseRuns(caseId: string, runA: string, runB: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/runs-compare?run_a=${runA}&run_b=${runB}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Run comparison failed: ${res.status}`);
  }
  return res.json();
}

export async function deleteCase(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cases/${caseId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete case ${caseId}: ${res.status}`);
  }
  return res.json();
}

export async function fetchVesselIntelligence(mmsi: string): Promise<any> {
  const res = await fetch(`${API_BASE}/vessels/${mmsi}/intelligence`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch vessel profile: ${res.status}`);
  }
  return res.json();
}

export async function createInvestigationFromVessel(payload: {
  mmsi: string;
  title?: string;
  description?: string;
  buffer_degrees?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/from-vessel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create investigation from vessel: ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Authentication & Security APIs
// ---------------------------------------------------------------------------

let authToken: string | null = localStorage.getItem('maritime_auth_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('maritime_auth_token', token);
  } else {
    localStorage.removeItem('maritime_auth_token');
  }
}

export function getAuthToken(): string | null {
  if (!authToken) {
    authToken = localStorage.getItem('maritime_auth_token');
  }
  return authToken;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiLogin(payload: { username: string; password: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Login failed: ${res.status}`);
  }
  const data = await res.json();
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function apiLogout(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: { ...getAuthHeaders() },
    });
    return res.json().catch(() => ({}));
  } finally {
    setAuthToken(null);
  }
}

export async function apiGetMe(): Promise<any> {
  const token = getAuthToken();
  if (!token) return null;

  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    setAuthToken(null);
    return null;
  }
  return res.json();
}

export async function apiListUsers(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/auth/users`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to list users: ${res.status}`);
  }
  return res.json();
}

export async function apiGetAuditLogs(limit: number = 100): Promise<any[]> {
  const res = await fetch(`${API_BASE}/auth/audit-logs?limit=${limit}`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch audit logs: ${res.status}`);
  }
  return res.json();
}





