/**
 * Centralised type definitions shared across the ArenaMind frontend.
 *
 * Domain-model types (User, Incident, etc.) remain in types/stadium.ts.
 * This file contains UI-level shared interfaces that were previously
 * duplicated across multiple page-level and component files.
 */

/* ------------------------------------------------------------------ */
/*  WebSocket Event Shape                                             */
/* ------------------------------------------------------------------ */

/** Raw event payload received over the dashboard WebSocket. */
export interface WsRawEvent {
  id: string;
  topic: string;
  timestamp?: string;
  payload: Record<string, unknown>;
}

/* ------------------------------------------------------------------ */
/*  Timeline / Audit Event                                            */
/* ------------------------------------------------------------------ */

export type TimelineEventType =
  | "raised"
  | "resolved"
  | "info"
  | "warning"
  | "error";

export interface TimelineEvent {
  id: string;
  time: string;
  topic: string;
  source: string;
  message: string;
  type: TimelineEventType;
}

/* ------------------------------------------------------------------ */
/*  Notification Items (Fan & Volunteer)                              */
/* ------------------------------------------------------------------ */

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  read: boolean;
  priority: string;
  type: string;
  created_at: string;
}

/* ------------------------------------------------------------------ */
/*  Chat Message (shared across Copilot, Assistant, Accessibility)    */
/* ------------------------------------------------------------------ */

export interface ChatMessage {
  id: string;
  sender: "user" | "bot";
  text: string;
  timestamp?: Date;
}

/* ------------------------------------------------------------------ */
/*  Dashboard Telemetry Shapes                                        */
/* ------------------------------------------------------------------ */

export interface SectorData {
  sector: string;
  count: number;
  capacity: number;
  density: number;
  status: string;
}

export interface GateData {
  gate: string;
  queueDepth: number;
  serviceRate: number;
  waitTime: number;
  malfunctioning: boolean;
}

/* ------------------------------------------------------------------ */
/*  Fan Portal Shapes                                                 */
/* ------------------------------------------------------------------ */

export interface ParkingItem {
  name: string;
  available_spots: number;
  status: string;
  occupancy_pct: number;
}

export interface TransportItem {
  route: string;
  type: string;
  status: string;
  current_stop: string;
  seats_available: number;
}

/* ------------------------------------------------------------------ */
/*  Prediction & Recommendation                                       */
/* ------------------------------------------------------------------ */

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  status: string;
}

export interface PredictionItem {
  id: string;
  type: string;
  probability: number;
  confidence: number;
  severity: string;
  reasoning: string;
  targetSector: string;
  recommendations: Recommendation[];
}
