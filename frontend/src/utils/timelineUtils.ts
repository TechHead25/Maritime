import { VesselPosition, ProbabilityCloud, ReleaseWindow } from '../types';

export interface InterpolatedVesselState {
  latitude: number;
  longitude: number;
  speed_knots: number;
  course_deg: number;
  is_in_gap: boolean;
  status?: string;
  is_visible: boolean;
}

/**
 * Interpolates vessel GPS position, speed, and heading at an exact target UTC timestamp.
 */
export function interpolateVesselPosition(
  waypoints: VesselPosition[],
  targetTime: Date,
  gapIntervals: [string, string][] = []
): InterpolatedVesselState | null {
  if (!waypoints || waypoints.length === 0) {
    return null;
  }

  const targetMs = targetTime.getTime();
  const sorted = [...waypoints].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const firstMs = new Date(sorted[0].timestamp).getTime();
  const lastMs = new Date(sorted[sorted.length - 1].timestamp).getTime();

  // Check if target time is within active track interval
  if (targetMs < firstMs - 30 * 60 * 1000 || targetMs > lastMs + 30 * 60 * 1000) {
    return null;
  }

  // Check if in AIS blackout gap
  const isInGap = gapIntervals.some(([startStr, endStr]) => {
    const sMs = new Date(startStr).getTime();
    const eMs = new Date(endStr).getTime();
    return targetMs >= sMs && targetMs <= eMs;
  });

  // Clamp if before first or after last
  if (targetMs <= firstMs) {
    const first = sorted[0];
    return {
      latitude: first.latitude,
      longitude: first.longitude,
      speed_knots: first.speed_over_ground_knots ?? 0,
      course_deg: first.course_over_ground_deg ?? 0,
      is_in_gap: isInGap,
      status: first.navigational_status,
      is_visible: true,
    };
  }

  if (targetMs >= lastMs) {
    const last = sorted[sorted.length - 1];
    return {
      latitude: last.latitude,
      longitude: last.longitude,
      speed_knots: last.speed_over_ground_knots ?? 0,
      course_deg: last.course_over_ground_deg ?? 0,
      is_in_gap: isInGap,
      status: last.navigational_status,
      is_visible: true,
    };
  }

  // Find surrounding waypoint bracket [w1, w2]
  for (let i = 0; i < sorted.length - 1; i++) {
    const t1 = new Date(sorted[i].timestamp).getTime();
    const t2 = new Date(sorted[i + 1].timestamp).getTime();

    if (targetMs >= t1 && targetMs <= t2) {
      const span = t2 - t1;
      const frac = span > 0 ? (targetMs - t1) / span : 0;

      const w1 = sorted[i];
      const w2 = sorted[i + 1];

      const lat = w1.latitude + frac * (w2.latitude - w1.latitude);
      const lon = w1.longitude + frac * (w2.longitude - w1.longitude);

      const spd1 = w1.speed_over_ground_knots ?? 0;
      const spd2 = w2.speed_over_ground_knots ?? spd1;
      const speed = spd1 + frac * (spd2 - spd1);

      const course = w1.course_over_ground_deg ?? w2.course_over_ground_deg ?? 0;

      return {
        latitude: lat,
        longitude: lon,
        speed_knots: speed,
        course_deg: course,
        is_in_gap: isInGap,
        status: w1.navigational_status,
        is_visible: true,
      };
    }
  }

  return null;
}

/**
 * Finds the probability cloud corresponding to the closest simulation timestep.
 */
export function findClosestProbabilityCloud(
  clouds: ProbabilityCloud[],
  targetTime: Date
): { cloud: ProbabilityCloud; index: number } | null {
  if (!clouds || clouds.length === 0) return null;

  const targetMs = targetTime.getTime();
  let minDiff = Infinity;
  let closestIndex = 0;

  for (let i = 0; i < clouds.length; i++) {
    const cMs = new Date(clouds[i].timestamp).getTime();
    const diff = Math.abs(cMs - targetMs);
    if (diff < minDiff) {
      minDiff = diff;
      closestIndex = i;
    }
  }

  return { cloud: clouds[closestIndex], index: closestIndex };
}

/**
 * Checks whether a timestamp falls inside the estimated release window.
 */
export function isTimestampInReleaseWindow(
  targetTime: Date,
  releaseWindow?: ReleaseWindow
): boolean {
  if (!releaseWindow) return false;
  const tMs = targetTime.getTime();
  const sMs = new Date(releaseWindow.estimated_start_time).getTime();
  const eMs = new Date(releaseWindow.estimated_end_time).getTime();
  return tMs >= sMs && tMs <= eMs;
}

/**
 * Formats a Date object to ISO UTC string.
 */
export function formatUTCTimestamp(date: Date): string {
  return date.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
}

/**
 * Calculates hours delta between target timestamp and observation timestamp.
 */
export function calculateRelativeHours(targetTime: Date, observationTime: Date): string {
  const deltaMs = observationTime.getTime() - targetTime.getTime();
  const hours = deltaMs / (1000 * 60 * 60);

  if (Math.abs(hours) < 0.05) {
    return 'T_obs (SAR Acquisition)';
  }

  const sign = hours >= 0 ? '-' : '+';
  const absHours = Math.abs(hours);
  const h = Math.floor(absHours);
  const m = Math.round((absHours - h) * 60);

  return `T ${sign} ${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m`;
}
