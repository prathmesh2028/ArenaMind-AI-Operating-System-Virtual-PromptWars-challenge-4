/**
 * Application-wide constants for the ArenaMind frontend.
 * Centralises magic numbers, environment URLs, and configuration values
 * so every page and component references a single source of truth.
 */

/* ------------------------------------------------------------------ */
/*  Environment / API Configuration                                   */
/* ------------------------------------------------------------------ */

/** Base URL for all REST API calls. */
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_BASE_URL = rawApiUrl.endsWith("/") ? rawApiUrl.slice(0, -1) : rawApiUrl;

/** Base URL for WebSocket connections. */
const rawWsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
export const WS_BASE_URL = rawWsUrl.endsWith("/") ? rawWsUrl.slice(0, -1) : rawWsUrl;

/* ------------------------------------------------------------------ */
/*  Health Score Thresholds                                           */
/* ------------------------------------------------------------------ */

/** Score at or above which health is considered "optimal". */
export const HEALTH_OPTIMAL_THRESHOLD = 90;

/** Score at or above which health is considered "elevated" (warning). */
export const HEALTH_WARNING_THRESHOLD = 75;

/* ------------------------------------------------------------------ */
/*  Density / Crowd Thresholds                                        */
/* ------------------------------------------------------------------ */

/** Density ratio at or above which a sector is flagged CRITICAL. */
export const DENSITY_CRITICAL_THRESHOLD = 0.9;

/** Density ratio at or above which a sector is flagged WARNING. */
export const DENSITY_WARNING_THRESHOLD = 0.8;

/** Integer percentage equivalent for density display. */
export const DENSITY_CRITICAL_PCT = 90;

/** Integer percentage equivalent for density warning display. */
export const DENSITY_WARNING_PCT = 75;

/* ------------------------------------------------------------------ */
/*  Prediction Probability Thresholds                                 */
/* ------------------------------------------------------------------ */

/** Probability at or above which a prediction is HIGH risk. */
export const PREDICTION_HIGH_THRESHOLD = 0.85;

/** Probability at or above which a prediction is MEDIUM risk. */
export const PREDICTION_MEDIUM_THRESHOLD = 0.65;

/* ------------------------------------------------------------------ */
/*  Health Score Computation Weights                                   */
/* ------------------------------------------------------------------ */

/** Points deducted from security health per active incident. */
export const SECURITY_INCIDENT_DEDUCTION = 12;

/** Points deducted from security health per critical incident. */
export const SECURITY_CRITICAL_DEDUCTION = 25;

/** Points deducted from transit health per high-probability transport delay. */
export const TRANSIT_DELAY_DEDUCTION = 15;

/** Probability threshold for counting transport delay predictions. */
export const TRANSPORT_DELAY_PROBABILITY = 0.7;

/** Points deducted from energy health per grid alert. */
export const ENERGY_ALERT_DEDUCTION = 10;

/** Probability threshold for counting energy forecast alerts. */
export const ENERGY_FORECAST_PROBABILITY = 0.75;

/** Density scaling factor used in crowd health calculation. */
export const CROWD_HEALTH_DENSITY_FACTOR = 45;

/** Base score for transit health before deductions. */
export const TRANSIT_BASE_SCORE = 98;

/** Base score for energy health before deductions. */
export const ENERGY_BASE_SCORE = 94;

/* ------------------------------------------------------------------ */
/*  Telemetry History Limits                                          */
/* ------------------------------------------------------------------ */

/** Maximum number of data points retained in crowd/energy history. */
export const TELEMETRY_HISTORY_LIMIT = 15;

/* ------------------------------------------------------------------ */
/*  UI Timing Constants                                               */
/* ------------------------------------------------------------------ */

/** Duration in ms before alert banners auto-dismiss. */
export const ALERT_DISMISS_DELAY_MS = 7_000;

/** Duration in ms before volunteer alert banners auto-dismiss. */
export const VOLUNTEER_ALERT_DISMISS_MS = 6_000;

/** Minimum playback tick interval in ms for replay engine. */
export const REPLAY_MIN_TICK_MS = 100;

/** Default playback tick base in ms for replay engine (divided by speed). */
export const REPLAY_BASE_TICK_MS = 1_000;

/* ------------------------------------------------------------------ */
/*  Replay Scenario Configuration                                     */
/* ------------------------------------------------------------------ */

/** Total duration of the replay scenario in seconds. */
export const REPLAY_DURATION_SECONDS = 300;

/** Time step between interpolated replay frames in seconds. */
export const REPLAY_STEP_SECONDS = 2;

/* ------------------------------------------------------------------ */
/*  Sector & Gate Names                                               */
/* ------------------------------------------------------------------ */

/** Standard sector names used across the stadium. */
export const SECTOR_NAMES = [
  "Sector A",
  "Sector B",
  "Sector C",
  "Sector D",
  "Sector E",
  "Sector F",
] as const;

/** Default sector coordinate mapping for stadium maps. */
export const SECTOR_POSITIONS: Record<string, { x: string; y: string }> = {
  "Sector A": { x: "25%", y: "30%" },
  "Sector B": { x: "50%", y: "20%" },
  "Sector C": { x: "75%", y: "30%" },
  "Sector D": { x: "75%", y: "70%" },
  "Sector E": { x: "50%", y: "80%" },
  "Sector F": { x: "25%", y: "70%" },
};

/* ------------------------------------------------------------------ */
/*  Chart Colour Palette                                              */
/* ------------------------------------------------------------------ */

/** Sector → stroke colour mapping for Recharts line charts. */
export const SECTOR_CHART_COLORS: Record<string, string> = {
  "Sector A": "#6366f1",
  "Sector B": "#10b981",
  "Sector C": "#f59e0b",
  "Sector D": "#f43f5e",
  "Sector E": "#06b6d4",
  "Sector F": "#a855f7",
};

/* ------------------------------------------------------------------ */
/*  Default Mock Credentials (demo seeded users)                      */
/* ------------------------------------------------------------------ */

/** Email used for Operations / Manager auto-login. */
export const MANAGER_EMAIL = "manager@fifa.com";

/** Email used for Fan Portal auto-login. */
export const FAN_EMAIL = "fan1@gmail.com";

/** Email used for Volunteer Portal auto-login. */
export const VOLUNTEER_EMAIL = "volunteer1@fifa.com";

/** Volunteer ID used for WebSocket event filtering. */
export const VOLUNTEER_ID = "V001";

/* ------------------------------------------------------------------ */
/*  Local-storage Cache Keys                                          */
/* ------------------------------------------------------------------ */

/** Key for cached volunteer tasks in localStorage. */
export const CACHE_KEY_TASKS = "volunteer_tasks";

/** Key for cached volunteer notifications in localStorage. */
export const CACHE_KEY_NOTIFICATIONS = "volunteer_notifications";

/** Key for the volunteer offline outbox in localStorage. */
export const CACHE_KEY_OUTBOX = "volunteer_outbox";

/* ------------------------------------------------------------------ */
/*  Dispatch Simulation Timings (ms)                                  */
/* ------------------------------------------------------------------ */

/** Delay before SOS transitions to DISPATCHED status. */
export const SOS_DISPATCH_DELAY_MS = 3_000;

/** Delay before SOS transitions to ARRIVED status. */
export const SOS_ARRIVAL_DELAY_MS = 9_000;

/** Delay before mock SOS transitions to DISPATCHED (backend offline). */
export const SOS_MOCK_DISPATCH_DELAY_MS = 3_500;
