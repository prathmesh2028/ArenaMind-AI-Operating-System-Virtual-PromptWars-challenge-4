export type UserRole = "ADMIN" | "OPERATIONS" | "VOLUNTEER" | "MEDICAL" | "SECURITY" | "FAN";
export type IncidentStatus = "ACTIVE" | "MITIGATING" | "RESOLVED";
export type IncidentPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
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
  payload: Record<string, any>;
}

export interface Decision {
  id: string;
  decision: string;
  reason: string;
  expected_impact: string;
  responsible_team: string;
  eta: number;
  createdAt?: string;
  action_type?: string;
  created_at?: string;
}
