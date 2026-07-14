/** Enumerated user roles across the ArenaMind platform. */
export type UserRole = "ADMIN" | "OPERATIONS" | "VOLUNTEER" | "MEDICAL" | "SECURITY" | "FAN";

/** Lifecycle status of an incident. */
export type IncidentStatus = "ACTIVE" | "MITIGATING" | "RESOLVED";

/** Severity priority of an incident. */
export type IncidentPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/** Lifecycle status of a volunteer task. */
export type TaskStatus = "PENDING" | "ACCEPTED" | "COMPLETED";

export interface User {
  id: string;
  email: string;
  displayName?: string;
  role: UserRole;
  createdAt: string;
}

export interface Incident {
  id: string;
  title: string;
  description?: string;
  status: IncidentStatus;
  priority: IncidentPriority;
  sector: string;
  reporterId?: string;
  assigneeId?: string;
  createdAt: string;
  resolvedAt?: string;
  aiSummary?: string;
  aiRootCause?: string;
  aiLessonsLearned?: string;
}

export interface VolunteerTask {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: string;
  incidentId: string;
  volunteerId?: string;
  createdAt: string;
  completedAt?: string;
  etaMinutes?: number;
}

export interface TelemetrySnapshot {
  crowdHealth: number; // 0-100
  transitHealth: number; // 0-100
  securityHealth: number; // 0-100
  sustainabilityHealth: number; // 0-100
  globalStadiumHealth: number; // overall index
}

export interface EventLog {
  id: string;
  timestamp: string;
  type: string;
  source: string;
  payload: Record<string, unknown>;
}

/**
 * AI-generated mitigation decision.
 *
 * Note: field names use snake_case to match the backend API response.
 * The optional `createdAt` alias is kept for local UI convenience.
 */
export interface Decision {
  id: string;
  decision: string;
  reason: string;
  expected_impact: string;
  responsible_team: string;
  eta: number;
  /** Local-only alias (camelCase convenience). */
  createdAt?: string;
  action_type?: string;
  /** API-native timestamp field. */
  created_at?: string;
}
