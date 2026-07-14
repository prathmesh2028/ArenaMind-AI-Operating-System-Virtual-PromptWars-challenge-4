/**
 * Shared utility functions used across multiple components.
 * Keeps helper logic DRY and unit-testable outside of React rendering.
 */

/* ------------------------------------------------------------------ */
/*  Value clamping                                                    */
/* ------------------------------------------------------------------ */

/** Clamps `value` to the range [min, max] and rounds to nearest integer. */
export function clampScore(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}

/* ------------------------------------------------------------------ */
/*  Time formatting                                                   */
/* ------------------------------------------------------------------ */

/** Formats an ISO timestamp string to a short "HH:MM:SS" label. */
export function formatTimestamp(isoString: string): string {
  if (!isoString) return "";
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return isoString;
  }
}

/** Formats total seconds into a "MM:SS" stopwatch display string. */
export function formatStopwatch(totalSeconds: number): string {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

/* ------------------------------------------------------------------ */
/*  Priority styling                                                  */
/* ------------------------------------------------------------------ */

/** Returns Tailwind class string for a given priority badge. */
export function getPriorityStyle(priority: string): string {
  switch (priority?.toUpperCase()) {
    case "CRITICAL":
      return "bg-danger/10 border-danger/30 text-danger";
    case "HIGH":
      return "bg-orange-500/10 border-orange-500/30 text-orange-400";
    case "MEDIUM":
      return "bg-warning/10 border-warning/30 text-warning";
    default:
      return "bg-blue-500/10 border-blue-500/30 text-blue-400";
  }
}

/* ------------------------------------------------------------------ */
/*  Health & density colour helpers                                   */
/* ------------------------------------------------------------------ */

import {
  HEALTH_OPTIMAL_THRESHOLD,
  HEALTH_WARNING_THRESHOLD,
  DENSITY_CRITICAL_THRESHOLD,
  DENSITY_WARNING_THRESHOLD,
} from "./constants";

/** Returns Tailwind classes for health-score colouring (text/border/bg). */
export function getHealthColor(score: number): string {
  if (score >= HEALTH_OPTIMAL_THRESHOLD)
    return "text-success border-success/20 bg-success/5";
  if (score >= HEALTH_WARNING_THRESHOLD)
    return "text-warning border-warning/20 bg-warning/5";
  return "text-danger border-danger/20 bg-danger/5";
}

/** Returns SVG stroke class for health-score ring colouring. */
export function getHealthStrokeClass(score: number): string {
  if (score >= HEALTH_OPTIMAL_THRESHOLD) return "stroke-success";
  if (score >= HEALTH_WARNING_THRESHOLD) return "stroke-warning";
  return "stroke-danger";
}

/** Returns gradient + border classes for sector density cards. */
export function getDensityColor(density: number): string {
  if (density >= DENSITY_CRITICAL_THRESHOLD)
    return 'from-danger/10 to-danger/5 border-danger/40 text-danger shadow-[0_0_12px_rgba(244,63,94,0.15)] animate-pulse';
  if (density >= DENSITY_WARNING_THRESHOLD)
    return 'from-warning/10 to-warning/5 border-warning/40 text-warning shadow-[0_0_12px_rgba(245,158,11,0.1)]';
  return "from-success/10 to-success/5 border-success/30 text-success";
}

/** Returns progress-bar fill class for sector density indicators. */
export function getDensityProgressColor(density: number): string {
  if (density >= DENSITY_CRITICAL_THRESHOLD)
    return "bg-danger shadow-[0_0_6px_#f43f5e]";
  if (density >= DENSITY_WARNING_THRESHOLD)
    return "bg-warning shadow-[0_0_6px_#f59e0b]";
  return "bg-success";
}

/* ------------------------------------------------------------------ */
/*  Wait-level styling (food queues, etc.)                            */
/* ------------------------------------------------------------------ */

/** Returns Tailwind classes for queue wait-time severity badges. */
export function getWaitLevelStyle(waitMinutes: number): string {
  if (waitMinutes >= 10) return "text-danger bg-danger/10 border-danger/25";
  if (waitMinutes >= 5) return "text-warning bg-warning/10 border-warning/25";
  return "text-success bg-success/10 border-success/25";
}

/* ------------------------------------------------------------------ */
/*  Text-to-Speech helper                                             */
/* ------------------------------------------------------------------ */

/** Speaks the given text using the Web Speech Synthesis API. */
export function speakText(text: string): void {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/\*\*|\[|\]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

/* ------------------------------------------------------------------ */
/*  Sector coordinate lookup                                          */
/* ------------------------------------------------------------------ */

import { SECTOR_POSITIONS } from "./constants";

/** Returns grid-coordinate percentages for a given sector name. */
export function getSectorCoords(sector: string): { x: string; y: string } {
  return SECTOR_POSITIONS[sector] ?? { x: "50%", y: "50%" };
}
